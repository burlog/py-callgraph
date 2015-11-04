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
from inspect import iscode, getclosurevars

from callgraph.utils import getsource

def_re = re.compile("^def", re.MULTILINE)
class_re = re.compile("^class", re.MULTILINE)

def scan_globals(function, name):
    return function.__globals__.get(name, None)

def scan_closure(function, name):
    closure_vars = getclosurevars(function)
    return closure_vars.nonlocals.get(name,
               closure_vars.globals.get(name,
                   closure_vars.builtins.get(name, None)))

def scan_const(function, name):
    # TODO(burlog): this is ugly bad code that should be improved
    for obj in function.__code__.co_consts:
        if not iscode(obj): continue
        if not obj.co_name == name: continue
        source = getsource(obj)
        if def_re.search(source):
            # TODO(burlog): closure, globals, ...
            try:
                return FunctionType(obj, function.__globals__.copy())
            except TypeError: return None
        if class_re.search(source):
            ## TODO(burlog): this is really ugly bad code
            class_dict = {}
            eval(obj, function.__globals__.copy(), class_dict)
            return type(name, (), class_dict)

def scan_builtins(function, name):
    return builtins.__dict__.get(name, None)

def find_object(function, name):
    # TODO(burlog): const don't respect decorators
    for scan in scan_globals, scan_closure, scan_const, scan_builtins:
        value = scan(function, name)
        if value is not None: return value

