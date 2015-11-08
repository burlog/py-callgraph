# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph builder.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from operator import attrgetter
from inspect import signature

from callgraph.hooks import Hooks
from callgraph.utils import AuPair
from callgraph.symbols import Symbol, UnarySymbol
from callgraph.symbols import IterableConstantSymbol, MappingConstantSymbol
from callgraph.nodes import make_node
from callgraph.indent_printer import IndentPrinter, NonePrinter, dump_tree

# TODO(burlog): hooks as callbacks
# TODO(burlog): properties tests
# TODO(burlog): process signature? are defs invoked during import?
# TODO(burlog): tests for global variables
# TODO(burlog): __getattr__, __getattribute__ overrides will be problem
# TODO(burlog): make result of list(), tuple(), dict(), ... iterable

class CallGraphBuilder(object):
    def __init__(self, global_variables={}, silent=False):
        self.printer = NonePrinter() if silent else IndentPrinter()
        self.global_symbols = self.make_kwargs_symbols(global_variables)
        self.hooks = Hooks(self)
        self.current_lineno = 0
        self.tot = None

    def print_banner(self, printer, node):
        extra = "<" + node.qualname + "> " if node.qualname != node.name else ""
        printer("@ Analyzing: {0} {1}at {2}:{3}"\
                .format(node.ast.name, extra, node.filename, node.lineno))

    def set_current_lineno(self, printer, expr_lineno):
        lineno = self.tot.lineno + expr_lineno
        if lineno == self.current_lineno: return
        self.current_lineno = lineno
        printer("+ line at {0}:{1}".format(self.tot.filename, lineno))
        printer("+", self.tot.source_line(expr_lineno).strip())

    def make_kwargs_symbols(self, kwargs):
        return dict((k, UnarySymbol(self, k, v)) for k, v in kwargs.items())

    def build(self, function, kwargs={}):
        self.root = None
        self.hooks.clear()
        symbol = UnarySymbol(self, function.__name__, function)
        return self.process(symbol, kwargs=self.make_kwargs_symbols(kwargs))

    def process(self, symbol, parent=None, args=[], kwargs={}):
        # attach new node to parent list
        node = make_node(symbol)
        with AuPair(self, node):
            if parent:
                where = parent.filename, self.current_lineno
                if not parent.attach(node, where): return node

            # builtins or c/c++ objects have no code
            if node.is_opaque: return node
            if not symbol.iscallable(): return node

            # print nice banner
            self.print_banner(self.printer, node)

            # magic follows
            with self.printer as printer:
                self.inject_arguments(printer, node, args, kwargs)
                self.process_function(printer, node, args, kwargs)
        return node

    def process_function(self, printer, node, args, kwargs):
        for expr in node.ast.body:
            for callee, args, kwargs in expr.evaluate(printer, node.symbol):
                self.process(callee, node, args.copy(), kwargs.copy())

    def inject_arguments(self, printer, node, args, kwargs):
        sig = signature(node.symbol.value)
        self.inject_self(printer, node, sig, args, kwargs)
        bound = sig.bind_partial(*args, **self.polish_kwargs(sig, kwargs))
        self.inject_defaults(printer, node, sig, bound)
        for name, value in bound.arguments.items():
            value_symbol = self.as_symbol(value)
            printer("% Binding argument:", name + "=" + str(value_symbol))
            node.symbol.set(name, value_symbol)

    def polish_kwargs(self, sig, kwargs):
        for param in sig.parameters.values():
            if param.kind == param.VAR_KEYWORD:
                return kwargs
        return dict(self.iter_kwargs(sig, kwargs))

    def iter_kwargs(self, sig, kwargs):
        for param in sig.parameters.values():
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                if param.name in kwargs:
                    yield param.name, kwargs[param.name]

    def inject_self(self, printer, node, sig, args, kwargs):
        if node.symbol.myself and sig.parameters:
            # TODO(burlog): better bound method detection
            if next(iter(sig.parameters.keys())) == "self":
                args.insert(0, node.symbol.myself)
            else:
                # TODO(burlog): improve detection logic
                kwargs["self"] = node.symbol.myself

    def inject_defaults(self, printer, node, sig, bound):
        for param in sig.parameters.values():
            if param.name not in bound.arguments:
                 if param.default is not param.empty:
                     symbol = UnarySymbol(self, param.name, param.default)
                     bound.arguments[param.name] = symbol

    def as_symbol(self, value):
        if isinstance(value, Symbol):
            return value
        elif isinstance(value, (tuple, list)):
            return IterableConstantSymbol(self, tuple, value)
        elif isinstance(value, dict):
            values = list(value.values())
            keys = list(UnarySymbol(self, "str", k) for k in value.keys())
            return MappingConstantSymbol(self, dict, keys, values)
        raise RuntimeError("Can't convert value to symbol: " + str(value))

# dogfooding build function
if __name__ == "__main__":
    builder = CallGraphBuilder()
    kwargs = {"self": CallGraphBuilder, "function": CallGraphBuilder.build}
    root = builder.build(CallGraphBuilder.build, kwargs)
    print(80 * "=")
    dump_tree(root, lambda x: x.children)

