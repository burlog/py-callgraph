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

def test_decorators_simple():
    def decorator(function):
        @wraps(function)
        def decorating():
            "".rstrip()
            return function()
        return decorating

    @decorator
    def decorated():
        "".lstrip()

    builder = CallGraphBuilder()
    root = builder.build(decorated)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["decorating", "decorating.rstrip", "decorating.decorated",
            "decorating.decorated.lstrip"]
    print("==")
    assert list(dfs_node_names(root)) == path

def test_decorators_chain():
    def kuku(function):
        @wraps(function)
        def decorating():
            return function()
        return decorating

    def decorator1(function):
        @wraps(function)
        def decorating1():
            return function()
        return decorating1

    def decorator2(function):
        @wraps(function)
        def decorating2():
            return function()
        return decorating2

    @decorator1
    @decorator2
    def decorated():
        pass

    builder = CallGraphBuilder()
    root = builder.build(decorated)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["decorating1", "decorating1.decorating2",
            "decorating1.decorating2.decorated"]
    assert list(dfs_node_names(root)) == path

def test_decorators_without_wrap():
    def decorator(function):
        def decorating():
            return function()
        return decorating

    @decorator
    def decorated():
        pass

    builder = CallGraphBuilder()
    root = builder.build(decorated)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["decorating", "decorating.decorated"]
    assert list(dfs_node_names(root)) == path

def test_decorators_no_decor():
    def decorator(function):
        return function

    @decorator
    def decorated():
        pass

    builder = CallGraphBuilder()
    root = builder.build(decorated)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["decorated"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="invoke decorator for FunctionDef")
def test_decorators_inner_decor():
    def decorator(function):
        @wraps(function)
        def decorating():
            return function()
        return function

    def fun():
        @decorator
        def decorated():
            pass
        decorated()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.decorating", "fun.decorating.decorated"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="invoke decorator for FunctionDef")
def test_decorators_inner_no_decor():
    def decorator(function):
        return function

    def fun():
        @decorator
        def decorated():
            pass
        decorated()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.decorator", "fun.decorated"]
    assert list(dfs_node_names(root)) == path

def test_decorators_no_call():
    def decorator(function):
        @wraps(function)
        def decorating():
            pass
        return decorating

    @decorator
    def decorated():
        pass

    builder = CallGraphBuilder()
    root = builder.build(decorated)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["decorating"]
    assert list(dfs_node_names(root)) == path

def test_decorators_calling_decorated():
    def decorator(function):
        @wraps(function)
        def decorating():
            return function()
        return decorating

    @decorator
    def decorated():
        pass

    def fun():
        decorated()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.decorating", "fun.decorating.decorated"]
    assert list(dfs_node_names(root)) == path

def test_decorators_parametrized():
    def decorator_maker(param):
        def decorator(function):
            @wraps(function)
            def decorating():
                return function(param)
            return decorating
        return decorator

    @decorator_maker("")
    def decorated(param):
        param.strip()

    builder = CallGraphBuilder()
    root = builder.build(decorated)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["decorating", "decorating.decorated", "decorating.decorated.strip"]
    assert list(dfs_node_names(root)) == path

def test_decorators_method():
    class DecoratorClass(object):
        def __init__(self):
            pass

        def decorator(self, function):
            @wraps(function)
            def decorating():
                return function()
            return decorating

    obj = DecoratorClass()

    @obj.decorator
    def decorated():
        pass

    builder = CallGraphBuilder()
    root = builder.build(decorated)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["decorating", "decorating.decorated"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="obj assignment and scan decor maker")
def test_decorators_class_decor():
    class decorator(object):
        def __init__(self, function):
            self.function = function
        def __call__(self, param):
            return self.function(param)

    @decorator
    def decorated(param):
        pass

    builder = CallGraphBuilder()
    root = builder.build(decorated)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["__call__", "__call__.decorated"]
    assert list(dfs_node_names(root)) == path

@pytest.mark.skipif(True, reason="discover class decor")
def test_decorators_class():
    def fun():
        def decorator(cls):
            def decorating():
                return cls()
            return decorating

        @decorator
        class DecoratedClass(object):
            def __init__(self):
                pass

            def method(self):
                pass

        obj = DecoratedClass()
        obj.method()

    builder = CallGraphBuilder()
    root = builder.build(fun)
    from callgraph.indent_printer import dump_tree
    dump_tree(root, lambda x: x.children)

    path = ["fun", "fun.decorating", "fun.decorating.DecoratedClass",
            "fun.method"]
    assert list(dfs_node_names(root)) == path

