# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Test suite for constants.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import pytest, re
from functools import wraps

from callgraph.builder import CallGraphBuilder
from tests.helpers import dfs_node_names

def test_const_load():
    def fun():
        "".strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_const_set():
    def fun():
        a = {1, 2, 3}
        a.add(4)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.add"]
    assert list(dfs_node_names(root)) == path

def test_const_dict():
    def fun():
        a = {"a": 1, None: 2, fun: "3"}
        a.get("a")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.get"]
    assert list(dfs_node_names(root)) == path

def test_const_ellipsis():
    def fun():
        a = ...

    fun()
    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun"]
    assert list(dfs_node_names(root)) == path


