#!/usr/bin/env python

### TODO(stephentu): move me to a nosetest

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


def test4():
    x = Variable("x", float)
    f = Function(
            name="foo",
            params=(x,),
            rettype=float,
            expr=x ** 2)
    engine = create_execution_engine()
    module = f.compile(engine)
    func_ptr = engine.get_pointer_to_function(module.get_function("foo"))
    cfunc = CFUNCTYPE(c_double, c_double)(func_ptr)

    assert almost_eq(cfunc(23.45), 23.45 * 23.45)


def test5():
    # logpdf of Gaussian
    mu = 10.0
    sigma = 2.0

    x = Variable("x", float)
    loggauss = -0.5 * math.log( 2.0 * math.pi * sigma * sigma ) - 0.5 * ((x - mu) ** 2) / (sigma * sigma)
    f = Function(
            name="foo",
            params=(x,),
            rettype=float,
            expr=loggauss)
    engine = create_execution_engine()
    module = f.compile(engine)
    func_ptr = engine.get_pointer_to_function(module.get_function("foo"))
    cfunc = CFUNCTYPE(c_double, c_double)(func_ptr)

    from scipy.stats import norm
    assert almost_eq(cfunc(5.0), norm.logpdf(5.0, loc=mu, scale=sigma))



if __name__ == '__main__':
    test1()
    test2()
    test3()
    test4()
    test5()
