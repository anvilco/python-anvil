"""Keeps requests within the API's rate limit, and retries those that weren't.

The API counts requests over a sliding window: at most `X-RateLimit-Limit`
requests in any `X-RateLimit-Interval-Ms`. The limiter counts the same way,
so it only holds a request back when the limit has been reached, and never
delays requests that are within it.

The API counts a request from the moment it arrives, which the client
can't see. It is somewhere between when the request was sent and when the
response came back, so a request counts here from when it is sent until an
interval after its response arrives. That way the API never counts more
requests in its window than the client counted in its own, whatever the
latency, and a new connection's handshake can't put a request on the wrong
side of the window.

Every response carries those headers, so the client's first request goes out
alone, and the limits in its response become the limits for every request
after it. Requests made in the meantime wait for that first response.

A request that still gets a `429 Too Many Requests` is retried after the
`Retry-After` in the response, plus a small buffer.

The API's limit is per account, so every client in the process with the
same base URL and credentials shares one limiter (`shared_limiter`), and
with it the limits the first response taught. Separate processes can't
share one; each learns the limits for itself.
"""

from __future__ import annotations

import hashlib
import logging
import math
import threading
import time
import weakref
from collections import deque
from collections.abc import Callable, Mapping
from typing import Any

import requests

from python_anvil.constants import (
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_REQUEST_LIMIT_MS,
    DEFAULT_RETRY_AFTER_MS,
    MAX_RETRY_AFTER_MS,
    RETRY_BUFFER_MS,
)


logger = logging.getLogger(__name__)

LIMIT_HEADER = "x-ratelimit-limit"
INTERVAL_HEADER = "x-ratelimit-interval-ms"
RETRY_AFTER_HEADER = "retry-after"


class RateLimiter:
    """A thread-safe sliding window rate limiter that learns its limits from the API."""

    def __init__(
        self,
        limit: Any = DEFAULT_REQUEST_LIMIT,
        interval_ms: Any = DEFAULT_REQUEST_LIMIT_MS,
    ):
        self._condition = threading.Condition()
        # Fall back to 1 request per second if the starting limits are invalid
        self.limit: int = DEFAULT_REQUEST_LIMIT
        self.interval_ms: int = DEFAULT_REQUEST_LIMIT_MS
        self.set_limits(limit, interval_ms)

        # How many requests are out now, and when the responses of recent
        # ones arrived, oldest first. A request counts from when it is sent
        # until an interval after its response.
        self._in_flight = 0
        self._finished_at: deque[float] = deque()
        # Whether the limits have been set from an API response. Until they
        # have, every response is checked for the headers.
        self.has_set_from_response = False
        # Whether the first response has arrived, whatever it carried. Until
        # it has, only the request whose response it will be may go.
        self._gate_open = False
        self._setting_in_progress = False

    def set_limits(self, limit: Any, interval_ms: Any) -> bool:
        """Set the limits, if both are positive numbers. Returns whether they were."""
        limit, interval_ms = _positive_int(limit), _positive_int(interval_ms)
        if limit is None or interval_ms is None:
            return False

        with self._condition:
            # Requests already sent still count against the new limits
            self.limit = limit
            self.interval_ms = interval_ms
            self._condition.notify_all()
        return True

    def update_from_headers(self, headers: Mapping[str, Any]) -> None:
        """Set the limits from a response's rate limit headers.

        The first response, whatever it carries, lets the requests waiting on
        it go. The limits are taken from the first response that has them: a
        response from a proxy, or an error served before the API's rate limit
        middleware, doesn't fix the client at its starting limits for good.
        """
        with self._condition:
            self._gate_open = True
            self._setting_in_progress = False
            self._condition.notify_all()

            if self.has_set_from_response:
                return
            if self.set_limits(
                _header(headers, LIMIT_HEADER), _header(headers, INTERVAL_HEADER)
            ):
                self.has_set_from_response = True
            else:
                logger.debug(
                    "The response had no valid rate limit headers; keeping %s "
                    "requests per %sms until one does",
                    self.limit,
                    self.interval_ms,
                )

    def run(self, send: Callable[[], requests.Response]) -> requests.Response:
        """Call `send` when the rate limit allows, retrying it after any 429.

        `send` is called again for each retry, so it must be able to build its
        request again.
        """
        while True:
            # `_wait_for_turn` takes a slot, which `_finish` must give back
            # whatever happens, even an interrupt that lands between the two
            acquired = False
            try:
                self._wait_for_turn()
                acquired = True
                response = send()
            except BaseException:
                # The request may still have reached the API, so it counts.
                # There won't be a response to set the limits from, so let
                # the requests waiting for one go ahead.
                if acquired:
                    self._finish()
                self._release_setup_gate()
                raise
            self._finish()

            if not self.has_set_from_response:
                self.update_from_headers(response.headers)

            if response.status_code != 429:
                return response

            delay = retry_delay_seconds(_header(response.headers, RETRY_AFTER_HEADER))
            # Nothing will read the body, so free the connection for the retry
            response.close()
            logger.warning(
                "Rate limited: the request was not accepted. Retrying in %.2f seconds.",
                delay,
            )
            time.sleep(delay)

    def _wait_for_turn(self) -> None:
        with self._condition:
            # Until the first response has arrived, only the request whose
            # response it will be may go
            while self._setting_in_progress and not self._gate_open:
                self._condition.wait()
            if not self._gate_open:
                self._setting_in_progress = True

            # Wait until another request would keep us within `limit` requests
            # in any `interval_ms`: the ones out now, plus those whose response
            # arrived within the last interval
            while True:
                # Not time.time(), so that changes to the system clock can't hold requests up
                now = time.monotonic()
                # Responses that arrived before this no longer count. The buffer
                # allows for the API's clock and the client's ticking apart.
                window_start = now - (self.interval_ms + RETRY_BUFFER_MS) / 1000
                while self._finished_at and self._finished_at[0] <= window_start:
                    self._finished_at.popleft()

                if self._in_flight + len(self._finished_at) < self.limit:
                    self._in_flight += 1
                    return

                if self._finished_at:
                    # Wait for the oldest response to leave the window, then check again
                    self._condition.wait(timeout=self._finished_at[0] - window_start)
                else:
                    # Every slot is a request still out; a response will wake us
                    self._condition.wait()

    def _finish(self) -> None:
        """A request's response arrived, or it failed: it counts for another interval."""
        with self._condition:
            self._in_flight -= 1
            self._finished_at.append(time.monotonic())
            self._condition.notify_all()

    def _release_setup_gate(self) -> None:
        with self._condition:
            if not self._gate_open:
                self._setting_in_progress = False
                self._condition.notify_all()


