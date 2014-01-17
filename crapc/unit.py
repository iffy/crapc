from zope.interface import implements

from functools import wraps, partial
from weakref import WeakKeyDictionary

from twisted.internet import defer

from crapc.error import MethodNotFound
from crapc.interface import ISystem



class RPCSystem(object):
    """
    This is a collection of named functions and subsystems.
    This is a building block for general purpose RPC.

    Add functions with L{addFunction}.
    Add more L{ISystem} instances with L{addSystem}.
    
    Then execute procedures by passing L{crapc._request.Request} instances
    to L{runProcedure}.
    """

    implements(ISystem)

    def __init__(self):
        self._functions = {}
        self._systems = {}


    def runProcedure(self, request):
        """
        Find and run the procedure identified by C{request}.

        @param request: A L{crapc._request.Request} instance.

        @raise MethodNotFound: If the method named could not be found.

        @return: Whatever the procedure returns.
        """
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
        """
        Add a function to this system.

        @param name: Name of function.
        @param func: Function to be called.
        """
        self._functions[name] = func


    def addSystem(self, name, system):
        """
        Add a subsystem to this system.

        @param name: Name of system.
        @param system: A L{ISystem}-providing instance.
        """
        self._systems[name] = system



class _BoundRPC(object):

    implements(ISystem)


    def __init__(self, instance, descriptor):
        self.instance = instance
        self.descriptor = descriptor


    def runProcedure(self, request):
        """
        Run the requested procedure with pre hooks.

        @rtype: C{Deferred}
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
        for running the given request.  A factory function is a function that
        accepts a L{Request} instance and returns either a procedure's end
        result or else an L{ISystem}.
        """
        factory = None

        system_name = request.method.split('.')[0]

        try:
            factory = partial(self.descriptor._routes[system_name],
                              self.instance)
        except KeyError:
            pass

        if not factory and self.descriptor._default_system:
            factory = partial(self.descriptor._default_system, self.instance)

        if not factory:
            raise MethodNotFound(request.full_method)

        return factory


    def _getAndRunFactory(self, request):
        d = defer.maybeDeferred(self._getFactory, request)
        d.addCallback(lambda func: func(request))
        d.addCallback(self._maybeRunProcedureOnSystem, request)
        return d


    def _maybeRunProcedureOnSystem(self, system_or_response, request):
        if ISystem.providedBy(system_or_response):
            # it's a system
            d = defer.maybeDeferred(system_or_response.runProcedure, request)
            return d.addCallback(self._maybeRunProcedureOnSystem, request)

        # it's a response
        return system_or_response



class RPC(object):
    """
    Descriptor interface for RPC routing.
    """


    def __init__(self):
        self._bound_instances = WeakKeyDictionary()
        self._routes = {}
        self._prehook = None
        self._default_system = None


    def __get__(self, obj, type=None):
        bound_rpc = self._bound_instances.get(obj)
        if bound_rpc is None:
            bound_rpc = _BoundRPC(obj, self)
            self._bound_instances[obj] = bound_rpc
        return bound_rpc


    def route(self, system_name):
        def deco(f):
            
            @wraps(f)
            def routeWrapper(instance, request):
                return f(instance, request.child())
            self._routes[system_name] = routeWrapper

            return routeWrapper

        return deco


    def default(self, f):
        self._default_system = f
        return f


    def prehook(self, function):
        """
        Call C{function} instead of doing the normal routing lookup.
        """
        self._prehook = function





