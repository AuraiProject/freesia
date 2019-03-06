"""
This module implements the route class of the framework.
"""
import re
import itertools
from inspect import signature, iscoroutinefunction
from abc import ABC, abstractmethod
from typing import Callable, MutableMapping, Tuple, Any, Iterable, Union, List

from aiohttp import web


class AbstractRoute(ABC):
    """
    AbstractRoute can only be used if you want to replace the default :class:`Route`.
    If you really want to do, you should inherit this class and
    implement the methods :func:`__init__`, :func:`set_filter` it requires. Then replace the default :attr:`app.Freesia.route_cls`
    with you own defined class before instantiating :class:`app.Freesia`. See example::

        class CustomRoute(AbstractRoute):
            def __init__(self, rule, methods, target, options):
                pass

            def set_filter(self, name, url_filter):
                pass

        Freesia.route_cls = CustomRoute

    :param rule: The url rule of the route.
    :param methods: The method list that this route can accept.
    :param target: The handler function that handles the request.
    :param options: Optional control parameters.
    """

    @abstractmethod
    def __init__(self, rule: str, methods: Iterable[str], target: Callable[..., Any], options: MutableMapping):
        pass

    @abstractmethod
    def set_filter(self, name: str, url_filter: Tuple[str, Callable, Callable]):
        pass


class AbstractRouter(ABC):
    """
    AbstractRouter can only be used if you want to replace the default :class:`Router`.
    If you really want to do, you should inherit this class and
    implement the methods :func:`add_route`, :func:`get` it requires. Then replace the default :attr:`app.Freesia.url_map_cls`
    with you own defined class before instantiating :class:`app.Freesia`. See example::

        class CustomRouter(AbstractRouter):
            def add_route(self, route):
                pass

            def get(self, rule, method):
                pass

        Freesia.url_map_cls = CustomRouter
    """

    @abstractmethod
    def add_route(self, route: AbstractRoute) -> None:
        pass

    @abstractmethod
    def get(self, rule: str, method: str) -> Tuple[Callable[..., Any], Tuple]:
        pass


