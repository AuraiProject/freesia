"""
This module implements the :class:`Group` of the web framework.
"""
from typing import Callable, Any, MutableMapping, Union, Tuple, Iterable

from .app import Freesia


class Group:
    """
    Use group to divide an app by the different logic. Its instance will be added in
    :attr:`freesia.app.Freesia.groups`.

    :param name: Name of this group.
    :param url_prefix: Url prefix of this group. All rules registered to this group will be prefixed to the `url_prefix`.
    """

    def __init__(self, name: str, url_prefix: str):
        self.name = name
        self.url_prefix = url_prefix
        self.deferred_function = []

    def record(self, func: Callable) -> None:
        def decorator(app):
            func(app)

        self.deferred_function.append(decorator)

    def register(self, app):
        proxy = self.make_proxy(app)

        for deferred in self.deferred_function:
            deferred(proxy)

    def make_proxy(self, app):
        return GroupRegisterProxy(self, app)

    def route(self, rule: str, **options: Any) -> Callable:
        options.setdefault("method", ("GET",))
        methods = options["method"]

        def decorator(func):
            self.add_route(rule, methods, func, options)
            return func

        return decorator

    def add_route(self, rule: str, methods: Iterable[str], target: Callable, options: MutableMapping) -> None:
        self.record(
            lambda s: s.add_route(rule, methods, target, options)
        )

    def set_filter(self, name: str, url_filter: Tuple[str, Union[None, Callable], Union[None, Callable]]):
        self.record(
            lambda s: s.app.set_filter(name, url_filter)
        )


class GroupRegisterProxy:
    def __init__(self, group: Group, app: Freesia):
        self.group = group
        self.app = app

    def add_route(self, rule: str, methods: Iterable[str], target: Callable, options: MutableMapping) -> None:
        if self.group.url_prefix:
            rule = '/'.join((
                self.group.url_prefix.rstrip('/'),
                rule.lstrip('/')
            )) if rule else self.group.url_prefix

        if "endpoint" in options:
            options["endpoint"] = "{}.{}".format(self.group.name, options["endpoint"])
        else:
            options["endpoint"] = "{}.{}".format(self.group.name, target.__name__)

        self.app.add_route(rule, methods, target, options)
