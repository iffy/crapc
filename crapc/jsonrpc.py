
import json

from twisted.internet import defer
from twisted.python.failure import Failure

from crapc._request import Request
from crapc import error


class JsonRPCError(error.RPCError):
    message = "Error"
    code = -32603

    def __init__(self, message=None):
        self.message = message or self.message


class ParseError(JsonRPCError):
    message = "Parse error"
    code = -32700

class InvalidRequest(JsonRPCError):
    message = "Invalid request"
    code = -32600

class MethodNotFound(JsonRPCError):
    message = "Method not found"
    code = -32601

class InvalidParams(JsonRPCError):
    message = "Invalid parameters"
    code = -32602

class InternalError(JsonRPCError):
    message = "Internal error"
    code = -32603



class JsonInterface(object):


    def __init__(self, rpc, serialize=None, deserialize=None):
        self.rpc = rpc
        self._serialize = serialize or json.dumps
        self._deserialize_fn = deserialize or json.loads


    def _deserialize(self, json_string):
        d = defer.maybeDeferred(self._deserialize_fn, json_string)
        d.addErrback(lambda _: Failure(ParseError()))
        return d


    def _makeSuccess(self, result, request_id):
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': result,
        }


    def _makeErrorResponse(self, failure, request_id):
        exc = failure.value
        code = getattr(exc, 'code', InternalError.code)
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': code,
                'message': exc.message,
            },
        }


    def run(self, json_string):
        d = self._deserialize(json_string)
        
        d.addCallback(self._runDeserialized)
        d.addErrback(self._makeErrorResponse, None)
        
        d.addCallback(self._serialize)
        return d


    def _runDeserialized(self, data):
        request_id = data['id']

        d = defer.maybeDeferred(self._runWithRequestID, data, request_id)
        d.addCallback(self._makeSuccess, request_id)
        d.addErrback(self._makeErrorResponse, request_id)
        return d


    def _runWithRequestID(self, data, request_id):
        try:
            if data['jsonrpc'] != '2.0':
                raise InvalidRequest('only jsonrpc 2.0 accepted')
        except:
            raise InvalidRequest('jsonrpc version not provided')

        if 'method' not in data:
            raise InvalidRequest('method not provided')

        req = Request(data['method'], data.get('params'))

        d = defer.maybeDeferred(self.rpc.runProcedure, req)
        d.addErrback(self._mapErrors)

        return d


    def _mapErrors(self, failure):
        if failure.check(error.MethodNotFound):
            raise MethodNotFound()
        raise InternalError(str(failure.value))


