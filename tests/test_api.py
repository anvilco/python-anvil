"""The client's methods: what each sends, with the transport mocked. See test_http.py for the wire."""

from __future__ import annotations

import json
from unittest import mock

import pytest

from python_anvil import Anvil, AnvilRequestError
from python_anvil.api_resources.mutations import CreateEtchPacket
from python_anvil.api_resources.payload import (
    CreateEtchPacketPayload,
    FillPDFPayload,
    ForgeSubmitPayload,
    GeneratePDFPayload,
)
from python_anvil.graphql import mutations, queries
from tests import payloads


DEV_KEY = "MY-SECRET-KEY"


@pytest.fixture
def anvil():
    return Anvil(api_key=DEV_KEY)


@pytest.fixture
def rest(anvil):
    with mock.patch.object(anvil, "request_rest", return_value=b"%PDF-") as m:
        yield m


@pytest.fixture
def graphql(anvil):
    with mock.patch.object(anvil, "request_graphql", return_value={}) as m:
        yield m


def describe_init():
    def it_requires_an_api_key_or_access_token():
        with pytest.raises(
            ValueError, match=r"`api_key` or `access_token` is required"
        ):
            Anvil()
        with pytest.raises(ValueError):
            Anvil(api_key="")

    def it_accepts_an_access_token():
        client = Anvil(access_token="token")
        assert client.client.auth_header.startswith("Bearer ")

    def it_defaults_the_base_url_to_production(anvil):
        assert anvil.base_url == "https://app.useanvil.com"

    def it_accepts_a_custom_base_url():
        assert (
            Anvil(DEV_KEY, base_url="https://staging.useanvil.com/").base_url
            == "https://staging.useanvil.com"
        )

    def it_starts_with_a_limit_of_one_request_per_second(anvil):
        limiter = anvil.client.rate_limiter
        assert (limiter.limit, limiter.interval_ms) == (1, 1000)

    def it_accepts_custom_starting_rate_limits():
        limiter = Anvil(
            DEV_KEY, request_limit=5, request_limit_ms=2000
        ).client.rate_limiter
        assert (limiter.limit, limiter.interval_ms) == (5, 2000)

    def it_rejects_the_removed_endpoint_url():
        with pytest.raises(
            TypeError, match=r"`endpoint_url` was removed in 6\.0\.0\. Pass `base_url`"
        ):
            Anvil(DEV_KEY, endpoint_url="https://graphql.staging.useanvil.com")

    def it_warns_that_environment_does_nothing():
        with pytest.warns(DeprecationWarning, match="`environment` does nothing"):
            Anvil(DEV_KEY, environment="prod")

    def it_only_takes_the_api_key_positionally():
        with pytest.raises(TypeError):
            Anvil(DEV_KEY, "https://staging.useanvil.com")  # type: ignore[misc]


def describe_version_constants():
    def it_exposes_version_latest_as_minus_one():
        assert Anvil.VERSION_LATEST == -1

    def it_exposes_version_latest_published_as_minus_two():
        assert Anvil.VERSION_LATEST_PUBLISHED == -2


