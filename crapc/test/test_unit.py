from twisted.trial.unittest import TestCase
from zope.interface.verify import verifyObject

from mock import create_autospec

from crapc.interface import ISystem
from crapc._request import Request
from crapc.error import MethodNotFound
from crapc.unit import RPCSystem


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