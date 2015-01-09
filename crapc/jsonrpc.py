
import json

from twisted.internet import defer
from twisted.python.failure import Failure

from crapc._request import Request
from crapc import error


class JsonRPCError(error.RPCError):
    public_message = "Error"
    code = -32603

class ParseError(JsonRPCError):
    public_message = "Parse error"
    code = -32700

class InvalidRequest(JsonRPCError):
    public_message = "Invalid request"
    code = -32600

class MethodNotFound(JsonRPCError):
    public_message = "Method not found"
    code = -32601

class InvalidParams(JsonRPCError):
    public_message = "Invalid parameters"
    code = -32602

class InternalError(JsonRPCError):
    public_message = "Internal error"
    code = -32603



class JsonInterface(object):


    def __init__(self, rpc, serialize=None, deserialize=None,
                 logError=None):
        """
        @param logError: Function that will be called with Failure instances
            when they happen.
        """
        self.rpc = rpc
        self._serialize = serialize or json.dumps
        self._deserialize_fn = deserialize or json.loads
        self._logError = logError or (lambda x:None)


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


    def _makeErrorResponse(self, failure, request_id=None):
        logging_message = ''
        try:
            self._logError(failure)
        except:
            logging_message = ' (Logging failed)'
        exc = failure.value
        code = getattr(exc, 'code', InternalError.code)
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': code,
                'message': '%s%s' % (exc.public_message, logging_message),
            },
        }


    def run(self, json_string):
        d = self._deserialize(json_string)
        d.addCallback(self._forkBatch)
        d.addErrback(self._makeErrorResponse)
        d.addCallback(self._serialize)
        return d


    def _runSingleRequest(self, request):
        """
        Run a single request.
        """
        d = defer.maybeDeferred(self._runDeserialized, request)
        d.addErrback(self._makeErrorResponse)
        return d


    def _forkBatch(self, data):
        """
        If data is a list, make several calls.  If it's a dict, just make one.
        """
        if isinstance(data, dict):
            # single
            return self._runSingleRequest(data)
        elif data and isinstance(data, list):
            # multiple
            dlist = []
            for item in data:
                dlist.append(self._runSingleRequest(item))
            return defer.gatherResults(dlist)
        else:
            # no requests
            raise InvalidRequest("empty request")


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
        raise InternalError(failure.value)

