


class Request(object):


    def __init__(self, method, params=None, id=None):
        self.full_method = self.method = method
        self.full_params = self.params = params or ()
        self.id = id
        self.context = {}


    def child(self):
        """
        Make a nearly identical L{Request} with one less segment in the
        method attribute.
        """
        self.method = '.'.join(self.method.split('.')[1:])
        return self


    def stripParams(self, keys):
        """
        Create an identical request but with some keyword parameters missing.

        @param keys: A list of keys to remove from the current params dict.
        """
        kwargs = self.kwargs().copy()
        map(kwargs.pop, keys)
        self.params = kwargs
        return self


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
