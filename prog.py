#!/usr/bin/env python

from xpr import create_execution_engine
from xpr.ast import *

from ctypes import CFUNCTYPE, c_double, c_longlong

import math


def almost_eq(x, y, tol=1e-8):
    return math.fabs(x - y) <= tol


def test1():
    x = Variable("x", float)
    y = Variable("y", float)
    f = Function(
            name="foo",
            params=(x, y),
            rettype=float,
            expr=10 * x + y)
    engine = create_execution_engine()
    module = f.compile(engine)
    func_ptr = engine.get_pointer_to_function(module.get_function("foo"))
    cfunc = CFUNCTYPE(c_double, c_double, c_double)(func_ptr)
    assert almost_eq(cfunc(1.0, 3.5), 10 * 1.0 + 3.5)


def test2():
    x = Variable("x", int)
    y = Variable("y", int)
    f = Function(
            name="foo",
            params=(x, y),
            rettype=int,
            expr=10 * x - y)
    engine = create_execution_engine()
    module = f.compile(engine)
    func_ptr = engine.get_pointer_to_function(module.get_function("foo"))
    cfunc = CFUNCTYPE(c_longlong, c_longlong, c_longlong)(func_ptr)
    assert cfunc(5, 3) == 10 * 5 - 3


def test3():
    x = Variable("x", float)
    f = Function(
            name="foo",
            params=(x,),
            rettype=float,
            expr=10 * Log(x) + Exp(x) + 1)
    engine = create_execution_engine()
    module = f.compile(engine)
    func_ptr = engine.get_pointer_to_function(module.get_function("foo"))
    cfunc = CFUNCTYPE(c_double, c_double)(func_ptr)

    assert almost_eq(cfunc(3.5), 10.0 * math.log(3.5) + math.exp(3.5) + 1.0)


if __name__ == '__main__':
    test1()
    test2()
    test3()
