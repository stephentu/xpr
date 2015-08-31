xpr
===

This is a simple library which builds on top of [llvmlite](https://github.com/numba/llvmlite) mimicing a very small subset of [theano](http://deeplearning.net/software/theano/). The emphasis here is on generating compiled entry points which are easy to pass as function pointers to C/C++. The target application in mind is a sampler where the user specifes probability densities in python, and the code is JIT-ed out and passed to fast C++ samplers.
