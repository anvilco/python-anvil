import os
import requests
from base64 import b64encode
from gql import Client
from gql.dsl import DSLSchema
from gql.transport.requests import RequestsHTTPTransport
from logging import getLogger
from ratelimit import limits, sleep_and_retry
from ratelimit.exception import RateLimitException
from requests.auth import HTTPBasicAuth
from typing import Optional

from python_anvil.exceptions import AnvilRequestException

from .constants import GRAPHQL_ENDPOINT, RATELIMIT_ENV, REQUESTS_LIMIT, RETRIES_LIMIT


logger = getLogger(__name__)


def _handle_request_error(e: Exception):
    raise e


def get_local_schema(raise_on_error=False) -> Optional[str]:
    """
    Retrieve local GraphQL schema.

    :param raise_on_error:
    :return:
    """
    try:
        file_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(file_dir, "..", "schema", "anvil_schema.graphql")
        with open(file_path, encoding="utf-8") as file:
            schema = file.read()
    except Exception:  # pylint: disable
        logger.warning(
            "Unable to find local schema. Will not use schema for local "
            "validation. Use `fetch_schema_from_transport=True` to allow "
            "fetching the remote schema."
        )
        if raise_on_error:
            raise
        schema = None

    return schema


def get_gql_ds(client: Client) -> DSLSchema:
    if not client.schema:
        raise ValueError("Client does not have a valid GraphQL schema.")
    return DSLSchema(client.schema)


class GQLClient:
    """GraphQL client factory class."""

    @staticmethod
    def get_client(
        api_key: str,
        environment: str = "dev",  # pylint: disable=unused-argument
        endpoint_url: Optional[str] = None,
        fetch_schema_from_transport: bool = False,
        force_local_schema: bool = False,
    ) -> Client:
        auth = HTTPBasicAuth(username=api_key, password="")
        endpoint_url = endpoint_url or GRAPHQL_ENDPOINT
        transport = RequestsHTTPTransport(
            retries=RETRIES_LIMIT,
            auth=auth,
            url=endpoint_url,
            verify=True,
        )

        schema = None
        if force_local_schema or not fetch_schema_from_transport:
            schema = get_local_schema(raise_on_error=False)

        return Client(
            schema=schema,
            transport=transport,
            fetch_schema_from_transport=fetch_schema_from_transport,
        )


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
        files=None,
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
                files=files,
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
        files=None,
        **kwargs,
    ):
        """Make an HTTP request.

        :param method: HTTP method to use
        :param url: URL to make the request on.
        :param headers:
        :param data:
        :param auth:
        :param params:
        :param files:
        :param retry: Whether to retry on any rate-limited requests
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
                files=files,
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
