import unittest
from aiohttp.web import HTTPNotFound, HTTPMethodNotAllowed

from freesia.route import Route, Router


async def temp():
    pass


class RouterTestCase(unittest.TestCase):
    def test_add_static_route(self):
        r = Route("/", "GET", temp, {
            "checking_param": False
        })
        router = Router()
        router.add_route(r)
        self.assertEqual(len(router.static_url_map), 1)

    def test_add_non_static_route(self):
        r = Route("/<name>", ["GET"], temp, {
            "checking_param": False
        })
        router = Router()
        router.add_route(r)
        self.assertIn("GET", router.method_map)
        self.assertEqual(len(router.method_map["GET"]), 1)

    def test_get_route_from_static(self):
        r = Route("/", ["GET"], temp, {
            "checking_param": False
        })
        router = Router()
        router.add_route(r)
        t, _ = router.get("/", "GET")
        self.assertIsNotNone(t)
        with self.assertRaises(HTTPNotFound):
            router.get("/notexist", "GET")

    def test_get_from_dyna(self):
        r = Route("/hello/<name>", ["GET"], temp, {
            "checking_param": False
        })
        router = Router()
        router.add_route(r)
        t, _ = router.get("/hello/name", "GET")
        self.assertIsNotNone(t)
        with self.assertRaises(HTTPNotFound):
            router.get("/hello/not/name", "GET")

    def test_method_not_allowed(self):
        r = Route("/", "GET", temp, {
            "checking_param": False
        })
        router = Router()
        router.add_route(r)
        with self.assertRaises(HTTPMethodNotAllowed):
            router.get("/", "POST")
