"""Sends the client's requests: auth, rate limiting, retries and error handling."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlsplit

import requests

from python_anvil.auth import build_auth_header
from python_anvil.constants import (
    DATA_TYPE_BYTES,
    DATA_TYPE_JSON,
    DATA_TYPE_STREAM,
    DATA_TYPES,
    DEFAULT_BASE_URL,
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_REQUEST_LIMIT_MS,
    DEFAULT_TIMEOUT,
)
from python_anvil.errors import (
    AnvilRequestError,
    normalize_exception,
    normalize_json_errors,
)
from python_anvil.rate_limit import RateLimiter


logger = logging.getLogger(__name__)


def default_user_agent() -> str:
    from python_anvil import __version__

    return f"python-anvil/{__version__}"


class HTTPClient:
    """Sends requests to one Anvil environment with one set of credentials.

    Every request gets the Authorization and User-Agent headers, waits for the
    rate limit, and is retried after a 429. See `RateLimiter`.
    """

    def __init__(
        self,
        api_key: str | None = None,
        access_token: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        user_agent: str | None = None,
        request_limit: int = DEFAULT_REQUEST_LIMIT,
        request_limit_ms: int = DEFAULT_REQUEST_LIMIT_MS,
        timeout: float | tuple[float, float] | None = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ):
        self.base_url = normalize_base_url(base_url)
        self.auth_header = build_auth_header(api_key, access_token)
        self.user_agent = user_agent or default_user_agent()
        self.timeout = timeout
        self._owns_session = session is None
        self.session = session or requests.Session()
        self.rate_limiter = RateLimiter(request_limit, request_limit_ms)

    def url(self, path_or_url: str) -> str:
        """The full URL for a path like `/api/v1/fill/abc.pdf`.

        A full URL is used as-is if it is on the base URL. One on another host
        is refused: it would get this client's credentials.
        """
        parts = urlsplit(path_or_url)
        if parts.scheme or parts.netloc:
            base = urlsplit(self.base_url)
            if (parts.scheme, parts.netloc) != (base.scheme, base.netloc):
                raise ValueError(
                    f"{path_or_url!r} is not on this client's base_url, "
                    f"{self.base_url}. Pass a path like /api/v1/..., or make a "
                    "client with that base_url."
                )
            return path_or_url
        return f"{self.base_url}/{path_or_url.lstrip('/')}"

    def request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Callable[[], Any] | None = None,
        headers: Mapping[str, str] | None = None,
        stream: bool = False,
        timeout: float | tuple[float, float] | None = None,
    ) -> requests.Response:
        """Send a request, within the rate limit and retried after any 429.

        The response is returned as the server sent it, errors and all. Use
        `process_response` to turn it into data or an `AnvilRequestError`.

        :param files: A function that returns the multipart parts to send, so
            they can be built again for a retry.
        """
        url = self.url(path_or_url)
        all_headers = {
            "User-Agent": self.user_agent,
            "Authorization": self.auth_header,
            **(headers or {}),
        }
        timeout = self.timeout if timeout is None else timeout

        def send() -> requests.Response:
            return self.session.request(
                method.upper(),
                url,
                params=params,
                json=json,
                data=data,
                files=files() if files else None,
                headers=all_headers,
                stream=stream,
                timeout=timeout,
            )

        return self.rate_limiter.run(send)

    def close(self) -> None:
        """Close the HTTP session, if it is the client's own."""
        if self._owns_session:
            self.session.close()


def process_response(
    response: requests.Response, data_type: str = DATA_TYPE_JSON
) -> Any:
    """The data in a response, or an `AnvilRequestError` if it is an error.

    An error is any status outside 2xx, or a 2xx GraphQL response with
    `errors`. Whatever was asked for, a JSON response is parsed: the API
    answers every request with JSON when something is wrong.
    """
    if data_type not in DATA_TYPES:
        raise ValueError(f"data_type must be one of: {'|'.join(DATA_TYPES)}")

    status_code = response.status_code
    content_type = response.headers.get("content-type", "")

    json_body: Any = None
    parse_error: Exception | None = None
    is_json = "application/json" in content_type.lower()
    if is_json:
        try:
            json_body = response.json()
        except ValueError as e:
            parse_error = e
            logger.debug(
                "Problem parsing the JSON response for status %s: %s", status_code, e
            )

    graphql_errors = isinstance(json_body, Mapping) and bool(json_body.get("errors"))
    if parse_error or graphql_errors or status_code >= 300:
        status_text = response.reason or "Unknown Error"
        if parse_error:
            errors = normalize_exception(parse_error)
        elif is_json:
            errors = normalize_json_errors(json_body, status_text)
        else:
            # Not JSON, so not from the API itself: a proxy or a load balancer.
            # Keep some of the body, which is all there is to go on.
            errors = normalize_json_errors(None, status_text)
            body = _body_snippet(response)
            if body:
                errors[0]["body"] = body
        # A GraphQL response can have data alongside its errors
        data = json_body.get("data") if isinstance(json_body, Mapping) else None
        response.close()
        raise AnvilRequestError(
            errors,
            status_code=status_code,
            headers=response.headers,
            data=data,
            response=response,
        )

    if is_json:
        return json_body
    if data_type == DATA_TYPE_JSON:
        try:
            return response.json()
        except ValueError as e:
            raise ValueError(
                f"Expected a JSON response, but got {content_type or 'no content type'}. "
                "Pass data_type='bytes' or 'stream' for a binary endpoint."
            ) from e
    if data_type == DATA_TYPE_BYTES:
        return response.content
    if data_type == DATA_TYPE_STREAM:
        return response
    raise ValueError(
        f"data_type must be one of: {'|'.join(DATA_TYPES)}"
    )  # pragma: no cover


def _body_snippet(response: requests.Response, limit: int = 2000) -> str:
    try:
        return response.content[:limit].decode(response.encoding or "utf-8", "replace")
    except Exception:
        return ""


def normalize_base_url(base_url: str) -> str:
    if not isinstance(base_url, str) or not base_url:
        raise ValueError("`base_url` must be a URL like https://app.useanvil.com")
    parts = urlsplit(base_url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(
            f"`base_url` must be a URL like https://app.useanvil.com, not {base_url!r}"
        )
    return base_url.rstrip("/")
