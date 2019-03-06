"""
This module implements the WSGI app of the web framework.
"""
import asyncio
from typing import Any, Callable, MutableMapping, Tuple, Union
from pprint import pprint as print

from aiohttp import web

from .route import Route, Router


class Freesia:
    route_cls = Route
    url_map_cls = Router
    rules = []

    def __init__(self):
        self.url_map = self.url_map_cls()

    def route(self, rule: str, **options: Any) -> Callable:
        options.setdefault("method", ("GET",))
        methods = options["method"]

        def decorator(func):
            self.add_route(rule, methods, func, options)
            return func

        return decorator

    def set_filter(self, name: str, url_filter: Tuple[str, Union[None, Callable], Union[None, Callable]]):
        self.route_cls.set_filter(name, url_filter)

    def add_route(self, rule: str, method: str, target: Callable, options: MutableMapping):
        r = self.route_cls(rule, method, target, options)
        self.rules.append(r)
        self.url_map.add_route(r)
        return r

    async def handler(self, request: web.BaseRequest):
        print(request.path)
        target, params = self.url_map.get(request.path, request.method)
        return await target(request, *params)

    async def serve(self, host: str, port: int):
        server = web.Server(self.handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        print("============ Servint on http://{}:{}/ ============".format(host, port))

        while True:
            await asyncio.sleep(1000 * 3600)

    def run(self, host="localhost", port=8080):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.serve(host, port))
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
