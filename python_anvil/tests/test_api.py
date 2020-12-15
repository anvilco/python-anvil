# pylint: disable=unused-variable
import json
import pytest
from unittest import mock

from python_anvil.api import Anvil, CreateEtchPacket

from . import payloads


DEV_KEY = "MY-SECRET-KEY"


def describe_api():
    @pytest.fixture
    def anvil():
        return Anvil(api_key=DEV_KEY)

    def describe_init():
        @mock.patch('python_anvil.api.HTTPClient')
        def test_init_key(mock_client):
            Anvil(api_key="what")
            mock_client.assert_called_once_with(api_key="what")

    def describe_query():
        def test_query():
            pass

    def describe_fill_pdf():
        @mock.patch('python_anvil.api.RestRequest.post')
        def test_dict_payload(m_request_post, anvil):
            payload = {"data": {"this_data": "yes"}}
            anvil.fill_pdf("some_template", payload=payload)
            m_request_post.assert_called_once_with("fill/some_template.pdf", payload)

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_json_payload(m_request_post, anvil):
            payload = """{ "data": {"jsonData": "is here"} }"""
            anvil.fill_pdf("some_template", payload=payload)
            m_request_post.assert_called_once_with(
                "fill/some_template.pdf", {'data': {'jsonData': 'is here'}}
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_empty_payload(m_request_post, anvil):
            with pytest.raises(ValueError):
                anvil.fill_pdf("some_template", payload={})
                assert m_request_post.call_count == 0

    def describe_generate_pdf():
        @mock.patch('python_anvil.api.RestRequest.post')
        def test_dict_payload(m_request_post, anvil):
            anvil.generate_pdf({"data": [{"d1": "data"}]})
            m_request_post.assert_called_once_with(
                "generate-pdf", data={'data': [{'d1': 'data'}]}
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_json_payload(m_request_post, anvil):
            payload = """{ "data": [{ "d1": "data" }] }"""
            anvil.generate_pdf(payload)
            m_request_post.assert_called_once_with(
                "generate-pdf", data={'data': [{'d1': 'data'}]}
            )

    def describe_current_user_query():
        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_get_current_user(m_request_post, anvil):
            anvil.get_current_user()
            assert m_request_post.call_count == 1

    def describe_get_welds():
        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_get_weld(m_request_post, anvil):
            anvil.get_welds()
            assert m_request_post.call_count == 1

    def describe_get_queries():
        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_get_queries(m_request_post, anvil):
            anvil.get_queries()
            assert m_request_post.call_count == 1

    def describe_generate_etch_signing_url():
        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_get_url(m_request_post, anvil):
            anvil.generate_etch_signing_url(
                signer_eid='someId', client_user_id='anotherId'
            )
            assert m_request_post.call_count == 1

    def describe_download_documents():
        @mock.patch('python_anvil.api.PlainRequest.get')
        def test_get_docs(m_request_post, anvil):
            anvil.download_documents('someEid')
            assert m_request_post.call_count == 1

    def describe_get_cast():
        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_get_cast(m_request_post, anvil):
            anvil.get_cast('castEid')
            assert m_request_post.call_count == 1

    def describe_get_casts():
        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_get_casts(m_request_post, anvil):
            anvil.get_casts()
            assert m_request_post.call_count == 1

    def describe_create_etch_packet():
        expected_data = {
            'name': 'Packet name',
            'signatureEmailSubject': 'The subject',
            'signers': [],
            'files': [],
            'isDraft': False,
            'isTest': True,
            'data': {'payloads': {}},
            'signaturePageOptions': {},
        }

        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_create_etch_packet_empty_payload(m_request_post, anvil):
            with pytest.raises(TypeError):
                anvil.create_etch_packet(payload={})
                assert m_request_post.call_count == 0

        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_create_etch_packet_invalid_payload(m_request_post, anvil):
            with pytest.raises(TypeError):
                anvil.create_etch_packet({})
                assert m_request_post.call_count == 0

        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_create_etch_packet_valid_payload_type(m_request_post, anvil):
            payload = CreateEtchPacket(
                name="Packet name",
                signature_email_subject="The subject",
            )
            anvil.create_etch_packet(payload=payload)
            assert m_request_post.call_count == 1
            assert expected_data in m_request_post.call_args[0]

        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_create_etch_packet_valid_dict_type(m_request_post, anvil):
            anvil.create_etch_packet(
                dict(name="Packet name", signature_email_subject="The subject")
            )
            assert m_request_post.call_count == 1
            assert expected_data in m_request_post.call_args[0]

        @mock.patch(
            'python_anvil.api_resources.mutations.create_etch_packet.create_unique_id'
        )
        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_create_etch_packet_dict_with_signer(
            m_request_post, m_create_unique, anvil
        ):
            m_create_unique.return_value = "signer-mock-generated"
            anvil.create_etch_packet(payload=payloads.ETCH_TEST_PAYLOAD)
            assert m_request_post.call_count == 1
            assert payloads.EXPECTED_ETCH_TEST_PAYLOAD in m_request_post.call_args[0]

        @mock.patch(
            'python_anvil.api_resources.mutations.create_etch_packet.create_unique_id'
        )
        @mock.patch('python_anvil.api.GraphqlRequest.post')
        def test_create_etch_packet_json(m_request_post, m_create_unique, anvil):
            m_create_unique.return_value = "signer-mock-generated"
            anvil.create_etch_packet(
                json=json.dumps(payloads.EXPECTED_ETCH_TEST_PAYLOAD_JSON)
            )
            assert m_request_post.call_count == 1
            assert (
                payloads.EXPECTED_ETCH_TEST_PAYLOAD_JSON in m_request_post.call_args[0]
            )
