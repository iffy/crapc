from zope.interface import implements


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