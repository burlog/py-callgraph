# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph codnitional ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from callgraph.ast_tree import Node

class IfNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.test = self.make_node(expr_tree.test)
        self.body = self.make_nodes(expr_tree.body)
        self.orelse = self.make_nodes(expr_tree.orelse)

    def eval_node(self, printer, ctx):
        yield from self.test.evaluate(printer, ctx)
        for node in self.body:
            yield from node.evaluate(printer, ctx)
        for node in self.orelse:
            yield from node.evaluate(printer, ctx)

class IfExpNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.test = self.make_node(expr_tree.test)
        self.body = self.make_node(expr_tree.body)
        self.orelse = self.make_node(expr_tree.orelse)

    def eval_node(self, printer, ctx):
        yield from self.test.evaluate(printer, ctx)
        yield from self.body.evaluate(printer, ctx)
        yield from self.orelse.evaluate(printer, ctx)

    def var_types(self, printer, ctx):
        yield from self.body.var_types(printer, ctx)
        if self.orelse:
            yield from self.orelse.var_types(printer, ctx)

# TODO(burlog):
#           | For(expr target, expr iter, stmt* body, stmt* orelse)
#           | While(expr test, stmt* body, stmt* orelse)
#           | With(withitem* items, stmt* body)

