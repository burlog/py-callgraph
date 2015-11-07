# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Callgraph symbols representations.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

import os
from itertools import chain, islice
from inspect import isclass, isbuiltin, getmro
from abc import ABCMeta, abstractmethod

from callgraph.finder import find_object
from callgraph.utils import empty

class Symbol(metaclass=ABCMeta):
    def __init__(self, builder, name):
        self.builder = builder
        self.name = name
        self.scope = {}
        self.return_list = []
        self.yield_list = []
        self.myself = None
        self.var_names = set()

    @abstractmethod
    def values(self):
        while False: yield None

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def set(self):
        pass

    @property
    def cls_name(self):
        return self.__class__.__name__

    @property
    def qualname(self):
        return self.name

    @property
    def hooks(self):
        return self.builder.hooks

    @property
    def inst_name(self):
        return self.name

    def returns(self):
        yield from self.return_list

    def yields(self):
        yield from self.yield_list

    def geners(self):
        while False: yield None

    def aux_repr(self):
        while False: yield None

    def iscallable(self):
        return any(map(lambda x: callable(x.value), self.values()))

    def isiterable(self):
        return "__iter__" in dir(self)

    def __bool__(self):
        return True

    def can_return(self, symbol):
        self.return_list.extend(symbol.values())
        self.yield_list.extend(symbol.geners())

    def can_yield(self, symbol):
        self.yield_list.extend(symbol.values())

    def can_yield_from(self, symbol):
        self.yield_list.extend(symbol.geners())

    def __repr__(self):
        aux = ", ".join(self.aux_repr())
        if aux: aux = ", " + aux
        if self.myself:
            aux += ", myself=" + self.myself.inst_name
        if not empty(self.returns()):
            aux += ", returns=["
            aux += ",".join(map(lambda x: x.inst_name, self.returns())) + "]"
        if not empty(self.yields()):
            aux += ", yields=["
            aux += ",".join(map(lambda x: x.inst_name, self.yields())) + "]"
        return "{0}(name={1}{2})".format(self.cls_name, self.name, aux)

class UnarySymbol(Symbol):
    def __init__(self, builder, name, value):
        super().__init__(builder, name)
        UnarySymbol.counter = 0
        self.force_myself = None
        self.class_scope = {}
        self.value = value

    @property
    def qualname(self):
        return getattr(self.value, "__qualname__", super().qualname)

    def values(self):
        yield self

    def get(self, name, free=True, nocache=False):
        # cached attributes in symbol scope
        if name in self.scope: return self.scope[name]
        if name in self.class_scope: return self.class_scope[name]

        # attributes of the held value
        if hasattr(self.value, name):
            symbol = UnarySymbol(self.builder, name, getattr(self.value, name))
            symbol.myself = self.force_myself or self
            return self.scope.setdefault(name, symbol)

        # global symbols if they are allowed
        if not free: return
        if name in self.builder.global_symbols:
            symbol = self.builder.global_symbols[name]
        else:
            symbol = find_symbol(self, self.value, name)
        kwargs = {}
        if hasattr(symbol, "value"): kwargs["value"] = symbol.value
        self.hooks.global_symbol_load(name=symbol.name, **kwargs)
        return self.scope.setdefault(name, symbol)

    def set(self, name, value):
        assert isinstance(value, Symbol)
        if value:
            if name in self.scope:
                self.scope[name] = merge_symbols(name, self.scope[name], value)
            else:
                self.scope[name] = value
                self.var_names.add(name)

    def make_instance(self):
        instance_symbol = UnarySymbol(self.builder, self.name, self.value)
        instance_symbol.class_scope = self.scope
        instance_symbol.scope = {}
        instance_symbol.return_list = []
        instance_symbol.yield_list = []
        instance_symbol.myself = None
        instance_symbol.var_names = set()
        self.counter += 1
        instance_symbol.instance_id = self.counter
        return instance_symbol

    def make_instance_and_return_init(self):
        assert isinstance(self.value, type)
        instance_symbol = self.make_instance()
        init = getattr(self.value, "__init__")
        init_symbol = UnarySymbol(self.builder, "__init__", init)
        init_symbol.can_return(instance_symbol)
        init_symbol.myself = instance_symbol
        return init_symbol

    @property
    def inst_name(self):
        if hasattr(self, "instance_id"):
            return self.name + "{" + str(self.instance_id) + "}"
        return self.name

    def aux_repr(self):
        if hasattr(self, "instance_id"):
            yield "instance=" + str(self.instance_id)
        yield "value=" + repr(self.value)

