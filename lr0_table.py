class LR0Table:

    def __init__(self, grammar, states, transitions):

        self.grammar = grammar
        self.states = states
        self.transitions = transitions

        self.action = {}
        self.goto = {}

    def build_table(self):

        for i, state in enumerate(self.states):

            state = set(state)

            for item in state:

                # ACCEPT
                if item.lhs == self.grammar.start_symbol and item.dot == len(item.rhs):
                    self.action[(i, "$")] = "acc"

                # REDUCE
                elif item.dot == len(item.rhs) or item.rhs == ['ε']:

                    rule = f"{item.lhs} -> {' '.join(item.rhs)}"

                    for terminal in self.grammar.terminals.union({"$"}):
                        self.action[(i, terminal)] = f"r({rule})"

                # SHIFT
                else:

                    symbol = item.rhs[item.dot]

                    if (i, symbol) in self.transitions:

                        j = self.transitions[(i, symbol)]

                        if symbol in self.grammar.terminals:
                            self.action[(i, symbol)] = f"s{j}"
                        else:
                            self.goto[(i, symbol)] = j
    def display(self):

        print("\n--- LR(0) PARSING TABLE ---")

        terminals = sorted(list(self.grammar.terminals)) + ["$"]
        non_terminals = sorted(list(self.grammar.non_terminals - {self.grammar.start_symbol}))

        header = ["State"] + terminals + non_terminals

        print("{:<6}".format("State"), end=" ")
        for h in terminals + non_terminals:
            print("{:<8}".format(h), end="")
        print()

        print("-" * (8 * (len(header))))

        for i in range(len(self.states)):

            print("{:<6}".format(i), end=" ")

            for t in terminals:
                print("{:<8}".format(self.action.get((i, t), "")), end="")

            for nt in non_terminals:
                print("{:<8}".format(self.goto.get((i, nt), "")), end="")

            print()