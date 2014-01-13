


class Request(object):


    def __init__(self, method, params=None, id=None):
        self.method = method
        self.params = params or ()
        self.id = id
        self.context = {}


    def _clone(self, method=None, params=None, id=None):
        child = Request(method or self.method, params or self.params,
                        id or self.id)
        child.context = self.context
        return child


    def child(self):
        """
        Make a nearly identical L{Request} with one less segment in the
        method attribute.
        """
        return self._clone(self.method.split('.',1)[1])


    def stripParams(self, keys):
        """
        Create an identical request but with some keyword parameters missing.

        @param keys: A list of keys to remove from the current params dict.
        """
        kwargs = self.kwargs().copy()
        map(kwargs.pop, keys)
        return self._clone(params=kwargs)


    def args(self):
        """
        Get the args of this request (if positional args were given)
        """
        if type(self.params) is dict:
            return ()
        else:
            return self.params


    def kwargs(self):
        """
        Get the keyword arguments of this request (if keyword arguments were
        given)
        """
        if type(self.params) is dict:
            return self.params
        else:
            return {}
