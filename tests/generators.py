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

def test_generators_multi():
    def generator():
        yield ""

    def fun():
        a = generator()
        if None: a = None
        for entry in a:
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

def test_generators_two_yields():
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

def test_generators_object_yield():
    class A(object):
        def __init__(self):
            pass

        def __iter__(self):
            yield ""

    def fun():
        for entry in A():
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.__iter__", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_object_next():
    class A(object):
        def __init__(self):
            pass

        def __iter__(self):
            return self

        def __next__(self):
            return ""

    def fun():
        for entry in A():
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.__iter__", "fun.__next__", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_from_gener_var():
    def generator():
        yield ""

    def fun():
        a = generator()
        for entry in a:
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.generator", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_from_obj_var():
    class A(object):
        def __init__(self):
            pass

        def __iter__(self):
            return self

        def __next__(self):
            return ""

    def fun():
        a = A()
        for entry in a:
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.__iter__", "fun.__next__", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_from_two_obj():
    class B(object):
        def __init__(self):
            pass

        def __next__(self):
            return ""

    class A(object):
        def __init__(self):
            pass

        def __iter__(self):
            return B()

    def fun():
        for entry in A():
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.__iter__", "fun.__iter__.B", "fun.__next__",
            "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_from_gener_fun():
    def generator():
        yield ""

    def indirect():
        return generator()

    def fun():
        for entry in indirect():
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.indirect", "fun.indirect.generator", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_from_gener_two_fun():
    def generator():
        yield ""

    def indirect2():
        return generator()

    def indirect1():
        return indirect2()

    def fun():
        for entry in indirect1():
            entry.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.indirect1", "fun.indirect1.indirect2",
            "fun.indirect1.indirect2.generator", "fun.strip"]
    assert list(dfs_node_names(root)) == path

def test_generators_from_obj_and_gener():
    def generator():
        yield ""

    class A(object):
        def __init__(self):
            pass

        def __iter__(self):
            return generator() if None else 3

    def fun():
        for entry in A():
            entry.strip()
            entry.to_bytes(1, "big")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.__iter__", "fun.__iter__.generator",
            "fun.strip"]
    assert list(dfs_node_names(root)) == path

