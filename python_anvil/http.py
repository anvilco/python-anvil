import requests
from base64 import b64encode
from logging import getLogger
from ratelimit import limits
from requests.auth import HTTPBasicAuth


logger = getLogger(__name__)

REQUESTS_LIMIT = 200
REQUESTS_LIMIT_MS = 5000


class HTTPClient:
    def __init__(self, api_key=None):
        self._session = requests.Session()
        self.api_key = api_key

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

    @limits(calls=REQUESTS_LIMIT, period=REQUESTS_LIMIT_MS)
    def request(
        self, method, url, headers=None, data=None, auth=None, params=None, **kwargs
    ):
        """Make an HTTP request.

        :param method: HTTP method to use
        :param url: URL to make the request on.
        :param headers:
        :param data:
        :param auth:
        :param kwargs:
        :param params:
        :return:
        """
        parse_json = kwargs.pop("parse_json", False)
        if self.api_key and not auth:
            auth = HTTPBasicAuth(self.get_auth(), "")

        try:
            res = self._session.request(
                method,
                url,
                headers=headers,
                data=data,
                auth=auth,
                params=params,
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
        except Exception as e:
            self._handle_request_error(e)

        return content, status_code, res.headers

    def _handle_request_error(self, e: Exception):
        raise e
