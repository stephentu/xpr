from libc.stdint cimport intptr_t
from libcpp.vector cimport vector

cdef extern from "xpr/sampler.hpp" namespace "xpr":

    cdef void _call_and_print_result(intptr_t) except +
    cdef vector[double] _metropolis_hastings(
        intptr_t, 
  	    double, 
  	    double, 
  	    size_t,
  	    size_t) except +

def call_and_print_result(px):
    _call_and_print_result(px)
    

def metropolis_hastings(px, prop_sigma, x0, iters, seed):
    cdef vector[double] ret
    ret = _metropolis_hastings(px, prop_sigma, x0, iters, seed)
    return list(ret)