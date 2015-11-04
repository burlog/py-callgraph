# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Simple indent enabled printer.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import sys

class IndentState(object):
    def __init__(self, indentation=4):
        self.current = 0
        self.indentation = indentation

class IndentPrinter(object):
    def __init__(self, indentation=4):
        self.indent_state = IndentState(indentation)

    def __call__(self, *args):
        sys.stdout.write(" " * self.indent_state.current)
        print(*args)

    def __enter__(self):
        self.indent_state.current += self.indent_state.indentation
        return self

    def __exit__(self, *args):
        self.indent_state.current -= self.indent_state.indentation

class NonePrinter(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

def dump_tree(parent, get_children, printer=IndentPrinter()):
    printer(parent)
    with printer as iprinter:
        for node in get_children(parent):
            dump_tree(node, get_children, iprinter)

def dump_ast_tree(parent, printer=IndentPrinter()):
    def get_children(ast_node):
        for field_name in getattr(ast_node[1], "_fields", []):
            field_value = getattr(ast_node[1], field_name)
            if isinstance(field_value, (tuple, list)):
                for sub_field_value in field_value:
                    yield field_name, sub_field_value
            else: yield field_name, field_value
    dump_tree(("root", parent), get_children, printer)

