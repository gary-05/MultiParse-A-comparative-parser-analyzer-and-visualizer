class Grammar:
    def __init__(self):
        self.productions = {}
        self.non_terminals = set()
        self.terminals = set()
        self.start_symbol = None

    def add_production(self, lhs, rhs_list):
        if self.start_symbol is None:
            self.start_symbol = lhs

        self.non_terminals.add(lhs)

        if lhs not in self.productions:
            self.productions[lhs] = []

        for rhs in rhs_list:
            symbols = rhs.split()
            self.productions[lhs].append(symbols)

            for symbol in symbols:
                if symbol == "ε":
                    continue
                if symbol[0].isupper():
                    self.non_terminals.add(symbol)
                else:
                    self.terminals.add(symbol)

    def validate(self):
        errors = []
        warnings = []

        if not self.productions:
            errors.append("Grammar has no productions.")
            return errors, warnings

        # 1. Undefined non-terminals
        defined_nts = set(self.productions.keys())
        undefined = self.non_terminals - defined_nts
        if undefined:
            errors.append(f"Undefined non-terminals (used in RHS but no production): {', '.join(undefined)}")

        # 2. Reachability from start symbol
        if self.start_symbol:
            reachable = {self.start_symbol}
            queue = [self.start_symbol]
            while queue:
                current = queue.pop(0)
                if current in self.productions:
                    for rhs in self.productions[current]:
                        for symbol in rhs:
                            if symbol in self.non_terminals and symbol not in reachable:
                                reachable.add(symbol)
                                queue.append(symbol)
            unreachable = defined_nts - reachable
            if unreachable:
                warnings.append(f"Unreachable non-terminals from start symbol '{self.start_symbol}': {', '.join(unreachable)}")
        else:
            errors.append("Start symbol not defined.")

        # 3. Non-terminating non-terminals (productivity)
        productive = set()
        changed = True
        while changed:
            changed = False
            for lhs, rhs_list in self.productions.items():
                if lhs in productive:
                    continue
                for rhs in rhs_list:
                    # A production is productive if all its symbols are terminals, ε, or already productive NTs
                    if all(symbol in self.terminals or symbol in productive or symbol == "ε" for symbol in rhs):
                        productive.add(lhs)
                        changed = True
                        break
        
        non_productive = defined_nts - productive
        if non_productive:
            errors.append(f"Non-terminating non-terminals (cannot derive a string of terminals): {', '.join(non_productive)}")

        return errors, warnings

    def display(self):
        print("\nGrammar:")
        for lhs in self.productions:
            right = [" ".join(prod) for prod in self.productions[lhs]]
            print(f"{lhs} -> {' | '.join(right)}")
