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

def test_args_stararg_simple():
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

def test_args_stararg_from_call():
    def fun2():
        return [""]

    def fun1(a):
        a.strip()

    def fun():
        fun1(*fun2())

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun2", "fun.fun1", "fun.fun1.strip"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="static list/tuple implementation")
def test_args_stararg_opaque():
    def fun1(a):
        a.strip()

    def fun():
        b = list("")
        for a in []:
            b.append(a)
        fun1(*b)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.list", "fun.append", "fun.fun1", "fun.fun1.strip"]
    assert list(dfs_node_names(root)) == path

def test_args_starkwarg_simple():
    def fun1(a):
        a.strip()

    def fun():
        a = {"a": ""}
        fun1(**a)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun1.strip"]
    assert list(dfs_node_names(root)) == path

def test_args_starkwarg_from_call():
    def fun2():
        return {"a": "1"}
        return {"b": "2"}
        return {"c": "3"}
        return {"a": 4}

    def fun1(a):
        a.strip()
        return a

    def fun():
        fun1(**fun2()).to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun2", "fun.fun1", "fun.fun1.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

