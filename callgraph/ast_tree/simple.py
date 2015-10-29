# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph ast tree: constants.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from callgraph.ast_tree import Node

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
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.value = expr_tree.value

class StrNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.value = expr_tree.s

    def var_types(self, printer, ctx):
        yield str

class BytesNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.value = expr_tree.s

    def var_types(self, printer, ctx):
        yield bytes

class NumNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.value = expr_tree.n

    def var_types(self, printer, ctx):
        yield int

class TupleNode(Node):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self.values = self.make_nodes(expr_tree.elts)

    def eval_node(self, printer, ctx):
        for value in self.values:
            yield from value.evaluate(printer, ctx)

    def eval_assign(self, printer, ctx, value):
        for i, target in enumerate(self.values):
            target.eval_assign(printer, ctx, value.assigment_value(i))

    def assigment_value(self, i):
        return self.values[min(i, len(self.values) - 1)]

    def var_types(self, printer, ctx):
        yield tuple

class ListNode(TupleNode):
    def __init__(self, expr_tree):
        super().__init__(expr_tree)

    def var_types(self, printer, ctx):
        yield list

# TODO(burlog):
#          | Dict(expr* keys, expr* values)
#          | Set(expr* elts)
#          | Ellipsis

