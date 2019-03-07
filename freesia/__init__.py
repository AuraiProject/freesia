"""
    freesia
    ~~~~~~~~~

    A concise and lightweight web framework.✨

    :copyright: © 2019 by ArianX.
    :license: MIT, see LICENSE for more details.
"""
from .app import Freesia
from .utils import jsonify
from .group import Group
from .view import MethodView
from .session import get_session, set_up_session

from aiohttp.web import Response

AUTHOR = "ArianX"
VERSION = "0.0.1"
