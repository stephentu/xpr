
from xpr import create_execution_engine
from xpr.ast import *
from xpr.sampler import *

import ctypes
from ctypes.util import find_library
import math
import matplotlib.pylab as plt
import numpy as np

def test1():

    x = Variable("x", float)
    f = Function(
            name="foo",
            params=(x,),
            rettype=float,
            expr=x ** 2)
    engine = create_execution_engine()
    module = f.compile(engine)
    func_ptr = engine.get_pointer_to_function(module.get_function("foo"))
    call_and_print_result(func_ptr)


def test2():
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

    samples = metropolis_hastings(func_ptr, sigma, 0.0, 100, 2)
    plt.plot(np.arange(len(samples)), samples)
    plt.show()


if __name__ == '__main__':
    test2()
