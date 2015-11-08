# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph statement ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import ast
from inspect import isclass

from callgraph.ast_tree import Node
from callgraph.symbols import MultiSymbol, InvalidSymbol, LambdaSymbol
from callgraph.symbols import make_result_symbol, merge_symbols
from callgraph.ast_tree.helpers import VariablesScope

class ExprNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = self.make_node(expr_tree.value)

class AssignNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.targets = self.make_nodes(expr_tree.targets)
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        yield from self.value.evaluate(printer, ctx)
        for target in self.targets:
            yield from target.evaluate(printer, ctx)
            target.store(printer, ctx, self.value.load(printer, ctx))

class CallNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.func = self.make_node(expr_tree.func)
        self.args = self.make_nodes(expr_tree.args)
        self.keywords = self.make_nodes(expr_tree.keywords)
        self.starargs = self.make_node(expr_tree.starargs)
        self.kwargs = self.make_node(expr_tree.kwargs)
        self.local.callee_symbols = []
        self.local.kwargs = {}
        self.local.args = []

    def eval_node(self, printer, ctx):
        yield from self.func.evaluate(printer, ctx)
        yield from self.unroll_args(printer, ctx)
        yield from self.unroll_kwargs(printer, ctx)
        for obj_symbol in self.func.load(printer, ctx).values():
            callee_symbol = self.expand(printer, ctx, obj_symbol)
            printer("- New callee discovered:", callee_symbol)
            yield callee_symbol, self.local.args, self.local.kwargs
            self.local.callee_symbols.append(callee_symbol)

    def load(self, printer, ctx):
        if not self.local.callee_symbols: name = "__callee_result__"
        else: name = self.local.callee_symbols[0].name
        callee_symbol = merge_symbols(name, *self.local.callee_symbols)
        result_symbol = make_result_symbol(ctx.builder, callee_symbol)
        if not result_symbol:
            printer("? Can't load callee result:", callee_symbol)
        return result_symbol

    def expand(self, printer, ctx, obj_symbol):
        if not obj_symbol or not isclass(obj_symbol.value): return obj_symbol
        return obj_symbol.make_instance_and_return_init()\
            or printer("? Can't extract __init__:", obj_symbol)\
            or obj_symbol

    def unroll_args(self, printer, ctx):
        for arg in self.args:
            yield from arg.evaluate(printer, ctx)
            self.local.args.append(arg.load(printer, ctx))
        if self.starargs:
            yield from self.starargs.evaluate(printer, ctx)
            starargs = self.starargs.load(printer, ctx)
            if starargs.isiterable():
                for stararg in starargs:
                    self.local.args.append(stararg)
            else: printer("? Can't unroll *args:", starargs)

    def unroll_kwargs(self, printer, ctx):
        for keyword in self.keywords:
            yield from keyword.evaluate(printer, ctx)
            self.local.kwargs[keyword.arg] = keyword.value.load(printer, ctx)
        if self.kwargs:
            yield from self.kwargs.evaluate(printer, ctx)
            kwargs = self.kwargs.load(printer, ctx)
            if kwargs.ismapping():
                for key_symbol, value_symbol in kwargs.__iter_items__():
                    for key in key_symbol.values():
                        if isinstance(key.value, str):
                            self.local.kwargs[key.value] = value_symbol
                            continue
                        printer("? Skipping dynamic subscription:", key_symbol)
            else: printer("? Can't unroll **kwargs:", kwargs)

class NameNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.name = expr_tree.id
        self.action = self.make_node(expr_tree.ctx)

    def eval_node(self, printer, ctx):
        while False: yield None

    def load(self, printer, ctx):
        return ctx.get(self.name)\
            or printer("? Can't load symbol:", self.name)\
            or InvalidSymbol(ctx.builder, self.name)

    def store(self, printer, ctx, value):
        if value:
            printer("* Storing variable:", self.name + "=" + str(value))
            ctx.set(self.name, value)
        else: printer("? Can't store variable:", self.name + "=" + str(value))

class AttributeNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = self.make_node(expr_tree.value)
        self.attr = expr_tree.attr
        self.action = self.make_node(expr_tree.ctx)
        self.local.callee = []

    def eval_node(self, printer, ctx):
        yield from self.value.evaluate(printer, ctx)

    def load(self, printer, ctx):
        symbol = self.value.load(printer, ctx)
        return symbol.get(self.attr, free=False)\
            or printer("? Can't load attr:", str(symbol) + "." + self.attr)\
            or InvalidSymbol(ctx.builder, self.attr)

    def store(self, printer, ctx, value):
        symbol = self.value.load(printer, ctx)
        if symbol:
            name = str(symbol) + "." + self.attr
            printer("* Storing attr variable:", name + "=" + str(value))
            symbol.set(self.attr, value)
        else: printer("? Can't store attr:", str(symbol) + "." + self.attr)

class RaiseNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.exc = self.make_node(expr_tree.exc)
        self.cause = self.make_node(expr_tree.cause)

    def eval_node(self, printer, ctx):
        if self.exc:
            yield from self.exc.evaluate(printer, ctx)

class ReturnNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        if self.value:
            yield from self.value.evaluate(printer, ctx)
            symbol = self.value.load(printer, ctx)
            if symbol:
                printer("* Function can return:", str(symbol))
                ctx.can_return(symbol)

class YieldNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        if self.value:
            yield from self.value.evaluate(printer, ctx)
            symbol = self.value.load(printer, ctx)
            if symbol:
                printer("* Function can yield:", str(symbol))
                ctx.can_yield(symbol)

class YieldFromNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        if self.value:
            yield from self.value.evaluate(printer, ctx)
            symbol = self.value.load(printer, ctx)
            if symbol:
                printer("* Function can yield from:", str(symbol))
                ctx.can_yield_from(symbol)

class TryNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.body = self.make_nodes(expr_tree.body)
        self.handlers = self.make_nodes(expr_tree.handlers)
        self.orelse = self.make_nodes(expr_tree.orelse)
        self.finalbody = self.make_nodes(expr_tree.finalbody)

    def eval_node(self, printer, ctx):
        for expr in self.body:
            yield from expr.evaluate(printer, ctx)
        for expr in self.handlers:
            yield from expr.evaluate(printer, ctx)
        for expr in self.orelse:
            yield from expr.evaluate(printer, ctx)
        for expr in self.finalbody:
            yield from expr.evaluate(printer, ctx)

class ExceptHandlerNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.name = expr_tree.name
        self.excs = self.make_node(expr_tree.type)
        self.body = self.make_nodes(expr_tree.body)

    def eval_node(self, printer, ctx):
        with VariablesScope(ctx) as scope:
            for exc in self.get_excs_symbols(printer, ctx):
                printer("* Storing exc variable:", self.name + "=" + str(exc))
                ctx.set(self.name, exc)
            scope.freeze()
            for expr in self.body:
                yield from expr.evaluate(printer, ctx)

    def get_excs_symbols(self, printer, ctx):
        if self.name:
            symbol = self.excs.load(printer, ctx)
            if symbol.isiterable():
                yield MultiSymbol(ctx.builder, "__unroll__", list(symbol))
            else: yield self.excs.load(printer, ctx)

    def unroll_iterables(self, printer, ctx, iter_symbol):
        self.target.store(printer, ctx, symbol)

class AssertNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.msg = expr_tree.msg
        self.test = self.make_node(expr_tree.test)

    def eval_node(self, printer, ctx):
        yield from self.test.evaluate(printer, ctx)

class LambdaNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.args = expr_tree.args
        self.body = ast.Return(expr_tree.body)
        # TODO(burlog): make new function node

    def eval_node(self, printer, ctx):
        while False: yield None

    def load(self, printer, ctx):
        return LambdaSymbol(ctx.builder, self.args, self.body)

