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
from inspect import isroutine, isclass, isbuiltin
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
    def __init__(self, obj, name, local_name=None):
        self.obj = obj
        self.children = []
        self.root, self.parent = None, None
        self.local_name = local_name or name
        self.name = name
        self.decored_by = ""
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

    @property
    def real_local_name(self):
        return self.decored_by or self.local_name

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

    def get_child(self, obj):
        for child in self.children:
            if child.obj == obj:
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
        super().__init__(None, "root", *args, **kwargs)

    @property
    def id(self):
        return "root"

    def __repr__(self):
        return "RootNode()"

class OpaqueNode(Node):
    def __init__(self, obj, code):
        super().__init__(obj, obj.__qualname__, obj.__name__)
        # TODO(burlog): make global registry of fuctions and what they return
        if self.name == "open":
            import _io
            self.returns.append(_io.TextIOWrapper)
            self.returns.append(_io.BufferedReader)

    @property
    def id(self):
        return None

    def is_opaque(self):
        return True

    def __repr__(self):
        return "OpaqueNode(name={0})".format(self.name)

class OpaqueFunctionNode(Node):
    def __init__(self, obj, code):
        super().__init__(obj, obj.__qualname__, obj.__name__)
        self.code = code
        # TODO(burlog): make global registry of fuctions and what they return
        if self.name == "_IOBase.__enter__":
            import _io
            self.returns.append(_io.TextIOWrapper)
            self.returns.append(_io.BufferedReader)

    @property
    def id(self):
        return "python:{0}:{1}:{2}:{3}"\
               .format(self.code.__objclass__.__module__,
                       self.code.__objclass__.__name__,
                       self.local_name,
                       self.name)

    def is_opaque(self):
        return True

    def __repr__(self):
        return "OpaqueFunctionNode(name={0})".format(self.name)

class FunctionNode(Node):
    def __init__(self, obj, code):
        super().__init__(obj, obj.__qualname__, obj.__name__)
        self.code = code
        self.ast = ASTTree(self.source)
        self.return_classes = []

    @property
    def id(self):
        return "{0}:{1}".format(self.filename, self.lineno)

    @property
    def filename(self):
        return self.code.__code__.co_filename

    @property
    def lineno(self):
        return self.code.__code__.co_firstlineno

    @cached_property
    def source(self):
        return getsource(self.code)

    def get_object(self, name):
        return super().get_object(name) or find_object(self.code, name)

    def __repr__(self):
        db = ", decored_by=" + self.decored_by if self.decored_by else ""
        return "FunctionNode(name={0}{1})".format(self.name, db)

class InstanceNode(Node):
    def __init__(self, obj, code):
        cls = obj.__class__
        super().__init__(obj, cls.__qualname__, cls.__name__)
        print(dir(obj))
        self.code = code
        self.ast = ASTTree(self.source)
        self.return_classes = []

    @property
    def id(self):
        return "{0}:{1}".format(self.filename, self.lineno)

    @property
    def filename(self):
        return self.code.__code__.co_filename

    @property
    def lineno(self):
        return self.code.__code__.co_firstlineno

    @cached_property
    def source(self):
        return getsource(self.code)

    def get_object(self, name):
        return super().get_object(name) or find_object(self.code, name)

    def __repr__(self):
        #db = ", decored_by=" + self.decored_by if self.decored_by else ""
        return "InstanceNode(name={0})".format(self.name)

def make_routine_node(obj, code):
    if "__code__" in dir(code): return FunctionNode(obj, code)
    if "__objclass__" in dir(code): return OpaqueFunctionNode(obj, code)
    if "__func__" in dir(code): return FunctionNode(obj, code.__func__)
    if isbuiltin(code): return OpaqueNode(obj, code)
    raise NotImplementedError("Unknown object type %s" % str(obj))

def make_node(obj):
    if isroutine(obj): return make_routine_node(obj, obj)
    if isclass(obj):
        node = make_routine_node(obj, code=obj.__init__)
        node.returns.append(obj)
        return node
    if "__call__" in dir(obj):
        return InstanceNode(obj, code=obj.__call__.__func__)
    raise NotImplementedError("Unknown object type %s" % str(obj))

