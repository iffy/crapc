from zope.interface import implements

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



class _BoundRPC(object):

    implements(ISystem)


    def __init__(self, instance, descriptor):
        self.instance = instance
        self.descriptor = descriptor


    def runProcedure(self, request):
        d = defer.maybeDeferred(self._getSystemFactory, request)
        d.addCallback(lambda (s,r): self._callSystemFactoryWithRequest(s, r))
        return d


    def _getSystemFactory(self, request):
        system_factory = None

        if '.' in request.method:
            system_name, rest = request.method.split('.', 1)
            try:
                system_factory = self.descriptor._systems[system_name]
            except KeyError:
                pass

        if system_factory:
            request = request.child()
        else:
            system_factory = self.descriptor._default_system

        if not system_factory:
            raise MethodNotFound(request.method)

        return system_factory, request


    def _callSystemFactoryWithRequest(self, factory, request):
        d = defer.maybeDeferred(factory, self.instance, request)
        d.addCallback(self._runProcedureOnSystem, request)
        return d


    def _runProcedureOnSystem(self, system, request):
        return system.runProcedure(request)



class RPC(object):
    """
    Descriptor interface for RPC routing.
    """


    def __init__(self):
        self._bound_instances = WeakKeyDictionary()
        self._systems = {}
        self._default_system = None


    def __get__(self, obj, type=None):
        bound_rpc = self._bound_instances.get(obj)
        if bound_rpc is None:
            bound_rpc = _BoundRPC(obj, self)
            self._bound_instances[obj] = bound_rpc
        return bound_rpc


    def subSystem(self, system_name):
        def deco(f):
            self._systems[system_name] = f
            return f
        return deco


    def default(self, f):
        self._default_system = f
        return f




