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
                if not self: raise RuntimeError()

            def method():
                if not self: raise RuntimeError()

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
                if not self: raise RuntimeError()

            @staticmethod
            def static_method(x=None):
                if x: raise RuntimeError()

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
                if not self: raise RuntimeError()

            @classmethod
            def class_method(x=None):
                if x: raise RuntimeError()

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
                if not self: raise RuntimeError()

            def method_b():
                if not self: raise RuntimeError()

        class A(object):
            def __init__(self):
                if not self: raise RuntimeError()

            def method_b():
                if not self: raise RuntimeError()

            def method_a(cls):
                if not cls: raise RuntimeError()

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

