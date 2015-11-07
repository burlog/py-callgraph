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

def dfs_node_names(root):
    for node in depth_first_traverse(root):
        path = [x.name for x in node.path_to_root()]
        if path: yield ".".join(reversed(path))

