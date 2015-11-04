# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph operators ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from callgraph.ast_tree import Node
from callgraph.symbols import ConstantSymbol, MultiSymbol

class UnaryOpBaseNode(Node):
    def load(self, printer, ctx):
        return self.operand.load(printer, ctx)

class InvertNode(UnaryOpBaseNode):
    pass

class NotNode(UnaryOpBaseNode):
    def load(self, printer, ctx):
        return ConstantSymbol(True)

class UAddNode(UnaryOpBaseNode):
    pass

class USubNode(UnaryOpBaseNode):
    pass

class AddNode(Node):
    pass

class SubNode(Node):
    pass

class MultNode(Node):
    pass

class DivNode(Node):
    pass

class ModNode(Node):
    pass

class PowNode(Node):
    pass

class LShiftNode(Node):
    pass

class RShiftNode(Node):
    pass

class BitOrNode(Node):
    pass

class BitXorNode(Node):
    pass

class BitAndNode(Node):
    pass

class FloorDivNode(Node):
    pass

class AndNode(Node):
    pass

class OrNode(Node):
    pass

class EqNode(Node):
    pass

class NotEqNode(Node):
    pass

class LtNode(Node):
    pass

class LtENode(Node):
    pass

class GtNode(Node):
    pass

class GtENode(Node):
    pass

class IsNode(Node):
    pass

class IsNotNode(Node):
    pass

class InNode(Node):
    pass

class NotInNode(Node):
    pass

# TODO(burlog): operators can be overriden and I should look in theese functions
# TODO(burlog): do it in UnaryOpNode way

class UnaryOpNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.operator = self.make_node(expr_tree.op)
        self.operator.operand = self.make_node(expr_tree.operand)

    def eval_node(self, printer, ctx):
        yield from self.operator.evaluate(printer, ctx)

    def load(self, printer, ctx):
        return self.operator.load(printer, ctx)

class BinOpNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.left = self.make_node(expr_tree.left)
        self.operator = self.make_node(expr_tree.op)
        self.right = self.make_node(expr_tree.right)

    def eval_node(self, printer, ctx):
        yield from self.left.evaluate(printer, ctx)
        yield from self.operator.evaluate(printer, ctx)
        yield from self.right.evaluate(printer, ctx)

class BoolOpNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.operator = self.make_node(expr_tree.op)
        self.operands = self.make_nodes(expr_tree.values)

    def eval_node(self, printer, ctx):
        yield from self.operator.evaluate(printer, ctx)
        for operand in self.operands:
            yield from operand.evaluate(printer, ctx)

    def load(self, printer, ctx):
        symbols = iter(o.load(printer, ctx) for o in self.operands)
        return MultiSymbol("__boolop__", symbols)

class CompareNode(Node):
    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self.left = self.make_node(expr_tree.left)
        self.operators = self.make_nodes(expr_tree.ops)
        self.comparators = self.make_nodes(expr_tree.comparators)

    def eval_node(self, printer, ctx):
        yield from self.left.evaluate(printer, ctx)
        for operator in self.operators:
            yield from operator.evaluate(printer, ctx)
        for comparator in self.comparators:
            yield from comparator.evaluate(printer, ctx)

    def load(self, printer, ctx):
        return ConstantSymbol(True)

