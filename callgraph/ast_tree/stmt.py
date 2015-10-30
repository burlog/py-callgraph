# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph statement ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from callgraph.ast_tree import Node

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
            target.eval_assign(printer, ctx, self.value)

class CallNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.func = self.make_node(expr_tree.func)
        self.args = self.make_nodes(expr_tree.args)
        self.keywords = self.make_nodes(expr_tree.keywords)
        self.starargs = self.make_node(expr_tree.starargs)
        self.kwargs = self.make_node(expr_tree.kwargs)

    def eval_node(self, printer, ctx):
        yield from self.func.evaluate(printer, ctx)

        # params
        for arg in self.args:
            yield from arg.evaluate(printer, ctx)
        for keyword in self.keywords:
            yield from keyword.evaluate(printer, ctx)
        # TODO(burlog): eval starargs, kwargs

        # call
        args = list(self.make_args(printer, ctx))
        kwargs = dict(self.make_kwargs(printer, ctx))
        yield from self.func.get_callee(printer, ctx, args, kwargs)

    def make_args(self, printer, ctx):
        for arg in self.args:
            yield list(arg.var_types(printer, ctx))

    def make_kwargs(self, printer, ctx):
        for keyword in self.keywords:
            yield keyword.arg, keyword.value.var_types(printer, ctx)

    def var_types(self, printer, ctx):
        yield from self.func.call_types(printer, ctx)

class NameNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.local.callee = None
        self.value = expr_tree.id
        self.action = self.make_node(expr_tree.ctx)

    def eval_node(self, printer, ctx):
        while False: yield None

    def get_callee(self, printer, ctx, args, kwargs):
        self.local.callee = ctx.get_object(self.value)
        if self.local.callee: yield self.local.callee, args, kwargs

    def eval_assign(self, printer, ctx, value):
        types = list(value.var_types(printer, ctx))
        if not types: return printer("? ignoring assign for value:", value)
        printer("* Storing variable:", self.value, "=", types)
        ctx.replace_variable(self.value, types, self.lineno)

    def call_types(self, printer, ctx):
        if self.local.callee:
            child = ctx.get_child(self.local.callee)
            if child and child.returns:
                for return_class in child.returns:
                    yield return_class
            else: printer("! Empty returns list for function:", self.value)
        else: printer("! Inaccessible callee for function:", self.value)

    def var_types(self, printer, ctx):
        if self.value in ctx.variables:
            for var_type in ctx.variables[self.value].types:
                yield var_type
        else: printer("! Empty returns list for function:", self.value)

class RaiseNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.exc = self.make_node(expr_tree.exc)
        self.cause = self.make_node(expr_tree.cause)
        if self.cause: raise NotImplementedError()

    def eval_node(self, printer, ctx):
        yield from self.exc.evaluate(printer, ctx)

class ReturnNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        if self.value:
            yield from self.value.evaluate(printer, ctx)
            for var_type in self.value.var_types(printer, ctx):
                printer("* Function can return: ", var_type)
                ctx.returns.append(var_type)

class AttributeNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = self.make_node(expr_tree.value)
        self.attr = expr_tree.attr
        self.action = self.make_node(expr_tree.ctx)
        self.local.callee = []

    def eval_node(self, printer, ctx):
        yield from self.value.evaluate(printer, ctx)

    def get_callee(self, printer, ctx, args, kwargs):
        var_types = list(self.filter_value_var_types(printer, ctx))
        if var_types:
            for var_type in var_types:
                self.local.callee.append(getattr(var_type, self.attr))
                yield self.local.callee[-1], args, kwargs
        else: printer("! Inaccessible attribute:", self.attr)

    def filter_value_var_types(self, printer, ctx):
        for var_type in self.value.var_types(printer, ctx):
            if self.attr in dir(var_type):
                yield var_type

    def call_types(self, printer, ctx):
        # TODO(burlog): self.local.callee should be cached property
        if self.local.callee:
            for callee in self.local.callee:
                child = ctx.get_child(callee)
                if child and child.returns:
                    for return_class in child.returns:
                        yield return_class
                else: printer("! Empty returns list for method:", self.value)
        else: printer("! Empty callee list for method:", self.value)

