# -*- coding: utf-8 -*-
#
# LICENCE       Public Domain
#
# DESCRIPTION   Gather reachable symbols from enter function.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#
# Copyright (C) Michal Bukovsky
# All Rights Reserved
#
#       2015-09-11 (bukovsky)
#                  First draft
#

from functools import wraps
from itertools import islice, product
from types import FunctionType
import inspect, re, ast, sys, ctypes

#TODO(burlog): wrap the line will cause code_analyzer crash

C = None

def fake(a, b):
    def xfake():
        a, b
    global C
    C = xfake.__closure__

fake(1, 2)

def strip_indent(code):
    leading = next((i for i, c in enumerate(code) if c != " "), len(code))
    return re.sub("^" + " " * leading, "", code, flags=re.MULTILINE)

def zip_reversed(*args):
    return zip(*map(reversed, args))

def iter_fields(node, filter_callback = None):
    splat = (lambda args: filter_callback(*args)) if filter_callback else None
    for _, field in filter(splat, product([node], node._fields)):
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass

def iter_child_nodes(node, filter_callback = None):
    from ast import AST
    for name, field in iter_fields(node, filter_callback):
        if isinstance(field, AST):
            yield field
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, AST):
                    yield item

def walk(node, filter_callback = None):
    from collections import deque
    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(iter_child_nodes(node, filter_callback))
        yield node

def filter_node(nodes, Class, walk_filter_callback = None):
    is_class = lambda cls: isinstance(cls, Class)
    for node in nodes if isinstance(nodes, (tuple, list)) else [nodes]:
        for subnode in filter(is_class, walk(node, walk_filter_callback)):
            yield subnode

def no_if_tests(node, field):
    return not isinstance(node, ast.If) or field != "test"

def no_class_and_function_def(node, field):
    if isinstance(node, ast.ClassDef): return False
    if isinstance(node, ast.FunctionDef) and field in ("body"): return False
    return True

def skip_leader(lines):
    leader = 0
    for line in lines:
        if line and line[0] in " \t": break
        leader += 1
    return leader

def getsource(code):
    lines = open(code.co_filename).readlines()
    source = strip_indent("".join(lines[code.co_firstlineno - 1:]))
    lines = source.split("\n")
    leader = skip_leader(lines)
    for i, line in enumerate(islice(lines, leader, len(lines))):
        if line and line[0] not in " \t":
            return "\n".join(lines[:i + leader])
    return "\n".join(lines)

def strip_decors(source):
    lines = source.split("\n")
    for i, line in enumerate(lines):
        if line and line[0] not in "@ \t":
            return "\n".join(lines[i:])
    return ""

def expand_closure(function):
    for cell in function.__closure__ or []:
        #print("CELL", cell, cell.cell_contents, hasattr(cell.cell_contents, "func_closure"))
        if hasattr(cell.cell_contents, "__closure__"):
            if cell.cell_contents != function:
                for subcell in expand_closure(cell.cell_contents):
                    yield subcell
        yield cell.cell_contents

def dump_node(iprint, node):
    try:
        if iprint.indent_state.silent: return
        if isinstance(node, ast.ClassDef): return
        def print_node(node, stack):
            import sys
            from astdump import dumpattrs
            nodename = node.__class__.__name__
            sys.stdout.write(" " * iprint.indent_state.current)
            sys.stdout.write(" " * len(stack) * 2 + nodename + "->")
            dumpattrs(node, indent = len(stack) * 2, oneline = True)
        from astdump import TreeDumper, dumpattrs
        dumper = TreeDumper()
        iprint(100 * "=")
        dumper.dump(node, callback = print_node)
    except ImportError:
        iprint("Dump node unavailable due to missing astdump module.")
        iprint("You can install running this commands: pip install astdump")
        iprint("You can download it from https://pypi.python.org/pypi/astdump/")

def get_object(function, name):
    # its a global object
    obj = function.__globals__.get(name, None)
    if obj: return obj

    # or we can found it in function closure
    for obj in expand_closure(function):
        if inspect.isfunction(obj) or inspect.isclass(obj):
            if obj.__name__ == name:
                return obj

    # last chance is function consts 
    #print(name, function.func_code.co_consts)
    #print(dir(function))
    #print(function.__dict__)
    #print(function.func_dict)
    #for const in function.func_code.co_consts:
    #    if not inspect.iscode(const): continue
    #    if not const.co_name == name: continue
    #    source = strip_decors(getsource(const))
    #    if source.startswith("def"):
    #        # TODO(burlog): path should be improved
    #        #code = compile(source, const.co_filename, "exec")
    #        func_globals = function.func_globals.copy()
    #        func_globals["omit_file"] = "eeee"
    #        #print(C)
    #        closure = C
    #        o = FunctionType(const, func_globals, closure = closure)
    #        #print(o)
    #        return o
    #    elif source.startswith("class"):
    #        return ClassType(name, const)
    #        open("/tmp/xxx" + name + ".py", "w").write(source)
    #        import imp
    #        xxxA = imp.load_source("xxxA", "/tmp/xxx" + name + ".py")
    #        return getattr(xxxA, name)
    #                #print(xxxA.A)
    #                #module = compile(source, const.co_filename, mode="exec")
    #                #print("===========")
    #                #print(module.co_names)
    #                #print("===========")
    #                #obj = new.classobj(const, function.func_globals)

