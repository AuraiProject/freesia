import unittest
from collections import namedtuple

from freesia.route import Route

TestRule = namedtuple("TestRule", ["rule", "regex", "matching", "not_matching"])
test_rules = (TestRule(*u) for u in [
    ("/test", "/test", "/test", "/testtest"),
    ("/test/<name>", "/test/(?P<name>[^/]+)", "/test/mike", "/test/mike/mike"),
    ("/test/<int:age>", "/test/(?P<age>-?\d+)", "/test/1", "/test1.o"),
    ("/test/<float:money>", "/test/(?P<money>-?[\d.]+)", "/test/1.0", "/test/1")
])


async def temp():
    pass


class RouteTestCase(unittest.TestCase):
    def setUp(self):
        self.route_bak = Route
        globals()["Route"] = type("Route", Route.__bases__, dict(Route.__dict__))

    def tearDown(self):
        globals()["Route"] = self.route_bak

    def test_route_backup(self):
        self.assertNotEqual(id(self.route_bak), id(Route))

    def test_expect_regex_rules(self, rules=None):
        if rules is None:
            rules = test_rules
        for r in rules:
            route = Route(r.rule, "GET", temp, {
                "checking_param": False
            })
            with self.subTest(expect=r.regex, actual=route.regex_pattern):
                self.assertEqual(r.regex, route.regex_pattern)

    def test_custom_filter(self):
        custom_f = (
            r".*",
            lambda _: "to_url",
            lambda _: "to_origin",
        )
        Route.set_filter("custom", custom_f)

        rules = [
            TestRule("/test/<custom:name>", "/test/(?P<name>.*)", "", ""),
        ]
        self.test_expect_regex_rules(rules)

    def test_url_match(self):
        for r in test_rules:
            route = Route(r.rule, "GET", temp, {
                "checking_param": False
            })
            with self.subTest(matching=r.matching):
                t, _ = route.match(r.matching, "GET")
                self.assertIsNotNone(t)
            with self.subTest(not_matching=r.not_matching):
                t, _ = route.match(r.not_matching, "GET")
                self.assertIsNone(t)
