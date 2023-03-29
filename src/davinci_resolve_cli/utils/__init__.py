import inspect


def call_with_partial_args(func, **kw):
    signature = inspect.signature(func)
    kw = {k: v for k, v in kw.items() if k in signature.parameters}
    func(**kw)


def has_arg(func, arg_name):
    signature = inspect.signature(func)
    return arg_name in signature.parameters
