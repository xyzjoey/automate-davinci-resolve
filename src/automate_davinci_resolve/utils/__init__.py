import inspect


def forward_partial_args(func):
    def func_wrapper(**kw):
        signature = inspect.signature(func)
        kw = {k: v for k, v in kw.items() if k in signature.parameters}
        func(**kw)

    return func_wrapper


def has_arg(func, arg_name):
    signature = inspect.signature(func)
    return arg_name in signature.parameters
