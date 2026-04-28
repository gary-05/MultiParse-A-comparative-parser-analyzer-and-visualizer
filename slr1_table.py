class SLR1Table:
    def __init__(self, grammar, states, transitions, follow):
        self.grammar = grammar
        self.states = states
        self.transitions = transitions
        self.follow = follow

        self.action = {}
        self.goto = {}
        self.conflicts = []

    def build_table(self):
        self.productions_list = []
        for lhs in self.grammar.productions:
            for rhs in self.grammar.productions[lhs]:
                self.productions_list.append((lhs, rhs))

        for i, state in enumerate(self.states):
            state = set(state)

            for item in state:

                # ACCEPT
                if (item.lhs == self.grammar.start_symbol and
                        item.dot == len(item.rhs)):
                    self.action[(i, "$")] = "acc"

                # REDUCE — only on FOLLOW(lhs)
                # Also handle epsilon: rhs==['ε'] with dot=0 counts as a complete item
                elif item.dot == len(item.rhs) or item.rhs == ['ε']:
                    # Skip augmented start symbol — handled by ACCEPT, not reduce
                    if item.lhs == self.grammar.start_symbol:
                        continue

                    rule = f"{item.lhs} -> {' '.join(item.rhs)}"
                    lhs = item.lhs
                    # Use actual FOLLOW set only — never fall back to all terminals
                    follow_set = self.follow.get(lhs, set())

                    for terminal in follow_set:
                        key = (i, terminal)
                        new_action = f"r({rule})"
                        if key in self.action and self.action[key] != new_action:
                            self.conflicts.append((i, terminal, self.action[key], new_action))
                        self.action[key] = new_action

                # SHIFT / GOTO
                else:
                    symbol = item.rhs[item.dot]
                    if (i, symbol) in self.transitions:
                        j = self.transitions[(i, symbol)]
                        if symbol in self.grammar.terminals:
                            key = (i, symbol)
                            new_action = f"s{j}"
                            if key in self.action and self.action[key] != new_action:
                                self.conflicts.append((i, symbol, self.action[key], new_action))
                            self.action[key] = new_action
                        else:
                            self.goto[(i, symbol)] = j

    def display(self):
        print("\n--- SLR(1) PARSING TABLE ---")

        terminals = sorted(list(self.grammar.terminals)) + ["$"]
        non_terminals = sorted(list(
            self.grammar.non_terminals - {self.grammar.start_symbol}
        ))

        print("{:<6}".format("State"), end=" ")
        for h in terminals + non_terminals:
            print("{:<20}".format(h), end="")
        print()
        print("-" * (20 * (len(terminals) + len(non_terminals)) + 7))

        for i in range(len(self.states)):
            print("{:<6}".format(i), end=" ")
            for t in terminals:
                print("{:<20}".format(self.action.get((i, t), "")), end="")
            for nt in non_terminals:
                print("{:<20}".format(self.goto.get((i, nt), "")), end="")
            print()

        if self.conflicts:
            print("\n⚠ Conflicts detected (grammar is NOT SLR(1)):")
            for state, terminal, old, new in self.conflicts:
                print(f"  State {state}, terminal '{terminal}': {old} vs {new}")
        else:
            print("\n✓ No conflicts. Grammar is SLR(1).")