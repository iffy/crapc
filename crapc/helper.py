
__all__ = ['RPCFromObject', 'PythonInterface', 'RPCFromClass']


import inspect

from zope.interface import implements

from crapc.error import MethodNotFound
from crapc.interface import ISystem
from crapc._request import Request


class _LazyWrappingRPCSystem(object):
    """
    Create an L{ISystem} from the public methods of an object that are looked
    up lazily.
    """

    implements(ISystem)

    def __init__(self, original):
        self.original = original


    def runProcedure(self, request):
        if request.method.startswith('_'):
            raise MethodNotFound(request.method)
        try:
            func = getattr(self.original, request.method)
            if inspect.ismethod(func) or inspect.isfunction(func):
                return func(*request.args(), **request.kwargs())
            else:
                raise MethodNotFound(request.method)
        except AttributeError:
            raise MethodNotFound(request.method)


def RPCFromObject(obj):
    """
    Create an L{ISystem} from the public methods on this object.

    @return: An L{ISystem}-implementing instance.
    """
    return _LazyWrappingRPCSystem(obj)



def RPCFromClass(cls):
    """
    Wrap an existing class to make a new class, that, when instantiated is
    an L{ISystem} for an instance of the wrapped class.

    You will be able to get at the instance by accessing the C{original}
    attribute.

    By default, all public methods are turned into RPC-available methods.
    """
    methods = inspect.getmembers(cls)
    class _RPC(object):

        implements(ISystem)

        def __init__(self, *args, **kwargs):
            self.original = cls(*args, **kwargs)

        def runProcedure(self, request):
            try:
                func = self._functions[request.method]
            except KeyError:
                raise MethodNotFound(request.full_method)
            return func(self.original, *request.args(), **request.kwargs())

        _functions = {}
        for name, func in methods:
            if name.startswith('_'):
                continue
            _functions[name] = func

    return _RPC



class PythonInterface(object):
    """
    An in-memory interface to an L{ISystem}.
    Just read (all 2 lines of) the source.
    """

    def __init__(self, rpc):
        self.rpc = rpc


    def call(self, method, *args, **kwargs):
        return self.rpc.runProcedure(Request(method, args or kwargs))
