# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph representations.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from cached_property import cached_property
from operator import attrgetter

from callgraph.code import make_code

class NodePath(object):
    def __init__(self, leaf):
        self.leaf = leaf

    def __iter__(self):
        current = self.leaf
        while current.parent:
            yield current
            current = current.parent
        yield current

    def __contains__(self, other):
        for current in self:
            if current == other:
                return True
        return False

class Node(object):
    def __init__(self, symbol, invalid=False):
        self.root = None
        self.parent = None
        self.children = []
        self.recur_children = []
        self.invalid = invalid
        self.called_at = []
        self.symbol = symbol
        self.code = make_code(None if invalid else symbol.value)

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id

    @property
    def cls_name(self):
        return self.__class__.__name__

    @property
    def id(self):
        return self.code.id

    @property
    def name(self):
        if self.code.is_opaque: return self.symbol.name
        return self.code.ast.name

    @property
    def qualname(self):
        return self.symbol.qualname

    @property
    def filename(self):
        return self.code.filename

    @property
    def lineno(self):
        return self.code.lineno

    @property
    def source(self):
        return self.code.source

    @property
    def is_opaque(self):
        return self.code.is_opaque

    @property
    def ast(self):
        return self.code.ast

    def path_to_root(self):
        return NodePath(self)

    def source_line(self, fun_lineno=None, file_lineno=None):
        if fun_lineno is None and file_lineno is None:
            raise ValueError("The fun_lineno and file_lineno are both None")
        lineno = file_lineno - self.lineno if fun_lineno is None else fun_lineno
        return self.code.source_line(lineno)

    def attach(self, child, where=None):
        # handle recurrent calls
        for ancestor in self.path_to_root():
            if child == ancestor:
                if child not in self.recur_children:
                    self.recur_children.append(ancestor)
                ancestor.mark_called_at(where)
                return False

        # don't attach same child twice but share children between nodes
        for my_child in self.children:
            if my_child == child:
                child.children = my_child.children
                my_child.mark_called_at(where)
                break
        else: self.children.append(child)

        # update nodes 
        child.root = self.root
        child.parent = self
        child.mark_called_at(where)
        return True

    def mark_called_at(self, where):
        self.called_at.append(where)

    def __repr__(self):
        aux = ""
        if self.recur_children:
            rc = list(map(attrgetter("name"), self.recur_children))
            aux += ", recur_children={0}".format(rc)
        return "{0}(name={1}, id={2}{3})"\
               .format(self.cls_name, self.name, self.id, aux)

class InvalidNode(Node):
    def __init__(self, symbol):
        super().__init__(symbol, invalid=True)
        self.symbol = symbol

    @property
    def id(self):
        return "invalid:{0}".format(self.name)

    @property
    def name(self):
        return self.symbol.name

    @property
    def qualname(self):
        return self.symbol.name

    @property
    def is_opaque(self):
        return True

def make_node(symbol):
    if symbol and symbol.iscallable():
        return Node(symbol)
    return InvalidNode(symbol)