def describe_fill_pdf():
    def it_posts_a_dict_payload(anvil, rest):
        assert (
            anvil.fill_pdf("some_template", {"data": {"jsonData": "yes"}}) == b"%PDF-"
        )
        rest.assert_called_once_with(
            "POST",
            "/api/v1/fill/some_template.pdf",
            json={"data": {"jsonData": "yes"}},
            params=None,
            data_type="bytes",
        )

    def it_posts_a_json_payload(anvil, rest):
        anvil.fill_pdf("some_template", '{ "data": {"jsonData": "is here"} }')
        assert rest.call_args.kwargs["json"] == {"data": {"jsonData": "is here"}}

    def it_posts_a_payload_object(anvil, rest):
        anvil.fill_pdf("some_template", FillPDFPayload(data={"a": 1}, font_size=10))
        assert rest.call_args.kwargs["json"] == {"data": {"a": 1}, "fontSize": 10}

    def it_accepts_camel_case_keys(anvil, rest):
        anvil.fill_pdf(
            "some_template", {"data": {"a": 1}, "fontSize": 10, "textColor": "#333"}
        )
        assert rest.call_args.kwargs["json"] == {
            "data": {"a": 1},
            "fontSize": 10,
            "textColor": "#333",
        }

    def it_rejects_an_empty_payload(anvil, rest):
        with pytest.raises(ValueError):
            anvil.fill_pdf("some_template", {"data": {}})
        with pytest.raises(ValueError):
            anvil.fill_pdf("some_template", 123)  # type: ignore[arg-type]
        assert rest.call_count == 0

    def it_sends_the_version_number(anvil, rest):
        anvil.fill_pdf(
            "some_template", {"data": {"one": "1"}}, version_number=Anvil.VERSION_LATEST
        )
        assert rest.call_args.kwargs["params"] == {"versionNumber": -1}

    def it_sends_extra_params(anvil, rest):
        anvil.fill_pdf(
            "some_template",
            {"data": {"one": "1"}},
            params={"arbitrary": "Param"},
            version_number=3,
        )
        assert rest.call_args.kwargs["params"] == {
            "arbitrary": "Param",
            "versionNumber": 3,
        }

    def it_streams_when_asked(anvil, rest):
        anvil.fill_pdf("some_template", {"data": {"one": "1"}}, data_type="stream")
        assert rest.call_args.kwargs["data_type"] == "stream"

    def it_rejects_json_as_a_data_type(anvil, rest):
        with pytest.raises(
            ValueError, match=r"data_type must be one of: bytes\|stream"
        ):
            anvil.fill_pdf("some_template", {"data": {"one": "1"}}, data_type="json")


def describe_generate_pdf():
    def it_posts_a_dict_payload_as_markdown_by_default(anvil, rest):
        anvil.generate_pdf({"data": [{"d1": "data"}]})
        rest.assert_called_once_with(
            "POST",
            "/api/v1/generate-pdf",
            json={"data": [{"d1": "data"}], "type": "markdown"},
            params=None,
            data_type="bytes",
        )

    def it_posts_a_json_payload(anvil, rest):
        anvil.generate_pdf(json.dumps({"data": [{"d1": "data"}], "title": "T"}))
        assert rest.call_args.kwargs["json"] == {
            "data": [{"d1": "data"}],
            "title": "T",
            "type": "markdown",
        }

    def it_posts_an_html_payload(anvil, rest):
        anvil.generate_pdf(
            {"type": "html", "data": {"html": "<h1>Hi</h1>", "css": "h1 {}"}}
        )
        assert rest.call_args.kwargs["json"] == {
            "type": "html",
            "data": {"html": "<h1>Hi</h1>", "css": "h1 {}"},
        }

    def it_posts_a_payload_object(anvil, rest):
        anvil.generate_pdf(GeneratePDFPayload(data=[{"content": "x"}], font_size=12))
        assert rest.call_args.kwargs["json"] == {
            "data": [{"content": "x"}],
            "type": "markdown",
            "fontSize": 12,
        }

    def it_rejects_an_empty_or_invalid_payload(anvil, rest):
        with pytest.raises(ValueError):
            anvil.generate_pdf({})
        with pytest.raises(ValueError):
            anvil.generate_pdf({"type": "html", "data": {"not_html": "x"}})
        with pytest.raises(ValueError):
            anvil.generate_pdf({"data": [{"d1": "data"}], "type": "unknown"})
        assert rest.call_count == 0


def describe_download_documents():
    def it_gets_the_zip(anvil, rest):
        anvil.download_documents("dg123")
        rest.assert_called_once_with(
            "GET", "/api/document-group/dg123.zip", data_type="bytes"
        )


