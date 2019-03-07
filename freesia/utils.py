"""
Some common tools are defined in this module.
"""
from typing import Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json

from aiohttp.helpers import sentinel
from aiohttp.typedefs import LooseHeaders
from aiohttp.web import Response

block_pool_exc = ThreadPoolExecutor()


async def asy_json_dump(data):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(block_pool_exc, lambda: json.dumps(data))


async def asy_json_load(data):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(block_pool_exc, lambda: json.loads(data))


async def jsonify(
        data: Any = sentinel, *,
        text: str = None,
        body: bytes = None,
        status: int = 200,
        reason: Optional[str] = None,
        headers: LooseHeaders = None,
        content_type: str = 'application/json',
        dumps: Callable = asy_json_dump
) -> Response:
    if data is not sentinel:
        if text or body:
            raise ValueError(
                "only one of data, text, or body should be specified"
            )
        else:
            text = await dumps(data)
    return Response(text=text, body=body, status=status, reason=reason,
                    headers=headers, content_type=content_type)


def redirect(url, permanent=False):
    return Response(
        status=301 if permanent else 302,
        headers={
            "Location": str(url)
        }
    )
