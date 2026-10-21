from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pytest

from python_anvil import Anvil
from tests.server import RecordedRequest, Server, start_server


Handler = Callable[[RecordedRequest, int], Mapping[str, Any] | None]


class TestServer(Server):
    """The local server, with a `respond` to set what it answers with."""

    __test__ = False

    def __init__(self, base_url: str = ""):
        super().__init__(base_url=base_url)
        self.handler: Handler = lambda request, index: {"json": {"data": {}}}

    def respond(self, handler: Handler | Mapping[str, Any]) -> None:
        """Answer every request with `handler`'s response, or with one response."""
        if callable(handler):
            self.handler = handler
        else:
            self.handler = lambda request, index: handler

    def respond_in_turn(self, *responses: Mapping[str, Any]) -> None:
        """Answer the first request with the first response, and so on. The last repeats."""
        self.handler = lambda request, index: responses[min(index, len(responses) - 1)]


@pytest.fixture
def server():
    test_server = TestServer()
    with start_server(
        lambda request, index: test_server.handler(request, index)
    ) as running:
        test_server.base_url = running.base_url
        test_server.requests = running.requests
        yield test_server


@pytest.fixture
def make_client(server):
    """A client that talks to the local server. Starts allowing 10 requests a second so tests aren't slow."""

    def factory(**options: Any) -> Anvil:
        options.setdefault("api_key", "my-api-key")
        options.setdefault("base_url", server.base_url)
        options.setdefault("request_limit", 10)
        options.setdefault("request_limit_ms", 1000)
        options.setdefault("timeout", 5)
        return Anvil(**options)

    return factory


@pytest.fixture
def client(make_client) -> Anvil:
    return make_client()
