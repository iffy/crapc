from twisted.trial.unittest import TestCase


from crapc._request import Request


class RequestTest(TestCase):


    def test_init(self):
        """
        Requests are initialized with a method at the very least.
        """
        r = Request('foo')
        self.assertEqual(r.method, 'foo')
        self.assertEqual(r.params, ())
        self.assertEqual(r.id, None)
        self.assertEqual(r.context, {})


    def test_init_params(self):
        """
        You can initialize with parameters.
        """
        r = Request('foo', {'foo': 'bar'})
        self.assertEqual(r.params, {'foo': 'bar'})


    def test_init_id(self):
        """
        You can initialize with an id
        """
        r = Request('foo', id=10)
        self.assertEqual(r.id, 10)


    def test_args_dict(self):
        """
        If the params are a dict, then args is ()
        """
        r = Request('foo', {'foo': 'bar'})
        self.assertEqual(r.args(), ())


    def test_args_tuple(self):
        """
        If params is a tuple/list, then args is a tuple/list
        """
        r = Request('foo', ('a', 'b'))
        self.assertEqual(r.args(), ('a', 'b'))


    def test_kwargs_dict(self):
        """
        If params is a dict, then kwargs is that dict
        """
        r = Request('foo', {'foo': 'bar'})
        self.assertEqual(r.kwargs(), {'foo': 'bar'})


    def test_kwargs_tuple(self):
        """
        If params is a tuple/list, then kwargs is {}
        """
        r = Request('foo', ['a', 'b'])
        self.assertEqual(r.kwargs(), {})


    def test_child(self):
        """
        You can make a child request out of a parent request, which will just
        pop a part off of the method string.
        """
        r = Request('foo.bar')
        child = r.child()
        self.assertEqual(child.method, 'bar', "Should have child method")
        r.context['foo'] = 'foo'
        self.assertEqual(child.context['foo'], 'foo', "Child should share the "
                         "context of the parent")


    def test_child_params(self):
        """
        Children should inherit a copy of the parent's params.
        """
        r = Request('foo.bar', {'a': 'apple'})
        child = r.child()
        self.assertEqual(child.params, {'a': 'apple'})


    def test_child_id(self):
        """
        Children should inherit the parent's id
        """
        r = Request('foo.bar', id=10)
        child = r.child()
        self.assertEqual(child.id, 10)


    def test_stripParams(self):
        """
        You can make a new request object that is missing a named parameter.
        """
        r = Request('foo.bar', {'foo': 'bar', 'baz': 'wow'})
        child = r.stripParams(['foo'])
        self.assertEqual(child.method, 'foo.bar')
        self.assertEqual(child.params, {'baz': 'wow'})
        self.assertEqual(r.params, {'foo': 'bar', 'baz': 'wow'},
                         "The original request should retain the original "
                         "parameters.")

        r.context['foo'] = 'foo'
        self.assertEqual(child.context['foo'], 'foo', "The context should "
                         "be shared among the requests")


    def test_stripParams_id(self):
        """
        Children should inherit the parent id
        """
        r = Request('foo.bar', id=12)
        child = r.stripParams([])
        self.assertEqual(child.id, 12)

        
