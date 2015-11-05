# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Test suite for variable assigns.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import pytest, re
from functools import wraps

from callgraph.builder import CallGraphBuilder
from tests.helpers import dfs_node_names

def test_self_obj_simple():
    class A(object):
        def __init__(self):
            self.a = ""

        def method(self):
            self.a.rstrip()

    def fun():
        a = A()
        a.method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method", "fun.method.rstrip"]
    assert list(dfs_node_names(root)) == path

def test_self_obj_sharing_between_calls():
    class A(object):
        def __init__(self):
            self.a = ""

        def method(self):
            self.a.rstrip()

    def fun1(a):
        a.method()

    def fun():
        a = A()
        fun1(a)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.fun1", "fun.fun1.method",
            "fun.fun1.method.rstrip"]
    assert list(dfs_node_names(root)) == path

def test_self_obj_change_out_of_obj():
    class A(object):
        def __init__(self):
            pass

        def method(self):
            self.a.rstrip()

    def fun():
        a = A()
        a.a = ""
        a.method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method", "fun.method.rstrip"]
    assert list(dfs_node_names(root)) == path

