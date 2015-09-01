from libc.stdint cimport intptr_t

cdef extern from "xpr/sampler.hpp" namespace "xpr":

    cdef void _call_and_print_result(intptr_t) except +


def call_and_print_result(px):
    _call_and_print_result(px)
