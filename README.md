# 🚀 Multiparse – Comparative Parser Analyzer and Visualizer

Multiparse is a compiler design project that implements and compares multiple parsing techniques within a unified framework. It helps visualize how different parsers work internally through grammar analysis, parsing table generation, state construction, and parsing simulation.

The project bridges theoretical compiler concepts with practical implementation, making parser design easier to understand for students and learners.

---

## 📌 Project Objective

Parsing is one of the most important phases of a compiler. However, understanding the differences between top-down and bottom-up parsing methods can be difficult when studied only through theory.

Multiparse provides a hands-on environment to explore and compare different parser families through implementation and analysis.

---

## ✨ Key Features

- Multiple parser implementations in one project
- FIRST and FOLLOW set computation
- Parsing table generation
- Grammar conflict detection
- Stack-based parsing simulation
- Canonical state generation
- Comparative analysis of parser techniques
- Educational visualization of parsing workflow

---

## 🧠 Parsing Techniques Implemented

### 🔹 LL(1) Parser
Top-down predictive parser using FIRST and FOLLOW sets.

**Includes:**
- Predictive parsing table
- Stack simulation
- Grammar validation
- Conflict detection

---

### 🔹 LR(0) Parser
Basic bottom-up shift-reduce parser using LR(0) items.

**Includes:**
- Grammar augmentation
- Closure and GOTO
- Canonical LR(0) states
- Parsing actions

---

### 🔹 SLR(1) Parser
Improved LR(0) parser using FOLLOW sets for reductions.

**Includes:**
- LR(0) state reuse
- FOLLOW-based reduce actions
- Reduced conflicts compared to LR(0)

---

### 🔹 CLR(1) Parser (Canonical LR)

More powerful parser using LR(1) items with lookahead symbols.

**Includes:**
- Canonical LR(1) states
- Lookahead-based reductions
- Handles larger class of grammars

---

### 🔹 LALR(1) Parser

Optimized version of CLR(1) by merging similar LR(1) states.

**Includes:**
- Reduced number of states
- Memory-efficient tables
- Commonly used in parser generators

---

## ⚙️ Core Modules

### 1️⃣ Grammar Module
- Stores grammar productions
- Detects terminals and non-terminals
- Handles start symbol

### 2️⃣ FIRST & FOLLOW Module
- Iterative fixed-point computation
- Epsilon handling
- Used in LL(1) and SLR(1)

### 3️⃣ LL(1) Engine
- Table construction
- Predictive parsing
- Input validation

### 4️⃣ LR Family Engines
- Closure / GOTO computation
- Canonical state generation
- Shift-reduce parsing

### 5️⃣ Comparative Analyzer
- Number of states comparison
- Table size comparison
- Conflict analysis
- Parser power comparison

---

## 📊 Comparison Covered

| Parser Type | Parsing Style | Power | States |
|------------|--------------|-------|--------|
| LL(1) | Top-Down | Basic | Low |
| LR(0) | Bottom-Up | Moderate | Medium |
| SLR(1) | Bottom-Up | Better | Medium |
| CLR(1) | Bottom-Up | High | High |
| LALR(1) | Bottom-Up | High | Medium |

---

## 🛠️ Tech Stack

- Python
- Compiler Design Concepts
- Data Structures & Algorithms
- Git & GitHub

---

## 🎯 Use Cases

- Compiler Design Mini Project
- Educational Parser Visualizer
- Grammar Analysis Tool
- Learning Top-down vs Bottom-up Parsing
- Academic Demonstration Project

---

## ▶️ How to Run

```bash
python main.py
