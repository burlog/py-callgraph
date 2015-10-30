# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Finds and returns instacies of functions, classes, ...
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import ast, re, builtins
from types import FunctionType
from inspect import isfunction, isclass, iscode

from callgraph.utils import getsource

def expand_closure(function):
    for cell in function.__closure__ or []:
        if hasattr(cell.cell_contents, "__closure__"):
            if cell.cell_contents != function:
                for subcell in expand_closure(cell.cell_contents):
                    yield subcell
        yield cell.cell_contents

def scan_globals(function, name):
    return function.__globals__.get(name, None)

def scan_closure(function, name):
    for obj in expand_closure(function):
        if isfunction(obj) or isclass(obj):
            if obj.__name__ == name:
                return obj

def scan_const(function, name):
    # TODO(burlog): this is ugly bad code that should be improved
    for obj in function.__code__.co_consts:
        if not iscode(obj): continue
        if not obj.co_name == name: continue
        source = getsource(obj)
        if source.startswith("def"):
            # TODO(burlog): closure, globals, ...
            return FunctionType(obj, {})
        if source.startswith("class"):
            ## TODO(burlog): this is really ugly bad code
            class_dict = {}
            eval(obj, function.__globals__.copy(), class_dict)
            return type(name, (), class_dict)

def scan_builins(function, name):
    return builtins.__dict__.get(name, None)

def find_object(function, name):
    return scan_globals(function, name)\
        or scan_closure(function, name)\
        or scan_const(function, name)\
        or scan_builins(function, name)

