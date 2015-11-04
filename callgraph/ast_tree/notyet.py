#          | Delete(expr* targets)
#          | Assign(expr* targets, expr value)
#          | AugAssign(expr target, operator op, expr value)
#
#
#          | Raise(expr? exc, expr? cause)
#          | Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)
#          | Assert(expr test, expr? msg)
#
#          | Import(alias* names)
#          | ImportFrom(identifier? module, alias* names, int? level)
#
#          | Lambda(arguments args, expr body)
#          | ListComp(expr elt, comprehension* generators)
#          | SetComp(expr elt, comprehension* generators)
#          | DictComp(expr key, expr value, comprehension* generators)
#          | GeneratorExp(expr elt, comprehension* generators)

#
#          -- the following expression can appear in assignment context
#          | Subscript(expr value, slice slice, expr_context ctx)
#          | Starred(expr value, expr_context ctx)
#          | Name(identifier id, expr_context ctx)
#
#           -- col_offset is the byte offset in the utf8 string the parser uses
#           attributes (int lineno, int col_offset)
#
#     expr_context = Load | Store | Del | AugLoad | AugStore | Param
#
#     slice = Slice(expr? lower, expr? upper, expr? step)
#           | ExtSlice(slice* dims)
#           | Index(expr value)
#
#     comprehension = (expr target, expr iter, expr* ifs)
#
#     excepthandler = ExceptHandler(expr? type, identifier? name, stmt* body)
#                     attributes (int lineno, int col_offset)
#
#     arguments = (arg* args, arg? vararg, arg* kwonlyargs, expr* kw_defaults,
#                  arg? kwarg, expr* defaults)
#
#     arg = (identifier arg, expr? annotation)
#            attributes (int lineno, int col_offset)
#
#     -- keyword arguments supplied to call
#     keyword = (identifier arg, expr value)
#
#     -- import name with optional 'as' alias.
#     alias = (identifier name, identifier? asname)
#

