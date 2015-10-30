# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph codnitional ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import ast

from callgraph.ast_tree import Node
from callgraph.ast_tree.helpers import VariablesContext
from callgraph.ast_tree.helpers import UniqueNameGenerator

class IfNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
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
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
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

class ForNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.target = self.make_node(expr_tree.target)
        self.foriter = self.make_node(expr_tree.iter)
        self.body = self.make_nodes(expr_tree.body)
        self.orelse = self.make_nodes(expr_tree.orelse)

    def eval_node(self, printer, ctx):
        yield from self.target.evaluate(printer, ctx)
        yield from self.foriter.evaluate(printer, ctx)
        for node in self.body:
            yield from node.evaluate(printer, ctx)
        for node in self.orelse:
            yield from node.evaluate(printer, ctx)

class WhileNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.test = self.make_node(expr_tree.test)
        self.body = self.make_nodes(expr_tree.body)
        self.orelse = self.make_nodes(expr_tree.orelse)

    def eval_node(self, printer, ctx):
        yield from self.test.evaluate(printer, ctx)
        for node in self.body:
            yield from node.evaluate(printer, ctx)
        for node in self.orelse:
            yield from node.evaluate(printer, ctx)

class WithNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.items = self.make_nodes(expr_tree.items)
        self.body = self.make_nodes(expr_tree.body)

    def eval_node(self, printer, ctx):
        with VariablesContext(ctx.variables):
            for item in self.items:
                yield from item.evaluate(printer, ctx)
            for expr in self.body:
                yield from expr.evaluate(printer, ctx)
            for item in self.items:
                yield from item.local.exit_expr.evaluate(printer, ctx)

class WithItemNode(Node, UniqueNameGenerator):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        # Can be simply translated to:

        # var_name = context_expr
        var_name = self.make_unique_name("with_ctx_var")
        targets = [ast.Name(var_name, ast.Store())]
        assign_expr = ast.Assign(targets, expr_tree.context_expr)

        # optional_vars = var_name.__enter__()
        var = expr_tree.optional_vars
        call_enter = self.make_attr_call(var_name, "__enter__")
        enter_expr = ast.Assign([var], call_enter) if var else call_enter
        self.enter_exprs = self.make_nodes([assign_expr, enter_expr])

        # var_name.__exit__()
        exit_expr = self.make_attr_call(var_name, "__exit__")
        self.local.exit_expr = self.make_node(exit_expr)

    def make_attr_call(self, var_name, attr):
        node = ast.Attribute(ast.Name(var_name, ast.Load()), attr, ast.Load())
        return ast.Call(func=node, args=[], keywords=[], starargs=[], kwargs=[])

    def eval_node(self, printer, ctx):
        for expr in self.enter_exprs:
            yield from expr.evaluate(printer, ctx)

