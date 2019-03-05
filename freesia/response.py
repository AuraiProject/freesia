"""
This module wraps :class:`aiohttp.web.Response` for user's convenience.
"""
from aiohttp.web import Response


def response(res):
    return Response(text=res)
