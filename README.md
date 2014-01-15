[![Build Status](https://secure.travis-ci.org/iffy/crapc.png?branch=master)](http://travis-ci.org/iffy/crapc)

# crapc #

Yet another RPC thing, with support for Twisted and JSON-RPC 2.0.


# Usage #

## Public methods ##

You can easily expose the public methods of any class for use in RPC systems
using `RPCFromPublicMethods`:

```python
from crapc import RPCFromPublicMethods

class Tickets(object):

    def __init__(self, data_store):
        self.data_store = data_store

    def create(self, name):
        self.data_store[name] = {}

    def delete(self, name):
        self.data_store.pop(name)

    def updateCost(self, name, cost):
        self.data_store[name]['cost'] = cost


if __name__ == '__main__':
    from crapc.helper import PythonInterface
    tickets = RPCFromPublicMethods(Tickets({}))
    i = PythonInterface(tickets)
    i.call('create', {'name': 'bob'})
```

(This makes use of the `PythonInterface` which is mostly useful for
demonstration and manual testing.)


## JSON-RPC 2.0 ##

Here's an example using [klein](http://github.com/twisted/klein)
(`pip install klein`) to serve
[JSON-RPC 2.0](http://www.jsonrpc.org/specification) over HTTP using
POST requests:

```python
from crapc import RPCFromPublicMethods
from crapc.jsonrpc import JsonInterface

from klein import Klein


class Balls(object):

    location = 0

    def kick(self, distance=10):
        self.location += distance
        return 'kicked %s to %s' % (distance, self.location)

    def throw(self, distance):
        self.location += distance
        return 'threw %s to %s' % (distance, self.location)


class BallsApp(object):

    app = Klein()

    def __init__(self):
        rpc = RPCFromPublicMethods(Balls())
        self.json_interface = JsonInterface(rpc)

    @app.route('/rpc', methods=['POST'])
    def rpc(self, request):
        request.setHeader('Content-Type', 'application/json')
        return self.json_interface.run(request.content.read())

if __name__ == '__main__':
    balls_app = BallsApp()
    balls_app.app.run('localhost', 8080)
```

Try it out with `curl`:

```bash
curl -X POST -d '{"jsonrpc":"2.0","id":1,"method":"kick"}' http://127.0.0.1:8080/rpc
curl -X POST -d '{"jsonrpc":"2.0","id":1,"method":"kick", "params":{"distance":3}}' http://127.0.0.1:8080/rpc
curl -X POST -d '{"jsonrpc":"2.0","id":1,"method":"throw","params":[1]}' http://127.0.0.1:8080/rpc
```


## Routing ##

You can use decorators if you want.  This includes the ability to perform
pre-checks (with `@prehook`) and fallback (with `@default`).  Note that you
can nest other RPCs (as is done with `Earth`):

```python
from twisted.internet import defer, task
from crapc import RPC

class Space(object):

    rpc = RPC()

    def __init__(self, planets=9):
        self.planets = planets

    @rpc.prehook
    def congrats(self, func, request):
        result = defer.maybeDeferred(func, request)
        return result.addCallback(lambda x: 'Congratulations.  %s' % (x,))

    @rpc.route('destroy')
    def destroy(self, request):
        self.planets -= 1
        return self.planets

    @rpc.route('earth')
    def earth(self, request):
        return Earth().rpc

    @rpc.default
    def default(self, request):
        return 'You are trying to %s, huh?' % (request.method,)


class Earth(object):

    rpc = RPC()

    @rpc.route('save')
    def save(self, request):
        return 'You saved the Earth.'


@defer.inlineCallbacks
def main(reactor):
    from crapc.helper import PythonInterface

    space = Space()
    py = PythonInterface(space.rpc)
    result = yield py.call('earth.save')
    print result
    result = yield py.call('mars.eat')
    print result
    result = yield py.call('destroy')
    print result


if __name__ == '__main__':
    task.react(main)

```

`@prehook` can also be used for logging or authentication or whatever else
you can dream up.


# How is this different than X? #

- Composition is used instead of inheritance.  (So your code doesn't have to
  import and use RPC-specific stuff all over).

- Only JSON-RPC version 2 is supported.

- Batch operations are not supported.

- [txJSON-RPC](https://github.com/oubiwann/txjsonrpc) - I wrote this thinking
  txJSON-RPC didn't support v2.0, but apparently it does ... perhaps the good
  parts of this code will make their way into txJSON-RPC.

- [txjason](https://github.com/flowroute/txjason) - crapc differs with txjason
  mostly in that things are composed instead of inherited.