class ConstantSymbol(UnarySymbol):
    def __init__(self, builder, value):
        super().__init__(builder, type(value).__name__, value)

    def set(self, name, value):
        raise RuntimeError("Invalid assingment into constant symbol")

class IterableConstantSymbol(ConstantSymbol):
    def __init__(self, builder, cls, iterable):
        super().__init__(builder, cls)
        self.iterable = iterable

    def __iter__(self):
        yield from self.iterable

    def aux_repr(self):
        yield from super().aux_repr()
        yield "iterable=[{0}]"\
              .format(",".join(map(lambda x: x.inst_name, self.iterable)))

class InvalidSymbol(Symbol):
    def __init__(self, builder, name):
        super().__init__(builder, name)

    def get(self, name, free=True):
        return None

    def set(self, name, value):
        raise RuntimeError("Invalid assingment into invalid symbol")

    def values(self):
        yield self

    def __bool__(self):
        return False

    def __iter__(self):
        while False: yield self

class LambdaSymbol(Symbol):
    def __init__(self, builder, args, body):
        super().__init__(builder, "__lambda__")
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
    def __init__(self, builder, name, value_list=[], gener_list=[]):
        super().__init__(builder, name)
        self.value_list = list(value_list)
        self.gener_list = list(gener_list)

    @property
    def qualname(self):
        return "multi:" + super().qualname

    def values(self):
        for value in self.value_list:
            yield from value.values()

    def geners(self):
        for value in self.gener_list:
            yield from value.values()

    def returns(self):
        for value in self.values():
            yield from value.returns()

    def yields(self):
        for value in self.values():
            yield from value.yields()

    def get(self, name, free=True):
        def list_values(attr_symbol):
            yield from iter(x.value for x in attr_symbol.value_list)
        attr_symbol = MultiSymbol(self.builder, name)
        for symbol in filter(None, self.values()):
            assert not isinstance(symbol, MultiSymbol)
            attr = symbol.get(name, free)
            if not attr: continue
            for sub_attr in attr.values():
                if sub_attr.value not in list_values(attr_symbol):
                    attr_symbol.value_list.append(sub_attr)
        return attr_symbol

    def set(self, name, value):
        assert isinstance(value, Symbol)
        for symbol in filter(None, self.values()):
            if not isinstance(symbol, ConstantSymbol):
                symbol.set(name, value)

    def aux_repr(self):
        names = lambda s: map(lambda x: x.inst_name, s)
        yield from super().aux_repr()
        if self.value_list:
            yield "values=[{0}]".format(",".join(names(self.value_list)))
        if self.gener_list:
            yield "geners=[{0}]".format(",".join(names(self.gener_list)))

    def __iter__(self):
        # TODO(burlog): and what about geners?
        # for a in [generator()]: for b in a: ...?
        only_iterable = filter(lambda x: x.isiterable(), self.values())
        for symbols in zip(*[symbol for symbol in only_iterable]):
            yield MultiSymbol(self.builder, self.name, symbols)

    def __bool__(self):
        return bool(self.value_list or self.gener_list)

class ResultSymbol(MultiSymbol):
    def __init__(self, builder, callee_symbol):
        super().__init__(builder,
                         "__result_of_" + callee_symbol.inst_name + "__",
                         callee_symbol.returns(),
                         callee_symbol.yields())

class BuiltinSymbol(UnarySymbol):
    def __init__(self, builder, obj):
        super().__init__(builder, obj.__name__, obj)

    def set(self, name, value):
        raise RuntimeError("You can't assing attribute to builtin symbol")

