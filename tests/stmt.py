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

def test_stmt_call_none():
    def fun():
        a = None
        a()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun"]
    assert list(dfs_node_names(root)) == path

def test_stmt_for_tuple():
    def fun1():
        for var in ("", 1):
            var.to_bytes()

    def fun():
        for var in ["", 1]:
            var.strip()
        fun1()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.fun1", "fun.fun1.to_bytes"]
    assert list(dfs_node_names(root)) == path

def test_stmt_for_none_and_tuple():
    def fun():
        var_list = ["", ""]
        if None: var_list = None
        for var1, var2 in var_list:
            var1.lstrip()
            var2.rstrip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.lstrip", "fun.rstrip"]
    assert list(dfs_node_names(root)) == path

def test_stmt_for_dict():
    def fun():
        for key in {"k1": 1, "k2": 2}:
            key.strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip"]
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
        f.write()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.open", "fun.__enter__", "fun.read", "fun.__exit__"]
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

    path = ["fun", "fun.A", "fun.__enter__", "fun.to_bytes", "fun.strip",
            "fun.__exit__"]
    assert list(dfs_node_names(root)) == path

def test_stmt_try():
    def fun():
        try:
            "".strip()
        except RuntimeError as e:
            print(e.with_traceback())

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.with_traceback", "fun.print"]
    assert list(dfs_node_names(root)) == path

def test_stmt_try_two_types():
    def fun():
        try:
            "".strip()
        except (RuntimeError, ValueError) as e:
            print(e.with_traceback())

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.with_traceback", "fun.print"]
    assert list(dfs_node_names(root)) == path

def test_stmt_try_two_except():
    def fun1(e):
        print(e.with_traceback())

    def fun():
        try:
            "".strip()
        except RuntimeError as e:
            print(e.with_traceback())
        except ValueError as e:
            fun1(e)

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip", "fun.with_traceback", "fun.print", "fun.fun1",
            "fun.fun1.with_traceback", "fun.fun1.print"]
    assert list(dfs_node_names(root)) == path

def test_stmt_try_empty_var():
    def fun():
        try:
            "".lstrip()
        except RuntimeError:
            "".rstrip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.lstrip", "fun.rstrip"]
    assert list(dfs_node_names(root)) == path

def test_stmt_try_empty():
    def fun():
        try:
            "".lstrip()
        except:
            "".rstrip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.lstrip", "fun.rstrip"]
    assert list(dfs_node_names(root)) == path

def test_stmt_try_finally():
    def fun():
        try:
            "".lstrip()
        except:
            "".rstrip()
        finally:
            "".index()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.lstrip", "fun.rstrip", "fun.index"]
    assert list(dfs_node_names(root)) == path

def test_stmt_try_else():
    def fun():
        try:
            "".lstrip()
        except:
            "".rstrip()
        else:
            "".index()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.lstrip", "fun.rstrip", "fun.index"]
    assert list(dfs_node_names(root)) == path

def test_stmt_raise_simple():
    def fun():
        raise RuntimeError()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.RuntimeError"]
    assert list(dfs_node_names(root)) == path

def test_stmt_raise_cause():
    def fun():
        try:
            pass
        except RuntimeError as e:
            raise RuntimeError() from e

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.RuntimeError"]
    assert list(dfs_node_names(root)) == path

def test_stmt_assert():
    def fun1():
        return 1

    def fun2():
        return 2

    def fun():
        assert fun1() == fun2()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.fun1", "fun.fun2"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="lambda implementation")
def test_stmt_lambda_simple():
    def fun():
        a = lambda x: x.strip()
        a("")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="lambda implementation")
def test_stmt_lambda_two_lambdas():
    def fun():
        a = lambda x: x.lstrip()
        b = lambda x: x.rstrip()
        a("")
        b("")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.lstrip", "fun.rstrip"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="lambda implementation")
def test_stmt_lambda_closure():
    def fun():
        y = ""
        a = lambda x: x.rstrip() and y.lstrip()
        a("")

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.rstrip", "fun.lstrip"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="lambda implementation")
def test_stmt_lambda_returns():
    def fun():
        a = lambda x: x
        a("").strip()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.strip"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="lambda implementation")
def test_stmt_lambda_in_ctor():
    class A:
        def __init__(self):
            a = lambda x: x.strip()
            a("")

    def fun():
        A()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.A", "fun.A.strip"]
    assert list(dfs_node_names(root)) == path

