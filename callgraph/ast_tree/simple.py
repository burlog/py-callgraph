# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph ast tree: constants.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from callgraph.ast_tree import Node
from callgraph.symbols import ConstantSymbol, IterableConstantSymbol

class PassNode(Node):
    pass

class BreakNode(Node):
    pass

class ContinueNode(Node):
    pass

class GlobalNode(Node):
    # TODO(burlog): change variable context?
    pass

class Nonlocal(Node):
    # TODO(burlog): change variable context?
    pass

class NameConstantNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = expr_tree.value

    def load(self, printer, ctx):
        return ConstantSymbol(ctx.builder, self.value)

class StrNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = expr_tree.s

    def load(self, printer, ctx):
        return ConstantSymbol(ctx.builder, self.value)

class BytesNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = expr_tree.s

    def load(self, printer, ctx):
        return ConstantSymbol(ctx.builder, self.value)

class NumNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.value = expr_tree.n

    def load(self, printer, ctx):
        return ConstantSymbol(ctx.builder, self.value)

class TupleNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.values = self.make_nodes(expr_tree.elts)

    def eval_node(self, printer, ctx):
        for value in self.values:
            yield from value.evaluate(printer, ctx)

    def load(self, printer, ctx):
        values = [value.load(printer, ctx) for value in self.values]
        return IterableConstantSymbol(ctx.builder, tuple, values)

    def store(self, printer, ctx, value):
        for dst, src in zip(self.values, value):
            dst.store(printer, ctx, src)

class ListNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.values = self.make_nodes(expr_tree.elts)

    def eval_node(self, printer, ctx):
        for value in self.values:
            yield from value.evaluate(printer, ctx)

    def load(self, printer, ctx):
        values = [value.load(printer, ctx) for value in self.values]
        return IterableConstantSymbol(ctx.builder, list, values)

    def store(self, printer, ctx, value):
        for dst, src in zip(self.values, value):
            dst.store(printer, ctx, src)

class SetNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.values = self.make_nodes(expr_tree.elts)

    def eval_node(self, printer, ctx):
        for value in self.values:
            yield from value.evaluate(printer, ctx)

    def load(self, printer, ctx):
        values = [value.load(printer, ctx) for value in self.values]
        return IterableConstantSymbol(ctx.builder, set, values)

class DictNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.keys = self.make_nodes(expr_tree.keys)
        self.values = self.make_nodes(expr_tree.values)

    def eval_node(self, printer, ctx):
        for key, value in zip(self.keys, self.values):
            yield from key.evaluate(printer, ctx)
            yield from value.evaluate(printer, ctx)

    def load(self, printer, ctx):
        values = [k.load(printer, ctx) for k in self.keys]
        return IterableConstantSymbol(ctx.builder, dict, values)

class EllipsisNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)

    def load(self, printer, ctx):
        return ConstantSymbol(ctx.builder, Ellipsis)

class KeywordNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.arg = expr_tree.arg
        self.value = self.make_node(expr_tree.value)

    def eval_node(self, printer, ctx):
        yield from self.value.evaluate(printer, ctx)

    def load(self, printer, ctx):
        return ConstantSymbol(ctx.builder, self.value)

