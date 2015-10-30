# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph helpers for ast nodes.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

class VariablesContext(object):
    def __init__(self, dst):
        self.dst, self.keys = dst, list(dst.keys())

    def __enter__(self):
        print(">>>", self.keys)
        pass

    def __exit__(self, exp_type, exp_value, traceback):
        print("<<<", self.keys)
        map(self.dst.pop, self.keys)

class UniqueNameGenerator(object):
    """ Generates unique names.
    """

    counter = 0

    def make_unique_name(self, prefix="unique_name"):
        UniqueNameGenerator.counter += 1
        return "{0}_{1}".format(prefix, UniqueNameGenerator.counter)


