# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph operators ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

#     expr = BoolOp(boolop op, expr* values)
#          | BinOp(expr left, operator op, expr right)
#          | UnaryOp(unaryop op, expr operand)

#     operator = Add | Sub | Mult | Div | Mod | Pow | LShift
#                  | RShift | BitOr | BitXor | BitAnd | FloorDiv
#
#     unaryop = Invert | Not | UAdd | USub
#
#     cmpop = Eq | NotEq | Lt | LtE | Gt | GtE | Is | IsNot | In | NotIn
#

#     boolop = And | Or
#

#          | Compare(expr left, cmpop* ops, expr* comparators)