def format_function_id(function):
    filename = function.__code__.co_filename
    lineno = function.__code__.co_firstlineno
    return "{0}:{1}".format(filename, lineno)

class IndentState(object):
    def __init__(self, silent=False, indentation=4):
        self.current = 0
        self.indentation = indentation
        self.silent = silent

class IndentPrinter(object):
    def __init__(self, indent_state):
        self.indent_state = indent_state

    def __call__(self, *args):
        if self.indent_state.silent: return
        sys.stdout.write(" " * self.indent_state.current)
        print(*args)

    def __enter__(self):
        self.indent_state.current += self.indent_state.indentation
        return self

    def __exit__(self, *args):
        self.indent_state.current -= self.indent_state.indentation

class Symbol(object):
    def __init__(self, name, function, filename, lineno):
        self.name = name
        self.function = function
        self.filename = filename
        self.lineno = lineno

    def __repr__(self):
        return "Symbol(name={0}, function={1}, filename={2}, lineno={3}"\
               .format(self.name,
                       self.function.__name__,
                       self.filename,
                       self.lineno)

class Variable(object):
    def __init__(self, name, origin):
        self.name = name
        self.origin = origin

    def get_free_calls(self, expr):
        for call in filter_node(expr, ast.Call):
            if isinstance(call.func, ast.Name):
                yield call.func.id, call

    def get_origins(self, iprint, function, return_map, bound_call):
        if isinstance(self.origin, ast.AST):
            for name, _ in self.get_free_calls(self.origin):
                obj = get_object(function, name)
                if not obj or inspect.isbuiltin(obj): continue
                # analyze simple bound cals
                if inspect.isclass(obj): yield obj
                # analyze bound class from functions results
                if inspect.isfunction(obj):
                    function_id = format_function_id(obj)
                    iprint("% process function results for call:",
                           "{0}.{1}(...):".format(self.name, bound_call))
                    for results in return_map.get(function_id, None) or []:
                        for cls in results:
                            iprint("% found variable class:", cls.__name__)
                            yield cls
        else:
            if isinstance(self.origin, (tuple, list)):
                for origin in self.origin: yield origin
            else: yield self.origin

class ReturnValue(object):
    def __init__(self, function, ret, variables, return_map):
        self.ret = ret
        self.function = function
        self.return_map = return_map
        self.variables = {}
        for name in filter_node(ret, ast.Name, no_if_tests):
            if name.id in variables:
                self.variables[name.id] = variables[name.id]

    def __iter__(self):
        def return_value_generator(retval):
            # at the first return classes ctors
            # as the second step forwards result from free calls
            for call in filter_node(self.ret, ast.Call):
                if not isinstance(call.func, ast.Name): continue
                obj = get_object(self.function, call.func.id)
                if not obj: continue
                if inspect.isclass(obj): yield obj
                elif inspect.isfunction(obj):
                    function_id = format_function_id(obj)
                    for results in retval.return_map(function_id):
                        for cls in results:
                            yield cls
            # TODO(burlog): bound_calls
            # as the last step return all classes from variables source
            #for var_name, origin in self.variables.iteritems():
            #    for cls in return_value_generator(origin):
            #        yield cls
        return return_value_generator(self)

