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

def test_simple_assign():
    def fun():
        a = ""
        a.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_simple_explode_assign():
    def fun():
        a, b = "", 1
        c, d = ["", 2]
        a.lstrip()
        c.rstrip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.lstrip", "fun.rstrip"]
    assert list(dfs_node_names(root)) == path

def test_nested_explode_assign():
    def fun():
        (a, b), c = ("", []), 1
        a.strip()
        b.append(None)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.append"]
    assert list(dfs_node_names(root)) == path

def test_fun_explode_assign():
    def explode():
        return "", 1

    def fun():
        a, b = explode()
        a.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.explode", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_multi_assign():
    def fun():
        a = b = ""
        a.strip()
        b.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_assign_from_fun_str():
    def fun1():
        return ""

    def fun():
        a = fun1()
        a.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_assign_from_fun_obj():
    class A(object):
        def method(self):
            pass

    def fun1():
        return A()

    def fun():
        a = fun1()
        a.method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun1.A", "fun.method"]
    assert list(dfs_node_names(root)) == path

def test_assign_from_fun_var():
    class A(object):
        def method(self):
            pass

    def fun1():
        a = A()
        return a

    def fun():
        a = fun1()
        a.method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun1.A", "fun.method"]
    assert list(dfs_node_names(root)) == path

def test_cond_assign():
    def fun():
        a = 3 if None else "3"
        a.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip"]
    assert list(dfs_node_names(root)) == path

