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

def test_methods_simple():
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
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method"]
    assert list(dfs_node_names(root)) == path

def test_methods_static():
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
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.static_method"]
    assert list(dfs_node_names(root)) == path

def test_methods_class():
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
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.class_method"]
    assert list(dfs_node_names(root)) == path

def test_methods_class_change():
    def fun():
        class B(object):
            def __init__(self):
                pass

            def method_b(self):
                pass

        class A(object):
            def __init__(self):
                pass

            def method_a(self):
                pass

        a = A()
        a.method_a()
        a = B()
        a.method_b()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method_a", "fun.B", "fun.method_b"]
    assert list(dfs_node_names(root)) == path

def test_methods_methods_mismatch():
    class A(object):
        def __init__(self):
            pass

        def f(self):
            return ""

    class B(object):
        def __init__(self):
            pass

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

def test_methods_self_init():
    def fun():
        class A(object):
            def __init__(self):
                self.method()

            def method(self):
                self.other_method()

            def other_method(self):
                pass

        A()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.A.method", "fun.A.method.other_method"]
    assert list(dfs_node_names(root)) == path

def test_methods_from_var():
    def fun():
        class A(object):
            def __init__(self):
                pass

            def method(self):
                pass

        a = A()
        b = a.method
        b()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method"]
    assert list(dfs_node_names(root)) == path

def test_methods_self_with_params():
    def fun():
        class A(object):
            def __init__(self):
                pass

            def method(self, a):
                self.other_method()
                a.strip()

            def other_method(self):
                pass

        a = A()
        a.method("")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.method", "fun.method.other_method",
            "fun.method.strip"]
    assert list(dfs_node_names(root)) == path

def test_methods_self_class():
    def fun():
        class A(object):
            def __init__(self):
                pass

            def method(self):
                pass

            @classmethod
            def class_method(cls):
                self.method()

            @staticmethod
            def static_method():
                self.method()

        a = A()
        a.class_method()
        a.static_method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.class_method", "fun.static_method"]
    assert list(dfs_node_names(root)) == path

def test_methods_missing():
    def fun():
        class B(object):
            def __init__(self):
                pass

            def method_b(self):
                "".lstrip()

        class A(object):
            def __init__(self):
                pass

            def method_b(self):
                "".rstrip()

        a = A()
        a = B()
        a.method_b()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.B", "fun.method_b", "fun.method_b.rstrip",
            "fun.method_b", "fun.method_b.lstrip"]
    assert list(dfs_node_names(root)) == path

def test_methods_str():
    def fun():
        a = str()
        a.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.object", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_methods_two_ctors_and_one_method():
    def fun():
        class B(object):
            def __init__(self):
                pass

            def method(self):
                "".lstrip()

        class A(object):
            def __init__(self):
                pass

            def method(self):
                "".rstrip()

        a = A() if None else B()
        a.method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.B", "fun.method", "fun.method.rstrip",
            "fun.method", "fun.method.lstrip"]
    assert list(dfs_node_names(root)) == path

def test_methods_two_ctors_and_two_methods():
    class A(object):
        def __init__(self):
            pass

        def f(self):
            return ""

    class B(object):
        def __init__(self):
            pass

        def f(self):
            return []

    def fun():
        a = A() if None else B()
        a.f().strip()
        a.f().sort()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path =  ["fun", "fun.A", "fun.B", "fun.f", "fun.f", "fun.strip", "fun.sort"]
    assert list(dfs_node_names(root)) == path

def test_methods_two_ctors_and_method_and_ctor():
    class A(object):
        def __init__(self):
            pass

        def f(self):
            return ""

    class B(object):
        def __init__(self):
            pass

        def f(self):
            return C

    class C(object):
        def __init__(self):
            pass

        def f(self):
            return []

    def fun():
        a = A() if None else B()
        a.f().strip()
        a.f()().f().sort()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.B", "fun.f", "fun.f", "fun.strip", "fun.C",
            "fun.f", "fun.sort"]
    assert list(dfs_node_names(root)) == path