class CodeAnlyzer(object):
    def __init__(self, symbol_matcher, global_variables = {}, silent=False):
        self.init(silent)
        self.symbol_matcher = symbol_matcher
        items = global_variables.items()
        self.global_variables = dict([k, Variable(k, v)] for k, v in items)

    def init(self, silent=False):
        self.processed = set()
        self.res = {}
        self.return_map = {}
        self.indent_state = IndentState(silent=silent)

    def print_banner(self, fprint, function, body):
        filename = function.__code__.co_filename
        lineno = function.__code__.co_firstlineno
        name, real_name = function.__name__, body.name
        extra = "<" + name + "> " if name != real_name else ""
        fprint("@ Analyzing: {0} {1}at {2}:{3}"\
               .format(real_name, extra, filename, lineno))

    def gather_symbols(self, iprint, function, where):
        for node in walk(where, no_class_and_function_def):
            if not isinstance(node, ast.Name): continue
            if self.symbol_matcher(node.id):
                iprint("* add symbol: {0}".format(node.id))
                filename = function.__code__.co_filename
                lineno = function.__code__.co_firstlineno + node.lineno - 1
                symbol = Symbol(node.id, function, filename, lineno)
                self.res.setdefault(node.id, []).append(symbol)

    def analyze(self, function, flush=True):
        if flush: self.init(self.indent_state.silent)
        # builtins or c/c++ functions have no code
        if not hasattr(function, "__code__"): return

        # handle recursive code
        function_id = format_function_id(function)
        if function_id in self.processed: return
        self.processed.add(function_id)

        # prepare source of the function for next usage
        variables = self.global_variables.copy()
        source = strip_indent(getsource(function.__code__))
        source_ast = ast.parse(source)
        fprint = IndentPrinter(self.indent_state)
        if not isinstance(source_ast, ast.Module): return
        if not isinstance(source_ast.body[0], ast.FunctionDef): return
        self.print_banner(fprint, function, source_ast.body[0])
        #dump_node(fprint, source_ast)

        # magic follows
        with IndentPrinter(self.indent_state) as iprint:
            #if flush: dump_node(iprint, source_ast.body[0])

            # gather all symbols that are in function signature
            self.gather_symbols(iprint, function, source_ast)

            # gather all variables defined in function signature
            args = source_ast.body[0].args
            for arg, default in zip_reversed(args.args, args.defaults):
                variables[arg.id] = Variable(arg.id, default)
            # TODO(burlog): dive into free/bound calls in args default

            # process body of function
            for expr in source_ast.body[0].body:
                self.gather_symbols(iprint, function, expr)
                self.analyze_expr(iprint, function, variables, expr)

            # process decorated function
            for decorated in expand_closure(function):
                self.analyze(decorated, flush=False)
            # process decorators
            for decor_name in source_ast.body[0].decorator_list:
                self.analyze_decor(iprint, function, decor_name)

    def analyze_decor(self, iprint, function, decor):
        for name, call in self.get_free_calls(decor):
            obj = get_object(function, name)
            if not obj or inspect.isbuiltin(obj): continue
            if inspect.isfunction(obj): self.analyze(obj, flush=False)
            elif inspect.isclass(obj): self.analyze(obj.__init__, flush=False)

    def analyze_expr(self, iprint, function, variables, expr):
        #dump_node(iprint, expr)

        # dive into called free functions and object ctors
        for name, free_call in self.get_free_calls(expr):
            obj = get_object(function, name)
            if not obj or inspect.isbuiltin(obj): continue
            if inspect.isfunction(obj): self.analyze(obj, flush=False)
            elif inspect.isclass(obj): self.analyze(obj.__init__, flush=False)

        # pickup variables assigment
        for target, origin in self.get_variable_assigns(expr):
            variables[target] = Variable(target, origin)
            iprint(". store variable: {0} [{1}]".format(target, origin))

        # dive into called bound functions
        for var_name, bound_call in self.get_bound_calls(expr):
            if var_name not in variables: continue
            args = iprint, function, self.return_map, bound_call
            for obj in variables[var_name].get_origins(*args):
                self.analyze(getattr(obj, bound_call, None), flush=False)

        # if there is return we must gather all possible return values
        function_id = format_function_id(function)
        for ret in filter_node(expr, ast.Return):
            retval = ReturnValue(function, ret, variables, self.return_map)
            self.return_map.setdefault(function_id, []).append(retval)
            iprint("_ return expr detected")

    def get_free_calls(self, expr):
        for call in filter_node(expr, ast.Call):
            if isinstance(call.func, ast.Name):
                yield call.func.id, call

    def get_variable_assigns(self, expr):
        for assign in filter_node(expr, ast.Assign, no_if_tests):
            for target in filter_node(assign.targets, ast.Name):
                yield target.id, assign.value

    def get_bound_calls(self, expr):
        for call in filter_node(expr, ast.Call):
            names, attr = [], call.func
            while isinstance(attr, ast.Attribute):
                names.append(attr.attr)
                if isinstance(attr.value, ast.Name):
                    names.append(attr.value.id)
                attr = attr.value
            if names: yield ".".join(reversed(names[1:])), names[0]

def print_matched_symbols(function, symbol_matcher, global_variables = {}):
    analyzer = CodeAnlyzer(symbol_matcher, global_variables)
    analyzer.analyze(function)
    print(100 * "=")
    for symbol in sorted(analyzer.res.items(), key=lambda x: x[0]):
        print("{0}: {1}".format(name, where))

def gather_symbols(function, symbol_matcher, global_variables = {}):
    #analyzer = CodeAnlyzer(symbol_matcher, global_variables, silent=True)
    analyzer = CodeAnlyzer(symbol_matcher, global_variables, silent=False)
    analyzer.analyze(function)
    return sorted(analyzer.res.items(), key=lambda x: x[0])

