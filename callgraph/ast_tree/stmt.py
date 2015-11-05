# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph statement ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import ast
from types import FunctionType

from callgraph.ast_tree import Node
from callgraph.symbols import MultiSymbol, InvalidSymbol, LambdaSymbol
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
        self.local.kwargs = {}
        self.local.args = []

    def eval_node(self, printer, ctx):
        yield from self.func.evaluate(printer, ctx)
        for arg in self.args:
            yield from arg.evaluate(printer, ctx)
            self.local.args.append(arg.load(printer, ctx))
        for keyword in self.keywords:
            yield from keyword.evaluate(printer, ctx)
            self.local.kwargs[keyword.arg] = keyword.value.load(printer, ctx)
        # TODO(burlog): eval starargs, kwargs
        for obj in self.func.load(printer, ctx).values():
            if not callable(obj.value): continue
            printer("- New call discovered:", obj)
            yield obj, self.local.args, self.local.kwargs

    def load(self, printer, ctx):
        symbol = self.func.load(printer, ctx)
        return MultiSymbol("__returns__", symbol.returns)\
            or printer("? Can't detect function result:", symbol)\
            or InvalidSymbol("__returns__")

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
            or InvalidSymbol(self.name)

    def store(self, printer, ctx, value):
        printer("* Storing variable:", self.name + "=" + str(value))
        ctx.set(self.name, value)

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
            or InvalidSymbol(str(symbol) + "." + self.attr)

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
                ctx.returns.append(symbol)

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
                ctx.returns.append(symbol)

class YieldFromNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        if self.value:
            yield from self.value.evaluate(printer, ctx)
            symbol = self.value.load(printer, ctx)
            if symbol:
                printer("* Function can yield:", str(symbol))
                ctx.returns.append(symbol)

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
            if hasattr(self.excs, "unroll"):
                yield from self.excs.unroll(printer, ctx)
            yield self.excs.load(printer, ctx)

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
        return LambdaSymbol(self.args, self.body)

