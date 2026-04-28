class CLRTable:
    def __init__(self, grammar, states, transitions):
        self.grammar = grammar
        self.states = states
        self.transitions = transitions

        self.action = {}
        self.goto = {}
        self.conflicts = []

    def build_table(self):
        for i, state in enumerate(self.states):
            for item in state:
                # ACCEPT
                if (item.lhs == self.grammar.start_symbol and
                        item.dot == len(item.rhs) and
                        item.lookahead == "$"):
                    self.action[(i, "$")] = "acc"

                # REDUCE — only on item.lookahead
                elif item.dot == len(item.rhs) or item.rhs == ['ε']:
                    if item.lhs == self.grammar.start_symbol:
                        continue
                    
                    rule = f"{item.lhs} -> {' '.join(item.rhs)}"
                    terminal = item.lookahead
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
