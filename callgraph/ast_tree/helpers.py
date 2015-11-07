# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph helpers for ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

class VariablesScope(object):
    def __init__(self, ctx):
        self.ctx, self.var_names = ctx, ctx.var_names.copy()

    def __enter__(self):
        return self

    def __exit__(self, exp_type, exp_value, traceback):
        for var_name in self.vars_in_scope(): self.ctx.scope.pop(var_name)

    def freeze(self):
        self.freezed_var_names = self.ctx.var_names.copy()

    def vars_in_scope(self):
        var_names = getattr(self, "freezed_var_names", self.ctx.var_names)
        yield from var_names - self.var_names

class UniqueNameGenerator(object):
    """ Generates unique names.
    """

    counter = 0

    def make_unique_name(self, prefix="unique_name"):
        UniqueNameGenerator.counter += 1
        return "{0}_{1}".format(prefix, UniqueNameGenerator.counter)

