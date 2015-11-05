# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph symbols representations.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import os
from functools import wraps
from itertools import chain
from inspect import isclass, isbuiltin
from abc import ABCMeta, abstractmethod

from callgraph.finder import find_object

def isiterable(symbol):
    return "__iter__" in dir(symbol)

class Symbol(metaclass=ABCMeta):
    def __init__(self, name):
        self.name = name
        self.scope = {}
        self.returns = []
        self.myself = None
        self.var_names = set()

    @abstractmethod
    def values():
        while False: yield None

    @abstractmethod
    def get():
        pass

    @abstractmethod
    def set():
        pass

    @property
    def cls_name(self):
        return self.__class__.__name__

    @property
    def qualname(self):
        return self.name

    def aux_repr(self):
        while False: yield None

    def __bool__(self):
        return True

    def __repr__(self):
        aux = ", ".join(self.aux_repr())
        return "{0}(name={1}{2}, returns=[{3}])"\
               .format(self.cls_name, self.name,
                       ", " + aux if aux else "",
                       ", ".join(map(lambda x: x.name, self.returns)))

class UnarySymbol(Symbol):
    def __init__(self, name, value):
        super().__init__(name)
        self.value = value
        if isclass(self.value):
            self.returns.append(self)
            self.myself = self

    @property
    def qualname(self):
        return getattr(self.value, "__qualname__", super().qualname)

    def values(self):
        yield self

    def get(self, name, free=True):
        if name in self.scope: return self.scope[name]
        if hasattr(self.value, name):
            symbol = UnarySymbol(name, getattr(self.value, name))
            symbol.myself = self
            return self.scope.setdefault(name, symbol)
        if free:
            symbol = find_symbol(self.value, name)
            return self.scope.setdefault(name, symbol)

    def set(self, name, value):
        assert isinstance(value, Symbol)
        if name in self.scope:
            value_list = chain(self.scope[name].values(), [value])
            self.scope[name] = MultiSymbol(name, value_list)
        else:
            self.scope[name] = value
            self.var_names.add(name)

    def aux_repr(self):
        yield "value=" + repr(self.value)

class ConstantSymbol(UnarySymbol):
    def __init__(self, value):
        super().__init__(type(value).__name__, value)
    # TODO(burlog): should make scope assigment impossible

class IterableConstantSymbol(ConstantSymbol):
    def __init__(self, cls, iterable):
        super().__init__(cls)
        self.iterable = iterable

    def __iter__(self):
        yield from self.iterable

    def aux_repr(self):
        yield from super().aux_repr()
        yield "iterable=[{0}]"\
              .format(", ".join(map(lambda x: x.name, self.iterable)))

class InvalidSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def get(self, name, free=True):
        return None

    def set(self, name, value):
        raise RuntimeError("You can't assing attribute to invalid symbol")

    def values(self):
        while False: yield None

    def __bool__(self):
        return False

    def __iter__(self):
        while True: yield self

class LambdaSymbol(Symbol):
    def __init__(self, args, body):
        super().__init__("__lambda__")
        self.args = args
        self.value = body

    def get(self, name, free=True):
        return None

    def set(self, name, value):
        raise RuntimeError("You can't assing attribute to lambda symbol")

    def values(self):
        yield self

    def __bool__(self):
        return True

    def __iter__(self):
        # TODO(burlog): can be lambda iterable?
        while True: yield self

class MultiSymbol(Symbol):
    def __init__(self, name, value_list):
        super().__init__(name)
        self.value_list = value_list

    @property
    def qualname(self):
        return "multi:" + super().qualname

    def values(self):
        for value in self.value_list:
            yield from value.values()

    def get(self, name, free=True):
        def list_values(attr_symbol):
            yield from iter(x.value for x in attr_symbol.value_list)
        attr_symbol = MultiSymbol(name, [])
        for symbol in filter(None, self.values()):
            assert not isinstance(symbol, MultiSymbol)
            attr = symbol.get(name, free)
            if not attr: continue
            for sub_attr in attr.values():
                if sub_attr.value not in list_values(attr_symbol):
                    attr_symbol.value_list.append(sub_attr)
                    attr_symbol.returns.extend(sub_attr.returns)
        return attr_symbol

    def set(self, name, value):
        assert isinstance(value, Symbol)
        for symbol in self.value_list:
            symbol.set(name, value)

    def aux_repr(self):
        yield from super().aux_repr()
        yield "values=[{0}]"\
              .format(", ".join(map(lambda x: x.name, self.value_list)))

    def __iter__(self):
        iterable = [symbol for symbol in filter(isiterable, self.values())]
        for symbols in zip(*iterable):
            iter_symbol = MultiSymbol(self.name, symbols)
            for symbol in symbols:
                iter_symbol.returns.extend(symbol.returns)
            yield iter_symbol

    def __bool__(self):
        return not not self.value_list

class BuiltinSymbol(UnarySymbol):
    def __init__(self, obj):
        super().__init__(obj.__name__, obj)

class OpenResultBuiltinSymbol(BuiltinSymbol):
    def __init__(self, obj):
        super().__init__(obj.__class__)
        self.get("__enter__").returns.append(self)

class OpenBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(open)
        self.returns.append(OpenResultBuiltinSymbol(open(os.devnull, "r")))

class DirBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(dir)
        self.returns.append(UnarySymbol("__returns__", type(dir())))

class GetattrBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(getattr)
        # TODO(burlog): we can add default to returns
        # TODO(burlog): we inspect static objects and add to returns...

class IsinstanceBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(isinstance)
        self.returns.append(UnarySymbol("__returns__", bool))

class PrintBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(print)

class CallableBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(callable)
        self.returns.append(UnarySymbol("__returns__", bool))

class IdBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(id)
        self.returns.append(UnarySymbol("__returns__", type(id(""))))

class HasattrBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(hasattr)
        self.returns.append(UnarySymbol("__returns__", bool))

class IterBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(iter)
        # TODO(burlog): we can guess types...

class LenBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(len)
        self.returns.append(UnarySymbol("__returns__", int))

class OrdBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(ord)
        self.returns.append(UnarySymbol("__returns__", int))

class MinBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(min)
        self.returns.append(UnarySymbol("__returns__", min))

class MaxBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(max)
        self.returns.append(UnarySymbol("__returns__", max))

class NextBuiltinSymbol(BuiltinSymbol):
    def __init__(self):
        super().__init__(next)
        # TODO(burlog): we can guess types...

def find_symbol(value, name):
    obj = find_object(value.__init__ if isclass(value) else value, name)
    if obj is None: return InvalidSymbol(name)
    if isbuiltin(obj) and not isclass(obj):
        if obj == open: return OpenBuiltinSymbol()
        if obj == dir: return DirBuiltinSymbol()
        if obj == getattr: return GetattrBuiltinSymbol()
        if obj == hasattr: return HasattrBuiltinSymbol()
        if obj == isinstance: return IsinstanceBuiltinSymbol()
        if obj == print: return PrintBuiltinSymbol()
        if obj == callable: return CallableBuiltinSymbol()
        if obj == id: return IdBuiltinSymbol()
        if obj == iter: return IterBuiltinSymbol()
        if obj == len: return LenBuiltinSymbol()
        if obj == ord: return OrdBuiltinSymbol()
        if obj == min: return MinBuiltinSymbol()
        if obj == max: return MaxBuiltinSymbol()
        if obj == next: return NextBuiltinSymbol()
        return InvalidSymbol(name)
        #raise NotImplementedError("Unknown builtin symbol: " + name)
    return UnarySymbol(name, obj)

