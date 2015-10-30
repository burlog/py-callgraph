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

def test_ops_not():
    def fun():
        if not "".strip(): return
        (not "").to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

def test_ops_un_add():
    class Int(int):
        def __pos__(self):
            return self

        def test(self):
            pass

    def fun():
        a = Int()
        (+a).test()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.Int", "fun.test"]
    assert list(dfs_node_names(root)) == path

def test_ops_bin_add():
    def fun():
        if "".strip() + "".find(): return

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.find"]
    assert list(dfs_node_names(root)) == path

def test_ops_and():
    def fun():
        if 1 and "".strip(): return
        if 1 and 2 and "".find(): return
        if (1 and "").index(): return
        if (1 and "").to_bytes(1, "big"): return

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.find", "fun.index", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

def test_ops_cmp():
    def fun():
        if "".find() < "".strip(): return
        (1 < 2).to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.find", "fun.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="operators implementation")
def test_ops_add_returns_other_type():
    class Int(int):
        def __add__(self, other):
            return 1 + 2

    def fun():
        a = Int()
        b = Int()
        (a + b).to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.Int", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

