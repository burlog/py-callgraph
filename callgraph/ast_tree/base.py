# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph base ast node.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from callgraph.symbols import InvalidSymbol

class NodeLocalVariables(object):
    pass

class NodeRegistry(type):
    """ Metaclass that registers all subclasses for make_node method.
    """

    def __new__(cls, name, bases, cls_dict):
        child_cls = type.__new__(cls, name, bases, cls_dict)
        return child_cls.registry.setdefault(name.lower(), child_cls)

class NodeFactory(object, metaclass=NodeRegistry):
    """ Node factory that contains methods for creating new node instancies
        from python.ast nodes.
    """

    registry = {}

    def make_node(self, expr):
        if not expr: return None
        node_name = (expr.__class__.__name__ + "Node").lower()
        return NodeFactory.registry.get(node_name, UnknownNode)(self, expr)

    def make_nodes(self, ast_list):
        return list(map(self.make_node, ast_list or []))

    @classmethod
    def make_root_node(cls, expr):
        return cls.make_node(None, expr)

    @classmethod
    def make_root_nodes(cls, ast_list):
        return list(map(cls.make_root_node, ast_list or []))

class NodeBase(object):
    """ Node base class that contains implementation of common
        functionality for all AST nodes.
    """

    def __init__(self, parent, expr_tree):
        self.local = NodeLocalVariables()
        self.ast_name = expr_tree.__class__.__name__
        if hasattr(expr_tree, "lineno"):
            self.lineno = expr_tree.lineno - 1
        else:
            self.lineno = parent.lineno
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

    def evaluate(self, printer, ctx):
        ctx.builder.set_current_lineno(printer, self.lineno)
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
        return repr(obj)

    def __repr__(self):
        fields = iter(f + "=" + self.field_repr(f) for f in self._fields)
        return "{0}({1})".format(self.__class__.__name__, ", ".join(fields))

class Node(NodeFactory, NodeBase):
    """ This class is interface that all AST nodes should implement.
    """

    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)

    def eval_node(self, printer, ctx):
        for field in self.node_fields():
            yield from field.evaluate(printer, ctx)

    def load(self, printer, ctx):
        printer("? Can't load symbol:", self)
        return InvalidSymbol(ctx.builder, "__none__")

    def store(self, printer, ctx, value):
        printer("? Can't store symbol:", self)

class UnknownNode(Node):
    """ The class for all nodes that are not implemented.
    """

    def __init__(self, parent, expr_tree):
        super().__init__(parent, expr_tree)
        self._fields.append("ast_name")

    def evaluate(self, printer, ctx):
        printer("! Skipping unknown ast node:", self)
        while False: yield None

class LoadNode(Node):
    pass

class StoreNode(Node):
    pass

