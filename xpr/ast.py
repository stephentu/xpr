"""ast.py

"""

from llvmlite import ir

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

    def __sub__(self, other):
        return BinOp(self, other, '-')

    def __mul__(self, other):
        return BinOp(self, other, '*')

    def __rmul__(self, other):
        return BinOp(other, self, '*')

    def __div__(self, other):
        return BinOp(self, other, '/')


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
        op_name = _SUPPORTED_OPS_LLVM[self.op]
        my_tpe = self._coerce_type()
        if my_tpe == float:
            op_name = 'f' + op_name
        elif my_tpe == int and self.op == '/':
            op_name = 'sdiv' # ugh
        lhs = self.lhs._compile(ctx)
        rhs = self.rhs._compile(ctx)
        # TODO(stephentu): very hacky
        if self.lhs._coerce_type() != my_tpe:
            lhs = ctx.builder.sitofp(lhs, ir.DoubleType())
        if self.rhs._coerce_type() != my_tpe:
            rhs = ctx.builder.sitofp(rhs, ir.DoubleType())
        return getattr(ctx.builder, op_name)(lhs, rhs)


class Context(object):

    def __init__(self, builder, env):
        self.builder = builder
        self.env = env


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

