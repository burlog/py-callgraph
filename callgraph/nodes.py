# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph representations.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from operator import attrgetter
from abc import ABCMeta, abstractmethod
from inspect import isroutine, isclass
from cached_property import cached_property

from callgraph.utils import getsource
from callgraph.ast_tree import ASTTree
from callgraph.finder import find_object

class Variable(object):
    def __init__(self, name, types, lineno):
        self.name = name
        self.types = types
        self.lineno = lineno

class Node(metaclass=ABCMeta):
    def __init__(self, name, local_name=None):
        self.children = []
        self.root, self.parent = None, None
        self.local_name = local_name or name
        self.name = name
        self.variables = {}
        self.returns = []

    @property
    @abstractmethod
    def id(self):
        return None

    @property
    def filename(self):
        raise NotImplementedError()

    @property
    def lineno(self):
        raise NotImplementedError()

    @property
    def source(self):
        return ""

    def ids(self):
        return list(map(attrgetter("id"), self.children))

    def attach(self, child):
        if child.id in self.ids(): return
        self.children.append(child)
        child.root = self.root
        child.parent = self
        return child

    def path_to_root(self):
        current = self
        while current.parent:
            yield current
            current = current.parent

    def id_path_to_root(self):
        return map(attrgetter("id"), self.path_to_root())

    def is_opaque(self):
        return False

    def get_object(self, name):
        for child in self.children:
            if child.local_name == name:
                return child.obj
        return None

    def get_child(self, name):
        for child in self.children:
            if child.local_name == name:
                return child
        return None

    def source_line(self, i):
        lines = self.source.split("\n")
        if i > len(lines):
            return "# invalid lineno: lines={0}, line={1}".format(len(lines), i)
        line = lines[i]
        while line.endswith("\\"):
            i += 1
            line = line.rstrip(" \t\\") + " " + lines[i].lstrip(" \t")
        return line

    def replace_variable(self, name, types, lineno):
        self.variables[name] = Variable(name, types, lineno)

class RootNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__("root", *args, **kwargs)

    @property
    def id(self):
        return "root"

    def __repr__(self):
        return "RootNode()"

class OpaqueNode(Node):
    def __init__(self, obj):
        super().__init__(obj.__qualname__, obj.__name__)
        self.obj = obj

    @property
    def id(self):
        return None

    def is_opaque(self):
        return True

    def __repr__(self):
        return "OpaqueNode(name={0})".format(self.name)

class OpaqueFunctionNode(Node):
    def __init__(self, obj):
        super().__init__(obj.__qualname__, obj.__name__)
        self.obj = obj

    @property
    def id(self):
        return "python:{0}:{1}:{2}"\
               .format(self.obj.__objclass__.__module__,
                       self.obj.__objclass__.__name__,
                       self.obj.__name__)

    def is_opaque(self):
        return True

    def __repr__(self):
        return "OpaqueFunctionNode(name={0})".format(self.name)

class FunctionNode(Node):
    def __init__(self, obj):
        super().__init__(obj.__qualname__, obj.__name__)
        self.obj = obj
        self.ast = ASTTree(self.source)
        self.return_classes = []

    @property
    def id(self):
        return "{0}:{1}".format(self.filename, self.lineno)

    @property
    def filename(self):
        return self.obj.__code__.co_filename

    @property
    def lineno(self):
        return self.obj.__code__.co_firstlineno

    @cached_property
    def source(self):
        return getsource(self.obj)

    def get_object(self, name):
        return super().get_object(name) or find_object(self.obj, name)

    def __repr__(self):
        return "FunctionNode(name={0})".format(self.name)

def make_routine_node(obj):
    if "__code__" in dir(obj): return FunctionNode(obj)
    if "__objclass__" in dir(obj): return OpaqueFunctionNode(obj)
    if "__func__" in dir(obj): return FunctionNode(obj.__func__)
    raise NotImplementedError("Unknown object type %s" % str(obj))

def make_node(obj):
    # TODO(burlog): copy global variables
    if isclass(obj):
        node = make_routine_node(getattr(obj, "__init__"))
        node.local_name = obj.__name__
        node.returns.append(obj)
        return node
    if isroutine(obj): return make_routine_node(obj)
    raise NotImplementedError("Unknown object type %s" % str(obj))

