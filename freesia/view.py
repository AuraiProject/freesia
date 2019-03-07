"""
This module implements the class based view of the web framework.
"""
from inspect import iscoroutinefunction
from typing import Any, Callable

from aiohttp import web

HTTP_METHODS = {'get', 'post', 'head', 'options',
                'delete', 'put', 'trace', 'patch'}


class View:
    """
    The basic view class. You must create a new class to inherit it and implement the :func:`View.dispatch_request`.
    And the call :func:`View.as_view` with :func:`freesia.app.Freesia.add_route` to register the view. Like::

        class MyView(View):
            self dispatch_request(self, request):
                pass

        app = Freesia()
        app.add_route("/my-view", view_func=MyView.as_view())
    """

    methods = None
    decorator = None

    def __init__(self, *args, **kwargs):
        pass

    async def dispatch_request(self, request: web.BaseRequest) -> Any:
        raise NotImplementedError()

    @classmethod
    def as_view(cls, endpoint: str = None, *cls_args, **cls_kwargs) -> Callable:
        if endpoint is None:
            endpoint = cls.__name__

        async def view(*args, **kwargs):
            self = cls(*cls_args, **cls_kwargs)
            return await self.dispatch_request(*args, **kwargs)

        if cls.decorator:
            for d in cls.decorator:
                view = d(view)

        view.methods = cls.methods
        view.__name__ = cls.__name__
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        return view


class MethodMetaView(type):
    """
    A meta used by class based class to collect the implemented methods.
    """

    def __init__(cls, name, bases, d):
        super().__init__(name, bases, d)

        if "methods" not in d:
            methods = set()
            for m in HTTP_METHODS:
                if hasattr(cls, m):
                    if not iscoroutinefunction(getattr(cls, m)):
                        raise ValueError("View method {}.{} should be awaitable.".format(name, m))
                    methods.add(m)
            cls.methods = methods


class MethodView(View, metaclass=MethodMetaView):
    """
    Method based class view. See example::

        class MyView(MethodView):
            def get(self, request, name):
                pass

        app = Freesia()
        app.add_route("/person/<name>", MyView.as_view())
    """

    async def dispatch_request(self, request: web.BaseRequest, *args, **kwargs) -> Any:
        m = request.method.lower()
        if m in self.methods:
            return await (getattr(self, m)(request, *args, **kwargs))
        else:
            raise web.HTTPMethodNotAllowed(m, self.methods)
