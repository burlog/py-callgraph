# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph code wrappers.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import ast
from cached_property import cached_property
from inspect import isclass, isbuiltin

from callgraph.ast_tree import ASTTree
from callgraph.utils import getsource

class Code(object): # TODO(burlog): meta?
    @property
    def filename(self):
        return self.code.co_filename

    @property
    def lineno(self):
        return self.code.co_firstlineno

    @cached_property
    def source(self):
        return getsource(self.code)

    @cached_property
    def ast(self):
        return ASTTree(self.source)

    @property
    def wraps(self):
        return None

    def source_line(self, i):
        lines = self.source.split("\n")
        if 0 <= i < len(lines):
            line = lines[i]
            while line.endswith("\\"):
                i += 1
                line = line.rstrip(" \t\\") + " " + lines[i].lstrip(" \t")
            return line
        pattern = "# invalid lineno: lines={0}, line={1}"
        return pattern.format(len(lines), i)

class TransparentCode(Code):
    def __init__(self, obj):
        self.code = obj.__code__
        self.wrapped_obj = getattr(obj, "__wrapped__", None)

    @property
    def id(self):
        return "{0}:{1}".format(self.filename, self.lineno)

    @property
    def is_opaque(self):
        return False

    @property
    def wraps(self):
        return self.wrapped_obj

class LambdaCode(Code):
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.ast_tree.name = "__lambda__"

    @property
    def id(self):
        return "TODO(burlog): " + str(self.ast_tree)

    @property
    def is_opaque(self):
        return False

    @property
    def filename(self):
        return "TODO(burlog): nowhere"

    @property
    def lineno(self):
        return self.ast_tree.value.lineno

    @cached_property
    def source(self):
        return ""

    @cached_property
    def ast(self):
        return self.ast_tree

    def source_line(self, i):
        return "TODO(burlog): temporary nothing"

class OpaqueCode(Code):
    def __init__(self, obj):
        self.obj = obj

    @property
    def is_opaque(self):
        return True

class OpaqueMethodCode(OpaqueCode):
    def __init__(self, obj):
        super().__init__(obj)

    @property
    def id(self):
        return "python:{0}:{1}"\
               .format(self.obj.__self__.__class__.__name__,
                       self.obj.__name__)

class OpaqueFunctionCode(OpaqueCode):
    def __init__(self, obj):
        super().__init__(obj)

    @property
    def id(self):
        return "python:{0}"\
               .format(self.obj.__name__)

class OpaqueSlotCode(OpaqueCode):
    def __init__(self, obj, aux_name):
        super().__init__(obj)
        self.aux_name = aux_name

    @property
    def id(self):
        return "python:{0}:{1}:{2}:{3}"\
               .format(self.obj.__objclass__.__class__.__name__,
                       self.obj.__objclass__.__qualname__,
                       self.aux_name,
                       self.obj.__name__)

class InvalidCode(OpaqueCode):
    def __init__(self, obj):
        super().__init__(obj)

    @property
    def id(self):
        return "python:{0}"\
               .format(self.obj)

def make_code(obj, aux_name=""):
    if "__code__" in dir(obj):
        return TransparentCode(obj)
    if "__self__" in dir(obj):
        if "__class__" in dir(obj.__self__):
            return OpaqueMethodCode(obj)
    if "__objclass__" in dir(obj):
        return OpaqueSlotCode(obj, aux_name)
    if isclass(obj):
        return make_code(obj.__init__, aux_name=obj.__qualname__)
    if isbuiltin(obj): return OpaqueFunctionCode(obj)
    if isinstance(obj, ast.AST): return LambdaCode(obj)
    # TODO(burlog): __call__ and OpaqueFunctionCode is hack
    if "__call__" in dir(obj): return OpaqueFunctionCode(obj.__call__)
    return InvalidCode(obj)

