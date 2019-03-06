import unittest

from freesia import Group, Freesia


class GroupTestCase(unittest.TestCase):
    def test_register_group(self):
        test = Group("test", "/")
        app = Freesia()
        app.register_group(test)

        self.assertEqual(app.groups["test"], test)

    def test_url_prefix(self):
        test = Group("test", "/test")

        @test.route("/api")
        async def temp(request):
            pass

        app = Freesia()
        app.register_group(test)

        t, _ = app.url_map.get("/test/api", "GET")
        self.assertEqual(temp, t)
