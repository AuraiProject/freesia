"""
This module implements the route class of the framework.
"""
import re
from inspect import signature
from abc import ABC, abstractmethod
from typing import Callable, MutableMapping, Tuple, Any, Iterable, Union, List

from aiohttp import web


class AbstractRoute(ABC):
    @abstractmethod
    def __init__(self, rule: str, methods: Iterable[str], target: Callable[..., Any], options: MutableMapping):
        pass

    @abstractmethod
    def set_filter(self, name: str, url_filter: Tuple[str, Callable, Callable]):
        pass


class AbstractRouter(ABC):
    @abstractmethod
    def add_route(self, route: AbstractRoute) -> None:
        pass

    @abstractmethod
    def get(self, rule: str, method: str) -> Tuple[Callable[..., Any], Tuple]:
        pass


class Route(AbstractRoute):
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
        super().__init__(rule, methods, target, options)
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
        if "checking_param" not in options or options["checking_param"]:
            if not self.param_check():
                raise ValueError(
                    "The rule asks for {} params, but the endpoint {} does not matching.".format(
                        len(self.in_filters), self.endpoint
                    ))

    @classmethod
    def set_filter(cls, name, url_filter):
        cls.url_filters[name] = url_filter

    @classmethod
    def iter_token(cls, rule: str):
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

    def parse_pattern(self):
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

    def param_check(self):
        p = signature(self.target).parameters
        if len(self.in_filters) != len(list(p.items())) - 1:
            return False
        return True

    def match(self, rule: str, method: str) -> Union[None, List[Any]]:
        if method not in self.methods:
            return None
        matching = re.fullmatch(self.regex_pattern, rule)
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
    def __init__(self):
        self.static_url_map = {}
        self.method_map = {}

    def add_route(self, route: Route):
        if route.is_static:
            self.static_url_map.setdefault(route.regex_pattern, [])
            self.static_url_map[route.regex_pattern].append(route)
        else:
            for m in route.methods:
                self.method_map.setdefault(m, [])
                self.method_map[m].append(route)

    def get(self, rule: str, method: str):
        if rule in self.static_url_map:
            for route in self.static_url_map[rule]:
                if method in route.methods:
                    return route.target, tuple()
        elif method not in self.method_map:
            raise web.HTTPNotFound()
        else:
            for r in self.method_map[method]:
                params = r.match(rule, method)
                if params:
                    return r.target, params
        raise web.HTTPNotFound()
