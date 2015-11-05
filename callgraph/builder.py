# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph builder.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from inspect import signature, unwrap, getclosurevars, isclass, ismethod
from operator import attrgetter

from callgraph.symbols import UnarySymbol
from callgraph.nodes import RootNode, make_node
from callgraph.indent_printer import IndentPrinter, NonePrinter, dump_tree

# TODO(burlog): hooks
# TODO(burlog): make global registry of fuctions and what they return

class CallGraphBuilder(object):
    def __init__(self, global_variables=None, silent=False):
        self.printer = NonePrinter() if silent else IndentPrinter()
        # TODO(burlog): global_variables
        #items = global_variables.items()
        #self.global_variables = dict([k, Variable(k, v)] for k, v in items)

    def print_banner(self, printer, node):
        extra = "<" + node.qualname + "> " if node.qualname != node.name else ""
        printer("@ Analyzing: {0} {1}at {2}:{3}"\
                .format(node.ast.name, extra, node.filename, node.lineno))

    def make_kwargs_symbols(self, kwargs):
        return dict((k, UnarySymbol(k, v)) for k, v in kwargs.items())

    def build(self, function, kwargs={}):
        self.root = RootNode()
        symbol = UnarySymbol(function.__name__, function)
        self.process(symbol, self.root, kwargs=self.make_kwargs_symbols(kwargs))
        return self.root

    def process(self, symbol, parent, args=[], kwargs={}):
        # attach new node to parent list
        node = make_node(symbol)
        parent.attach(node)
        # TODO(burlog): cache processed symbols with same args/kwargs

        # builtins or c/c++ objects have no code
        if node.is_opaque: return

        # handle recursive code
        if node in parent.path_to_root(): return

        # print nice banner
        self.print_banner(self.printer, node)

        # magic follows
        with self.printer as printer:
            # TODO(burlog): process signature? are defs invoked during import?
            self.inject_arguments(printer, node, args, kwargs)

            # process function body
            for expr in node.ast.body:
                lineno = node.lineno + expr.lineno
                printer("+ line at {0}:{1}".format(node.filename, lineno))
                printer("+", node.source_line(expr.lineno).strip())
                for callee, args, kwargs in expr.evaluate(printer, node.symbol):
                    self.process(callee, node, args.copy(), kwargs.copy())

    def inject_arguments(self, printer, node, args, kwargs):
        # TODO(burlog): fix __init__ rubbish
        function = node.symbol.value.__init__ \
                if isclass(node.symbol.value) else node.symbol.value
        # TODO(burlog): fix __lambda__ objects
        import ast
        if isinstance(function, ast.AST): return

        # insert self if there is one
        sig = signature(function)
        if node.symbol.myself and sig.parameters:
            # TODO(burlog): better bound mehtod detection
            if next(iter(sig.parameters.keys())) == "self":
                args.insert(0, node.symbol.myself)
            else: return # TODO(burlog): starargs implementation

        # bind params
        bound = sig.bind_partial(*args, **kwargs)
        ## TODO(burlog): default args
        #for param in sig.parameters.values():
        #    if param.name not in bound.arguments
        #         if param.default is not param.empty:
        #             pass #ba.arguments[param.name] = param.default
        for name, value in bound.arguments.items():
            printer("% Binding argument:", name + "=" + str(value))
            node.symbol.set(name, value)

if __name__ == "__main__":
    builder = CallGraphBuilder()
    kwargs = {"self": CallGraphBuilder, "function": CallGraphBuilder.build}
    root = builder.build(CallGraphBuilder.build, kwargs)
    print(80 * "=")
    dump_tree(root, lambda x: x.children)

