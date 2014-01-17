


class Request(object):
    """
    This is a single RPC request.

    @ivar method: The method name currently being looked for.  Segments are
        removed from this with L{child}.
    @type method: str

    @ivar full_method: The original method being looked for.  This is unchanged
        by calls to L{child}.
    @type full_method: str

    @ivar params: Either an iterable of positional arguments or a dictionary
        of keyword arguments to be used when calling the requested procedure.
    @type params: list/tuple or dict
    
    @ivar full_params: The original params for the request.  This is unchanged
        by calls to L{stripParams}.
    @type full_params: list/tuple or dict

    @ivar context: A dictionary of context for this request.  Application code
        is welcome to pollute and fight over the contents of this dictionary
        as much as it wants.
    @type context: dict
    """


    def __init__(self, method, params=None):
        self.full_method = self.method = method
        self.full_params = self.params = params or ()
        self.context = {}


    def __repr__(self):
        return '<Request(%r, %r, %r) %r>' % (self.full_method, self.full_params,
                                             self.id, self.context)


    def child(self):
        """
        Remove the leading segment from this Request's C{method} attribute.

        @return: self
        """
        self.method = '.'.join(self.method.split('.')[1:])
        return self


    def stripParams(self, keys):
        """
        Remove the given C{keys} from this Request's C{params} dict.

        @param keys: A list of keys to remove from the current params dict.

        @return: self
        """
        kwargs = self.kwargs().copy()
        map(kwargs.pop, keys)
        self.params = kwargs
        return self


    def args(self):
        """
        Get the args of this request (if positional args were given).

        @rtype: tuple/list
        """
        if type(self.params) is dict:
            return ()
        else:
            return self.params


    def kwargs(self):
        """
        Get the keyword arguments of this request (if keyword arguments were
        given)

        @rtype: dict
        """
        if type(self.params) is dict:
            return self.params
        else:
            return {}
