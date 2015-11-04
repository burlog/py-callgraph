# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph representations.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from cached_property import cached_property

from callgraph.code import make_code

class NodePath(object):
    def __init__(self, leaf):
        self.leaf = leaf

    def __iter__(self):
        current = self.leaf
        while current.parent:
            yield current
            current = current.parent

    def __contains__(self, other):
        for current in self:
            if current.id == other.id:
                return True
        return False

class Children(object):
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)

    def __iter__(self):
        yield from self.children

    def __contains__(self, other):
        for current in self.children:
            if current.id == other.id:
                return True
        return False

class Node(object):
    def __init__(self, symbol):
        self.root = None
        self.parent = None
        self.children = Children()
        if symbol:
            self.symbol = symbol
            self.code = make_code(symbol.value)

    @property
    def cls_name(self):
        return self.__class__.__name__

    @property
    def id(self):
        return self.code.id

    @property
    def name(self):
        if self.code.is_opaque: return self.symbol.name
        if self.code.ast.name == "__init__": return self.symbol.name
        return self.code.ast.name

    @property
    def qualname(self):
        return self.symbol.qualname

    @property
    def decorated_by(self):
        return self.code.decorated_by

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

    def source_line(self, i):
        return self.code.source_line(i)

    def attach(self, child):
        if child in self.children: return
        self.children.append(child)
        child.root = self.root
        child.parent = self
        return child

    def __repr__(self):
        return "{0}(name={1}, id={2})".format(self.cls_name, self.name, self.id)

class RootNode(Node):
    def __init__(self):
        super().__init__(None)

    @property
    def name(self):
        return "__main__"

    @property
    def id(self):
        return "__main__"

def make_node(symbol):
    return Node(symbol)

