# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph output formats.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

def dump_to_graphviz(root):
    from graphviz import Digraph
    from hashlib import md5
    name = next(iter(root.children)).name
    dot = Digraph(comment="Callgraph of the <{0}>".format(name))

    # maintains ids vector
    class NodeIdAppender(object):
        def __init__(self,  node_ids, call_node):
            self.node_ids = node_ids
            self.call_node = call_node

        def __enter__(self):
            self.node_ids.append(self.call_node.id)

        def __exit__(self, exp_type, exp_value, traceback):
            self.node_ids.pop()

    # tree construction function
    def make_nodes(call_node, node_ids):
        with NodeIdAppender(node_ids, call_node):
            node_id = md5(".".join(node_ids).encode("utf-8")).hexdigest()
            dot.node(node_id, call_node.name)
            for child in call_node.children:
                child_id = make_nodes(child, node_ids)
                dot.edge(node_id, child_id)
        return node_id

    # make digraph tree
    make_nodes(root, [])
    return dot.source

