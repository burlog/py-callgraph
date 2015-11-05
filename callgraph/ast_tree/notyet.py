#          | Delete(expr* targets)
#          | AugAssign(expr target, operator op, expr value)
#          | Import(alias* names)
#          | ImportFrom(identifier? module, alias* names, int? level)
#
#          | ListComp(expr elt, comprehension* generators)
#          | SetComp(expr elt, comprehension* generators)
#          | DictComp(expr key, expr value, comprehension* generators)
#          | GeneratorExp(expr elt, comprehension* generators)
#
#          -- the following expression can appear in assignment context
#          | Subscript(expr value, slice slice, expr_context ctx)
#          | Starred(expr value, expr_context ctx)
#
#     expr_context = Load | Store | Del | AugLoad | AugStore | Param
#
#     slice = Slice(expr? lower, expr? upper, expr? step)
#           | ExtSlice(slice* dims)
#           | Index(expr value)
