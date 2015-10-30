# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Some small utils.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import re, ast
from itertools import islice

indent_re = re.compile("(^[ \t]*)")

def strip_indent(lines):
    indent = indent_re.search(lines[0]).group(0)
    for line in lines:
        if not line.startswith(indent) and not indent_re.match(line):
            break
        yield line[len(indent):]

def skip_leader(lines):
    leader = 0
    for line in lines:
        if line and line[0] in " \t\r\n": break
        leader += 1
    return leader

def getsource(code):
    if "__code__" in dir(code): code = code.__code__
    lines = open(code.co_filename).readlines()
    lines = list(strip_indent(lines[code.co_firstlineno - 1:]))
    leader = skip_leader(lines)
    for i, line in enumerate(islice(lines, leader, None)):
        if line and line[0] not in " \t\r\n":
            return "".join(lines[:i + leader])
    return "".join(lines)

