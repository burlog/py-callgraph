# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Test suite for cycle statements.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import pytest, re
from functools import wraps

from callgraph.builder import CallGraphBuilder
from tests.helpers import dfs_node_names

@pytest.mark.skipif(True, reason="explode foriter: tuple, yield, ...")
def test_stmt_for():
    def fun1():
        for var in ["", 1]:
            var.to_bytes()

    def fun():
        for var in ["", 1]:
            var.strip()
        fun1()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

def test_stmt_while():
    def fun():
        a = 1
        while "".strip():
            a.to_bytes(1, "bug")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

def test_stmt_with_empty():
    def fun():
        with open("f"):
            pass

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.open", "fun.__enter__", "fun.__exit__"]
    assert list(dfs_node_names(root)) == path

def test_stmt_with_opaque():
    def fun():
        with open("f") as f:
            f.read()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.open", "fun.__enter__", "fun.read", "fun.read",
            "fun.__exit__"]
    assert list(dfs_node_names(root)) == path

def test_stmt_with_single():
    class A(object):
        def __enter__(self):
            b = ""
            b.find()
            return b
        def __exit__(self, t, v, tb):
            c = ""
            c.index()

    def fun():
        with A() as a:
            a.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.__enter__", "fun.__enter__.find", "fun.strip",
            "fun.__exit__", "fun.__exit__.index"]
    assert list(dfs_node_names(root)) == path

def test_stmt_with_pair():
    class A(object):
        def __enter__(self):
            b = ""
            b.find()
            return b
        def __exit__(self, t, v, tb):
            c = ""
            c.index()

    class B(object):
        def __enter__(self):
            b = 3
            b.to_bytes(1, "big")
            return b
        def __exit__(self, t, v, tb):
            c = 3
            c.from_bytes("")

    def fun():
        with A() as a, B() as b:
            a.lower()
            b.bit_length()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.__enter__", "fun.__enter__.find", "fun.B",
            "fun.__enter__", "fun.__enter__.to_bytes", "fun.lower",
            "fun.bit_length", "fun.__exit__", "fun.__exit__.index",
            "fun.__exit__", "fun.__exit__.from_bytes"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="explode tuple result values")
def test_stmt_with_tuple():
    class A():
        def __enter__(self):
            return 1, ""
        def __exit__(self, t, v, tb):
            pass

    def fun():
        with A() as (a, b):
            a.to_bytes(1, "big")
            a.strip()
            b.to_bytes(1, "big")
            b.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.to_bytes", "fun.strip"]
    assert list(dfs_node_names(root)) == path

