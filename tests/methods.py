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

def test_simple_methods():
    def fun():
        class A(object):
            def __init__(self):
                pass

            def method(self):
                pass

        a = A()
        a.method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    #from callgraph.indent_printer import dump_tree
    #dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method"]
    assert list(dfs_node_names(root)) == path

def test_static_methods():
    def fun():
        class A(object):
            def __init__(self):
                pass

            @staticmethod
            def static_method():
                pass

        a = A()
        a.static_method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    #from callgraph.indent_printer import dump_tree
    #dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.static_method"]
    assert list(dfs_node_names(root)) == path

def test_class_methods():
    def fun():
        class A(object):
            def __init__(self):
                pass

            @classmethod
            def class_method(cls):
                pass

        a = A()
        a.class_method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    #from callgraph.indent_printer import dump_tree
    #dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.class_method"]
    assert list(dfs_node_names(root)) == path

def test_class_change_methods():
    def fun():
        class B(object):
            def __init__(self):
                pass

            def method_b(self):
                pass

        class A(object):
            def __init__(self):
                pass

            def method_b(self):
                pass

            def method_a(self):
                pass

        a = A()
        a.method_a()
        a = B()
        a.method_a() # doesn't exist - shouldn't appear in tree
        a.method_b()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    #from callgraph.indent_printer import dump_tree
    #dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method_a", "fun.B", "fun.method_b"]
    assert list(dfs_node_names(root)) == path

def test_methods_mismatch():
    class A(object):
        def f(self):
            return ""

    class B(object):
        def f(self):
            return []

    def fun():
        A().f().strip()
        B().f().sort()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.f", "fun.strip", "fun.B", "fun.f", "fun.sort"]
    assert list(dfs_node_names(root)) == path

