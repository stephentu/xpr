"""ast.py

"""

from llvmlite import ir

import ctypes
from ctypes.util import find_library

import llvmlite.binding as llvm

_SUPPORTED_TYPES = {
    int: ir.IntType(64),
    float: ir.DoubleType()
}

_SUPPORTED_OPS = {
    '+': 'Add',
    '-': 'Sub',
    '*': 'Mult',
    '/': 'Div',
    '**': 'Pow',
}

_SUPPORTED_OPS_LLVM = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',
    '/': 'div',
}


class Expr(object):

    def __add__(self, other):
        return BinOp(self, other, '+')

    def __radd__(self, other):
        return BinOp(other, self, '+')

    def __sub__(self, other):
        return BinOp(self, other, '-')

    def __rsub__(self, other):
        return BinOp(other, self, '-')

    def __mul__(self, other):
        return BinOp(self, other, '*')

    def __rmul__(self, other):
        return BinOp(other, self, '*')

    def __div__(self, other):
        return BinOp(self, other, '/')

    def __rdiv__(self, other):
        return BinOp(other, self, '/')

    def __pow__(self, other):
        return BinOp(self, other, '**')

    def __rpow__(self, other):
        return BinOp(other, self, '**')


class Constant(Expr):

    def __init__(self, val):
        self.val = val

    def __str__(self):
        return "Constant({})".format(str(self.val))

    def _coerce_type(self):
        return type(self.val)

    def _compile(self, ctx):
        return ir.Constant(_SUPPORTED_TYPES[type(self.val)], self.val)


class Variable(Expr):

    def __init__(self, name, tpe):
        self.name = name
        self.tpe = tpe

    def __str__(self):
        return "Variable({}, {})".format(self.name, self.tpe)

    def _coerce_type(self):
        return self.tpe

    def _compile(self, ctx):
        return ctx.env[self.name]


def _type_coercion(a, b):
    prio = {
        int: 1,
        float: 2,
    }
    rev_prio = { v : k for k, v in prio.iteritems() }
    return rev_prio[max(prio[a], prio[b])]


def _expr_coercion(expr, expected, actual, ctx):
    # TODO(stephentu): very hacky
    if expected == actual:
        return expr
    return ctx.builder.sitofp(expr, ir.DoubleType())

def _try_promote_to_expr(expr):
    if isinstance(expr, Expr):
        return expr
    if isinstance(expr, int) or isinstance(expr,float):
        return Constant(expr)
    raise ValueError("could not promote expr: " + expr)


class BinOp(Expr):

    def __init__(self, lhs, rhs, op):
        self.lhs = _try_promote_to_expr(lhs)
        self.rhs = _try_promote_to_expr(rhs)
        if not op in _SUPPORTED_OPS.keys():
            raise ValueError("invalid op")
        self.op = op

    def __str__(self):
        return "{}({}, {})".format(_SUPPORTED_OPS[self.op], str(self.lhs), str(self.rhs))

    def _coerce_type(self):
        return _type_coercion(
                self.lhs._coerce_type(),
                self.rhs._coerce_type())

    def _compile(self, ctx):
        my_tpe = self._coerce_type()
        if self.op == '**':
            if not isinstance(self.rhs, Constant) or (self.rhs.val not in (2, 2.0)):
                raise NotImplementedError("can only square things for now")
            if my_tpe == float:
                op_name = 'fmul'
            else:
                op_name = 'mul'
            expr = _expr_coercion(
                    self.lhs._compile(ctx), my_tpe, self.lhs._coerce_type(), ctx)
            return getattr(ctx.builder, op_name)(expr, expr)
        op_name = _SUPPORTED_OPS_LLVM[self.op]
        if my_tpe == float:
            op_name = 'f' + op_name
        elif my_tpe == int and self.op == '/':
            op_name = 'sdiv' # ugh
        lhs = _expr_coercion(
                self.lhs._compile(ctx), my_tpe, self.lhs._coerce_type(), ctx)
        rhs = _expr_coercion(
                self.rhs._compile(ctx), my_tpe, self.rhs._coerce_type(), ctx)
        return getattr(ctx.builder, op_name)(lhs, rhs)


class UnaryFunc(Expr):

    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return "{}({})".format(self._name(), str(self.arg))


class NativeFloatToFloatFunc(UnaryFunc):

    def __init__(self, arg):
        UnaryFunc.__init__(self, arg)

    def _coerce_type(self):
        return float

    def _compile(self, ctx):
        arg = self.arg._compile(ctx)
        if self.arg._coerce_type() != float:
            arg = ctx.builder.sitofp(arg, ir.DoubleType())

        f = self._get_native_function(ctx)
        log_addr = ctypes.cast(f, ctypes.c_void_p).value

        log_ty = ir.FunctionType(ir.DoubleType(), [ir.DoubleType()])
        # TODO(stephentu): generate random names to avoid name clashing
        f = ctx.builder.inttoptr(ir.Constant(ir.IntType(64), log_addr), log_ty.as_pointer(), name='LogFunc')
        return ctx.builder.call(f, [arg])


class Log(NativeFloatToFloatFunc):

    def __init__(self, arg):
        NativeFloatToFloatFunc.__init__(self, arg)

    def _name(self):
        return "Log"

    def _get_native_function(self, ctx):
        libm = ctx.library("m")
        return libm.log


class Exp(NativeFloatToFloatFunc):

    def __init__(self, arg):
        NativeFloatToFloatFunc.__init__(self, arg)

    def _name(self):
        return "Exp"

    def _get_native_function(self, ctx):
        libm = ctx.library("m")
        return libm.exp


class Context(object):

    def __init__(self, builder, env):
        self.builder = builder
        self.env = env

    def library(self, name):
        return ctypes.cdll.LoadLibrary(find_library(name))


class Function(object):

    def __init__(self, name, params, rettype, expr):
        self.name = name
        self.params = params
        self.rettype = rettype
        self.expr = expr

    def compile(self, engine):
        fnty = ir.FunctionType(
            _SUPPORTED_TYPES[self.rettype],
            [_SUPPORTED_TYPES[t.tpe] for t in self.params])
        module = ir.Module(name="foo")
        func = ir.Function(module, fnty, name=self.name)

        block = func.append_basic_block(name="entry")

        builder = ir.IRBuilder(block)
        env = { node.name : obj for node, obj in zip(self.params, func.args) }
        ctx = Context(builder, env)

        builder.ret(self.expr._compile(ctx))

        llvm_mod = llvm.parse_assembly(str(module))
        llvm_mod.verify()
        engine.add_module(llvm_mod)
        engine.finalize_object()
        return llvm_mod