class Route(AbstractRoute):
    """
    Default route class.

    :param rule: The url rule of the route.
    :param methods: The method list that this route can accept.
    :param target: The handler function that handles the request.
    :param options: Optional control parameters.
    """
    is_static = False
    rule_syntax = re.compile("(\\\\*)"
                             "(?:<(?:(.*?):)?([a-zA-Z_][a-zA-Z_0-9]*)>)")

    url_filters = {
        "int": (r'-?\d+', int, lambda s: str(int(s))),
        "float": (r'-?[\d.]+', int, lambda s: str(float(s))),
        'str': (r'[^/]+', str, str),
    }
    url_filters['default'] = url_filters["str"]

    def __init__(self, rule, methods, target, options):
        # sometimes we might recombine the cls so we display the class that specified for use.
        super(self.__class__, self).__init__(rule, methods, target, options)

        if not iscoroutinefunction(target):
            raise ValueError("The route function `{}` should be awaitable.".format(target.__name__))
        if isinstance(methods, str):
            raise ValueError("The param `methods` should be wrapped with the container.")

        self.rule = rule
        self.methods = set(methods)
        self.target = target
        self.endpoint = target.__name__
        self.regex_pattern = ""
        self.in_filters = {}
        self.builder = []

        if "endpoint" in options:
            self.endpoint = options.pop("endpoint")
        if "<" not in rule:
            self.is_static = True
        self.parse_pattern()
        if ("checking_param" not in options or options["checking_param"]) and not self.param_check():
            raise ValueError(
                "The rule asks for {} params, but the endpoint {} does not matching.".format(
                    len(self.in_filters), self.endpoint
                ))

    @classmethod
    def set_filter(cls, name: str, url_filter: Tuple[str, Union[None, Callable], Union[None, Callable]]) -> None:
        """
        Set a custom filter to the route.

        :param name: filter name
        :param url_filter: A tuple that includ regex, in_filter and out_filter
        :return: None
        """
        cls.url_filters[name] = url_filter

    @classmethod
    def iter_token(cls, rule: str) -> Tuple[str, str]:
        """
        Traverse the rule and generate the prefix and param info.

        :param rule: url rule to be iter
        :return: A tuple that includ the url filter name and param name.
        """
        offset, prefix = 0, ''
        for match in cls.rule_syntax.finditer(rule):
            prefix += rule[offset: match.start()]
            g = match.groups()
            if len(g[0]) % 2:
                # the parentheses have been escaped
                prefix += match.group(0)[len(g[0]):]
                offset = match.end()
                continue
            if prefix:
                yield prefix, None
            url_filter, name = g[1:3]
            yield url_filter or 'default', name
            offset, prefix = match.end(), ''
        if offset <= len(rule) or prefix:
            yield prefix + rule[offset:], None

    def parse_pattern(self) -> None:
        """
        Parse the :attr:`rule` to get regex pattern then store in :attr:`regex_pattern`

        :return: None
        """
        for url_filter, name in self.iter_token(self.rule):
            if name is None:
                self.regex_pattern += url_filter
                self.builder.append((None, url_filter))
            else:
                try:
                    mode, in_filter, out_filter = self.url_filters[url_filter]
                except KeyError:
                    raise ValueError(
                        "The url filter '{}' is not found.\n"
                        "Do you forget to use `Freesia.set_filter` to register it?".format(
                            url_filter))
                self.regex_pattern += '(?P<%s>%s)' % (name, mode)
                self.in_filters[name] = in_filter
                self.builder.append((name, out_filter))

    def param_check(self) -> bool:
        """
        Check if the number of parameters matches.

        :return: bool
        """
        p = signature(self.target).parameters
        if len(self.in_filters) != len(list(p.items())) - 1:
            # the first param is the instance of the :class:`Freesia.Request`
            return False
        return True

    def match(self, path: str, method: str) -> Union[None, List[Any]]:
        """
        Check that this route matches the incoming parameters.

        :param path: path to be matched
        :param method: the request method
        :return: A List of the matching param or None.
        """
        if method not in self.methods:
            return None
        matching = re.fullmatch(self.regex_pattern, path)
        if matching is None:
            return None
        else:
            groups = matching.groupdict()
            params = []
            for k, v in groups.items():
                try:
                    params.append(self.in_filters[k](v))
                except ValueError:
                    raise web.HTTPBadRequest()
            return params


class Router(AbstractRouter):
    """
    Default router.
    """

    def __init__(self):
        self.static_url_map = {}
        self.method_map = {}

    def add_route(self, route: Route) -> None:
        """
        Add a route to the router.

        :param route: the instance of the :class:`Route`
        :return: None
        """
        if route.is_static:
            self.static_url_map.setdefault(route.regex_pattern, [])
            self.static_url_map[route.regex_pattern].append(route)
        else:
            for m in route.methods:
                self.method_map.setdefault(m, [])
                self.method_map[m].append(route)

    def get_from_static_url(self, path: str, method: str) -> Tuple[Callable, Tuple]:
        """
        Match the static url. Throw a exception if not matches.

        :param path: incoming path
        :param method: the method of the request
        :return: A tuple include the handler function and the params.
        """
        if path not in self.static_url_map:
            raise web.HTTPNotFound()

        allowed_methods = set()
        for route in self.static_url_map[path]:
            for m in route.methods:
                allowed_methods.add(m)
            if method in route.methods:
                return route.target, tuple()
        else:
            raise web.HTTPMethodNotAllowed(method, allowed_methods)

    def get(self, path: str, method: str) -> Tuple[Callable, Tuple]:
        """
        Match giving path. Throw a exception if not matches.

        :param path: incoming path.
        :param method: the method of the request.
        :return: A tuple include the handler function and the params.
        """
        if path in self.static_url_map:
            return self.get_from_static_url(path, method)

        if method not in self.method_map:
            raise web.HTTPNotFound()

        for r in self.method_map[method]:
            params = r.match(path, method)
            if params:
                return r.target, params

        allowed_methods = set()
        for r in itertools.chain(*self.method_map.values()):
            if r.match(path, method):
                allowed_methods.add(r.method)
        if allowed_methods:
            raise web.HTTPMethodNotAllowed(method, allowed_methods)

        raise web.HTTPNotFound()
