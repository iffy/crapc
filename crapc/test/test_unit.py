from twisted.trial.unittest import TestCase
from twisted.internet import defer

from zope.interface import implements
from zope.interface.verify import verifyObject

from mock import create_autospec

from crapc.interface import ISystem
from crapc._request import Request
from crapc.error import MethodNotFound
from crapc.unit import RPCSystem, RPC



class _StaticValueSystem(object):

    implements(ISystem)

    def __init__(self, value):
        self.value = value


    def runProcedure(self, request):
        return self.value



class RPCSystemTest(TestCase):


    def test_ISystem(self):
        verifyObject(ISystem, RPCSystem())


    def test_runProcedure_MethodNotFound(self):
        """
        An empty system will raise MethodNotFound for everything.
        """
        s = RPCSystem()
        self.assertRaises(MethodNotFound, s.runProcedure, Request('foo'))


    def test_runProcedure_args(self):
        """
        If positional args are given, they should work when calling the
        function.
        """
        s = RPCSystem()
        s.addFunction('foo', lambda x:x+1)
        r = s.runProcedure(Request('foo', [2]))
        self.assertEqual(r, 3)


    def test_runProcedure_noSystem(self):
        """
        If the given system can't be found, raise MethodNotFound
        """
        s = RPCSystem()
        self.assertRaises(MethodNotFound, s.runProcedure, Request('foo.bar'))


    def test_addFunction(self):
        """
        You can add functions and then run them.
        """
        s = RPCSystem()
        s.addFunction('foo', lambda x:x+'foo')

        r = s.runProcedure(Request('foo', {'x':'xylo'}))
        self.assertEqual(r, 'xylofoo')


    def test_addSystem(self):
        """
        You can add subsystems to a system.
        """
        foo = RPCSystem()
        foo.runProcedure = create_autospec(foo.runProcedure,
                                           return_value='hey')
        
        parent = RPCSystem()
        parent.addSystem('foo', foo)

        req = Request('foo.bar')
        r = parent.runProcedure(req)

        foo_req = foo.runProcedure.call_args[0][0]
        self.assertEqual(foo_req.method, 'bar')
        self.assertEqual(foo.runProcedure.call_count, 1)
        self.assertEqual(r, 'hey', "Should")



class RPCTest(TestCase):


    def test_ISystem(self):
        class Foo(object):
            rpc = RPC()

        foo = Foo()
        verifyObject(ISystem, foo.rpc)


    def test_sameInstance(self):
        """
        You should get the same instance each time you access the descriptor
        """
        class Foo(object):
            rpc = RPC()

        foo = Foo()
        self.assertEqual(foo.rpc, foo.rpc)


    def test_subSystem(self):
        """
        You can register subSystem fetchers by decorating them.
        """
        called = []

        class Foo(object):
            rpc = RPC()
            @rpc.subSystem('foo')
            def foo_system(self, request):
                called.append(request)
                return _StaticValueSystem('ret val')

        foo = Foo()
        req = Request('foo.bar')
        
        result = foo.rpc.runProcedure(req)
        
        self.assertEqual(len(called), 1, "Should have called foo_system")
        child_req = called[0]
        self.assertEqual(child_req.method, 'bar')
        self.assertIdentical(child_req.context, req.context)

        self.assertEqual(self.successResultOf(result), 'ret val')


    def test_subSystem_noDot(self):
        """
        subSystems can handle things without dots.
        """
        class Foo(object):
            rpc = RPC()
            @rpc.subSystem('foo')
            def foo_system(self, request):
                return 'foo ret'

        foo = Foo()
        result = foo.rpc.runProcedure(Request('foo'))
        self.assertEqual(self.successResultOf(result), 'foo ret')


    def test_default(self):
        """
        You can register a handler to generate a system that will handle all
        non-prefixed requests.
        """
        called = []

        class Foo(object):
            rpc = RPC()
            @rpc.default
            def default(self, request):
                called.append(request)
                return _StaticValueSystem('ret val')

        foo = Foo()
        req = Request('foo.bar.baz')

        result = foo.rpc.runProcedure(req)

        self.assertEqual(len(called), 1, "Should have called default")
        child_req = called[0]
        self.assertEqual(child_req.method, 'foo.bar.baz', "Should NOT have "
                         "removed any prefix segments")
        self.assertIdentical(child_req.context, req.context)

        self.assertEqual(self.successResultOf(result), 'ret val')


    def test_noDefault_noSubsystem(self):
        """
        If there is no subsystem and no default factory, then raise
        MethodNotFound
        """
        class Foo(object):
            rpc = RPC()

        foo = Foo()
        self.assertFailure(foo.rpc.runProcedure(Request('foo')),
                           MethodNotFound)
        self.assertFailure(foo.rpc.runProcedure(Request('foo.bar')),
                           MethodNotFound)


    def test_subSystem_deferred(self):
        """
        A subsystem factory function can return a deferred system.
        """
        class Foo(object):
            rpc = RPC()

            @rpc.subSystem('later')
            def later(self, request):
                return defer.succeed(_StaticValueSystem('ret val'))

        foo = Foo()
        result = foo.rpc.runProcedure(Request('later.something'))

        self.assertEqual(self.successResultOf(result), 'ret val')


    def test_prehook(self):
        """
        You can replace the normal subsystem-finding function with one of your
        choosing.
        """
        called = []

        class Foo(object):
            rpc = RPC()

            @rpc.prehook
            def hook(self, func, request):
                called.append(request)
                return _StaticValueSystem('ret val')

        foo = Foo()
        req = Request('whatever.you.want')
        result = foo.rpc.runProcedure(req)

        self.assertEqual(self.successResultOf(result), 'ret val')
        self.assertEqual(called, [req])


    def test_prehook_continue(self):
        """
        You can do the normal processing by calling the included function
        inside a prehook.
        """
        called = []

        class Foo(object):
            rpc = RPC()
            @rpc.prehook
            def hook(self, func, request):
                called.append(request)
                return func(request)

            @rpc.default
            def default(self, request):
                return 'hello'

        foo = Foo()
        req = Request('something.else')

        result = foo.rpc.runProcedure(req)
        self.assertEqual(len(called), 1, "Should have called the prehook")
        self.assertEqual(self.successResultOf(result), 'hello')