def describe_request_graphql():
    def it_returns_the_data(anvil):
        response = mock.Mock(
            status_code=200, headers={"content-type": "application/json"}
        )
        response.json.return_value = {"data": {"currentUser": {"eid": "u1"}}}
        with mock.patch.object(
            anvil.client, "request", return_value=response
        ) as request:
            data = anvil.request_graphql("{ currentUser { eid } }", {"a": 1})

        assert data == {"currentUser": {"eid": "u1"}}
        request.assert_called_once_with(
            "POST",
            "/graphql",
            json={"query": "{ currentUser { eid } }", "variables": {"a": 1}},
            timeout=None,
        )

    def it_raises_for_an_unexpected_body(anvil):
        response = mock.Mock(
            status_code=200, headers={"content-type": "application/json"}
        )
        response.json.return_value = {"unexpected": True}
        with (
            mock.patch.object(anvil.client, "request", return_value=response),
            pytest.raises(ValueError, match="Unexpected GraphQL response"),
        ):
            anvil.request_graphql("{ x }")

    def it_is_also_called_query(anvil, graphql):
        anvil.query("{ x }", {"a": 1})
        graphql.assert_called_once_with("{ x }", {"a": 1})

    def it_is_also_called_mutate(anvil, graphql):
        anvil.mutate("mutation { x }", {"a": 1})
        graphql.assert_called_once_with("mutation { x }", {"a": 1})

    def it_mutates_with_a_mutation_class(anvil, graphql):
        builder = CreateEtchPacket(name="Packet")
        anvil.mutate(builder, {"name": "Packet"})
        graphql.assert_called_once_with(
            mutations.create_etch_packet.generate_mutation(), {"name": "Packet"}
        )


def describe_create_etch_packet():
    expected_data = {
        "name": "Packet name",
        "signatureEmailSubject": "The subject",
        "signers": [],
        "files": [],
        "isDraft": False,
        "isTest": True,
        "data": {"payloads": {}},
        "signaturePageOptions": {},
    }

    def it_requires_a_payload(anvil, graphql):
        with pytest.raises(TypeError):
            anvil.create_etch_packet()
        with pytest.raises(ValueError):
            anvil.create_etch_packet("not a payload")  # type: ignore[arg-type]
        assert graphql.call_count == 0

    def it_sends_a_mutation_builder(anvil, graphql):
        graphql.return_value = {"createEtchPacket": {"eid": "p1"}}
        builder = CreateEtchPacket(
            name="Packet name", signature_email_subject="The subject"
        )

        data = anvil.create_etch_packet(payload=builder)

        assert data == {"createEtchPacket": {"eid": "p1"}}
        mutation, variables = graphql.call_args.args
        assert mutation == mutations.create_etch_packet.generate_mutation()
        assert variables == expected_data

    def it_sends_the_builder_options(anvil, graphql):
        builder = CreateEtchPacket(
            is_test=False,
            is_draft=True,
            name="Packet name",
            signature_email_subject="The subject",
            organization_eid="org1",
            allow_updates=True,
        )
        anvil.create_etch_packet(builder)
        variables = graphql.call_args.args[1]
        assert variables == {
            **expected_data,
            "isTest": False,
            "isDraft": True,
            "organizationEid": "org1",
            "allowUpdates": True,
        }

    def it_sends_a_dict(anvil, graphql):
        anvil.create_etch_packet(
            {"name": "Packet name", "signature_email_subject": "The subject"}
        )
        assert graphql.call_args.args[1] == expected_data

    @mock.patch(
        "python_anvil.api_resources.mutations.create_etch_packet.create_unique_id"
    )
    def it_sends_a_dict_with_signers_and_files(create_unique_id, anvil, graphql):
        create_unique_id.return_value = "signer-mock-generated"
        anvil.create_etch_packet(payload=payloads.ETCH_TEST_PAYLOAD)
        assert graphql.call_args.args[1] == payloads.EXPECTED_ETCH_TEST_PAYLOAD

    @mock.patch(
        "python_anvil.api_resources.mutations.create_etch_packet.create_unique_id"
    )
    def it_sends_json(create_unique_id, anvil, graphql):
        create_unique_id.return_value = "signer-mock-generated"
        # We are currently removing `None`s from the payload, so do that here too.
        payload = {
            k: v
            for k, v in payloads.EXPECTED_ETCH_TEST_PAYLOAD_JSON.items()
            if v is not None
        }

        anvil.create_etch_packet(json=json.dumps(payload))

        assert graphql.call_args.args[1] == payload

    def it_sends_a_payload_model_with_extra_fields(anvil, graphql):
        payload = {
            k: v
            for k, v in payloads.EXPECTED_ETCH_TEST_PAYLOAD_JSON.items()
            if v is not None
        }
        cep = CreateEtchPacketPayload.model_validate(payload)
        cep.newFeature = True  # type: ignore[attr-defined]

        anvil.create_etch_packet(payload=cep)

        variables = graphql.call_args.args[1]
        assert variables == cep.model_dump(by_alias=True, exclude_none=True)
        assert variables["newFeature"] is True

    def it_sends_a_custom_response_query(anvil, graphql):
        anvil.create_etch_packet(
            {"name": "Packet name"}, response_query="{ eid status }"
        )
        assert graphql.call_args.args[
            0
        ] == mutations.create_etch_packet.generate_mutation("{ eid status }")

    def it_sends_a_custom_mutation(anvil, graphql):
        anvil.create_etch_packet(
            {"name": "Packet name"},
            mutation="mutation Mine { createEtchPacket { eid } }",
        )
        assert graphql.call_args.args[0] == "mutation Mine { createEtchPacket { eid } }"

    def it_leaves_prepared_files_for_the_multipart_upload(anvil, graphql):
        file = Anvil.prepare_graphql_file(b"%PDF", filename="x.pdf")
        anvil.create_etch_packet(
            {
                "name": "Packet",
                "files": [{"id": "f", "title": "F", "file": file, "fields": []}],
            }
        )
        assert graphql.call_args.args[1]["files"][0]["file"] is file


