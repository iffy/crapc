[![Build Status](https://secure.travis-ci.org/iffy/crapc.png?branch=master)](http://travis-ci.org/iffy/crapc)

# crapc #

Yet another RPC thing, with support for Twisted and JSON-RPC 2.0.


# Usage #

## Public methods ##

You can easily expose the public methods of a class for use in RPC systems:

```python
from crapc import RPC, RPCFromPublicMethods
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


class MyRPC(object):

    rpc = RPC()

    def __init__(self, data_store):
        self.data_store = data_store

    @rpc.route('tickets')
    def tickets(self, request):
        return RPCFromPublicMethods(Tickets(self.data_store))


if __name__ == '__main__':
    my_rpc = MyRPC({})
    i = PythonInterface(my_rpc.rpc)
    i.call('tickets.create', {'name': 'bob'})
```

(This makes use of the `PythonInterface` which is mostly useful for
demonstration and manual testing.)


## JSON-RPC 2.0 ##

*coming*