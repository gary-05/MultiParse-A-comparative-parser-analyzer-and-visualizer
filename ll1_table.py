class LL1Table:
    def __init__(self, grammar, first, follow):
        self.grammar = grammar
        self.first = first
        self.follow = follow
        self.table = {nt: {} for nt in grammar.non_terminals}
        self.conflicts = []

    def compute_first_of_string(self, symbols):
        result = set()

        # If production is epsilon
        if symbols == ["ε"]:
            result.add("ε")
            return result

        for symbol in symbols:

            if symbol == "ε":
                result.add("ε")
                return result

            if symbol in self.grammar.terminals:
                result.add(symbol)
                return result

            result |= (self.first[symbol] - {"ε"})

            if "ε" not in self.first[symbol]:
                return result

        result.add("ε")
        return result


    def build_table(self):
        for lhs in self.grammar.productions:
            for production in self.grammar.productions[lhs]:

                first_alpha = self.compute_first_of_string(production)

                # Rule 1: For terminals in FIRST(alpha)
                for terminal in first_alpha - {"ε"}:
                    if terminal in self.table[lhs]:
                        self.conflicts.append((lhs, terminal))
                    self.table[lhs][terminal] = production

                # Rule 2: If epsilon in FIRST(alpha)
                if "ε" in first_alpha:
                    for terminal in self.follow[lhs]:
                        if terminal in self.table[lhs]:
                            self.conflicts.append((lhs, terminal))
                        self.table[lhs][terminal] = production

    def display(self):
        print("\nLL(1) Parsing Table:")

        for nt in sorted(self.table):
            for terminal in sorted(self.table[nt]):
                production = " ".join(self.table[nt][terminal])
                print(f"M[{nt}, {terminal}] = {production}")

        if self.conflicts:
            print("\nConflicts detected at:")
            for lhs, terminal in self.conflicts:
                print(f"Conflict at M[{lhs}, {terminal}]")
        else:
            print("\nNo conflicts. Grammar is LL(1).")
