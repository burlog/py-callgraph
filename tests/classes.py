# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Test suite for classes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import pytest, re
from functools import wraps

from callgraph.builder import CallGraphBuilder
from tests.helpers import dfs_node_names

def test_classes_in_class_call():
    def fun():
        def fun1():
            pass
        class A:
            a = fun1()
            def f(self):
                pass

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1"]
    assert list(dfs_node_names(root)) == path

def test_classes_in_class_call_seq():
    def fun():
        def fun1():
            return ""
        class A:
            a = fun1()
            a.strip()
        a.find() # a is invisible outside of class

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_classes_base_class():
    class A(object):
        def method_a(self):
            pass

    class B(A):
        def method_b(self):
            pass

    def fun():
        b = B()
        b.method_a()
        b.method_b()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.object", "fun.method_a", "fun.method_b"]
    assert list(dfs_node_names(root)) == path

