"""Keeps requests within the API's rate limit, and retries those that weren't.

The API counts requests over a sliding window: at most `X-RateLimit-Limit`
requests in any `X-RateLimit-Interval-Ms`. The limiter counts the same way,
so it only holds a request back when the limit has been reached, and never
delays requests that are within it.

Every response carries those headers, so the client's first request goes out
alone, and the limits in its response become the limits for every request
after it. Requests made in the meantime wait for that first response.

A request that still gets a `429 Too Many Requests` is retried after the
`Retry-After` in the response, plus a small buffer.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from collections.abc import Callable, Mapping
from typing import Any

import requests

from python_anvil.constants import (
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_REQUEST_LIMIT_MS,
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

        # When the requests in the current window were sent, oldest first
        self._request_times: deque[float] = deque()
        # Whether the limits have been set from an API response
        self.has_set_from_response = False
        # Whether a request is out whose response will set the limits
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
        """Set the limits from a response's rate limit headers, the first time only."""
        with self._condition:
            if self.has_set_from_response:
                return
            self.has_set_from_response = True
            self._setting_in_progress = False
            self._condition.notify_all()

        if not self.set_limits(
            _header(headers, LIMIT_HEADER), _header(headers, INTERVAL_HEADER)
        ):
            logger.debug(
                "The response had no valid rate limit headers; keeping %s requests "
                "per %sms",
                self.limit,
                self.interval_ms,
            )

    def run(self, send: Callable[[], requests.Response]) -> requests.Response:
        """Call `send` when the rate limit allows, retrying it after any 429.

        `send` is called again for each retry, so it must be able to build its
        request again.
        """
        while True:
            self._wait_for_turn()
            try:
                response = send()
            except BaseException:
                # There won't be a response to set the limits from, so let
                # the requests waiting for one go ahead
                self._release_setup_gate()
                raise

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
            # Until the first response has set the limits, only the request
            # whose response will set them may go
            while self._setting_in_progress and not self.has_set_from_response:
                self._condition.wait()
            if not self.has_set_from_response:
                self._setting_in_progress = True

            # Wait until another request would keep us within `limit` requests
            # in any `interval_ms`
            while True:
                # Not time.time(), so that changes to the system clock can't hold requests up
                now = time.monotonic()
                # Requests sent before this no longer count. The buffer allows for
                # requests that were sent further apart than they arrive.
                window_start = now - (self.interval_ms + RETRY_BUFFER_MS) / 1000
                while self._request_times and self._request_times[0] <= window_start:
                    self._request_times.popleft()

                if len(self._request_times) < self.limit:
                    self._request_times.append(now)
                    return

                # Wait for the oldest request to leave the window, then check again
                self._condition.wait(timeout=self._request_times[0] - window_start)

    def _release_setup_gate(self) -> None:
        with self._condition:
            if not self.has_set_from_response:
                self._setting_in_progress = False
                self._condition.notify_all()


def retry_delay_seconds(retry_after: Any) -> float:
    """How long to wait before retrying a 429: its Retry-After seconds plus the buffer."""
    try:
        seconds = abs(float(retry_after))
    except (TypeError, ValueError):
        seconds = 0.0
    return seconds + RETRY_BUFFER_MS / 1000


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
