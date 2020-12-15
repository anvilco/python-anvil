# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison
import pytest
from unittest import mock

from python_anvil.http import HTTPClient


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
        pass
