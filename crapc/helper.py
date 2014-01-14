
__all__ = ['RPCFromPublicMethods', 'PythonInterface']


import inspect

from crapc.unit import RPCSystem
from crapc._request import Request


def RPCFromPublicMethods(obj):
    """
    Create an L{ISystem} from the public methods on this object.
    """
    rpc = RPCSystem()
    methods = inspect.getmembers(obj, inspect.ismethod)
    for name, value in methods:
        # exclude private methods
        if name.startswith('_'):
            continue
        rpc.addFunction(name, value)
    return rpc



class PythonInterface(object):


    def __init__(self, rpc):
        self.rpc = rpc


    def call(self, method, *args, **kwargs):
        return self.rpc.runProcedure(Request(method, args or kwargs))
