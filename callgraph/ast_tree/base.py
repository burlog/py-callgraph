# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph base ast node.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

class NodeRegistry(type):
    """ Metaclass that registers all subclasses for make_node method.
    """

    def __new__(cls, name, bases, cls_dict):
        child_cls = type.__new__(cls, name, bases, cls_dict)
        return child_cls.registry.setdefault(name, child_cls)

class NodeFactory(object, metaclass=NodeRegistry):
    """ Node factory that contains methods for creating new node instancies
        from python.ast nodes.
    """

    registry = {}

    @classmethod
    def make_node(cls, expr):
        if not expr: return None
        node_name = expr.__class__.__name__ + "Node"
        if node_name in ("StoreNode", "LoadNode"): return None
        return cls.registry.get(node_name, UnknownNode)(expr)

    @classmethod
    def make_nodes(cls, ast_list):
        return list(map(cls.make_node, ast_list or []))

class NodeBase(object):
    """ Node base class that contains implementation of common
        functionality for all AST nodes.
    """

    def __init__(self, expr_tree):
        self.ast_name = expr_tree.__class__.__name__
        self.lineno = expr_tree.lineno - 1
        self._fields = []

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if hasattr(self, "_fields"):
            if name != "_fields" and name not in self._fields:
                self._fields.append(name)

    def node_fields(self):
        for field_name in self._fields:
            field_value = getattr(self, field_name)
            if isinstance(field_value, Node):
                yield field_value

    def all_fields(self):
        for field_name in self._fields:
            yield getattr(self, field_name)

    def evaluate(self, printer, ctx):
        printer("= Evaluating node:", self)
        with printer as iprinter:
            yield from self.eval_node(iprinter, ctx)

    def field_repr(self, obj):
        if isinstance(obj, str):
            obj = getattr(self, obj)
        if isinstance(obj, (tuple, list)):
            return "[" + ", ".join((map(self.field_repr, obj))) + "]"
        if isinstance(obj, Node):
            return obj.ast_name
        if isinstance(obj, str):
            return obj
        return repr(obj)

    def __repr__(self):
        fields = iter(f + "=" + self.field_repr(f) for f in self._fields)
        return "{0}({1})".format(self.__class__.__name__, ", ".join(fields))

class Node(NodeFactory, NodeBase):
    """ This class is interface that all AST nodes should implement.
    """

    def __init__(self, expr_tree):
        super().__init__(expr_tree)

    def eval_node(self, printer, ctx):
        for field in self.node_fields():
            yield from field.evaluate(printer, ctx)

    def get_callee(self, printer, ctx):
        printer("! Unimplemented callee extraction:", self)
        while False: yield None

    def var_name(self, printer, ctx):
        return None

    def var_types(self, printer, ctx):
        while False: yield None

    def call_types(self, printer, ctx):
        while False: yield None

    def assigment_value(self, i):
        return self

    def eval_assign(self, printer, ctx, value):
        printer("? ignoring assign for target:", self)

class UnknownNode(Node):
    """ The class for all nodes that are not implemented.
    """

    def __init__(self, expr_tree):
        super().__init__(expr_tree)
        self._fields.append("ast_name")

    def evaluate(self, printer, ctx):
        printer("! Skiping unknown ast node:", self)
        while False: yield None

