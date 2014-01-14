from twisted.trial.unittest import TestCase

from crapc.helper import RPCFromPublicMethods, PythonInterface
from crapc._request import Request
from crapc.error import MethodNotFound


class RPCFromPublicMethodsTest(TestCase):


    def test_works(self):
        """
        Should generate an L{RPCSystem} instance exposing all public methods
        but not private ones.
        """
        class Something(object):

            def proc1(self, hey):
                return 'apples'

            def proc2(self, ho):
                return 'bananas'

            def _private(self, arg):
                return 'private'

        rpc = RPCFromPublicMethods(Something())
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

        rpc = RPCFromPublicMethods(Foo())
        self.assertRaises(MethodNotFound, rpc.runProcedure, Request('attr1'))



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

        rpc = RPCFromPublicMethods(Foo())
        i = PythonInterface(rpc)

        r = i.call('proc1', 'auce')
        self.assertEqual(r, 'applesauce')

        r = i.call('proc1', hey='andgravy')
        self.assertEqual(r, 'applesandgravy')

        r = i.call('noargs')
        self.assertEqual(r, 'nothing')
