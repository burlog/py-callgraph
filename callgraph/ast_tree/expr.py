# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph expr ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from callgraph.ast_tree import Node

class ExprNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.value = self.make_node(expr_tree.value)

class AssignNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.targets = self.make_nodes(expr_tree.targets)
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        yield from self.value.evaluate(printer, ctx)
        for target in self.targets:
            yield from target.evaluate(printer, ctx)
            target.eval_assign(printer, ctx, self.value)

class CallNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.func = self.make_node(expr_tree.func)
        self.args = self.make_nodes(expr_tree.args)
        self.keywords = self.make_nodes(expr_tree.keywords)
        self.starargs = self.make_nodes(expr_tree.starargs)
        self.kwargs = self.make_nodes(expr_tree.kwargs)

    def eval_node(self, printer, ctx):
        # TODO(burlog): prepare params as globals for builder.process
        yield from self.func.evaluate(printer, ctx)
        yield from self.func.get_callee(printer, ctx)

    def var_types(self, printer, ctx):
        yield from self.func.call_types(printer, ctx)

class NameNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.value = expr_tree.id
        self.ctx = self.make_node(expr_tree.ctx)
        if self.ctx: raise NotImplementedError()

    def eval_node(self, printer, ctx):
        while False: yield None

    def get_callee(self, printer, ctx):
        obj = ctx.get_object(self.value)
        if obj: yield obj

    def var_name(self, printer, ctx):
        return self.value

    def eval_assign(self, printer, ctx, value):
        types = list(value.var_types(printer, ctx))
        if not types: return printer("? ignoring assign for value:", value)
        printer("* Storing variable:", self.value, "=", types)
        ctx.replace_variable(self.value, types, self.lineno)

    def call_types(self, printer, ctx):
        child = ctx.get_child(self.value)
        if child and child.returns:
            for return_class in child.returns:
                yield return_class
        else: printer("! Empty returns list for function:", self.value)

    def var_types(self, printer, ctx):
        if self.value in ctx.variables:
            for var_type in ctx.variables[self.value].types:
                yield var_type
        else: printer("! Empty returns list for function:", self.value)

class RaiseNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.exc = self.make_node(expr_tree.exc)
        self.cause = self.make_node(expr_tree.cause)
        if self.cause: raise NotImplementedError()

    def eval_node(self, printer, ctx):
        yield from self.exc.evaluate(printer, ctx)

class ReturnNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        if self.value:
            yield from self.value.evaluate(printer, ctx)
            for var_type in self.value.var_types(printer, ctx):
                ctx.returns.append(var_type)

class AttributeNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.value = self.make_node(expr_tree.value)
        self.attr = expr_tree.attr
        self.ctx = self.make_node(expr_tree.ctx)
        if self.ctx: raise NotImplementedError()

    def eval_node(self, printer, ctx):
            yield from self.value.evaluate(printer, ctx)

    def get_callee(self, printer, ctx):
        name = self.value.var_name(printer, ctx)
        if name in ctx.variables:
            var_types = list(self.filter_var_types(name, ctx))
            if var_types:
                for var_type in var_types:
                    yield getattr(var_type, self.attr)
            else: printer("! inaccessible function:", name + "." + self.attr)
        else: printer("! inaccessible variable:", name)

    def filter_var_types(self, name, ctx):
        for var_type in ctx.variables[name].types:
            if self.attr in dir(var_type):
                yield var_type

