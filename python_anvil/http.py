import requests
from base64 import b64encode
from logging import getLogger
from ratelimit import limits, sleep_and_retry
from ratelimit.exception import RateLimitException
from requests.auth import HTTPBasicAuth

from python_anvil.exceptions import AnvilRequestException


logger = getLogger(__name__)

REQUESTS_LIMIT = {
    "dev": {
        "calls": 2,
        "seconds": 1,
    },
    "prod": {
        "calls": 40,
        "seconds": 1,
    },
}

RATELIMIT_ENV = "dev"


def _handle_request_error(e: Exception):
    raise e


class HTTPClient:
    def __init__(self, api_key=None, environment="dev"):
        self._session = requests.Session()
        self.api_key = api_key
        global RATELIMIT_ENV  # pylint: disable=global-statement
        RATELIMIT_ENV = environment

    def get_auth(self, encode=False) -> str:
        # TODO: Handle OAuth + API_KEY
        if not self.api_key:
            raise AttributeError("You must have an API key")

        # By default, the `requests` package will base64encode things with
        # the `HTTPBasicAuth` method, so no need to handle that here, but the
        # option is here if you _really_ want it.
        if encode:
            return b64encode(f"{self.api_key}:".encode()).decode()

        return self.api_key

    @sleep_and_retry
    @limits(
        calls=REQUESTS_LIMIT[RATELIMIT_ENV]["calls"],
        period=REQUESTS_LIMIT[RATELIMIT_ENV]["seconds"],
    )
    def do_request(
        self,
        method,
        url,
        headers=None,
        data=None,
        auth=None,
        params=None,
        retry=True,
        **kwargs,
    ) -> requests.Response:
        for _ in range(5):
            # Retry a max of 5 times in case of hitting any rate limit errors
            res = self._session.request(
                method,
                url,
                headers=headers,
                data=data,
                auth=auth,
                params=params,
                **kwargs,
            )

            if res.status_code == 429:
                time_to_wait = int(res.headers.get("Retry-After", 1))
                if retry:
                    logger.warning(
                        "Rate-limited: request not accepted. Retrying in "
                        "%i second%s.",
                        time_to_wait,
                        's' if time_to_wait > 1 else '',
                    )

                    # This exception will raise up to the `sleep_and_retry` decorator
                    # which will handle waiting for `time_to_wait` seconds.
                    raise RateLimitException("Retrying", period_remaining=time_to_wait)

                raise AnvilRequestException(
                    f"Rate limit exceeded. Retry after {time_to_wait} seconds."
                )

            break

        return res

    def request(
        self,
        method,
        url,
        headers=None,
        data=None,
        auth=None,
        params=None,
        retry=True,
        **kwargs,
    ):
        """Make an HTTP request.

        :param method: HTTP method to use
        :param url: URL to make the request on.
        :param headers:
        :param data:
        :param auth:
        :param params:
        :param retry: Whether or not to retry on any rate-limited requests
        :param kwargs:
        :return:
        """
        parse_json = kwargs.pop("parse_json", False)
        if self.api_key and not auth:
            auth = HTTPBasicAuth(self.get_auth(), "")

        try:
            res = self.do_request(
                method,
                url,
                headers=headers,
                data=data,
                auth=auth,
                params=params,
                retry=retry,
                **kwargs,
            )

            if parse_json and res.headers.get("Content-Type") == "application/json":
                content = res.json()
            else:
                # This actually reads the content and can potentially cause issues
                # depending on the content.
                # The structure of this method is very similar to Stripe's requests
                # HTTP client: https://github.com/stripe/stripe-python/blob/afa872c538bee0a1e14c8e131df52dd3c24ff05a/stripe/http_client.py#L304-L308
                content = res.content
            status_code = res.status_code
        except Exception as e:  # pylint: disable=broad-except
            _handle_request_error(e)

        return content, status_code, res.headers
