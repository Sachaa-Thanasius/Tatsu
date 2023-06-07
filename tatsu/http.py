"""
tatsu.http
----------

The HTTP routes, requests, and response handlers for the Tatsu API.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Coroutine
from datetime import datetime, timedelta
from typing import Any, ClassVar, Literal
from urllib.parse import quote, urljoin

import aiohttp

from . import __version__
from .enums import ActionType

_LOGGER = logging.getLogger(__name__)


class Route:
    """A helper class for instantiating an HTTP method to Tatsu.

    Parameters
    ----------
    method : :class:`str`
        The HTTP request to make, e.g. ``"GET"``.
    path : :class:`str`
        The prepended path to the API endpoint you want to hit, e.g. ``"/user/{user_id}/profile"``.
    **parameters : Any
        Special keyword arguments that will be substituted into the corresponding spot in the `path` where the key is
        present, e.g. if your parameters are ``user_id=1234`` and your path is``"user/{user_id}/profile"``, the path
        will become ``"user/1234/profile"``.
    """

    BASE: ClassVar[str] = "https://api.tatsu.gg/v1/"

    def __init__(self, method: str, path: str, **parameters: Any) -> None:
        self.method = method
        self.path = path
        url = urljoin(self.BASE, path)
        if parameters:
            url = url.format_map({k: quote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        self.url = url


class HTTPClient:
    """A small HTTP client that sends requests to the Tatsu API."""

    def __init__(self, token: str, *, session: aiohttp.ClientSession | None = None) -> None:
        self.token = token
        self._session = session
        user_agent = "Tatsu (https://github.com/Sachaa-Thanasius/Tatsu {0} Python/{1[0]}.{1[1]} aiohttp/{2} (Currently testing in beta, please don't ban me)"
        self.user_agent = user_agent.format(__version__, sys.version_info, aiohttp.__version__)
        self._ratelimit_unlock = asyncio.Event()
        self._ratelimit_unlock.set()
        self._ratelimit_reset_time = None

    async def _start_session(self) -> None:
        """|coro|

        Create an internal HTTP session for this client if necessary.
        """

        if (not self._session) or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """|coro|

        Close the internal HTTP session.
        """

        if self._session and not self._session.closed:
            await self._session.close()

    async def request(self, route: Route, **kwargs) -> bytes:
        """|coro|

        Send an HTTP request to some endpoint in the Tatsu API.

        Parameters
        ----------
        route
            The filled-in API route that will be sent a request.
        **kwargs
            Arbitrary keyword arguments for :meth:`aiohttp.ClientSession.request`. See that method for more information.
        """

        method = route.method
        url = route.url

        headers = kwargs.pop("headers", {})
        headers["User-Agent"] = self.user_agent
        headers["Authorization"] = self.token
        kwargs["headers"] = headers

        await self._start_session()

        if not self._ratelimit_unlock.is_set():
            await self._ratelimit_unlock.wait()

        for _tries in range(5):
            async with self._session.request(method, url, **kwargs) as response:
                now = datetime.now()
                _LOGGER.debug("%s %s has returned %d.", method, response.url.human_repr(), response.status)

                limit = response.headers.get("X-RateLimit-Limit")
                remaining = response.headers.get("X-RateLimit-Remaining")
                reset = response.headers.get("X-RateLimit-Reset")
                _LOGGER.debug("Rate limit info: limit=%s, remaining=%s, reset=%s", limit, remaining, reset)

                # Check that the reset time for the rate limit makes sense.
                # Can't check the reset timestamp from the header since it's all relative to the time of first api
                # call. At least, I think so. The timestamp is a few seconds behind local time, so it's wrong in that
                # respect. Have to keep track of it locally.
                if not self._ratelimit_reset_time or self._ratelimit_reset_time < now:
                    self._ratelimit_reset_time = now + timedelta(seconds=61)

                if response.status == 429:
                    self._ratelimit_unlock.clear()
                    _LOGGER.debug(
                        "Comparison of timestamps (now vs. ratelimit reset time): %s vs %s",
                        now,
                        self._ratelimit_reset_time,
                    )
                    wait_delta = self._ratelimit_reset_time - now
                    _LOGGER.debug("Hit a rate limit. Waiting for %s seconds.", wait_delta.total_seconds())
                    await asyncio.sleep(wait_delta.total_seconds())
                    self._ratelimit_unlock.set()
                    continue

                if response.status not in (200, 429):
                    response.raise_for_status()

                data = await response.read()
                return data
        msg = "Unreachable code in HTTP handling."
        raise RuntimeError(msg)

    def get_guild_member_points(self, guild_id: int, member_id: int) -> Coroutine[Any, Any, bytes]:
        route = Route("GET", "guilds/{guild_id}/members/{member_id}/points", guild_id=guild_id, member_id=member_id)
        return self.request(route)

    def modify_guild_member_points(
            self,
            guild_id: int,
            member_id: int,
            action: ActionType,
            amount: int,
    ) -> Coroutine[Any, Any, bytes]:
        if amount < 1 or amount > 100_000:
            msg = "Points amount must be between 1 and 100,000."
            raise ValueError(msg)

        route = Route("PATCH", "guilds/{guild_id}/members/{member_id}/points", guild_id=guild_id, member_id=member_id)
        json_data = {"action": action, "amount": amount}
        return self.request(route, json=json_data)

    def modify_guild_member_score(
            self,
            guild_id: int,
            member_id: int,
            action: ActionType,
            amount: int,
    ) -> Coroutine[Any, Any, bytes]:
        if amount < 1 or amount > 100_000:
            msg = "Score amount must be between 1 and 100,000."
            raise ValueError(msg)

        route = Route("PATCH", "guilds/{guild_id}/members/{member_id}/score", guild_id=guild_id, member_id=member_id)
        json_data = {"action": action, "amount": amount}
        return self.request(route, json=json_data)

    def get_guild_member_ranking(
            self,
            guild_id: int,
            user_id: int,
            period: Literal["all", "month", "week"] = "all",
    ) -> Coroutine[Any, Any, bytes]:
        route = Route(
            "GET",
            "guilds/{guild_id}/rankings/members/{user_id}/{time_range}",
            guild_id=guild_id,
            user_id=user_id,
            time_range=period,
        )
        return self.request(route)

    def get_guild_rankings(
            self,
            guild_id: int,
            period: Literal["all", "month", "week"] = "all",
            *,
            offset: int = 0,
    ) -> Coroutine[Any, Any, bytes]:
        if offset < 0:
            msg = "Pagination offset must be greater than or equal to 0."
            raise ValueError(msg)

        route = Route("GET", "guilds/{guild_id}/rankings/{time_range}", guild_id=guild_id, time_range=period)
        params = {"offset": offset}
        return self.request(route, params=params)

    def get_user_profile(self, user_id: int) -> Coroutine[Any, Any, bytes]:
        route = Route("GET", "users/{user_id}/profile", user_id=user_id)
        return self.request(route)