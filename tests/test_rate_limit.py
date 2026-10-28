from __future__ import annotations

import contextlib
import threading
import time
from unittest import mock

from python_anvil.rate_limit import RateLimiter, retry_delay_seconds


def response(status: int = 200, headers: dict | None = None) -> mock.Mock:
    resp = mock.Mock()
    resp.status_code = status
    resp.headers = headers or {}
    return resp


def describe_rate_limiter():
    def it_starts_with_the_given_limits():
        limiter = RateLimiter(5, 2000)
        assert (limiter.limit, limiter.interval_ms) == (5, 2000)

    def it_falls_back_to_one_per_second_when_the_starting_limits_are_invalid():
        for limit, interval in [(0, 1000), (1, 0), ("x", 1000), (None, None), (-1, -1)]:
            limiter = RateLimiter(limit, interval)
            assert (limiter.limit, limiter.interval_ms) == (1, 1000)

    def it_sets_the_limits_from_the_first_response_only():
        limiter = RateLimiter()

        limiter.run(
            lambda: response(
                headers={"X-RateLimit-Limit": "40", "X-RateLimit-Interval-Ms": "1000"}
            )
        )
        limiter.run(
            lambda: response(
                headers={"x-ratelimit-limit": "2", "x-ratelimit-interval-ms": "100"}
            )
        )

        assert limiter.has_set_from_response
        assert (limiter.limit, limiter.interval_ms) == (40, 1000)

    def it_keeps_the_starting_limits_when_the_headers_are_missing():
        limiter = RateLimiter(3, 500)

        limiter.run(lambda: response())

        assert not limiter.has_set_from_response
        assert (limiter.limit, limiter.interval_ms) == (3, 500)

    def it_takes_the_limits_from_the_first_response_that_has_them():
        limiter = RateLimiter(3, 500)

        limiter.run(lambda: response(status=502))
        limiter.run(
            lambda: response(
                headers={"x-ratelimit-limit": "40", "x-ratelimit-interval-ms": "1000"}
            )
        )
        limiter.run(
            lambda: response(
                headers={"x-ratelimit-limit": "2", "x-ratelimit-interval-ms": "100"}
            )
        )

        assert limiter.has_set_from_response
        assert (limiter.limit, limiter.interval_ms) == (40, 1000)

    def it_holds_other_requests_until_the_first_response():
        limiter = RateLimiter(10, 1000)
        order: list[str] = []
        first_sent = threading.Event()

        def first():
            def send():
                order.append("first sent")
                first_sent.set()
                time.sleep(0.2)
                order.append("first responded")
                return response(
                    headers={
                        "x-ratelimit-limit": "10",
                        "x-ratelimit-interval-ms": "1000",
                    }
                )

            limiter.run(send)

        def second():
            first_sent.wait()

            def send():
                order.append("second sent")
                return response()

            limiter.run(send)

        threads = [threading.Thread(target=first), threading.Thread(target=second)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert order == ["first sent", "first responded", "second sent"]

    def it_lets_waiting_requests_go_when_the_first_request_fails():
        limiter = RateLimiter(10, 1000)

        def fail():
            raise ConnectionError("nope")

        with contextlib.suppress(ConnectionError):
            limiter.run(fail)

        # Would hang if the setup gate were still closed
        limiter.run(lambda: response())
        assert limiter._gate_open

    def it_waits_when_the_limit_is_reached():
        limiter = RateLimiter(2, 200)
        limiter.update_from_headers(
            {"x-ratelimit-limit": "2", "x-ratelimit-interval-ms": "200"}
        )
        sent: list[float] = []

        def send():
            sent.append(time.monotonic())
            return response()

        for _ in range(4):
            limiter.run(send)

        assert sent[2] - sent[0] >= 0.2
        assert sent[3] - sent[1] >= 0.2
        # But the first two went straight away
        assert sent[1] - sent[0] < 0.1

    def it_counts_a_request_until_an_interval_after_its_response():
        # The API counts from when a request arrives, which is somewhere between
        # when it was sent and when its response came back
        limiter = RateLimiter(2, 200)
        limiter.update_from_headers(
            {"x-ratelimit-limit": "2", "x-ratelimit-interval-ms": "200"}
        )
        sent: list[float] = []
        answered: list[float] = []

        def slow_send():
            sent.append(time.monotonic())
            time.sleep(0.15)
            answered.append(time.monotonic())
            return response()

        for _ in range(3):
            limiter.run(slow_send)

        # The third waits for the first's response to leave the window, not its send
        assert sent[2] - answered[0] >= 0.2
        assert sent[2] - sent[0] >= 0.35

    def it_counts_a_request_that_failed():
        limiter = RateLimiter(1, 200)
        limiter.update_from_headers(
            {"x-ratelimit-limit": "1", "x-ratelimit-interval-ms": "200"}
        )

        def fail():
            raise ConnectionError("dropped")

        failed_at = time.monotonic()
        with contextlib.suppress(ConnectionError):
            limiter.run(fail)
        sent: list[float] = []

        def send():
            sent.append(time.monotonic())
            return response()

        limiter.run(send)
        assert sent[0] - failed_at >= 0.2

    def it_retries_a_429_after_retry_after_plus_the_buffer():
        limiter = RateLimiter(10, 1000)
        responses = iter([response(429, {"retry-after": "0.1"}), response(200)])
        times: list[float] = []

        def send():
            times.append(time.monotonic())
            return next(responses)

        result = limiter.run(send)

        assert result.status_code == 200
        assert times[1] - times[0] >= 0.15

    def it_closes_the_429_response():
        limiter = RateLimiter(10, 1000)
        rate_limited = response(429)
        responses = iter([rate_limited, response(200)])

        limiter.run(lambda: next(responses))

        rate_limited.close.assert_called_once()


def describe_retry_delay_seconds():
    def it_adds_a_50ms_buffer_to_retry_after():
        assert retry_delay_seconds("2") == 2.05

    def it_accepts_fractions_and_negatives():
        assert retry_delay_seconds("0.5") == 0.55
        assert retry_delay_seconds("-1") == 1.05

    def it_waits_a_second_without_a_usable_retry_after():
        assert retry_delay_seconds(None) == 1.05
        assert retry_delay_seconds("soon") == 1.05
        assert retry_delay_seconds("Wed, 21 Oct 2026 07:28:00 GMT") == 1.05