def describe_get_etch_packet():
    def it_queries_the_packet(anvil, graphql):
        graphql.return_value = {"etchPacket": {"eid": "p1", "status": "sent"}}

        packet = anvil.get_etch_packet("p1")

        assert packet == {"eid": "p1", "status": "sent"}
        graphql.assert_called_once_with(
            queries.etch_packet.generate_query(), {"eid": "p1"}
        )

    def it_sends_a_custom_response_query(anvil, graphql):
        graphql.return_value = {"etchPacket": {}}
        anvil.get_etch_packet("p1", response_query="{ eid }")
        assert graphql.call_args.args[0] == queries.etch_packet.generate_query(
            "{ eid }"
        )


def describe_generate_etch_signing_url():
    def it_returns_the_url(anvil, graphql):
        graphql.return_value = {
            "generateEtchSignURL": "https://app.useanvil.com/sign/abc"
        }

        url = anvil.generate_etch_signing_url(
            signer_eid="someId", client_user_id="anotherId"
        )

        assert url == "https://app.useanvil.com/sign/abc"
        graphql.assert_called_once_with(
            mutations.generate_etch_sign_url.generate_mutation(),
            {"signerEid": "someId", "clientUserId": "anotherId"},
        )

    def it_is_also_called_generate_etch_sign_url(anvil, graphql):
        graphql.return_value = {"generateEtchSignURL": "https://x"}
        assert anvil.generate_etch_sign_url("s", "c") == "https://x"


def describe_forge_submit():
    expected_data = {
        "forgeEid": "forge1234",
        "payload": {"field1": "Some data"},
        "isTest": True,
    }

    def it_requires_a_payload(anvil, graphql):
        with pytest.raises(TypeError):
            anvil.forge_submit()
        with pytest.raises((TypeError, ValueError)):
            anvil.forge_submit({})
        with pytest.raises(ValueError):
            anvil.forge_submit("not a payload")  # type: ignore[arg-type]
        assert graphql.call_count == 0

    def it_sends_the_minimum_payload_model(anvil, graphql):
        anvil.forge_submit(
            payload=ForgeSubmitPayload(
                forge_eid="forge1234", payload={"field1": "Some data"}
            )
        )
        mutation, variables = graphql.call_args.args
        assert mutation == mutations.forge_submit.generate_mutation()
        assert variables == expected_data

    def it_sends_a_dict(anvil, graphql):
        anvil.forge_submit(
            {"forge_eid": "forge1234", "payload": {"field1": "Some data"}}
        )
        assert graphql.call_args.args[1] == expected_data

    def it_sends_json(anvil, graphql):
        anvil.forge_submit(
            json=json.dumps(
                {"forgeEid": "forge1234", "payload": {"field1": "Some data"}}
            )
        )
        assert graphql.call_args.args[1] == expected_data

    def it_sends_an_update_to_a_submission(anvil, graphql):
        payload = ForgeSubmitPayload(
            forge_eid="forge1234",
            submission_eid="sub1234",
            weld_data_eid="wd1234",
            payload={"field1": "Updated data"},
            enforce_payload_valid_on_create=True,
        )
        anvil.forge_submit(payload=payload)
        assert graphql.call_args.args[1] == {
            **expected_data,
            "submissionEid": "sub1234",
            "weldDataEid": "wd1234",
            "payload": {"field1": "Updated data"},
            "enforcePayloadValidOnCreate": True,
        }

    def it_sends_a_custom_response_query_or_mutation(anvil, graphql):
        anvil.forge_submit({"forge_eid": "f", "payload": {}}, response_query="{ eid }")
        assert graphql.call_args.args[0] == mutations.forge_submit.generate_mutation(
            "{ eid }"
        )
        anvil.forge_submit(
            {"forge_eid": "f", "payload": {}},
            mutation="mutation Mine { forgeSubmit { eid } }",
        )
        assert graphql.call_args.args[0] == "mutation Mine { forgeSubmit { eid } }"


