from twisted.trial.unittest import TestCase
from twisted.python.failure import Failure

import json
from mock import MagicMock

from crapc.unit import RPCSystem
from crapc.test.test_unit import _StaticValueSystem
from crapc.jsonrpc import JsonInterface
from crapc.jsonrpc import ParseError, InvalidRequest, InvalidParams
from crapc.jsonrpc import MethodNotFound, InternalError



class ErrorsTest(TestCase):


    def test_ParseError(self):
        self.assertEqual(ParseError.code, -32700)


    def test_InvalidRequest(self):
        self.assertEqual(InvalidRequest.code, -32600)


    def test_MethodNotFound(self):
        self.assertEqual(MethodNotFound.code, -32601)


    def test_InvalidParams(self):
        self.assertEqual(InvalidParams.code, -32602)


    def test_InternalError(self):
        self.assertEqual(InternalError.code, -32603)


def run(interface, method, params=None):
    """
    Run a method on an interface
    """
    data = {
        'jsonrpc': '2.0',
        'id': 123,
        'method': method,
    }
    if params is not None:
        data['params'] = params
    d = interface.run(json.dumps(data))
    d.addCallback(json.loads)
    return d


class JsonInterfaceTest(TestCase):


    def test_serialization_default(self):
        """
        json.dumps and json.loads are the default (de)serializers.
        """
        rpc = _StaticValueSystem('b')

        i = JsonInterface(rpc)
        result = i.run(json.dumps({
            'jsonrpc': '2.0',
            'method': 'something',
            'id': 12
        }))

        data = json.loads(self.successResultOf(result))
        self.assertEqual(data['jsonrpc'], '2.0')
        self.assertEqual(data['id'], 12)
        self.assertEqual(data['result'], 'b')


    def test_serialization_custom(self):
        """
        You can customize the serializer/deserializer
        """
        rpc = _StaticValueSystem('b')

        deserialize = MagicMock(return_value={
                'jsonrpc': '2.0',
                'method': 'something',
                'id': 14,
            })

        serialize = MagicMock(return_value='serialized')

        i = JsonInterface(rpc, serialize=serialize,
                          deserialize=deserialize)

        result = i.run('input string')

        deserialize.assert_called_once_with('input string')
        serialize.assert_called_once_with({
            'jsonrpc': '2.0',
            'result': 'b',
            'id': 14,
        })
        self.assertEqual(self.successResultOf(result), 'serialized',
                         "Should have used the default serializer")


    def test_makeErrorResponse(self):
        """
        You can turn a failure into the correct JSON-RPC 2.0 response dict.
        """
        i = JsonInterface(None)
        exc = Exception()
        exc.code = 12344
        exc.public_message = 'Some message'

        result = i._makeErrorResponse(Failure(exc), 13)
        self.assertEqual(result['jsonrpc'], '2.0', "Errors should include the "
                         "jsonrpc version number")
        self.assertEqual(result['id'], 13, "Should include the request id")
        self.assertEqual(result['error']['code'], 12344)
        self.assertEqual(result['error']['message'], 'Some message')


    def test_makeErrorResponse_noID(self):
        """
        If no ID is given, use None
        """
        i = JsonInterface(None)
        exc = Exception()
        exc.code = 12344
        exc.public_message = 'Some message'

        result = i._makeErrorResponse(Failure(exc), None)
        self.assertEqual(result['id'], None)


    def test_makeErrorResponse_noCode(self):
        """
        If no code is given, use InternalError.code
        """
        i = JsonInterface(None)
        exc = Exception()
        exc.public_message = 'Some message'

        result = i._makeErrorResponse(Failure(exc), None)
        self.assertEqual(result['id'], None)
        self.assertEqual(result['error']['code'], InternalError.code)
        self.assertEqual(result['error']['message'], 'Some message')


    def test_run_MethodNotFound(self):
        """
        If the method is not found, make sure the right code and message are
        given.
        """
        i = JsonInterface(RPCSystem())
        response = self.successResultOf(run(i, 'foo.bar'))
        self.assertEqual(response['error']['code'], MethodNotFound.code)
        self.assertEqual(response['error']['message'], 'Method not found')


    def test_run_ParseError(self):
        """
        If there's an error parsing the input, fail with ParseError
        """
        i = JsonInterface(RPCSystem())
        r = i.run('not real json')
        response = json.loads(self.successResultOf(r))
        self.assertEqual(response['error']['code'], ParseError.code)


    def test_run_InvalidRequest_noVersion(self):
        """
        It is an invalid request to omit the "jsonrpc": "2.0" item.
        """
        i = JsonInterface(None)
        r = i.run(json.dumps({"id": 10, "method": "foo"}))
        response = json.loads(self.successResultOf(r))
        self.assertEqual(response['error']['code'], InvalidRequest.code)


    def test_run_InvalidRequest_noMethod(self):
        """
        It is an invalid request to omit the "method"
        """
        i = JsonInterface(None)
        r = i.run(json.dumps({"id": 10, "jsonrpc": "2.0"}))
        response = json.loads(self.successResultOf(r))
        self.assertEqual(response['error']['code'], InvalidRequest.code)


    def test_run_InternalError(self):
        """
        If the wrapped RPC object raises an exception, it should be returned
        as an InternalError
        """
        def fail():
            raise Exception('the error')
        rpc = RPCSystem()
        rpc.addFunction('foo', fail)

        i = JsonInterface(rpc)
        response = self.successResultOf(run(i, 'foo'))
        self.assertEqual(response['error']['code'], InternalError.code)
        self.assertNotIn('the error', response['error']['message'])


    def test_logError(self):
        """
        Errors can be logged.
        """
        def fail():
            raise Exception('the error')
        rpc = RPCSystem()
        rpc.addFunction('foo', fail)

        errors = []

        i = JsonInterface(rpc, logError=errors.append)
        self.successResultOf(run(i, 'foo'))
        exc = errors[0]
        self.assertIn('the error', str(exc.getTraceback()))


    def test_logError_fails(self):
        """
        If logError fails, don't fail the whole thing.
        """
        def fail():
            raise Exception('the error')
        rpc = RPCSystem()
        rpc.addFunction('foo', fail)

        i = JsonInterface(rpc, logError='foo')
        response = self.successResultOf(run(i, 'foo'))
        self.assertIn('log', response['error']['message'].lower(),
                      "Should indicate something about logging failing")


    def test_run_params(self):
        """
        The parameters should be sent along too.
        """
        rpc = RPCSystem()
        rpc.addFunction('sum', lambda a,b: a+b)

        i = JsonInterface(rpc)
        response = self.successResultOf(run(i, 'sum', [1, 2]))
        self.assertEqual(response['result'], 3)