# Keyed on a hash of the credentials, not the credentials, and holding each
# limiter only as long as a client does: a service that makes a client per
# OAuth token must not keep every token it has ever seen.
_shared: weakref.WeakValueDictionary[tuple[str, str], RateLimiter] = (
    weakref.WeakValueDictionary()
)
_shared_lock = threading.Lock()


def shared_limiter(
    base_url: str,
    auth_header: str,
    limit: Any = DEFAULT_REQUEST_LIMIT,
    interval_ms: Any = DEFAULT_REQUEST_LIMIT_MS,
) -> RateLimiter:
    """The limiter every client with this base URL and credentials shares.

    The starting limits only apply when this makes the limiter, i.e. for the
    first client; after that the limits come from the API anyway. A limiter
    lives as long as a client holds it; the next client made after the last
    one is gone learns the limits again from its first response.
    """
    key = (base_url, hashlib.sha256(auth_header.encode()).hexdigest())
    with _shared_lock:
        limiter = _shared.get(key)
        if limiter is None:
            limiter = _shared[key] = RateLimiter(limit, interval_ms)
        return limiter


def retry_delay_seconds(retry_after: Any) -> float:
    """How long to wait before retrying a 429: its Retry-After seconds plus the buffer.

    Without a usable Retry-After (the header is optional, and may be an HTTP
    date), a second: retrying every 50ms would hammer a server that is
    already turning requests away.
    """
    try:
        seconds = abs(float(retry_after))
    except (TypeError, ValueError):
        seconds = DEFAULT_RETRY_AFTER_MS / 1000
    if not math.isfinite(seconds):
        seconds = DEFAULT_RETRY_AFTER_MS / 1000
    return min(seconds, MAX_RETRY_AFTER_MS / 1000) + RETRY_BUFFER_MS / 1000


def _header(headers: Mapping[str, Any], name: str) -> Any:
    # requests gives case-insensitive headers, but a plain dict might not be
    value = headers.get(name)
    if value is None:
        for key, val in headers.items():
            if key.lower() == name:
                return val
    return value


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
