from zope.interface import implements

from functools import wraps, partial
from weakref import WeakKeyDictionary

from twisted.internet import defer

from crapc.error import MethodNotFound
from crapc.interface import ISystem



class RPCSystem(object):

    implements(ISystem)

    def __init__(self):
        self._functions = {}
        self._systems = {}


    def runProcedure(self, request):
        # look for a subsystem
        if '.' in request.method:
            system_name, rest = request.method.split('.', 1)
            try:
                system = self._systems[system_name]
            except KeyError:
                raise MethodNotFound(request.method)
            return system.runProcedure(request.child())

        # look for a function
        try:
            func = self._functions[request.method]
            return func(*request.args(), **request.kwargs())
        except KeyError:
            raise MethodNotFound(request.method)


    def addFunction(self, name, func):
        self._functions[name] = func


    def addSystem(self, name, system):
        self._systems[name] = system



class _StaticValueSystem(object):

    implements(ISystem)

    def __init__(self, value):
        self.value = value


    def runProcedure(self, request):
        return self.value



class _BoundRPC(object):

    implements(ISystem)


    def __init__(self, instance, descriptor):
        self.instance = instance
        self.descriptor = descriptor


    def runProcedure(self, request):
        """
        Run the requested procedure with pre hooks.
        """
        return defer.maybeDeferred(self._runProcedure, request)


    def _runProcedure(self, request):
        # 1. get a factory function
        if self.descriptor._prehook:
            factory = partial(self.descriptor._prehook, self.instance,
                              self._getAndRunFactory)
        else:
            factory = self._getFactory(request)

        # 2. run the factory function to produce either a system or a final
        # result
        d_system = defer.maybeDeferred(factory, request)

        # 3. run the system's procedure if it is a system
        d_system.addCallback(self._maybeRunProcedureOnSystem, request)

        return d_system


    def _getFactory(self, request):
        """
        Get the factory function that will return an L{ISystem} responsible
        for running the given request.
        """
        factory = None

        if '.' in request.method:
            system_name, rest = request.method.split('.', 1)
            try:
                factory = partial(self.descriptor._systems[system_name],
                                  self.instance)
            except KeyError:
                pass

        if not factory and self.descriptor._default_system:
            factory = partial(self.descriptor._default_system, self.instance)

        if not factory:
            raise MethodNotFound(request.full_method)

        return factory


    def _getAndRunFactory(self, request):
        return self._getFactory(request)(request)


    def _maybeRunProcedureOnSystem(self, system_or_response, request):
        if ISystem.providedBy(system_or_response):
            # it's a system
            return system_or_response.runProcedure(request)

        # it's a response
        return system_or_response



class RPC(object):
    """
    Descriptor interface for RPC routing.
    """


    def __init__(self):
        self._bound_instances = WeakKeyDictionary()
        self._systems = {}
        self._prehook = None
        self._default_system = None


    def __get__(self, obj, type=None):
        bound_rpc = self._bound_instances.get(obj)
        if bound_rpc is None:
            bound_rpc = _BoundRPC(obj, self)
            self._bound_instances[obj] = bound_rpc
        return bound_rpc


    def subSystem(self, system_name):
        def deco(f):
            
            @wraps(f)
            def subSystemWrapper(instance, request):
                return f(instance, request.child())
            self._systems[system_name] = subSystemWrapper

            return subSystemWrapper

        return deco


    def default(self, f):
        self._default_system = f
        return f


    def prehook(self, function):
        """
        Call C{function} instead of doing the normal subSystem lookup.
        """
        self._prehook = function





