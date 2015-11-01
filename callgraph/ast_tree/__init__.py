# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph ast tree.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from callgraph.ast_tree.base import Node
from callgraph.ast_tree.simple import *
from callgraph.ast_tree.stmt import *
from callgraph.ast_tree.cond import *
from callgraph.ast_tree.defs import *
from callgraph.ast_tree.ops import *

def ast_parse(source):
    from callgraph.indent_printer import dump_ast_tree
    from ast import parse
    tree = parse(source)
    #dump_ast_tree(tree)
    #print(80 * "=")
    return tree

class ASTTree(object):
    def __init__(self, source):
        self.tree = ast_parse(source)
        self.name = self.tree.body[0].name
        self.body = Node.make_root_nodes(self.tree.body[0].body)
        self.decors = Node.make_root_nodes(self.tree.body[0].decorator_list)

