class FirstFollow:
    def __init__(self, grammar):
        self.grammar = grammar
        self.first = {}
        self.follow = {}

        for nt in grammar.non_terminals:
            self.first[nt] = set()
            self.follow[nt] = set()


    # ---------------- FIRST ----------------
    def compute_first(self):
        changed = True

        while changed:
            changed = False

            for lhs in self.grammar.productions:
                for production in self.grammar.productions[lhs]:

                    # If epsilon production
                    if production == ["ε"]:
                        if "ε" not in self.first[lhs]:
                            self.first[lhs].add("ε")
                            changed = True
                        continue

                    for symbol in production:

                        # If terminal
                        if symbol in self.grammar.terminals:
                            if symbol not in self.first[lhs]:
                                self.first[lhs].add(symbol)
                                changed = True
                            break

                        # If non-terminal
                        elif symbol in self.grammar.non_terminals:
                            before = len(self.first[lhs])

                            # Add FIRST(symbol) minus epsilon
                            self.first[lhs] |= (self.first[symbol] - {"ε"})

                            if len(self.first[lhs]) > before:
                                changed = True

                            # If symbol does NOT produce epsilon, stop
                            if "ε" not in self.first[symbol]:
                                break

                        # If symbol is epsilon
                        elif symbol == "ε":
                            if "ε" not in self.first[lhs]:
                                self.first[lhs].add("ε")
                                changed = True
                            break
                    else:
                        # All symbols can produce epsilon
                        if "ε" not in self.first[lhs]:
                            self.first[lhs].add("ε")
                            changed = True


    # ---------------- FOLLOW ----------------
    def compute_follow(self):
        self.follow[self.grammar.start_symbol].add("$")

        changed = True
        while changed:
            changed = False

            for lhs in self.grammar.productions:
                for production in self.grammar.productions[lhs]:

                    for i, symbol in enumerate(production):

                        if symbol in self.grammar.non_terminals:

                            next_symbols = production[i+1:]

                            if next_symbols:
                                first_next = set()

                                for next_symbol in next_symbols:

                                    if next_symbol in self.grammar.terminals:
                                        first_next.add(next_symbol)
                                        break

                                    first_next |= (self.first[next_symbol] - {"ε"})

                                    if "ε" not in self.first[next_symbol]:
                                        break
                                else:
                                    first_next.add("ε")

                                before = len(self.follow[symbol])

                                self.follow[symbol] |= (first_next - {"ε"})

                                if "ε" in first_next:
                                    self.follow[symbol] |= self.follow[lhs]

                                if before != len(self.follow[symbol]):
                                    changed = True
                            else:
                                before = len(self.follow[symbol])
                                self.follow[symbol] |= self.follow[lhs]

                                if before != len(self.follow[symbol]):
                                    changed = True

    def display(self):
        print("\nFIRST Sets:")
        for nt in sorted(self.first):
            print(f"FIRST({nt}) = {self.first[nt]}")

        print("\nFOLLOW Sets:")
        for nt in sorted(self.follow):
            print(f"FOLLOW({nt}) = {self.follow[nt]}")
