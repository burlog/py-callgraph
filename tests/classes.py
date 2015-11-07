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

def test_classes_base_class_method():
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

def test_classes_base_class_super():
    class A(object):
        def __init__(self):
            self.a = "str"

    class B(A):
        def __init__(self):
            super().__init__()

        def method(self):
            self.a.strip()

    def fun():
        b = B()
        b.method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.B", "fun.B.__super__", "fun.B.A", "fun.method",
            "fun.method.strip"]
    assert list(dfs_node_names(root)) == path

def test_classes_self_between_fun():
    class A(object):
        def __init__(self):
            self.a = "str"

        def method(self):
            self.b = "str"

    def fun1():
        a = A()
        a.method()
        return a

    def fun():
        fun1().b.lstrip()
        b = A()
        b.a.rstrip()
        b.b.index()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun1.A", "fun.fun1.method", "fun.lstrip",
            "fun.A", "fun.rstrip"]

    assert list(dfs_node_names(root)) == path

def test_classes_self_between_vars():
    class A(object):
        def __init__(self):
            self.a = "str"

        def method(self):
            self.b = "str"

    def fun():
        a = A()
        a.method()
        a.b.strip()
        b = A()
        b.b.index()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_classes_self_two_ctor():
    class A(object):
        def __init__(self):
            self.a = "str"

    def fun():
        a = A()
        b = A()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A"]
    assert list(dfs_node_names(root)) == path

def test_classes_self_call_only_for_second_instance():
    class A(object):
        def __init__(self, p):
            p.strip()

    def fun():
        a = A(3)
        b = A("")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.A.strip"]
    assert list(dfs_node_names(root)) == path

#@pytest.mark.skipif(True, reason="instance")
def test_classes_assigment_into_class_after_instatiation():
    class A(object):
        def __init__(self):
            pass

    def fun():
        A.a = ""
        a = A()
        a.a.strip()
        A.b = 3
        a.b.to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

def test_classes_assigment_into_instance_after_instatiation():
    class A(object):
        def __init__(self):
            pass

    def fun():
        A.a = ""
        a = A()
        a.a.strip()
        a.b = 3
        a.b.to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

