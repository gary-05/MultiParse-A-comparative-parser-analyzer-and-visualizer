from parse_tree import TreeNode
class SLR1Parser:
    def __init__(self, grammar, action, goto):
        self.grammar = grammar
        self.action = action
        self.goto = goto

    def parse(self, input_string):
        tokens = input_string.split() + ["$"]
        state_stack = [0]
        symbol_stack = ["$"]
        node_stack = [None]   # parallel tree-node stack

        print("\nSLR(1) Parsing Trace:")
        print(f"{'State Stack':<30}{'Symbol Stack':<30}{'Input':<30}{'Action'}")
        print("-" * 100)

        pos = 0

        while True:
            state = state_stack[-1]
            current = tokens[pos]

            state_str = " ".join(str(s) for s in state_stack)
            sym_str   = " ".join(symbol_stack)
            inp_str   = " ".join(tokens[pos:])

            action = self.action.get((state, current), None)

            print(f"{state_str:<30}{sym_str:<30}{inp_str:<30}", end="")

            if action is None:
                print("ERROR: No action found")
                return False

            elif action == "acc":
                print("ACCEPT")
                # The root is the node just below the augmented start
                root = node_stack[-1]
                print("\nParse Tree:")
                root.print_tree()
                return True

            elif action.startswith("s"):
                # SHIFT — create a leaf node for the terminal
                next_state = int(action[1:])
                print(f"Shift → go to state {next_state}")
                state_stack.append(next_state)
                symbol_stack.append(current)
                node_stack.append(TreeNode(current))
                pos += 1

            elif action.startswith("r"):
                # REDUCE
                rule_str = action[2:-1]          # strip r( and )
                arrow    = rule_str.index("->")
                lhs      = rule_str[:arrow].strip()
                rhs_str  = rule_str[arrow + 2:].strip()
                rhs      = rhs_str.split() if rhs_str != "ε" else []

                print(f"Reduce by {rule_str}")

                # Build the internal node for lhs
                parent = TreeNode(lhs)

                if rhs:
                    # Pop |rhs| items and collect their nodes as children
                    children = []
                    for _ in rhs:
                        state_stack.pop()
                        symbol_stack.pop()
                        children.append(node_stack.pop())
                    # Children were popped in reverse order
                    for child in reversed(children):
                        parent.add_child(child)
                else:
                    # Epsilon production
                    parent.add_child(TreeNode("ε"))

                symbol_stack.append(lhs)
                top_state = state_stack[-1]

                goto_state = self.goto.get((top_state, lhs), None)
                if goto_state is None:
                    print(f"ERROR: No GOTO for state {top_state}, symbol {lhs}")
                    return False

                state_stack.append(goto_state)
                node_stack.append(parent)

            else:
                print(f"ERROR: Unknown action '{action}'")
                return False