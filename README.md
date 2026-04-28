# LinkedIn Faculty Scraper
### AI-powered profile extraction · Patchright + OpenRouter + FastAPI

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Why This Approach Works](#why-this-approach-works)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [First-Run Login (Critical Step)](#first-run-login)
7. [Running the API](#running-the-api)
8. [Using the API](#using-the-api)
9. [Troubleshooting](#troubleshooting)
10. [Project Structure](#project-structure)

---

## Architecture Overview

```
                        ┌─────────────────────────────────────────────┐
                        │             FastAPI  (main.py)              │
                        │   POST /scrape   GET /session/status        │
                        └──────────────────────┬──────────────────────┘
                                               │
                        ┌──────────────────────▼──────────────────────┐
                        │         LinkedInScraper (pipeline)          │
                        │         scraper/linkedin_scraper.py         │
                        └─────────┬──────────────────────┬────────────┘
                                  │                      │
               ┌──────────────────▼──────┐   ┌──────────▼──────────────┐
               │    LinkedInBrowser      │   │      AIExtractor        │
               │  scraper/linkedin_      │   │  extraction/ai_         │
               │  browser.py             │   │  extractor.py           │
               │                         │   │                         │
               │  Patchright + Chrome    │   │  OpenRouter LLM         │
               │  Persistent profile     │   │  (OpenAI-compatible)    │
               │  Stealth JS injection   │   │  Temperature = 0        │
               └──────────┬──────────────┘   └──────────┬──────────────┘
                          │                             │
               ┌──────────▼──────────────────────────────▼──────────────┐
               │              FacultyProfile (Pydantic)                 │
               │              schemas/faculty_schema.py                 │
               │   name · title · affiliation · location · summary      │
               └─────────────────────────────────────────────────────────┘
```

**Data flow for a single scrape:**

```
POST /scrape {"profile": "williamhgates"}
    │
    ▼
build_profile_url()  →  https://www.linkedin.com/in/williamhgates
    │
    ▼
LinkedInBrowser.fetch_page()
    │  opens tab in persistent Chrome context
    │  navigates to profile URL
    │  scrolls page (triggers lazy-loaded sections)
    │  returns page.inner_text("body")  ← clean visible text, no HTML
    │
    ▼
AIExtractor.extract()
    │  trims text to MAX_TEXT_CHARS
    │  sends to OpenRouter with structured extraction prompt
    │  parses JSON response
    │
    ▼
FacultyProfile(**raw_dict)
    │  Pydantic validates / coerces / strips whitespace
    │
    ▼
ScrapeResponse  →  JSON HTTP response
```

---

## Why This Approach Works

### Problem: LinkedIn's Anti-Bot System

LinkedIn runs a sophisticated detection stack that checks:

| Signal | Naive scraper | This system |
|--------|--------------|-------------|
| `navigator.webdriver` flag | `true` (busted immediately) | Removed via init script |
| CDP leak in HTTP headers | Present in plain Playwright | Removed by Patchright |
| Browser binary fingerprint | Chromium (flagged build ID) | Real installed Chrome via `channel="chrome"` |
| Session tokens (li_at, JSESSIONID) | Injected one-time cookies | Full persistent profile |
| localStorage auth tokens | Not present with cookies only | Persisted in profile dir |
| Canvas / WebGL fingerprint | Default Chromium values | Spoofed to Intel GPU |
| Consistent device identity | New random fingerprint each run | Same profile = same fingerprint |
| Request cadence | Instant bot-speed navigation | Human-paced scrolling + random pauses |

### Key Insight: Persistent Profile > Cookie Injection

When you inject cookies (the naive approach), you only restore the HTTP
session layer. LinkedIn also maintains auth state in:
- **localStorage** — stores `voyager` API tokens
- **IndexedDB** — caches user identity data
- **Session fingerprint** — links the session to a specific browser identity

A persistent Chrome user-data directory stores ALL of this. LinkedIn sees
the exact same "browser" on every visit, so it keeps you logged in.

### Why Patchright Over Plain Playwright

Standard Playwright leaks several signals through the Chrome DevTools
Protocol connection that LinkedIn and Cloudflare can detect:

1. **CDP leak** — Playwright's default `--remote-debugging-port` flag is
   detectable via `window.cdc_*` properties
2. **Build ID** — Chromium has a different `CHROME_VERSION` string than
   real Chrome and is on a deny-list at some CDNs
3. **Missing extensions** — real Chrome has PDF viewer + Native Client plugins

Patchright patches all three. Combined with `channel="chrome"` (your real
installed Chrome binary), the resulting browser is indistinguishable from
a human's browser.

### Why `inner_text()` Over Raw HTML

Sending 300KB of raw LinkedIn HTML to an LLM is:
- Expensive (tokens = money)
- Slower (larger context = slower inference)
- Fragile (HTML structure changes with every LinkedIn deploy)

`page.inner_text("body")` returns only visible rendered text — the same
words a human reads. That's all the LLM needs. A typical profile goes from
~250KB HTML to ~8KB clean text, cutting token cost by ~97%.

---

## Prerequisites

- **Windows 10/11** (the setup is tested on Windows; Linux/macOS work too)
- **Python 3.11+** — `python --version`
- **Google Chrome installed** — must be in the default install path
  (`C:\Program Files\Google\Chrome\Application\chrome.exe`)
- **A LinkedIn account** — free account works for public profiles
- **An OpenRouter API key** — get one free at https://openrouter.ai/keys

---

## Installation

### Step 1 — Clone / unzip the project

```
linkedin_faculty_scraper/
├── scraper/
├── extraction/
├── schemas/
├── main.py
├── first_login.py
├── test_scrape.py
├── requirements.txt
└── .env.example
```

### Step 2 — Create a virtual environment

Open a terminal (PowerShell or CMD) in the project folder:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` in your prompt.

### Step 3 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

### Step 4 — Install Patchright's browser binaries

Patchright needs to download its own browser patches on top of your
Chrome binary:

```powershell
patchright install chrome
```

> **Note:** This does NOT replace your personal Chrome. It installs
> patched files into the Patchright package directory only.

If Chrome is not in the default path you may see an error like
`Executable doesn't exist`. Fix:

```powershell
# Tell Patchright where Chrome is
set CHROME_EXECUTABLE_PATH=C:\path\to\chrome.exe
patchright install chrome
```

---

## Configuration

Copy the example env file and fill in your values:

```powershell
copy .env.example .env
```

Open `.env` in any text editor:

```env
# REQUIRED: Your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Model — gpt-4o-mini is cheap and accurate enough for extraction
OPENROUTER_MODEL=openai/gpt-4o-mini

# Leave false for now — change to true AFTER first_login.py succeeds
HEADLESS=false

# Where to store the Chrome session (do not change unless needed)
PROFILE_DIR=./chrome_profile
```

---

## First-Run Login

> **This is the most important step.** Do it once; never repeat it.

```powershell
python first_login.py
```

What happens:
1. A visible Chrome window opens at `https://www.linkedin.com/login`
2. Log in normally — use your username + password
3. If LinkedIn shows a CAPTCHA or 2FA prompt, complete it
4. The script polls for a successful session every 3 seconds
5. When it detects you're logged in, it prints **✓ Login successful!** and exits
6. The full browser session is saved to `./chrome_profile/`

**You will never need to log in again** unless:
- You manually delete `./chrome_profile/`
- LinkedIn forces re-authentication after ~30-90 days of inactivity
- You run from a different machine (profiles are machine-specific)

When any of those happen, just run `python first_login.py` again.

---

## Running the API

### Quick smoke test (no server needed)

```powershell
python test_scrape.py williamhgates
```

Expected output:
```
[browser] Profile directory: C:\...\chrome_profile
[auth] ✓ Already logged in (persistent profile).
[browser] Fetching: https://www.linkedin.com/in/williamhgates
[browser] Captured 9,842 characters of visible text.
[extractor] Using model: openai/gpt-4o-mini
[extractor] Raw LLM response (215 chars): {"name": "Bill Gates", ...
[scraper] ✓ Validated profile for: 'Bill Gates'

============================================================
  Extracted Profile
============================================================
{
  "name": "Bill Gates",
  "title": "Co-chair, Bill & Melinda Gates Foundation",
  "affiliation": "Bill & Melinda Gates Foundation",
  "location": "Seattle, Washington, United States",
  "summary": "Co-chair of the Bill & Melinda Gates Foundation...",
  "confidence": 0.95,
  "error": null
}
```

### Start the FastAPI server

```powershell
# Option A: direct
python main.py

# Option B: uvicorn (recommended for production)
uvicorn main:app --host 127.0.0.1 --port 8000
```

The server boots, opens Chrome (or reuses the existing session if
`HEADLESS=true`), and prints:

```
[startup] Initialising browser and AI extractor…
[auth] ✓ Already logged in (persistent profile).
[startup] ✓ Ready.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Interactive API docs: http://127.0.0.1:8000/docs

---

## Using the API

### Scrape a single profile

```powershell
curl -X POST http://127.0.0.1:8000/scrape `
     -H "Content-Type: application/json" `
     -d '{"profile": "williamhgates"}'
```

Or with Python:

```python
import httpx, json

resp = httpx.post(
    "http://127.0.0.1:8000/scrape",
    json={"profile": "williamhgates"},
    timeout=60,
)
print(json.dumps(resp.json(), indent=2))
```

Response:

```json
{
  "success": true,
  "profile_url": "https://www.linkedin.com/in/williamhgates",
  "data": {
    "name": "Bill Gates",
    "title": "Co-chair, Bill & Melinda Gates Foundation",
    "affiliation": "Bill & Melinda Gates Foundation",
    "location": "Seattle, Washington, United States",
    "summary": "...",
    "confidence": 0.95,
    "error": null
  },
  "error": null
}
```

### Scrape a batch of profiles

```python
profiles = ["williamhgates", "jeffweiner", "satyanadella"]

resp = httpx.post(
    "http://127.0.0.1:8000/scrape/batch",
    json=profiles,
    timeout=300,
)
for item in resp.json():
    print(item["data"]["name"], "—", item["data"]["title"])
```

> Batch scrapes run sequentially with a 3-second delay between profiles
> to avoid rate limiting.

### Check session status

```powershell
curl http://127.0.0.1:8000/session/status
# {"logged_in": true}
```

---

## Troubleshooting

### "Executable doesn't exist at … chrome.exe"

Patchright can't find your Chrome installation.

```powershell
# Find where Chrome is
where chrome
# Then tell Patchright:
set CHROME_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
patchright install chrome
```

### "Auth-wall detected" error from /scrape

The LinkedIn session expired. Fix:

```powershell
# Set HEADLESS=false in .env first, then:
python first_login.py
```

### Chrome won't start ("Target page, context or browser has been closed")

Another Chrome process using the same `--user-data-dir` is running.
Close all Chrome windows and try again. If you need Chrome open while
scraping, change `PROFILE_DIR` in `.env` to a different path.

### LLM returns null for all fields

1. Check `OPENROUTER_API_KEY` is correct (test at https://openrouter.ai)
2. Try a stronger model: `OPENROUTER_MODEL=openai/gpt-4o`
3. Check the visible text length — if < 500 chars, the page likely wasn't
   fully loaded. Increase `NAV_TIMEOUT_MS=90000`.

### LinkedIn shows a CAPTCHA during first_login.py

Just solve it manually in the browser window. The script will keep
polling and detect your successful login automatically.

### "patchright: command not found" after pip install

```powershell
# Make sure the venv is activated
.venv\Scripts\activate
# Verify install
python -m patchright install chrome
```

---

## Project Structure

```
linkedin_faculty_scraper/
│
├── scraper/
│   ├── __init__.py
│   ├── linkedin_browser.py     # Persistent Chrome + stealth + auth
│   └── linkedin_scraper.py     # Pipeline orchestration
│
├── extraction/
│   ├── __init__.py
│   └── ai_extractor.py         # OpenRouter / LLM integration
│
├── schemas/
│   ├── __init__.py
│   └── faculty_schema.py       # Pydantic models + API schemas
│
├── chrome_profile/             # Created on first run — DO NOT delete
│   └── ...                     # Chrome session, cookies, localStorage
│
├── main.py                     # FastAPI app (startup, routes)
├── first_login.py              # One-time manual login helper
├── test_scrape.py              # CLI smoke test
├── requirements.txt
├── .env.example
└── .env                        # Your secrets — DO NOT commit to git
```

### Adding new extraction fields

1. Add the field to `schemas/faculty_schema.py` → `FacultyProfile`
2. Update the prompt in `extraction/ai_extractor.py` → `_USER_TEMPLATE`
3. That's it — Pydantic validation and FastAPI docs update automatically.

---

## Security Notes

- Never commit `.env` or `chrome_profile/` to git — both contain session secrets.
- The `chrome_profile/` directory contains your LinkedIn `li_at` cookie, which
  is equivalent to your password. Treat it accordingly.
- Add both to `.gitignore`:
  ```
  .env
  chrome_profile/
  ```
