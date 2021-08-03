# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison
import pytest
from typing import Dict
from unittest import mock

from python_anvil.exceptions import AnvilRequestException
from python_anvil.http import HTTPClient


class HTTPResponse:
    status_code = 200
    content = ""
    headers: Dict = {}


def describe_http_client():
    @pytest.fixture
    def mock_response():
        class MockResponse:
            status_code = 429
            headers = {"Retry-After": 1}

        return MockResponse

    def test_client():
        client = HTTPClient()
        assert isinstance(client, HTTPClient)

    def describe_get_auth():
        def test_no_key():
            """Test that no key will raise an exception."""
            client = HTTPClient()
            with pytest.raises(AttributeError):
                client.get_auth()

        def test_key():
            key = "my_secret_ket!!!11!!"
            client = HTTPClient(api_key=key)
            assert client.get_auth() == key

        @mock.patch('python_anvil.http.b64encode')
        def test_encoded_key(mock_b64):
            key = "my_secret_ket!!!11!!"
            client = HTTPClient(api_key=key)
            client.get_auth(encode=True)
            mock_b64.assert_called_once()

    def describe_request():
        @mock.patch("python_anvil.http.HTTPBasicAuth")
        @mock.patch("python_anvil.http.HTTPClient.do_request")
        def test_default_args(do_request, basic_auth):
            basic_auth.return_value = "my_auth"
            response = HTTPResponse()
            do_request.return_value = response

            client = HTTPClient(api_key="my_key")
            res = client.request("GET", "http://localhost")

            assert res == (response.content, response.status_code, response.headers)
            do_request.assert_called_once_with(
                "GET",
                "http://localhost",
                headers=None,
                data=None,
                auth="my_auth",
                params=None,
                retry=True,
            )

    def describe_do_request():
        @mock.patch("python_anvil.http.requests.Session")
        def test_default_args(session):
            mock_session = mock.MagicMock()
            session.return_value = mock_session
            client = HTTPClient(api_key="my_key")
            client.do_request("GET", "http://localhost")

            # Should only be called once, never retried.
            mock_session.request.assert_called_once_with(
                "GET",
                "http://localhost",
                headers=None,
                data=None,
                auth=None,
                params=None,
            )

        @mock.patch("python_anvil.http.RateLimitException")
        @mock.patch("python_anvil.http.requests.Session")
        def test_default_args_with_retry(session, ratelimit_exc, mock_response):
            class MockException(Exception):
                pass

            mock_session = mock.MagicMock()
            mock_session.request.return_value = mock_response()
            session.return_value = mock_session
            ratelimit_exc.return_value = MockException()

            client = HTTPClient(api_key="my_key")
            with pytest.raises(MockException):
                client.do_request("GET", "http://localhost", retry=True)

            assert ratelimit_exc.call_count == 1

            # Should only be called once, would retry but RateLimitException
            # is mocked here.
            mock_session.request.assert_called_once_with(
                "GET",
                "http://localhost",
                headers=None,
                data=None,
                auth=None,
                params=None,
            )

        @mock.patch("python_anvil.http.RateLimitException")
        @mock.patch("python_anvil.http.requests.Session")
        def test_default_args_without_retry(session, ratelimit_exc, mock_response):
            class MockException(Exception):
                pass

            mock_session = mock.MagicMock()
            mock_session.request.return_value = mock_response()
            session.return_value = mock_session
            ratelimit_exc.return_value = MockException()

            client = HTTPClient(api_key="my_key")
            with pytest.raises(AnvilRequestException):
                client.do_request("GET", "http://localhost", retry=False)

            assert ratelimit_exc.call_count == 0

            # Should only be called once, never retried.
            mock_session.request.assert_called_once_with(
                "GET",
                "http://localhost",
                headers=None,
                data=None,
                auth=None,
                params=None,
            )
