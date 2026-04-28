class LR0Item:
    def __init__(self, lhs, rhs, dot):
        self.lhs = lhs
        self.rhs = rhs
        self.dot = dot

    def __repr__(self):
        rhs = self.rhs.copy()
        rhs.insert(self.dot, "•")
        return f"{self.lhs} -> {' '.join(rhs)}"

    def __eq__(self, other):
        return (
            self.lhs == other.lhs and
            self.rhs == other.rhs and
            self.dot == other.dot
        )

    def __hash__(self):
        return hash((self.lhs, tuple(self.rhs), self.dot))
    
class LR0Engine:
    def __init__(self, grammar):
        self.grammar = grammar
        self.states = []
        self._closure_cache = {}
        self._goto_cache = {}

    def augment_grammar(self):
        start = self.grammar.start_symbol
        augmented_start = start + "''"   # E''

        self.grammar.productions[augmented_start] = [[start]]
        self.grammar.non_terminals.add(augmented_start)

        self.grammar.start_symbol = augmented_start

    def closure(self, items):
        key = frozenset(items)
        if key in self._closure_cache:
            return self._closure_cache[key]

        closure_set = set(items)
        changed = True
        while changed:
            changed = False
            new_items = set()
            for item in closure_set:
                if item.dot < len(item.rhs):
                    symbol = item.rhs[item.dot]
                    if symbol in self.grammar.non_terminals:
                        for prod in self.grammar.productions[symbol]:
                            new_item = LR0Item(symbol, prod, 0)
                            if new_item not in closure_set:
                                new_items.add(new_item)
            if new_items:
                closure_set |= new_items
                changed = True
        
        res = frozenset(closure_set)
        self._closure_cache[key] = res
        return res
    
    def goto(self, items, symbol):
        key = (frozenset(items), symbol)
        if key in self._goto_cache:
            return self._goto_cache[key]

        moved_items = set()
        for item in items:
            if item.dot < len(item.rhs) and item.rhs[item.dot] == symbol:
                moved_items.add(
                    LR0Item(item.lhs, item.rhs, item.dot + 1)
                )

        res = self.closure(moved_items)
        self._goto_cache[key] = res
        return res

    def build_canonical_collection(self):
        start_symbol = self.grammar.start_symbol
        start_prod = self.grammar.productions[start_symbol][0]
        start_item = LR0Item(start_symbol, start_prod, 0)

        I0 = self.closure({start_item})

        states = [I0]
        states_map = {I0: 0}
        transitions = {}

        symbols = self.grammar.terminals.union(self.grammar.non_terminals)

        i = 0
        while i < len(states):
            state = states[i]
            for symbol in symbols:
                goto_state = self.goto(state, symbol)
                if not goto_state:
                    continue

                if goto_state not in states_map:
                    states_map[goto_state] = len(states)
                    states.append(goto_state)

                transitions[(i, symbol)] = states_map[goto_state]
            i += 1

        return states, transitions