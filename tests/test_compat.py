"""Call patterns from 5.x that must keep working, and the conveniences added for 6.0."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest import mock

import pytest

from python_anvil import Anvil
from python_anvil.api_resources.mutations import CreateEtchPacket, ForgeSubmit
from python_anvil.api_resources.mutations.base import BaseQuery
from python_anvil.api_resources.mutations.create_etch_packet import CREATE_ETCH_PACKET
from python_anvil.api_resources.mutations.forge_submit import FORGE_SUBMIT
from python_anvil.api_resources.payload import (
    DocumentUpload,
    EtchCastRef,
    EtchSigner,
    GeneratePDFPayload,
)
from python_anvil.graphql import mutations, queries


DUMMY_PDF = Path(__file__).parent / "assets" / "dummy.pdf"


@pytest.fixture
def anvil():
    return Anvil(api_key="key")


@pytest.fixture
def graphql(anvil):
    with mock.patch.object(anvil, "request_graphql", return_value={}) as m:
        yield m


@pytest.fixture
def rest(anvil):
    with mock.patch.object(anvil, "request_rest", return_value=b"%PDF-") as m:
        yield m


def describe_the_constructor():
    def it_reads_the_api_key_from_the_environment(monkeypatch):
        monkeypatch.setenv("ANVIL_API_KEY", "from-env")
        client = Anvil()
        assert client.client.api_key == "from-env"

    def it_still_requires_a_key_without_the_variable(monkeypatch):
        monkeypatch.delenv("ANVIL_API_KEY", raising=False)
        with pytest.raises(ValueError, match="or set ANVIL_API_KEY"):
            Anvil()

    def it_keeps_the_credentials_on_the_client(anvil):
        assert anvil.client.api_key == "key"
        assert anvil.client.access_token is None


def describe_query_and_mutate():
    def they_take_a_timeout(anvil, graphql):
        anvil.query("{ x }", timeout=10)
        assert graphql.call_args.kwargs["timeout"] == 10
        anvil.mutate("mutation { x }", {"a": 1}, timeout=(5, 30))
        assert graphql.call_args.kwargs["timeout"] == (5, 30)

    def they_take_variables_as_a_json_string(anvil):
        response = mock.Mock(
            status_code=200, headers={"content-type": "application/json"}
        )
        response.json.return_value = {"data": {"x": 1}}
        with mock.patch.object(
            anvil.client, "request", return_value=response
        ) as request:
            anvil.query("query ($eid: String) { x(eid: $eid) }", '{"eid": "w1"}')
        assert request.call_args.kwargs["json"]["variables"] == {"eid": "w1"}

    def a_5x_subclass_with_a_mutation_template_still_works(anvil, graphql):
        class Mine(BaseQuery):
            mutation = "mutation Mine($eid: String!) {{ mine(eid: $eid) {query} }}"
            mutation_res_query = "{ eid }"

            def create_payload(self):
                return {"eid": "x"}

        anvil.mutate(Mine(), {"eid": "x"})
        assert (
            graphql.call_args.args[0]
            == "mutation Mine($eid: String!) { mine(eid: $eid) { eid } }"
        )

    def the_old_module_constants_are_the_mutations():
        assert mutations.create_etch_packet.generate_mutation() == CREATE_ETCH_PACKET
        assert mutations.forge_submit.generate_mutation() == FORGE_SUBMIT


def describe_every_method_taking_a_timeout():
    def rest_methods(anvil, rest):
        anvil.fill_pdf("t", {"data": {"a": 1}}, timeout=7)
        assert rest.call_args.kwargs["timeout"] == 7
        anvil.generate_pdf({"data": [{"content": "x"}]}, timeout=8)
        assert rest.call_args.kwargs["timeout"] == 8
        anvil.download_documents("dg", timeout=9)
        assert rest.call_args.kwargs["timeout"] == 9

    def graphql_methods(anvil, graphql):
        graphql.return_value = {
            "createEtchPacket": {},
            "etchPacket": {},
            "generateEtchSignURL": "u",
            "forgeSubmit": {},
            "removeWeldData": True,
        }
        anvil.create_etch_packet({"name": "n"}, timeout=1)
        assert graphql.call_args.kwargs["timeout"] == 1
        anvil.get_etch_packet("e", timeout=2)
        assert graphql.call_args.kwargs["timeout"] == 2
        anvil.generate_etch_signing_url("s", "c", timeout=3)
        assert graphql.call_args.kwargs["timeout"] == 3
        anvil.forge_submit({"forge_eid": "f", "payload": {}}, timeout=4)
        assert graphql.call_args.kwargs["timeout"] == 4
        anvil.remove_weld_data("w", timeout=5)
        assert graphql.call_args.kwargs["timeout"] == 5


def describe_create_etch_packet_payloads():
    def an_empty_dict_is_a_type_error_as_before(anvil, graphql):
        with pytest.raises(TypeError, match="`payload` or `json` must exist"):
            anvil.create_etch_packet({})
        with pytest.raises(TypeError, match="`payload` or `json` must exist"):
            anvil.create_etch_packet(payload={})
        with pytest.raises(TypeError, match="`name` is required"):
            CreateEtchPacket()

    def a_json_string_works_as_the_payload(anvil, graphql):
        anvil.create_etch_packet(json.dumps({"name": "n", "signers": [], "files": []}))
        assert graphql.call_args.args[1]["name"] == "n"

    def a_dict_may_hold_every_kind_of_file_and_model_instances(anvil, graphql):
        anvil.create_etch_packet(
            {
                "name": "n",
                "files": [
                    {"id": "tpl", "castEid": "cast1"},
                    {"id": "md", "filename": "md.pdf", "fields": [{"content": "hi"}]},
                    {"id": "html", "filename": "h.pdf", "markup": {"html": "<p>"}},
                    {
                        "id": "up",
                        "title": "T",
                        "file": {
                            "data": "aGk=",
                            "filename": "x.pdf",
                            "mimetype": "application/pdf",
                        },
                        "fields": [],
                    },
                    EtchCastRef(id="tpl2", cast_eid="cast2"),
                ],
                "signers": [EtchSigner(name="S", email="s@example.com", fields=[])],
            }
        )
        files = graphql.call_args.args[1]["files"]
        assert [f["id"] for f in files] == ["tpl", "md", "html", "up", "tpl2"]
        assert files[0] == {"id": "tpl", "castEid": "cast1"}
        assert files[1]["fields"][0]["content"] == "hi"
        assert files[2]["markup"] == {"html": "<p>"}
        assert files[3]["file"]["data"] == "aGk="
        assert graphql.call_args.args[1]["signers"][0]["name"] == "S"

    def an_in_person_signer_is_accepted(anvil, graphql):
        packet = CreateEtchPacket(name="n")
        packet.add_signer(
            EtchSigner(
                name="S", email="s@example.com", fields=[], signer_type="in-person"
            )
        )
        anvil.create_etch_packet(packet)
        assert graphql.call_args.args[1]["signers"][0]["signerType"] == "in-person"

    def response_fields_may_be_given_without_braces(anvil, graphql):
        graphql.return_value = {"createEtchPacket": {}, "etchPacket": {}}
        anvil.create_etch_packet({"name": "n"}, response_query="eid name")
        assert graphql.call_args.args[
            0
        ] == mutations.create_etch_packet.generate_mutation("{ eid name }")
        anvil.get_etch_packet("e", response_query="eid")
        assert graphql.call_args.args[0] == queries.etch_packet.generate_query(
            "{ eid }"
        )

    def an_uploaded_file_keeps_its_own_name():
        with DUMMY_PDF.open("rb") as pdf:
            upload = DocumentUpload(id="f", title="T", file=pdf, fields=[])
            dumped = upload.model_dump(by_alias=True)
        assert dumped["file"]["filename"] == "dummy.pdf"
        assert dumped["file"]["mimetype"] == "application/pdf"

        with DUMMY_PDF.open("rb") as pdf:
            packet = CreateEtchPacket(name="n")
            packet.add_file(DocumentUpload(id="f", title="T", file=pdf, fields=[]))
            dumped = packet.create_payload().model_dump(by_alias=True)
        assert dumped["files"][0]["file"]["filename"] == "dummy.pdf"

    def a_file_with_no_name_is_still_document_pdf():
        dumped = DocumentUpload(
            id="f", title="T", file=io.BytesIO(b"x"), fields=[]
        ).model_dump(by_alias=True)
        assert dumped["file"]["filename"] == "document.pdf"


def describe_forge_submit_payloads():
    def an_empty_dict_is_a_type_error_as_before(anvil, graphql):
        with pytest.raises(TypeError, match="`json` or `payload` are required"):
            anvil.forge_submit({})

    def a_json_string_works_as_the_payload(anvil, graphql):
        anvil.forge_submit(json.dumps({"forgeEid": "f", "payload": {"a": 1}}))
        assert graphql.call_args.args[1]["forgeEid"] == "f"

    def the_builder_still_takes_a_dict(anvil, graphql):
        anvil.mutate(
            ForgeSubmit({"a": 1}, forge_eid="f"), {"forgeEid": "f", "payload": {"a": 1}}
        )
        assert "forgeSubmit" in graphql.call_args.args[0]


def describe_generate_pdf_payload():
    def it_dumps_the_documented_examples_as_before():
        markdown = GeneratePDFPayload(
            title="Example",
            data=[
                {"label": "Name", "content": "Sally"},
                {"table": {"firstRowHeaders": True, "rows": [["a"]]}},
            ],
        )
        assert markdown.model_dump(by_alias=True, exclude_none=True) == {
            "title": "Example",
            "type": "markdown",
            "data": [
                {"label": "Name", "content": "Sally"},
                {"table": {"firstRowHeaders": True, "rows": [["a"]]}},
            ],
        }
        html = GeneratePDFPayload(
            type="html", title="T", data={"html": "<h2>h</h2>", "css": "h2 {}"}
        )
        assert html.model_dump(by_alias=True, exclude_none=True) == {
            "title": "T",
            "type": "html",
            "data": {"html": "<h2>h</h2>", "css": "h2 {}"},
        }

    def it_takes_every_documented_option():
        payload = GeneratePDFPayload(
            data=[{"content": "x"}],
            logo={"src": "https://x/l.png", "max_width": 100},
            page={"marginTop": "1in", "pageCount": "topRight"},
            font_size=36,
            font_family="Helvetica",
            text_color="#333",
            include_timestamp=False,
        )
        dumped = payload.model_dump(by_alias=True, exclude_none=True)
        assert dumped["logo"] == {"src": "https://x/l.png", "maxWidth": 100}
        assert dumped["page"] == {"marginTop": "1in", "pageCount": "topRight"}
        # A documented page option is validated; an unknown one is kept
        assert GeneratePDFPayload(
            data=[{"content": "x"}], page={"customKey": 1}
        ).model_dump(by_alias=True, exclude_none=True)["page"] == {"customKey": 1}
        assert dumped["fontSize"] == 36
        assert dumped["includeTimestamp"] is False
        assert "outputFormat" not in dumped

    def it_rejects_what_the_api_rejects():
        with pytest.raises(ValueError):
            GeneratePDFPayload(data=[{"content": "x"}], page={"pageCount": "middle"})
        with pytest.raises(ValueError):
            GeneratePDFPayload(data=[{"content": "x"}], type="docx")
