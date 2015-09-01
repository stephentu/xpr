
from xpr import create_execution_engine
from xpr.ast import *
from xpr.sampler import *

import ctypes
from ctypes.util import find_library


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


if __name__ == '__main__':
    test1()
