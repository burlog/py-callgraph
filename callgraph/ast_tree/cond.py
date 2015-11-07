# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph codnitional ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import ast
from itertools import chain

from callgraph.utils import empty
from callgraph.symbols import MultiSymbol, InvalidSymbol
from callgraph.symbols import make_result_symbol, merge_symbols
from callgraph.ast_tree import Node
from callgraph.ast_tree.helpers import VariablesScope
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

    def load(self, printer, ctx):
        if not self.orelse: return self.body.load(printer, ctx)
        body = self.body.load(printer, ctx)
        orelse = self.orelse.load(printer, ctx)
        return merge_symbols("__if__", body, orelse)

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
        with VariablesScope(ctx) as scope:
            yield from self.unroll_foriter(printer, ctx)
            scope.freeze()
            if empty(scope.vars_in_scope()):
                symbol = InvalidSymbol(ctx.builder, "__unroll__")
                self.target.store(printer, ctx, symbol)
            for node in self.body:
                yield from node.evaluate(printer, ctx)
            for node in self.orelse:
                yield from node.evaluate(printer, ctx)

    def unroll_foriter(self, printer, ctx):
        iter_symbol = self.foriter.load(printer, ctx)
        for symbol in iter_symbol.geners():
            self.target.store(printer, ctx, symbol)
        for symbol in iter_symbol.values():
            if symbol.isiterable(): self.unroll_iterables(printer, ctx, symbol)
            else: yield from self.unroll_generator_iter(printer, ctx, symbol)

    def unroll_iterables(self, printer, ctx, iter_symbol):
        symbol = MultiSymbol(ctx.builder, "__unroll__", list(iter_symbol))
        self.target.store(printer, ctx, symbol)

    def unroll_generator_iter(self, printer, ctx, obj_symbol):
        iter_symbol = obj_symbol.get("__iter__", free=False)
        if iter_symbol:
            yield iter_symbol, [], {}
            result_symbol = make_result_symbol(ctx.builder, iter_symbol)
            for symbol in result_symbol.geners():
                self.target.store(printer, ctx, symbol)
            for symbol in result_symbol.values():
                yield from self.unroll_generator_next(printer, ctx, symbol)

    def unroll_generator_next(self, printer, ctx, obj_symbol):
        next_symbol = obj_symbol.get("__next__", free=False)
        if next_symbol:
            yield next_symbol, [], {}
            result_symbol = make_result_symbol(ctx.builder, next_symbol)
            for symbol in result_symbol.values():
                self.target.store(printer, ctx, symbol)

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
        with VariablesScope(ctx) as scope:
            for item in self.items:
                yield from item.evaluate(printer, ctx)
            scope.freeze()
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