def describe_remove_weld_data():
    def it_sends_the_mutation(anvil, graphql):
        graphql.return_value = {"removeWeldData": True}

        assert anvil.remove_weld_data("wd1") is True
        graphql.assert_called_once_with(
            mutations.remove_weld_data.generate_mutation(), {"eid": "wd1"}
        )

    def it_sends_a_custom_mutation(anvil, graphql):
        graphql.return_value = {"removeWeldData": False}
        assert (
            anvil.remove_weld_data("wd1", mutation="mutation Mine { removeWeldData }")
            is False
        )
        assert graphql.call_args.args[0] == "mutation Mine { removeWeldData }"


def describe_convenience_queries():
    def it_gets_the_current_user(anvil, graphql):
        graphql.return_value = {"currentUser": {"name": "Cameron"}}
        assert anvil.get_current_user() == {"name": "Cameron"}

    def it_gets_a_cast(anvil, graphql):
        graphql.return_value = {"cast": {"eid": "c1"}}
        assert anvil.get_cast("c1") == {"eid": "c1"}
        assert 'cast(eid: "c1")' in graphql.call_args.args[0]
        assert "eid title fieldInfo" in graphql.call_args.args[0]

    def it_gets_a_cast_version_with_fields(anvil, graphql):
        graphql.return_value = {"cast": {}}
        anvil.get_cast("c1", fields=["eid", "name"], version_number=-1)
        query = graphql.call_args.args[0]
        assert 'cast(eid: "c1", versionNumber: -1)' in query
        assert "eid name" in query

    def it_gets_the_casts_of_every_organization(anvil, graphql):
        graphql.return_value = {
            "currentUser": {
                "organizations": [
                    {"casts": {"items": [{"eid": "a"}]}},
                    {"casts": {"items": [{"eid": "b"}]}},
                ]
            }
        }
        assert anvil.get_casts() == [{"eid": "a"}, {"eid": "b"}]
        assert "casts(isTemplate: true, limit: 500)" in graphql.call_args.args[0]
        anvil.get_casts(show_all=True)
        assert "casts(isTemplate: null, limit: 500)" in graphql.call_args.args[0]

    def it_gets_the_welds_of_every_organization(anvil, graphql):
        graphql.return_value = {
            "currentUser": {
                "organizations": [
                    {"welds": {"items": [{"eid": "a"}]}},
                    {"welds": {"items": []}},
                ]
            }
        }
        assert anvil.get_welds() == [{"eid": "a"}]
        assert "welds(limit: 500)" in graphql.call_args.args[0]

    def it_gets_a_weld(anvil, graphql):
        graphql.return_value = {"weld": {"eid": "w1"}}
        assert anvil.get_weld("w1") == {"eid": "w1"}
        assert graphql.call_args.args[1] == {"eid": "w1"}


def describe_errors():
    def it_propagates_request_errors(anvil, graphql):
        graphql.side_effect = AnvilRequestError(
            [{"message": "Not Found"}], status_code=200
        )
        with pytest.raises(AnvilRequestError, match=r"200: Not Found"):
            anvil.get_etch_packet("nope")
