"""
This module implements the async app of the web framework.
"""
import asyncio
from inspect import iscoroutinefunction
from typing import Any, Callable, MutableMapping, Tuple, Union, Container, Sized, Iterable
from pprint import pprint as print

from aiohttp import web
from aiohttp.web import Response

from .route import Route, Router


class Freesia:
    """
    The main class of this framework.
    """
    #: Default route class.
    #: See more information in :class:`freesia.route.Route` and :class:`freesia.route.AbstractRoute`.
    route_cls = Route
    #: Default router class.
    #: See more information in :class:`freesia.route.Router` and :class:`freesia.route.AbstractRouter`.
    url_map_cls = Router
    #: collected routes
    rules = []
    #: collected groups
    groups = {}

    def __init__(self):
        self.url_map = self.url_map_cls()

    def route(self, rule: str, **options: Any) -> Callable:
        """
        Register the new route to the framework.

        :param rule: url rule
        :param options: optional params
        :return: a decorator to collect the target function
        """
        options.setdefault("method", ("GET",))
        methods = options["method"]

        def decorator(func):
            self.add_route(rule, methods, func, options)
            return func

        return decorator

    def set_filter(self, name: str, url_filter: Tuple[str, Union[None, Callable], Union[None, Callable]]):
        """
        Add url filter.
        For more information see :attr:`route_cls`

        :param name: name of the url filter
        :param url_filter: A tuple that includ regex, in_filter and out_filter
        :return: None
        """
        self.route_cls.set_filter(name, url_filter)

    def add_route(self, rule: str, method: Iterable[str], target: Callable, options: MutableMapping) -> None:
        """
        Internal method of :func:`route`.

        :param rule: url rule
        :param method: the method that the target function should handles.
        :param target: target function
        :param options: optional prams
        :return: None
        """
        r = self.route_cls(rule, method, target, options)
        self.rules.append(r)
        self.url_map.add_route(r)

    async def cast(self, res: Any) -> Response:
        """
        Cast the res made by the user's handler to the normal response.

        :param res: route returned value
        :return: the instance of :class:`freesia.response.Response`
        """
        if iscoroutinefunction(res):
            return await self.cast(await res())

        if isinstance(res, Response): return res
        if isinstance(res, str) or isinstance(res, bytes):
            return Response(text=str(res))
        if isinstance(res, Container) and isinstance(res, Sized):
            if len(res) > 3:
                raise ValueError("Invalid response.")

            return Response(text=res[0],
                            status=res[1] if len(res) >= 1 else 200,
                            reason=res[2] if len(res) >= 2 else "ok",
                            )
        return Response(text=str(res))

    async def handler(self, request: web.BaseRequest):
        """
        hands out a incoming request

        :param request: the instance of :class:`aiohttp.web.BaseRequest`
        :return: result
        """
        print(request.path)
        target, params = self.url_map.get(request.path, request.method)
        res = await self.cast(await target(request, *params))
        return res

    async def serve(self, host: str, port: int):
        """
        Start to serve. Should be placed in a event loop.

        :param host: host
        :param port: port
        :return: None
        """
        server = web.Server(self.handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        print("============ Servint on http://{}:{}/ ============".format(host, port))

        while True:
            await asyncio.sleep(1000 * 3600)

    def run(self, host="localhost", port=8080):
        """
        start a async serve
        """
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.serve(host, port))
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()

    def register_group(self, group: Any) -> None:
        """
        Register :class:`freesia.groups.Group` to the app.

        :param group: The instance of :class:`freesia.groups.Group`.
        :return: None
        """
        if group.name in self.groups:
            raise ValueError("The group `{}` has been registered!".format(group.name))
        self.groups[group.name] = group
        group.register(self)
