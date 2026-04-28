class TreeNode:
    def __init__(self, label):
        self.label = label
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def display(self, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        print(prefix + connector + self.label)
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(self.children):
            child.display(child_prefix, i == len(self.children) - 1)

    def print_tree(self):
        print(self.label)
        for i, child in enumerate(self.children):
            child.display("", i == len(self.children) - 1)
