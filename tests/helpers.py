# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Test helpers.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

def depth_first_traverse(parent):
    yield parent
    for node in parent.children:
        if node.invalid: continue
        yield from depth_first_traverse(node)

def node_name(node):
    if node.name == "__init__":
        return node.qualname.split(".")[-2]
    return node.name

def dfs_node_names(root):
    for node in depth_first_traverse(root):
        path = [node_name(x) for x in node.path_to_root()]
        if path: yield ".".join(reversed(path))

