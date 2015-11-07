# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph hooks for evetns during building callgraph.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

class Event(object):
    def __init__(self, builder, **kwargs):
        self.filename = builder.tot.filename
        self.lineno = builder.current_lineno
        self.function_qualname = builder.tot.qualname
        self.function_name = builder.tot.name
        self.line = builder.tot.source_line(file_lineno=self.lineno)
        for k, v in kwargs.items(): setattr(self, k, v)

class Hook(object):
    def __init__(self, builder, name):
        self.name = name
        self.builder = builder
        self.events = []

    def __call__(self, **kwargs):
        self.events.append(Event(self.builder, **kwargs))

class Hooks(object):
    def __init__(self, builder):
        self.hooks = {}
        self.builder = builder

    def __getattr__(self, name):
        return self.hooks.setdefault(name, Hook(self.builder, name))

    def __iter__(self):
        yield from self.hooks.values()

    def clear(self):
        self.hooks.clear()

