from parse_tree import TreeNode

class LL1Parser:
    def __init__(self, grammar, table):
        self.grammar = grammar
        self.table = table

    def parse(self, input_string):
        root = TreeNode(self.grammar.start_symbol)

        # Stack holds (symbol, tree_node) pairs
        stack = [("$", None), (self.grammar.start_symbol, root)]
        input_tokens = input_string.split() + ["$"]

        print("\nParsing Trace:")
        print(f"{'Stack':<25}{'Input':<25}{'Action'}")
        print("-" * 60)

        while stack:
            top_sym, top_node = stack[-1]
            current_input = input_tokens[0]

            stack_display = " ".join(s for s, _ in stack)
            print(f"{stack_display:<25}{' '.join(input_tokens):<25}", end="")

            # Accept
            if top_sym == current_input == "$":
                print("ACCEPT")
                print("\nParse Tree:")
                root.print_tree()
                return True

            # Terminal match
            elif top_sym in self.grammar.terminals or top_sym == "$":
                if top_sym == current_input:
                    stack.pop()
                    input_tokens.pop(0)
                    print("Match")
                else:
                    print("ERROR")
                    return False

            # Non-terminal: expand
            else:
                if current_input in self.table[top_sym]:
                    production = self.table[top_sym][current_input]
                    stack.pop()

                    print(f"{top_sym} -> {' '.join(production)}")

                    if production != ["ε"]:
                        child_nodes = [TreeNode(sym) for sym in production]
                        for child in child_nodes:
                            top_node.add_child(child)
                        for sym, node in reversed(list(zip(production, child_nodes))):
                            stack.append((sym, node))
                    else:
                        # Epsilon production — add ε as leaf
                        top_node.add_child(TreeNode("ε"))
                else:
                    print("ERROR")
                    return False

        return False
