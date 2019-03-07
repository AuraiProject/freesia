"""
This module implements the cookie based async session.
"""
from collections import abc
from abc import ABC, abstractmethod
from typing import MutableMapping, Callable

from aiohttp.web import BaseRequest
from aiohttp import web

from .utils import asy_json_dump, asy_json_load, Response
from .app import Freesia


class Session(abc.MutableMapping):
    """
    A dict like object to represent the session attribute.
    """

    def __init__(self, data: MutableMapping = None, max_age: float = None):
        self._mapping = {}
        self._modified = False
        self._accessed = False
        self._new = True

        if data:
            for k, v in data.items():
                self._mapping[k] = v

    @property
    def modified(self):
        return self._modified

    @property
    def new(self):
        return self._new

    @property
    def accessed(self):
        return self._accessed

    def _get_session_data(self):
        return self._mapping

    def __delitem__(self, key):
        self._modified = True
        del self._mapping[key]

    def __getitem__(self, item):
        self._accessed = True
        return self._mapping[item]

    def __iter__(self):
        return iter(self._mapping)

    def __setitem__(self, key, value):
        self._modified = self._accessed = True
        self._mapping[key] = value

    def __len__(self):
        return len(self._mapping)


class SessionInterface(ABC):
    """
    Abstract session interface. Inherit this class and implement the :func:`SessionInterface.load_session` and
    :func:`SessionInterface.save_session`.
    """

    def __init__(self, *, cookie_name: str = "FREESIA_SESSION", domain: str = None, max_age: float = None,
                 path: str = "/", secure: bool = False, httponly: bool = True,
                 json_encoder: Callable = asy_json_dump, json_decoder: Callable = asy_json_load):
        self._cookie_name = cookie_name
        self._cookie_params = dict(domain=domain, max_age=max_age, path=path, secure=secure, httponly=httponly)
        self.max_age = max_age
        self.json_encoder = json_encoder
        self.json_decoder = json_decoder

    @property
    def cookie_name(self):
        return self._cookie_name

    @property
    def cookie_params(self):
        return self._cookie_params

    async def new_session(self):
        return Session()

    @abstractmethod
    async def load_session(self, request: BaseRequest):
        pass

    @abstractmethod
    async def save_session(self, request: BaseRequest, resposne: Response, session: Session):
        pass


class SimpleCookieSession(SessionInterface):
    """
    Simple cookie session.
    """

    def __init__(self, *, cookie_name: str = "FREESIA_SESSION", domain: str = None, max_age: float = None,
                 path: str = "/", secure: bool = False, httponly: bool = True,
                 json_encoder: Callable = asy_json_dump, json_decoder: Callable = asy_json_load):
        super().__init__(cookie_name=cookie_name, domain=domain, max_age=max_age, path=path, secure=secure,
                         httponly=httponly, json_encoder=json_encoder, json_decoder=json_decoder)

    def save_cookie(self, response: Response, data) -> None:
        param = self._cookie_params
        if not data:
            response.del_cookie(self.cookie_name, domain=param["domain"], path=param["path"])
        else:
            response.set_cookie(self.cookie_name, data, **param)

    def load_cookie(self, request: BaseRequest) -> str:
        return request.cookies.get(self.cookie_name) or "null"

    async def save_session(self, request: BaseRequest, resposne: Response, session: Session):
        self.save_cookie(resposne, await self.json_encoder(session._get_session_data()))

    async def load_session(self, request: BaseRequest) -> Session:
        return Session(await self.json_decoder(self.load_cookie(request)))


SESSION_KEY = "freesia_session"
SESSION_INTERFACE_KEY = "freesia_session_interface"


async def get_session(request: BaseRequest) -> Session:
    """
    Get session from request. It must be used after call :func:`set_up_session`.
    """
    session = request.get(SESSION_KEY, None)
    if not isinstance(session, Session):
        session_interface = request[SESSION_INTERFACE_KEY]
        if not issubclass(session_interface.__class__, SessionInterface):
            raise RuntimeError("It seem's that the session interface has not been bounded.")
        else:
            session = await session_interface.load_session(request)
            if not isinstance(session, Session):
                session = await new_session(request)
            request[SESSION_KEY] = session
    return session


async def new_session(request: BaseRequest) -> Session:
    """
    Build a new session then save in request. It must be used after call :func:`set_up_session`.
    """
    session_interface = request[SESSION_INTERFACE_KEY]
    if not issubclass(session_interface.__class__, SessionInterface):
        raise RuntimeError("It seem's that the session interface has not been bounded.")
    else:
        session = await session_interface.new_session()
        if not isinstance(session, Session):
            raise ValueError("Error session instance.")
        request[SESSION_KEY] = session
    return session


def set_up_session(app: Freesia, session_interface: Callable):
    """
    Setup the session middleware to the app.
    """
    session_interface = session_interface()

    async def session_middleware(request, handler):
        request[SESSION_INTERFACE_KEY] = session_interface
        handle_error = False
        try:
            res = await handler()
        except web.HTTPException as exc:
            res = exc
            handle_error = True
        session = request.get(SESSION_KEY)
        if session and session.modified:
            await session_interface.save_session(request, res, session)
        if handle_error:
            raise res
        return res

    app.use([session_middleware])