class SuperBuiltinSymbol(MultiSymbol):
    def __init__(self, parent):
        assert isinstance(parent.myself, UnarySymbol)
        assert isinstance(parent, UnarySymbol)
        assert not hasattr(parent, "instance_id")
        # TODO(burlog): bound methods?!
        super().__init__(parent.builder,
                         "__super_of_" + parent.inst_name + "__",
                         self.make_super(parent))

    def make_super(self, parent):
        __super__ = UnarySymbol(parent.builder, "__super__", super.__init__)
        for cls in getmro(parent.myself.value)[1:-1]:
            symbol = UnarySymbol(parent.builder, cls.__name__, cls)
            symbol.force_myself = parent.myself
            __super__.can_return(symbol)
        return [__super__]

    def set(self, name, value):
        raise RuntimeError("You can't assing attribute to builtin symbol")

class OpenResultBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder, obj):
        super().__init__(builder, obj.__class__)
        self.get("__enter__").can_return(self)

class OpenBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, open)
        self.can_return(OpenResultBuiltinSymbol(builder, open(os.devnull, "r")))

class DirBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, dir)
        self.can_return(UnarySymbol(builder, "__result__", type(dir())))

class GetattrBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, getattr)
        # TODO(burlog): we can add default to returns
        # TODO(burlog): we inspect static objects and add to returns...

class IsinstanceBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, isinstance)
        self.can_return(UnarySymbol(builder, "__result__", bool))

class PrintBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, print)

class CallableBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, callable)
        self.can_return(UnarySymbol(builder, "__result__", bool))

class IdBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, id)
        self.can_return(UnarySymbol(builder, "__result__", type(id(""))))

class HasattrBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, hasattr)
        self.can_return(UnarySymbol(builder, "__result__", bool))

class IterBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, iter)
        # TODO(burlog): we can guess types...

class LenBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, len)
        self.can_return(UnarySymbol(builder, "__result__", int))

class OrdBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, ord)
        self.can_return(UnarySymbol(builder, "__result__", int))

class MinBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, min)
        self.can_return(UnarySymbol(builder, "__result__", min))

class MaxBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, max)
        self.can_return(UnarySymbol(builder, "__result__", max))

class NextBuiltinSymbol(BuiltinSymbol):
    def __init__(self, builder):
        super().__init__(builder, next)
        # TODO(burlog): we can guess types...

def make_result_symbol(builder, callee_symbol):
    def expand_ctors(origin_symbol):
        for symbol in origin_symbol.values():
            if not symbol or not isclass(symbol.value):
                yield symbol
            else:
                yield symbol.get("__init__")
    symbols = list(expand_ctors(callee_symbol))
    result_symbol = merge_symbols(callee_symbol.name, *symbols)
    return ResultSymbol(builder, result_symbol)\
        or InvalidSymbol(builder, "__result__")

def merge_symbols(name, *args):
    def chain_values(symbols):
        for symbol in symbols:
            yield from symbol.values()
    def chain_geners(symbols):
        for symbol in symbols:
            yield from symbol.geners()
    value_list = list(chain_values(args))
    gener_list = list(chain_geners(args))
    return MultiSymbol(args[0].builder, name, value_list, gener_list)

def find_symbol(parent, value, name):
    obj = find_object(value.__init__ if isclass(value) else value, name)
    if obj is None: return InvalidSymbol(parent.builder, name)
    if isbuiltin(obj) and not isclass(obj):
        if obj == open: return OpenBuiltinSymbol(parent.builder)
        if obj == dir: return DirBuiltinSymbol(parent.builder)
        if obj == getattr: return GetattrBuiltinSymbol(parent.builder)
        if obj == hasattr: return HasattrBuiltinSymbol(parent.builder)
        if obj == isinstance: return IsinstanceBuiltinSymbol(parent.builder)
        if obj == print: return PrintBuiltinSymbol(parent.builder)
        if obj == callable: return CallableBuiltinSymbol(parent.builder)
        if obj == id: return IdBuiltinSymbol(parent.builder)
        if obj == iter: return IterBuiltinSymbol(parent.builder)
        if obj == len: return LenBuiltinSymbol(parent.builder)
        if obj == ord: return OrdBuiltinSymbol(parent.builder)
        if obj == min: return MinBuiltinSymbol(parent.builder)
        if obj == max: return MaxBuiltinSymbol(parent.builder)
        if obj == next: return NextBuiltinSymbol(parent.builder)
        return InvalidSymbol(parent.builder, name)
        #raise NotImplementedError("Unknown builtin symbol: " + name)
    if obj == super: return SuperBuiltinSymbol(parent)
    return UnarySymbol(parent.builder, name, obj)

