# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph output formats.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

def make_graphviz_tree(root):
    from graphviz import Digraph
    from hashlib import md5
    from operator import attrgetter
    name = next(iter(root.children)).name
    dot = Digraph(comment="Callgraph of the <{0}>".format(name))

    # node id generator
    def generate_id(node_ids):
        ids = map(attrgetter("id"), node_ids)
        return md5(".".join(ids).encode("utf-8")).hexdigest()

    # make nice label with info where is function called
    def make_label(call_node):
        def call_places(places):
            return map(lambda f: f[0] + ":" + str(f[1]), places)
        return "{0}|{1}"\
               .format(call_node.qualname,
                       "|".join(call_places(call_node.called_at)))

    # tree construction function
    def make_nodes(call_node):
        node_id = generate_id(call_node.path_to_root())
        shape = "triangle" if call_node.invalid else "record"
        dot.node(node_id, label=make_label(call_node), shape=shape)
        for child in call_node.children:
            child_id = make_nodes(child)
            dot.edge(node_id, child_id)
        for recur_child in call_node.recur_children:
            dot.edge(node_id, generate_id(recur_child.path_to_root()))
        return node_id

    # make digraph tree
    make_nodes(root)
    return dot

