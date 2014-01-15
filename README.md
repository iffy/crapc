[![Build Status](https://secure.travis-ci.org/iffy/crapc.png?branch=master)](http://travis-ci.org/iffy/crapc)

# crapc #

Yet another RPC thing, with support for Twisted and JSON-RPC 2.0.


# Usage #

## Public methods ##

You can easily expose the public methods of a class for use in RPC systems
using `crapc.RPCFromPublicMethods`:

```python
from crapc import RPCFromPublicMethods
from crapc.helper import PythonInterface

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
    tickets = RPCFromPublicMethods(Tickets({}))
    i = PythonInterface(tickets)
    i.call('create', {'name': 'bob'})
```

(This makes use of the `PythonInterface` which is mostly useful for
demonstration and manual testing.)


## JSON-RPC 2.0 ##

Here's an example using [klein](http://github.com/twisted/klein)
(`pip install klein`) to serve
[JSON-RPC 2.0](http://www.jsonrpc.org/specification) over HTTP:

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
