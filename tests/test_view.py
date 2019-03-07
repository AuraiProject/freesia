import unittest

from freesia import MethodView


class ViewTestCase(unittest.TestCase):
    def test_method_view(self):
        class MyView(MethodView):
            async def get(self, request):
                pass

            async def post(self, request):
                pass

        self.assertEqual(len(MyView.methods), 2)
