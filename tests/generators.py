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

def test_generators_simple():
    def generator():
        yield ""

    def fun():
        for entry in generator():
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.generator", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_explode():
    def generator():
        yield "", 1

    def fun():
        for entry, i in generator():
            entry.strip()
            i.to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.generator", "fun.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

def test_generators_with_param():
    def generator(param):
        yield param

    def fun():
        for entry in generator(""):
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.generator", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_multi():
    def generator():
        yield ""
        yield 3

    def fun():
        for entry in generator():
            entry.strip()
            entry.to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.generator", "fun.strip", "fun.to_bytes"]
    assert list(dfs_node_names(root)) == path

def test_generators_yield_from():
    def generator2():
        yield ""

    def generator1():
        yield from generator2()

    def fun():
        for entry in generator1():
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.generator1", "fun.generator1.generator2", "fun.strip"]
    assert list(dfs_node_names(root)) == path

