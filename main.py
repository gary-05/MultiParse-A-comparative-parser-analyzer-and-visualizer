from grammar import Grammar
from first_follow import FirstFollow
from ll1_table import LL1Table
from parser import LL1Parser
from lr0_engine import LR0Engine, LR0Item
from lr0_table import LR0Table
from slr1_table import SLR1Table
from slr1_parser import SLR1Parser

# -------- Grammar Input --------
def input_grammar(grammar):
    print("\nEnter grammar productions (type 'done' when finished)")
    print("Example: E -> T E' | id")

    while True:
        line = input("Production: ")

        if line.lower() == "done":
            break

        lhs, rhs = line.split("->")
        lhs = lhs.strip()
        rhs_list = [r.strip() for r in rhs.split("|")]
        grammar.add_production(lhs, rhs_list)


def main():
    grammar = Grammar()
    input_grammar(grammar)
    grammar.display()

    # -------- FIRST & FOLLOW --------
    ff = FirstFollow(grammar)
    ff.compute_first()
    ff.compute_follow()
    ff.display()

    # -------- LL(1) --------
    table = LL1Table(grammar, ff.first, ff.follow)
    table.build_table()
    table.display()

    parser = LL1Parser(grammar, table.table)
    input_string = input("\nEnter input string for LL(1) parsing (space separated): ")
    parser.parse(input_string)

    # -------- LR(0) Engine --------
    print("\n--- LR(0) Closure Test ---")
    engine = LR0Engine(grammar)
    engine.augment_grammar()

    start_symbol = grammar.start_symbol
    start_prod = grammar.productions[start_symbol][0]
    start_item = LR0Item(start_symbol, start_prod, 0)
    closure_items = engine.closure({start_item})

    order = {nt: i for i, nt in enumerate(grammar.productions)}

    print("\nInitial LR(0) Closure:")
    for item in _sorted_items(closure_items, grammar, order):
        print(item)

    print("\n--- LR(0) GOTO Test ---")
    symbols = sorted(grammar.terminals.union(grammar.non_terminals))
    for sym in symbols:
        goto_state = engine.goto(closure_items, sym)
        if goto_state:
            print(f"\nGOTO(I0, {sym})")
            for item in _sorted_items(goto_state, grammar, order):
                print(item)

    print("\n--- LR(0) Canonical Collection ---")
    states, transitions = engine.build_canonical_collection()
    for i, state in enumerate(states):
        print(f"\nState I{i}")
        for item in _sorted_items(set(state), grammar, order):
            print(item)

    print("\n--- LR(0) DFA Transitions ---")
    for (state, symbol), target in transitions.items():
        print(f"I{state} --{symbol}--> I{target}")

    # -------- LR(0) Table --------
    print("\n--- LR(0) Parsing Table ---")
    lr_table = LR0Table(grammar, states, transitions)
    lr_table.build_table()
    lr_table.display()

    # -------- SLR(1) Table --------
    print("\n--- SLR(1) Parsing Table ---")
    slr_table = SLR1Table(grammar, states, transitions, ff.follow)
    slr_table.build_table()
    slr_table.display()

    # -------- SLR(1) Parser --------
    slr_parser = SLR1Parser(grammar, slr_table.action, slr_table.goto)
    input_string = input("\nEnter input string for SLR(1) parsing (space separated): ")
    slr_parser.parse(input_string)

    # -------- LR(0) vs SLR(1) Comparison --------
    print("\n--- LR(0) vs SLR(1) Comparison ---")
    lr0_conflicts = _find_lr0_conflicts(lr_table)
    slr1_conflicts = slr_table.conflicts

    print(f"LR(0) conflicts : {len(lr0_conflicts)}")
    print(f"SLR(1) conflicts: {len(slr1_conflicts)}")

    if lr0_conflicts and not slr1_conflicts:
        print("→ Grammar is NOT LR(0) but IS SLR(1). SLR(1) resolved the conflicts.")
    elif not lr0_conflicts and not slr1_conflicts:
        print("→ Grammar is both LR(0) and SLR(1).")
    elif slr1_conflicts:
        print("→ Grammar is neither LR(0) nor SLR(1).")


def _sorted_items(items, grammar, order):
    return sorted(
        items,
        key=lambda x: (
            0 if x.lhs == grammar.start_symbol else 1,
            order.get(x.lhs, 100),
            " ".join(x.rhs)
        )
    )


def _find_lr0_conflicts(lr_table):
    seen = {}
    conflicts = []
    for (state, terminal), action in lr_table.action.items():
        key = (state, terminal)
        if key in seen and seen[key] != action:
            conflicts.append(key)
        seen[key] = action
    return conflicts


if __name__ == "__main__":
    main()