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

def test_args_simple():
    def fun1(a):
        a.strip()

    def fun():
        a = ""
        fun1(a)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun1.strip"]
    assert list(dfs_node_names(root)) == path

def test_args_kwarg():
    def fun1(a):
        a.strip()

    def fun():
        a = ""
        fun1(a=a)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun1.strip"]
    assert list(dfs_node_names(root)) == path

def test_args_from_return():
    def fun1(a):
        a.strip()

    def fun2():
        return ""

    def fun():
        fun1(fun2())

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun2", "fun.fun1", "fun.fun1.strip"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="explode tuple result values")
def test_args_stararg():
    def fun1(a):
        a.strip()

    def fun():
        a = [""]
        fun1(*a)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun1.strip"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="explode dict result values")
def test_args_starkwarg():
    def fun1(a):
        a.strip()

    def fun():
        a = {a: ""}
        fun1(**a)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun1.strip"]
    assert list(dfs_node_names(root)) == path

