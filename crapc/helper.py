
import inspect

from crapc.unit import RPCSystem


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