from clr_table import CLRTable

class LALRTable(CLRTable):
    def __init__(self, grammar, lr1_states, lr1_transitions):
        super().__init__(grammar, None, None)
        self.lr1_states = lr1_states
        self.lr1_transitions = lr1_transitions

    def build_table(self):
        # 1. Group LR(1) states by their LR(0) kernel
        # Kernel = set of (lhs, rhs, dot)
        groups = {} # kernel -> list of state indices
        for i, state in enumerate(self.lr1_states):
            kernel = frozenset([(item.lhs, tuple(item.rhs), item.dot) for item in state])
            if kernel not in groups:
                groups[kernel] = []
            groups[kernel].append(i)

        # 2. Map old indices to new indices
        old_to_new = {}
        sorted_kernels = sorted(list(groups.keys()), key=lambda k: min(groups[k]))
        new_states = []
        
        for new_idx, kernel in enumerate(sorted_kernels):
            old_indices = groups[kernel]
            for old_idx in old_indices:
                old_to_new[old_idx] = new_idx
            
            # Merge LR(1) items: same (lhs, rhs, dot) but union lookaheads
            merged_items = {} # (lhs, rhs, dot) -> set of lookaheads
            for old_idx in old_indices:
                for item in self.lr1_states[old_idx]:
                    key = (item.lhs, tuple(item.rhs), item.dot)
                    if key not in merged_items:
                        merged_items[key] = set()
                    merged_items[key].add(item.lookahead)
            
            # Create new items from merged lookaheads
            from lr1_engine import LR1Item
            new_state = []
            for (lhs, rhs, dot), lookaheads in merged_items.items():
                for la in lookaheads:
                    new_state.append(LR1Item(lhs, list(rhs), dot, la))
            new_states.append(frozenset(new_state))

        self.states = new_states
        
        # 3. Rebuild transitions for new indices
        new_transitions = {}
        for (old_idx, symbol), target_old_idx in self.lr1_transitions.items():
            new_idx = old_to_new[old_idx]
            new_target_idx = old_to_new[target_old_idx]
            new_transitions[(new_idx, symbol)] = new_target_idx
        
        self.transitions = new_transitions

        # 4. Call CLRTable's build_table with these new states/transitions
        super().build_table()
