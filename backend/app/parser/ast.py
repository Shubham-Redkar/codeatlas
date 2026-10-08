from tree_sitter import Node, Tree


def extract_ast(tree: Tree) -> Node:
    """
    Extract the root node from a Tree-sitter syntax tree.
    """
    return tree.root_node
