# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison
import pytest
from typing import Dict
from unittest import mock

from python_anvil.http import HTTPClient


class HTTPResponse:
    status_code = 200
    content = ""
    headers: Dict = {}


def describe_http_client():
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
