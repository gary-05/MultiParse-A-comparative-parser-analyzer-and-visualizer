import streamlit as st
import sys
import os
import pandas as pd
import copy

# Allow importing from the same directory
sys.path.insert(0, os.path.dirname(__file__))

from grammar import Grammar
from first_follow import FirstFollow
from ll1_table import LL1Table
from parser import LL1Parser
from lr0_engine import LR0Engine, LR0Item
from lr0_table import LR0Table
from slr1_table import SLR1Table
from slr1_parser import SLR1Parser
from lr1_engine import LR1Engine
from clr_table import CLRTable
from lalr_table import LALRTable

# ─────────────────────────────────────────────
st.set_page_config(page_title="Parser Visualizer", layout="wide")
st.title("🔍 Parser Visualizer")
st.caption("LL(1) · LR(0) · SLR(1) · CLR(1) · LALR(1) — interactive grammar analysis")

# ─────────────────────────────────────────────
# SIDEBAR — Grammar Input
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("📝 Grammar Input")

    default_grammar = """E -> T E'
E' -> + T E' | ε
T -> F T'
T' -> * F T' | ε
F -> ( E ) | id"""

    grammar_text = st.text_area(
        "Enter productions (one per line, use | for alternatives):",
        value=default_grammar,
        height=200,
    )

    st.markdown("**Format:** `LHS -> RHS1 | RHS2`  \nUse `ε` for epsilon.")

    parse_input = st.text_input(
        "Input string to parse (space-separated):",
        value="id + id * id",
    )

    run = st.button("▶ Run Analysis", type="primary", use_container_width=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def build_grammar(text):
    g = Grammar()
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or "->" not in line:
            continue
        lhs, rhs = line.split("->", 1)
        lhs = lhs.strip()
        rhs_list = [r.strip() for r in rhs.split("|")]
        g.add_production(lhs, rhs_list)
    return g


def sorted_items(items, grammar, order):
    return sorted(
        items,
        key=lambda x: (
            0 if x.lhs == grammar.start_symbol else 1,
            order.get(x.lhs, 100),
            " ".join(x.rhs),
        ),
    )


def capture_ll1_trace(grammar, table_obj, input_string):
    from parse_tree import TreeNode

    rows = []
    root = TreeNode(grammar.start_symbol)
    stack = [("$", None), (grammar.start_symbol, root)]
    tokens = input_string.split() + ["$"]

    accepted = False

    while stack:
        top_sym, top_node = stack[-1]
        current = tokens[0]
        stack_str = " ".join(s for s, _ in stack)
        inp_str = " ".join(tokens)

        if top_sym == current == "$":
            rows.append([stack_str, inp_str, "✅ ACCEPT"])
            accepted = True
            break
        elif top_sym in grammar.terminals or top_sym == "$":
            if top_sym == current:
                rows.append([stack_str, inp_str, f"Match '{top_sym}'"])
                stack.pop()
                tokens.pop(0)
            else:
                rows.append([stack_str, inp_str, "❌ ERROR"])
                break
        else:
            if current in table_obj.table.get(top_sym, {}):
                prod = table_obj.table[top_sym][current]
                rows.append([stack_str, inp_str, f"{top_sym} → {' '.join(prod)}"])
                stack.pop()
                if prod != ["ε"]:
                    child_nodes = [TreeNode(s) for s in prod]
                    for child in child_nodes:
                        top_node.add_child(child)
                    for s, n in reversed(list(zip(prod, child_nodes))):
                        stack.append((s, n))
                else:
                    top_node.add_child(TreeNode("ε"))
            else:
                rows.append([stack_str, inp_str, "❌ ERROR"])
                break

    tree_lines = []
    if accepted:
        import io, sys
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        root.print_tree()
        sys.stdout = old_stdout
        tree_lines = buf.getvalue().splitlines()

    return rows, tree_lines


def capture_slr1_trace(grammar, action, goto_table, input_string):
    from parse_tree import TreeNode
    import io, sys

    rows = []
    tokens = input_string.split() + ["$"]
    state_stack = [0]
    symbol_stack = ["$"]
    node_stack = [None]
    pos = 0
    accepted = False

    while True:
        state = state_stack[-1]
        current = tokens[pos]
        state_str = " ".join(str(s) for s in state_stack)
        sym_str = " ".join(symbol_stack)
        inp_str = " ".join(tokens[pos:])
        act = action.get((state, current))

        if act is None:
            rows.append([state_str, sym_str, inp_str, "❌ ERROR"])
            break
        elif act == "acc":
            rows.append([state_str, sym_str, inp_str, "✅ ACCEPT"])
            accepted = True
            break
        elif act.startswith("s"):
            next_state = int(act[1:])
            rows.append([state_str, sym_str, inp_str, f"Shift → s{next_state}"])
            state_stack.append(next_state)
            symbol_stack.append(current)
            node_stack.append(TreeNode(current))
            pos += 1
        elif act.startswith("r"):
            rule_str = act[2:-1]
            arrow = rule_str.index("->")
            lhs = rule_str[:arrow].strip()
            rhs_str = rule_str[arrow + 2:].strip()
            rhs = rhs_str.split() if rhs_str != "ε" else []
            rows.append([state_str, sym_str, inp_str, f"Reduce: {rule_str}"])
            parent = TreeNode(lhs)
            if rhs:
                children = []
                for _ in rhs:
                    state_stack.pop()
                    symbol_stack.pop()
                    children.append(node_stack.pop())
                for child in reversed(children):
                    parent.add_child(child)
            else:
                parent.add_child(TreeNode("ε"))
            symbol_stack.append(lhs)
            top_state = state_stack[-1]
            gs = goto_table.get((top_state, lhs))
            if gs is None:
                rows.append([state_str, sym_str, inp_str, "❌ GOTO ERROR"])
                break
            state_stack.append(gs)
            node_stack.append(parent)
        else:
            rows.append([state_str, sym_str, inp_str, f"❌ Unknown: {act}"])
            break

    tree_lines = []
    if accepted and len(node_stack) > 1:
        root = node_stack[-1]
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        root.print_tree()
        sys.stdout = old_stdout
        tree_lines = buf.getvalue().splitlines()

    return rows, tree_lines


def capture_lr_trace(grammar, action, goto_table, input_string):
    """Helper to capture trace for any LR-based parser."""
    return capture_slr1_trace(grammar, action, goto_table, input_string)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if not run:
    st.info("👈 Enter a grammar in the sidebar and click **Run Analysis**.")
    st.stop()

try:
    grammar = build_grammar(grammar_text)
    errors, warnings = grammar.validate()
    
    if warnings:
        for w in warnings:
            st.warning(f"⚠ {w}")
    
    if errors:
        for e in errors:
            st.error(f"❌ {e}")
        st.stop()

except Exception as e:
    st.error(f"Grammar parse error: {e}")
    st.stop()

# Tabs
tab_grammar, tab_ff, tab_ll1, tab_lr0, tab_slr1, tab_clr, tab_lalr, tab_compare = st.tabs([
    "Grammar", "FIRST / FOLLOW", "LL(1)", "LR(0)", "SLR(1)", "CLR(1)", "LALR(1)", "Comparison"
])

order = {nt: i for i, nt in enumerate(grammar.productions)}

# ── FIRST / FOLLOW ──────────────────────────
ff = FirstFollow(grammar)
ff.compute_first()
ff.compute_follow()

# ── LL(1) Table ──────────────────────────────
ll1_table = LL1Table(grammar, ff.first, ff.follow)
ll1_table.build_table()

# Save original grammar state for display BEFORE augment_grammar() mutates it
original_grammar_data = {
    "productions": copy.deepcopy(grammar.productions),
    "non_terminals": copy.deepcopy(grammar.non_terminals),
    "terminals": copy.deepcopy(grammar.terminals),
    "start_symbol": grammar.start_symbol
}
original_start = grammar.start_symbol

# ── LR(0) ────────────────────────────────────
engine = LR0Engine(grammar)
engine.augment_grammar()
states, transitions = engine.build_canonical_collection()

lr0_table = LR0Table(grammar, states, transitions)
lr0_table.build_table()

# ── SLR(1) ───────────────────────────────────
slr1 = SLR1Table(grammar, states, transitions, ff.follow)
slr1.build_table()

# ── LR(1) / CLR / LALR ───────────────────────
with st.spinner("Building LR(1) states (this can take a moment)..."):
    lr1_engine = LR1Engine(grammar, ff.first)
    lr1_states, lr1_transitions = lr1_engine.build_canonical_collection()

    clr_table = CLRTable(grammar, lr1_states, lr1_transitions)
    clr_table.build_table()

    lalr_table = LALRTable(grammar, lr1_states, lr1_transitions)
    lalr_table.build_table()


# ════════════════════════════════════════════
# TAB: Grammar
# ════════════════════════════════════════════
with tab_grammar:
    st.subheader("Grammar Productions")
    rows = []
    for lhs, prods in original_grammar_data["productions"].items():
        for rhs in prods:
            rows.append({"LHS": lhs, "→": " ".join(rhs)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Non-terminals", len(original_grammar_data["non_terminals"]))
    col2.metric("Terminals", len(original_grammar_data["terminals"]))
    col3.metric("Productions", sum(len(v) for v in original_grammar_data["productions"].values()))


# ════════════════════════════════════════════
# TAB: FIRST / FOLLOW
# ════════════════════════════════════════════
with tab_ff:
    st.subheader("FIRST and FOLLOW Sets")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**FIRST Sets**")
        ff_rows = [{"Non-terminal": nt, "FIRST": ", ".join(sorted(ff.first[nt]))}
                   for nt in sorted(ff.first)]
        st.dataframe(pd.DataFrame(ff_rows), use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**FOLLOW Sets**")
        follow_rows = [{"Non-terminal": nt, "FOLLOW": ", ".join(sorted(ff.follow[nt]))}
                       for nt in sorted(ff.follow)]
        st.dataframe(pd.DataFrame(follow_rows), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════
# TAB: LL(1)
# ════════════════════════════════════════════
with tab_ll1:
    st.subheader("LL(1) Parsing Table")
    st.info("💡 **LL(1) (Top-Down)**: Uses 1 token of lookahead and the **FIRST/FOLLOW** sets to predict the next production. It cannot handle left-recursive or ambiguous grammars.")

    terminals = sorted(grammar.terminals) + ["$"]
    non_terminals_ll1 = [nt for nt in grammar.non_terminals
                         if nt in ll1_table.table]

    table_data = {}
    for t in terminals:
        col_data = {}
        for nt in non_terminals_ll1:
            cell = ll1_table.table.get(nt, {}).get(t, "")
            if cell:
                cell = " ".join(cell)
            col_data[nt] = cell
        table_data[t] = col_data

    df_ll1 = pd.DataFrame(table_data, index=non_terminals_ll1)
    st.dataframe(df_ll1, use_container_width=True)

    if ll1_table.conflicts:
        st.error(f"⚠ {len(ll1_table.conflicts)} conflict(s) — grammar is NOT LL(1)")
        for lhs, t in ll1_table.conflicts:
            st.write(f"  Conflict at M[{lhs}, {t}]")
    else:
        st.success("✓ No conflicts — grammar IS LL(1)")

    st.subheader("LL(1) Parse Trace")
    st.caption(f"Input: `{parse_input}`")
    ll1_grammar_copy = copy.deepcopy(grammar)
    ll1_grammar_copy.start_symbol = original_start
    # Remove augmented symbol so LL(1) trace doesn't see it
    ll1_grammar_copy.non_terminals.discard(original_start + "''")
    trace, ll1_tree_lines = capture_ll1_trace(ll1_grammar_copy, ll1_table, parse_input)
    df_trace = pd.DataFrame(trace, columns=["Stack", "Input", "Action"])
    st.dataframe(df_trace, use_container_width=True, hide_index=True)

    if ll1_tree_lines:
        st.subheader("LL(1) Parse Tree")
        st.code("\n".join(ll1_tree_lines), language=None)


# ════════════════════════════════════════════
# TAB: LR(0)
# ════════════════════════════════════════════
with tab_lr0:
    st.subheader("LR(0) Canonical Collection")
    st.info("💡 **LR(0) (Bottom-Up)**: The simplest LR parser. It uses a **DFA of item sets** to track the state. It reduces without looking at the next token, which often leads to shift-reduce conflicts.")

    for i, state in enumerate(states):
        with st.expander(f"State I{i}"):
            items_str = [str(item) for item in sorted_items(set(state), grammar, order)]
            for s in items_str:
                st.code(s)

    st.subheader("LR(0) DFA Transitions")
    trans_rows = [{"From": f"I{s}", "Symbol": sym, "To": f"I{t}"}
                  for (s, sym), t in sorted(transitions.items())]
    st.dataframe(pd.DataFrame(trans_rows), use_container_width=True, hide_index=True)

    st.subheader("LR(0) Parsing Table")
    terminals_lr = sorted(grammar.terminals) + ["$"]
    nts_lr = sorted(grammar.non_terminals - {grammar.start_symbol})

    lr0_rows = []
    for i in range(len(states)):
        row = {"State": i}
        for t in terminals_lr:
            row[t] = lr0_table.action.get((i, t), "")
        for nt in nts_lr:
            row[nt] = lr0_table.goto.get((i, nt), "")
        lr0_rows.append(row)

    df_lr0 = pd.DataFrame(lr0_rows).set_index("State")
    st.dataframe(df_lr0, use_container_width=True)


# ════════════════════════════════════════════
# TAB: SLR(1)
# ════════════════════════════════════════════
with tab_slr1:
    st.subheader("SLR(1) Parsing Table")
    st.info("💡 **SLR(1) (Simple LR)**: An improvement over LR(0) that uses the **FOLLOW set** of the LHS to decide when to reduce, significantly reducing the number of conflicts.")

    slr_rows = []
    for i in range(len(states)):
        row = {"State": i}
        for t in terminals_lr:
            row[t] = slr1.action.get((i, t), "")
        for nt in nts_lr:
            row[nt] = slr1.goto.get((i, nt), "")
        slr_rows.append(row)

    df_slr1 = pd.DataFrame(slr_rows).set_index("State")
    st.dataframe(df_slr1, use_container_width=True)

    if slr1.conflicts:
        st.error(f"⚠ {len(slr1.conflicts)} conflict(s) — grammar is NOT SLR(1)")
        for state, terminal, old, new in slr1.conflicts:
            st.write(f"  State {state}, '{terminal}': `{old}` vs `{new}`")
    else:
        st.success("✓ No conflicts — grammar IS SLR(1)")

    st.subheader("SLR(1) Parse Trace")
    st.caption(f"Input: `{parse_input}`")
    slr_trace, slr_tree_lines = capture_slr1_trace(grammar, slr1.action, slr1.goto, parse_input)
    df_slr_trace = pd.DataFrame(slr_trace, columns=["State Stack", "Symbol Stack", "Input", "Action"])
    st.dataframe(df_slr_trace, use_container_width=True, hide_index=True)

    if slr_tree_lines:
        st.subheader("SLR(1) Parse Tree")
        st.code("\n".join(slr_tree_lines), language=None)


# ════════════════════════════════════════════
# TAB: CLR(1)
# ════════════════════════════════════════════
with tab_clr:
    st.subheader("CLR(1) Parsing Table")
    st.info("💡 **CLR(1) (Canonical LR)**: The most powerful LR parser. It uses specific **lookahead symbols** for each item in a state, allowing it to distinguish between states that SLR(1) merges incorrectly.")

    clr_rows = []
    for i in range(len(lr1_states)):
        row = {"State": i}
        for t in terminals_lr:
            row[t] = clr_table.action.get((i, t), "")
        for nt in nts_lr:
            row[nt] = clr_table.goto.get((i, nt), "")
        clr_rows.append(row)

    df_clr = pd.DataFrame(clr_rows).set_index("State")
    st.dataframe(df_clr, use_container_width=True)

    if clr_table.conflicts:
        st.error(f"⚠ {len(clr_table.conflicts)} conflict(s) — grammar is NOT CLR(1)")
        for state, terminal, old, new in clr_table.conflicts:
            st.write(f"  State {state}, '{terminal}': `{old}` vs `{new}`")
    else:
        st.success("✓ No conflicts — grammar IS CLR(1)")

    st.subheader("CLR(1) Parse Trace")
    st.caption(f"Input: `{parse_input}`")
    clr_trace, clr_tree_lines = capture_lr_trace(grammar, clr_table.action, clr_table.goto, parse_input)
    df_clr_trace = pd.DataFrame(clr_trace, columns=["State Stack", "Symbol Stack", "Input", "Action"])
    st.dataframe(df_clr_trace, use_container_width=True, hide_index=True)

    if clr_tree_lines:
        st.subheader("CLR(1) Parse Tree")
        st.code("\n".join(clr_tree_lines), language=None)


# ════════════════════════════════════════════
# TAB: LALR(1)
# ════════════════════════════════════════════
with tab_lalr:
    st.subheader("LALR(1) Parsing Table")
    st.info("💡 **LALR(1) (Lookahead LR)**: A middle ground between SLR(1) and CLR(1). It **merges states** with the same LR(0) core from the CLR(1) collection, resulting in a table as small as SLR(1) but nearly as powerful as CLR(1).")

    lalr_rows = []
    for i in range(len(lalr_table.states)):
        row = {"State": i}
        for t in terminals_lr:
            row[t] = lalr_table.action.get((i, t), "")
        for nt in nts_lr:
            row[nt] = lalr_table.goto.get((i, nt), "")
        lalr_rows.append(row)

    df_lalr = pd.DataFrame(lalr_rows).set_index("State")
    st.dataframe(df_lalr, use_container_width=True)

    if lalr_table.conflicts:
        st.error(f"⚠ {len(lalr_table.conflicts)} conflict(s) — grammar is NOT LALR(1)")
        for state, terminal, old, new in lalr_table.conflicts:
            st.write(f"  State {state}, '{terminal}': `{old}` vs `{new}`")
    else:
        st.success("✓ No conflicts — grammar IS LALR(1)")

    st.subheader("LALR(1) Parse Trace")
    st.caption(f"Input: `{parse_input}`")
    lalr_trace, lalr_tree_lines = capture_lr_trace(grammar, lalr_table.action, lalr_table.goto, parse_input)
    df_lalr_trace = pd.DataFrame(lalr_trace, columns=["State Stack", "Symbol Stack", "Input", "Action"])
    st.dataframe(df_lalr_trace, use_container_width=True, hide_index=True)

    if lalr_tree_lines:
        st.subheader("LALR(1) Parse Tree")
        st.code("\n".join(lalr_tree_lines), language=None)


# ════════════════════════════════════════════
# TAB: Comparison
# ════════════════════════════════════════════
with tab_compare:
    st.subheader("LL(1) vs LR(0) vs SLR(1) — Comparison")

    ll1_ok = len(ll1_table.conflicts) == 0
    lr0_ok = True
    slr1_ok = len(slr1.conflicts) == 0
    clr_ok = len(clr_table.conflicts) == 0
    lalr_ok = len(lalr_table.conflicts) == 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("LL(1)", "✅ Yes" if ll1_ok else "❌ No", "Conflicts: " + str(len(ll1_table.conflicts)))
    col2.metric("SLR(1)", "✅ Yes" if slr1_ok else "❌ No", "Conflicts: " + str(len(slr1.conflicts)))
    col3.metric("LALR(1)", "✅ Yes" if lalr_ok else "❌ No", "Conflicts: " + str(len(lalr_table.conflicts)))
    col4.metric("CLR(1)", "✅ Yes" if clr_ok else "❌ No", "Conflicts: " + str(len(clr_table.conflicts)))
    col5.metric("States", f"{len(lr1_states)} (LR1)", f"{len(lalr_table.states)} (LALR)")

    st.markdown("---")
    st.markdown("""
| Property | LL(1) | SLR(1) | LALR(1) | CLR(1) |
|---|---|---|---|---|
| Parsing | Top-down | Bottom-up | Bottom-up | Bottom-up |
| Lookahead | 1 (FIRST) | FOLLOW set | Lookahead symbols | Lookahead symbols |
| States | Small | Small (LR0) | Small (LR0 kernels) | Large (Exploded) |
| Power | Weakest | Stronger than LR(0) | Stronger than SLR | Most Powerful |
| Conflict Res. | FIRST/FOLLOW | FOLLOW(A) | Item-specific LA | Item-specific LA |
| Complexity | Low | Medium | High | Very High |
""")

    if slr1_ok and not ll1_ok:
        st.info("💡 This grammar is SLR(1) but not LL(1) — a common case for left-recursive or ambiguous-looking grammars.")
    elif ll1_ok and slr1_ok:
        st.success("🎉 Grammar is both LL(1) and SLR(1).")
    elif not slr1_ok:
        st.warning("⚠ Grammar is neither LL(1) nor SLR(1). Consider LALR(1) or GLR parsing.")

    st.subheader("Reduce Action Coverage")
    st.caption("SLR(1) reduces only on FOLLOW(A), while LR(0) reduces on all terminals — fewer reduce entries = fewer conflicts.")

    coverage_rows = []
    for lhs in grammar.productions:
        if lhs == grammar.start_symbol:
            continue
        follow_size = len(ff.follow.get(lhs, set()))
        all_terms = len(grammar.terminals) + 1  # +1 for $
        coverage_rows.append({
            "Non-terminal": lhs,
            "FOLLOW size": follow_size,
            "All terminals": all_terms,
            "SLR(1) reduces on": follow_size,
            "LR(0) reduces on": all_terms,
        })

    if coverage_rows:
        st.dataframe(pd.DataFrame(coverage_rows), use_container_width=True, hide_index=True)