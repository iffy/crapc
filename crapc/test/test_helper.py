from twisted.trial.unittest import TestCase

from zope.interface.verify import verifyObject

from crapc.helper import RPCFromObject, PythonInterface, RPCFromClass
from crapc.interface import ISystem
from crapc._request import Request
from crapc.error import MethodNotFound


class Something(object):

    def proc1(self, hey):
        return 'apples'

    def proc2(self, ho):
        return 'bananas'

    def _private(self, arg):
        return 'private'



class RPCFromObjectTest(TestCase):


    def test_works(self):
        """
        Should generate an L{RPCSystem} instance exposing all public methods
        but not private ones.
        """
        rpc = RPCFromObject(Something())
        verifyObject(ISystem, rpc)
        self.assertEqual(rpc.runProcedure(Request('proc1', ['a'])), 'apples')
        self.assertEqual(rpc.runProcedure(Request('proc2', ['b'])), 'bananas')
        self.assertRaises(MethodNotFound, rpc.runProcedure,
                          Request('_private', ['something']))


    def test_attributes(self):
        """
        Should ignore public attributes.
        """
        class Foo(object):
            attr1 = 'something'

        rpc = RPCFromObject(Foo())
        self.assertRaises(MethodNotFound, rpc.runProcedure, Request('attr1'))


class RPCFromClassTest(TestCase):


    def test_works(self):
        """
        You can create a new class that, when instantiated,
        returns an L{ISystem} with an C{original} attribute that is an instance
        of the original wrapped class.  The L{ISystem} returned maps to the
        public methods of the object by default.
        """
        RPCSomething = RPCFromClass(Something)

        rpc = RPCSomething()
        verifyObject(ISystem, rpc)
        self.assertEqual(rpc.runProcedure(Request('proc1', ['a'])), 'apples')
        self.assertEqual(rpc.runProcedure(Request('proc2', ['b'])), 'bananas')
        self.assertRaises(MethodNotFound, rpc.runProcedure,
                          Request('_private', ['something']))
        self.assertTrue(isinstance(rpc.original, Something))


    def test_init(self):
        """
        Should initialize the wrapped object.
        """
        class Foo(object):

            def __init__(self, x):
                self.x = x

            def add(self, y):
                return self.x + y

        RPCFoo = RPCFromClass(Foo)

        rpc = RPCFoo(8)
        self.assertEqual(rpc.original.x, 8, "Should pass along __init__ args")
        self.assertEqual(rpc.runProcedure(Request('add', [2])), 10)



class PythonInterfaceTest(TestCase):


    def test_call(self):
        """
        Call should construct the appropriate Request and call runProcedure
        """
        class Foo(object):

            def proc1(self, hey):
                return 'apples' + hey

            def noargs(self):
                return 'nothing'

        rpc = RPCFromObject(Foo())
        i = PythonInterface(rpc)

        r = i.call('proc1', 'auce')
        self.assertEqual(r, 'applesauce')

        r = i.call('proc1', hey='andgravy')
        self.assertEqual(r, 'applesandgravy')

        r = i.call('noargs')
        self.assertEqual(r, 'nothing')
