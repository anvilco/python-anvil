# pylint: disable=unused-variable,unused-argument,too-many-statements
import json
import pytest
from pydantic.v1 import ValidationError
from typing import Any, MutableMapping
from unittest import mock

from python_anvil.api import Anvil, CreateEtchPacket
from python_anvil.api_resources.payload import (
    CreateEtchPacketPayload,
    ForgeSubmitPayload,
)

from ..api_resources.payload import FillPDFPayload
from . import payloads


DEV_KEY = "MY-SECRET-KEY"

TEST_SCHEMA = """
type GenerateEmbedURLResponse {
  eid: String!
  url: String!
}
"""


def describe_api():
    @pytest.fixture
    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=TEST_SCHEMA)
    def anvil(m_open):
        return Anvil(api_key=DEV_KEY)

    def describe_init():
        @mock.patch('python_anvil.api.GQLClient')
        @mock.patch('python_anvil.api.HTTPClient')
        def test_init_key_default(mock_client, mock_gql):
            Anvil(api_key="what")
            mock_client.assert_called_once_with(api_key="what", environment="dev")
            mock_gql.get_client.assert_called_once_with(
                api_key="what", environment="dev", endpoint_url=None
            )

        @mock.patch('python_anvil.api.GQLClient')
        @mock.patch('python_anvil.api.HTTPClient')
        def test_init_with_endpoint(mock_client, mock_gql):
            Anvil(api_key="what", endpoint_url="http://somewhere.example")
            mock_client.assert_called_once_with(api_key="what", environment="dev")
            mock_gql.get_client.assert_called_once_with(
                api_key="what",
                environment="dev",
                endpoint_url="http://somewhere.example",
            )

        @mock.patch('python_anvil.api.GQLClient')
        @mock.patch('python_anvil.api.HTTPClient')
        def test_init_key_prod(mock_client, mock_gql):
            Anvil(api_key="what", environment="prod")
            mock_client.assert_called_once_with(api_key="what", environment="prod")
            mock_gql.get_client.assert_called_once_with(
                api_key="what", environment="prod", endpoint_url=None
            )

        @mock.patch('python_anvil.api.GQLClient')
        @mock.patch('python_anvil.api.HTTPClient')
        def test_init_no_key(mock_client, mock_gql):
            with pytest.raises(ValueError):
                Anvil(environment="prod")

            assert mock_client.call_count == 0
            assert mock_gql.get_client.call_count == 0

    def describe_query():
        def test_query():
            # TODO: ...
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
                "fill/some_template.pdf",
                {'data': {'jsonData': 'is here'}},
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_payload_obj(m_request_post, anvil):
            payload = FillPDFPayload(data={"jsonData": "this was a payload instance"})
            anvil.fill_pdf("some_template", payload=payload)
            m_request_post.assert_called_once_with(
                "fill/some_template.pdf",
                {'data': {'jsonData': 'this was a payload instance'}},
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_empty_payload(m_request_post, anvil):
            with pytest.raises(ValueError):
                anvil.fill_pdf("some_template", payload={})
            assert m_request_post.call_count == 0

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_with_kwargs(m_request_post, anvil):
            payload = """{ "data": {"jsonData": "is here"} }"""
            anvil.fill_pdf("some_template", payload=payload, include_headers=True)
            m_request_post.assert_called_once_with(
                "fill/some_template.pdf",
                {"data": {"jsonData": "is here"}},
                include_headers=True,
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_with_version(m_request_post, anvil):
            payload = {"data": {"one": "One string"}}
            anvil.fill_pdf(
                "some_template",
                payload=payload,
                include_headers=True,
                version_number=Anvil.VERSION_LATEST,
            )
            m_request_post.assert_called_once_with(
                "fill/some_template.pdf",
                {"data": {"one": "One string"}},
                include_headers=True,
                params={"versionNumber": Anvil.VERSION_LATEST},
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_with_params(m_request_post, anvil):
            payload = {"data": {"one": "One string"}}
            params = {"arbitrary": "Param"}
            anvil.fill_pdf(
                "some_template", payload=payload, include_headers=True, params=params
            )
            m_request_post.assert_called_once_with(
                "fill/some_template.pdf",
                {"data": {"one": "One string"}},
                include_headers=True,
                params=params,
            )

    def describe_generate_pdf():
        @mock.patch('python_anvil.api.RestRequest.post')
        def test_dict_payload(m_request_post, anvil):
            anvil.generate_pdf({"data": [{"d1": "data"}]})
            m_request_post.assert_called_once_with(
                # Defaults to 'markdown'
                "generate-pdf",
                data={'data': [{'d1': 'data'}], 'type': 'markdown'},
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_json_payload(m_request_post, anvil):
            payload = """{ "data": [{ "d1": "data" }] }"""
            anvil.generate_pdf(payload)
            m_request_post.assert_called_once_with(
                "generate-pdf", data={"data": [{"d1": "data"}], "type": "markdown"}
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_payload_html_type(m_request_post, anvil):
            anvil.generate_pdf({"data": {"html": "<h1>Hello</h1>"}, "type": "html"})
            m_request_post.assert_called_once_with(
                "generate-pdf",
                data={"data": {"html": "<h1>Hello</h1>"}, "type": "html"},
            )

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_invalid_payload_html_payload(m_request_post, anvil):
            with pytest.raises(ValueError):
                anvil.generate_pdf({"data": {"no_html_here": "Nope"}, "type": "html"})
            assert m_request_post.call_count == 0

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_payload_invalid_type(m_request_post, anvil):
            with pytest.raises(ValueError):
                anvil.generate_pdf(
                    {"data": [{"d1": "data"}], "type": "something_invalid"}
                )
            assert m_request_post.call_count == 0

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_invalid_data_for_html(m_request_post, anvil):
            with pytest.raises(ValueError):
                anvil.generate_pdf(
                    {
                        # This should be a plain dict, not a list
                        "data": [{"d1": "data"}],
                        "type": "html",
                    }
                )
            assert m_request_post.call_count == 0

        @mock.patch('python_anvil.api.RestRequest.post')
        def test_invalid_data_for_markdown(m_request_post, anvil):
            with pytest.raises(ValueError):
                anvil.generate_pdf(
                    {
                        # This should be a plain dict, not a list
                        "data": {"d1": "data"},
                        "type": "markdown",
                    }
                )
            assert m_request_post.call_count == 0

    def describe_current_user_query():
        @mock.patch('gql.Client.execute')
        def test_get_current_user(m_request_post, anvil):
            anvil.get_current_user()
            assert m_request_post.call_count == 1

    def describe_get_welds():
        @mock.patch('gql.Client.execute')
        def test_get_weld(m_request_post, anvil):
            anvil.get_welds()
            assert m_request_post.call_count == 1

    def describe_generate_etch_signing_url():
        @mock.patch('gql.Client.execute')
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
        @mock.patch('gql.Client.execute')
        def test_get_cast(m_request_post, anvil):
            anvil.get_cast('castEid')
            assert m_request_post.call_count == 1

    def describe_get_casts():
        @mock.patch('gql.Client.execute')
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

        @mock.patch('gql.Client.execute')
        def test_create_etch_packet_empty_payload(m_request_post, anvil):
            with pytest.raises(TypeError):
                anvil.create_etch_packet(payload={})
                assert m_request_post.call_count == 0

        @mock.patch('gql.Client.execute')
        def test_create_etch_packet_invalid_payload(m_request_post, anvil):
            with pytest.raises(TypeError):
                anvil.create_etch_packet({})
                assert m_request_post.call_count == 0

        @mock.patch('gql.Client.execute')
        def test_create_etch_packet_valid_payload_type(m_request_post, anvil):
            payload = CreateEtchPacket(
                name="Packet name",
                signature_email_subject="The subject",
            )
            anvil.create_etch_packet(payload=payload)
            assert m_request_post.call_count == 1

            variables = m_request_post.call_args[1]["variable_values"]
            assert expected_data == variables

        @mock.patch('gql.Client.execute')
        def test_create_etch_packet_passes_options(m_request_post, anvil):
            payload = CreateEtchPacket(
                is_test=False,
                is_draft=True,
                name="Packet name",
                signature_email_subject="The subject",
            )
            new_expected = dict(**expected_data)
            new_expected["isTest"] = False
            new_expected["isDraft"] = True
            anvil.create_etch_packet(payload)
            assert m_request_post.call_count == 1

            variables = m_request_post.call_args[1]["variable_values"]
            assert new_expected == variables

        @mock.patch('gql.Client.execute')
        def test_create_etch_packet_valid_dict_type(m_request_post, anvil):
            anvil.create_etch_packet(
                dict(name="Packet name", signature_email_subject="The subject")
            )
            assert m_request_post.call_count == 1

            variables = m_request_post.call_args[1]["variable_values"]
            assert expected_data == variables

        @mock.patch(
            'python_anvil.api_resources.mutations.create_etch_packet.create_unique_id'
        )
        @mock.patch('gql.Client.execute')
        def test_create_etch_packet_dict_with_signer(
            m_request_post, m_create_unique, anvil
        ):
            m_create_unique.return_value = "signer-mock-generated"
            anvil.create_etch_packet(payload=payloads.ETCH_TEST_PAYLOAD)
            assert m_request_post.call_count == 1

            variables = m_request_post.call_args[1]["variable_values"]
            assert payloads.EXPECTED_ETCH_TEST_PAYLOAD == variables

        @mock.patch(
            'python_anvil.api_resources.mutations.create_etch_packet.create_unique_id'
        )
        @mock.patch('gql.Client.execute')
        def test_create_etch_packet_json(m_request_post, m_create_unique, anvil):
            m_create_unique.return_value = "signer-mock-generated"
            # We are currently removing `None`s from the payload, so do that here too.
            payload = {
                k: v
                for k, v in payloads.EXPECTED_ETCH_TEST_PAYLOAD_JSON.items()
                if v is not None
            }
            anvil.create_etch_packet(json=json.dumps(payload))
            assert m_request_post.call_count == 1

            variables = m_request_post.call_args[1]["variable_values"]
            assert payload == variables

        @mock.patch(
            'python_anvil.api_resources.mutations.create_etch_packet.create_unique_id'
        )
        @mock.patch('gql.Client.execute')
        def test_adding_unsupported_fields(m_request_post, m_create_unique, anvil):
            m_create_unique.return_value = "signer-mock-generated"
            # We are currently removing `None`s from the payload, so do that here too.
            payload = {
                k: v
                for k, v in payloads.EXPECTED_ETCH_TEST_PAYLOAD_JSON.items()
                if v is not None
            }
            cep = CreateEtchPacketPayload.parse_obj(payload)
            cep.newFeature = True  # type: ignore[attr-defined]
            anvil.create_etch_packet(payload=cep)
            assert m_request_post.call_count == 1

            variables = m_request_post.call_args[1]["variable_values"]
            assert cep.dict(by_alias=True, exclude_none=True) == variables
            assert "newFeature" in variables

    def describe_forge_submit():
        expected_data = {
            "forgeEid": "forge1234",
            "payload": {"field1": "Some data"},
            "isTest": True,
        }

        @mock.patch('gql.Client.execute')
        def test_invalid_payload(m_request_post, anvil):
            with pytest.raises(TypeError):
                anvil.forge_submit({})
                assert m_request_post.call_count == 0

        @mock.patch('gql.Client.execute')
        def test_minimum_valid_data_forge_eid(m_request_post, anvil):
            payload = ForgeSubmitPayload(
                forge_eid="forge1234", payload=dict(field1="Some data")
            )
            anvil.forge_submit(payload=payload)
            assert m_request_post.call_count == 1
            assert {"variable_values": expected_data} in m_request_post.call_args

        @mock.patch('gql.Client.execute')
        def test_invalid_wd_submission(m_request_post, anvil):
            with pytest.raises(ValidationError):
                payload = dict(
                    forge_eid="forge1234",
                    # weld_data_eid and submission_eid must be provided
                    # if one exists.
                    weld_data_eid="wd1234",
                    payload=dict(field1="Updated data"),
                )
                anvil.forge_submit(payload=payload)
                assert m_request_post.call_count == 0

            with pytest.raises(ValidationError):
                payload = dict(
                    forge_eid="forge1234",
                    # weld_data_eid and submission_eid must be provided
                    # if one exists.
                    submission_eid="sub1234",
                    payload=dict(field1="Updated data"),
                )
                anvil.forge_submit(payload=payload)
                assert m_request_post.call_count == 0

        @mock.patch('gql.Client.execute')
        def test_minimum_valid_data_submission(m_request_post, anvil):
            payload = ForgeSubmitPayload(
                forge_eid="forge1234",
                submission_eid="sub1234",
                weld_data_eid="wd1234",
                payload=dict(field1="Updated data"),
            )

            # We copy `expected_data` here as it can cause a race condition
            # in other tests that use it.
            _expected_data: MutableMapping[str, Any] = {
                "variable_values": {
                    **expected_data,
                    "submissionEid": "sub1234",
                    "weldDataEid": "wd1234",
                    "payload": {"field1": "Updated data"},
                }
            }

            anvil.forge_submit(payload=payload)
            assert m_request_post.call_count == 1
            assert _expected_data in m_request_post.call_args
