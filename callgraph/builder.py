# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph builder.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from inspect import signature, unwrap, getclosurevars
from operator import attrgetter

from callgraph.finder import find_decor_var
from callgraph.nodes import Node, RootNode, make_node
from callgraph.indent_printer import IndentPrinter, NonePrinter, dump_tree

class CallGraphBuilder(object):
    def __init__(self, global_variables=None, silent=False):
        self.printer = NonePrinter() if silent else IndentPrinter()
        #items = global_variables.items()
        #self.global_variables = dict([k, Variable(k, v)] for k, v in items)

    def print_banner(self, printer, node):
        extra = "<" + node.name + "> " if node.name != node.ast.name else ""
        printer("@ Analyzing: {0} {1}at {2}:{3}"\
                .format(node.ast.name, extra, node.filename, node.lineno))

    def build(self, function):
        self.root = RootNode()
        self.process(function, self.root)
        return self.root

    def process(self, function, parent, args=[], kwargs={}):
        # attach new node to parent list
        node = parent.attach(make_node(function))
        if not node: return

        # builtins or c/c++ objects have no code
        if node.is_opaque(): return

        # handle recursive code
        if node.id in parent.id_path_to_root(): return

        # print nice banner
        self.print_banner(self.printer, node)

        # magic follows
        with self.printer as iprinter:
            # TODO(burlog): process signature? are defaults run during import?
            self.inject_decorated(iprinter, function, node)
            self.inject_arguments(iprinter, function, args, kwargs, node)

            # process function body
            for expr in node.ast.body:
                lineno = node.lineno + expr.lineno
                iprinter("+ line at {0}:{1}".format(node.filename, lineno))
                iprinter("+", node.source_line(expr.lineno).strip())
                for callee, args, kwargs in expr.evaluate(iprinter, node):
                    self.process(callee, node, args, kwargs)

    def inject_arguments(self, printer, function, args, kwargs, node):
        bound = signature(function).bind_partial(*args, **kwargs)
        ## TODO(burlog): default args
        #for param in sig.parameters.values():
        #    if param.name not in bound.arguments
        #         if param.default is not param.empty:
        #             pass #ba.arguments[param.name] = param.default
        for name, value in bound.arguments.items():
            printer("% Binding argument:", name + "=" + str(value))
            node.replace_variable(name, value, node.lineno)

    def inject_decorated(self, printer, function, node):
        name, value = find_decor_var(function, node)
        if name:
            node.replace_variable(name, [value], node.lineno)
            printer("% Binding decorated:", name + "=" + str(value))
            node.decored_by = node.ast.name

if __name__ == "__main__":
    builder = CallGraphBuilder()
    root = builder.build(CallGraphBuilder.process)
    #from tests.functions import func2
    #root = builder.build(func2)
    print(80 * "=")
    dump_tree(root, lambda x: x.children)

