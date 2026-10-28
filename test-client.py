#!/usr/bin/env python3
"""Runs every client method against a real Anvil environment (staging by default) and prints a pass or fail for each.

Run it against a release before and after a change to see which behaviors
changed. Everything it checks is the client's public behavior: what each
method sends, and the shape of what it returns.

Usage:
    ANVIL_API_KEY=<your staging API key> make test-client

Environment variables:
    ANVIL_API_KEY           Required. An API key for the environment being tested.
    ANVIL_BASE_URL          Optional. Defaults to https://staging.useanvil.com
    ANVIL_PDF_TEMPLATE_ID   Optional. The PDF template to fill. Defaults to the first one
                            in your organization that has example data.
    ANVIL_FORGE_EID         Optional. The webform (Forge) in a Workflow to submit to.
                            Defaults to the first one in your organization.

Everything this creates is test data: the Etch packet is a test packet, and the
Workflow submission is a test submission that gets removed at the end.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

from python_anvil.api import Anvil
from python_anvil.api_resources.mutations import CreateEtchPacket
from python_anvil.api_resources.payload import (
    DocumentUpload,
    EtchSigner,
    SignatureField,
    SignerField,
)
from python_anvil.api_resources.requests import PlainRequest, RestRequest
from python_anvil.http import GQLClient


API_KEY = os.environ.get("ANVIL_API_KEY")
BASE_URL = os.environ.get("ANVIL_BASE_URL") or "https://staging.useanvil.com"
PDF_TEMPLATE_ID = os.environ.get("ANVIL_PDF_TEMPLATE_ID")
FORGE_EID = os.environ.get("ANVIL_FORGE_EID")

PDF_TO_SIGN = Path(__file__).parent / "tests" / "assets" / "dummy.pdf"

results: list[tuple[str, str]] = []


class Skip(Exception):
    pass


def check(method: str, fn: Callable[[], str | None]) -> None:
    try:
        detail = fn()
        results.append((method, "PASS"))
        print(f"  PASS  {method}{f' ({detail})' if detail else ''}")
    except Skip as e:
        results.append((method, "SKIP"))
        print(f"  SKIP  {method}: {e}")
    except Exception as e:
        results.append((method, "FAIL"))
        print(f"  FAIL  {method}: {type(e).__name__}: {e}")


def skip_unless(value: object, reason: str) -> None:
    if not value:
        raise Skip(reason)


def assert_pdf(data: object) -> str:
    if not isinstance(data, bytes) or data[:5] != b"%PDF-":
        raise AssertionError("Expected PDF data")
    return f"{len(data)} bytes"


def make_client(api_key: str) -> Anvil:
    """Make a 5.x client pointed at BASE_URL.

    5.x has no base URL option: GraphQL goes to `endpoint_url`, and the REST
    hosts are class attributes. The GraphQL client is also recreated to fetch
    the schema from the API, instead of validating against the schema file
    checked in with the client, which has drifted from the API.
    """
    anvil = Anvil(api_key, endpoint_url=f"{BASE_URL}/graphql")
    RestRequest.API_HOST = BASE_URL
    PlainRequest.API_HOST = BASE_URL
    anvil.gql_client = GQLClient.get_client(
        api_key=api_key,
        endpoint_url=f"{BASE_URL}/graphql",
        fetch_schema_from_transport=True,
    )
    return anvil


def main() -> None:
    if not API_KEY:
        print(
            "ANVIL_API_KEY is required. Usage: ANVIL_API_KEY=<your API key> make test-client",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Testing the Anvil Python client against {BASE_URL}\n")

    client = make_client(API_KEY)

    # What the later steps need, found as we go
    state: dict[str, object] = {
        "cast_eid": PDF_TEMPLATE_ID,
        "cast_data": None,
        "forge_eid": FORGE_EID,
        "etch_packet_eid": None,
        "document_group_eid": None,
        "signer_eid": None,
        "weld_data_eid": None,
    }

    def query() -> str:
        data = client.query(
            """
            query TestClient {
              currentUser { eid }
              organization {
                eid
                casts(limit: 50) { items { eid exampleData } }
                forges(isArchived: false) { eid }
              }
            }
            """
        )
        current_user, organization = data.get("currentUser"), data.get("organization")
        if not current_user or not organization:
            raise AssertionError("Expected currentUser and organization")

        forges = organization.get("forges") or []
        state["forge_eid"] = state["forge_eid"] or (
            forges[0]["eid"] if forges else None
        )

        if state["cast_eid"]:
            # The API won't fill a PDF with empty data, so use the template's example data
            cast_data = client.query(
                "query TestClientCast ($eid: String!) { cast(eid: $eid) { exampleData } }",
                {"eid": state["cast_eid"]},
            )
            state["cast_data"] = (cast_data.get("cast") or {}).get("exampleData")
        else:
            casts = (organization.get("casts") or {}).get("items") or []
            cast = next((c for c in casts if c.get("exampleData")), None)
            if cast:
                state["cast_eid"] = cast["eid"]
                state["cast_data"] = cast["exampleData"]

        return f"organization {organization['eid']}"

    check("query", query)

    def request_rest() -> str:
        data = client.request_rest().post(
            "generate-pdf",
            {"title": "request_rest", "data": [{"content": "Sent with request_rest"}]},
        )
        return assert_pdf(data)

    check("request_rest", request_rest)

    def generate_pdf_markdown() -> str:
        data = client.generate_pdf(
            {
                "title": "Markdown",
                "data": [
                    {"label": "Hello", "content": "From the Anvil Python client"},
                    {
                        "table": {
                            "firstRowHeaders": True,
                            "rows": [["Method", "Status"], ["generate_pdf", "PASS"]],
                        }
                    },
                ],
            }
        )
        return assert_pdf(data)

    check("generate_pdf (markdown)", generate_pdf_markdown)

    def generate_pdf_html() -> str:
        data = client.generate_pdf(
            {
                "title": "HTML",
                "type": "html",
                "data": {
                    "html": "<h1>Hello</h1><p>From the Anvil Python client</p>",
                    "css": "h1 { color: #4c5bf1; }",
                },
            }
        )
        return assert_pdf(data)

    check("generate_pdf (HTML)", generate_pdf_html)

    def fill_pdf() -> str:
        skip_unless(
            state["cast_eid"],
            "No PDF template with example data found. Set ANVIL_PDF_TEMPLATE_ID.",
        )
        data = client.fill_pdf(
            str(state["cast_eid"]), {"data": state["cast_data"] or {}}
        )
        return f"{state['cast_eid']}, {assert_pdf(data)}"

    check("fill_pdf", fill_pdf)

    def fill_pdf_latest() -> str:
        skip_unless(
            state["cast_eid"],
            "No PDF template with example data found. Set ANVIL_PDF_TEMPLATE_ID.",
        )
        data = client.fill_pdf(
            str(state["cast_eid"]),
            {"data": state["cast_data"] or {}},
            version_number=Anvil.VERSION_LATEST,
        )
        return assert_pdf(data)

    check("fill_pdf (VERSION_LATEST)", fill_pdf_latest)

    def fill_pdf_with_headers() -> str:
        skip_unless(
            state["cast_eid"],
            "No PDF template with example data found. Set ANVIL_PDF_TEMPLATE_ID.",
        )
        res = client.fill_pdf(
            str(state["cast_eid"]),
            {"data": state["cast_data"] or {}},
            include_headers=True,
        )
        if "x-ratelimit-limit" not in {k.lower() for k in res["headers"]}:
            raise AssertionError("Expected the rate limit headers")
        return f"{assert_pdf(res['response'])}, with headers"

    check("fill_pdf (include_headers)", fill_pdf_with_headers)

    def create_etch_packet() -> str:
        packet = CreateEtchPacket(
            name="Anvil Python client test",
            is_test=True,
            # Send it right away, so it has signers that can sign
            is_draft=False,
        )
        # An open file is base64 encoded into the mutation's variables
        with PDF_TO_SIGN.open("rb") as pdf:
            packet.add_file(
                DocumentUpload(
                    id="testFile",
                    title="Test File",
                    file=pdf,
                    fields=[
                        SignatureField(
                            id="signature",
                            type="signature",
                            page_num=0,
                            rect={"x": 100, "y": 100, "width": 150, "height": 30},
                        )
                    ],
                )
            )
            packet.add_signer(
                EtchSigner(
                    id="signer",
                    name="Test Signer",
                    email="test-signer@example.com",
                    # Signs through a URL from generate_etch_signing_url rather than by email
                    signer_type="embedded",
                    fields=[SignerField(file_id="testFile", field_id="signature")],
                )
            )
            data = client.create_etch_packet(packet)

        created = data["createEtchPacket"]
        state["etch_packet_eid"] = created["eid"]
        document_group = created.get("documentGroup") or {}
        state["document_group_eid"] = document_group.get("eid")
        signers = document_group.get("signers") or []
        state["signer_eid"] = signers[0]["eid"] if signers else None
        return str(created["eid"])

    check("create_etch_packet", create_etch_packet)

    def get_etch_packet() -> str:
        skip_unless(state["etch_packet_eid"], "create_etch_packet failed")
        data = client.query(
            "query EtchPacket ($eid: String!) { etchPacket (eid: $eid) { eid status } }",
            {"eid": state["etch_packet_eid"]},
        )
        packet = data["etchPacket"]
        if packet["eid"] != state["etch_packet_eid"]:
            raise AssertionError("Got a different packet back")
        return str(packet["status"])

    check("etchPacket query", get_etch_packet)

    def generate_etch_signing_url() -> str:
        skip_unless(state["signer_eid"], "create_etch_packet failed")
        data = client.generate_etch_signing_url(
            signer_eid=str(state["signer_eid"]),
            client_user_id="anvil-python-test-client",
        )
        url = data["generateEtchSignURL"]
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise AssertionError(f"Expected a URL, got {url!r}")
        return "got a URL"

    check("generate_etch_signing_url", generate_etch_signing_url)

    def download_documents() -> str:
        skip_unless(state["document_group_eid"], "create_etch_packet failed")
        data = client.download_documents(str(state["document_group_eid"]))
        # Zip files start with "PK"
        if not isinstance(data, bytes) or data[:2] != b"PK":
            raise AssertionError("Expected a zip file")
        return f"{len(data)} bytes"

    check("download_documents", download_documents)

    def forge_submit() -> str:
        skip_unless(
            state["forge_eid"],
            "No webform (Forge) found in your organization. Set ANVIL_FORGE_EID.",
        )
        data = client.forge_submit(
            {"forge_eid": state["forge_eid"], "payload": {}, "is_test": True}
        )
        state["weld_data_eid"] = data["forgeSubmit"]["weldData"]["eid"]
        return f"{state['forge_eid']}, created {state['weld_data_eid']}"

    check("forge_submit", forge_submit)

    def remove_weld_data() -> str:
        skip_unless(state["weld_data_eid"], "forge_submit did not create a submission")
        data = client.mutate(
            "mutation RemoveWeldData ($eid: String!) { removeWeldData (eid: $eid) }",
            {"eid": state["weld_data_eid"]},
        )
        if data["removeWeldData"] is not True:
            raise AssertionError("Expected True")
        return f"removed {state['weld_data_eid']}"

    check("removeWeldData mutation", remove_weld_data)

    # The convenience queries
    check("get_current_user", lambda: client.get_current_user()["eid"])
    check("get_casts", lambda: f"{len(client.get_casts())} templates")
    check("get_welds", lambda: f"{len(client.get_welds())} welds")

    def count(status: str) -> int:
        return sum(1 for _, result in results if result == status)

    print(f"\n{count('PASS')} passed, {count('FAIL')} failed, {count('SKIP')} skipped")

    if count("FAIL"):
        sys.exit(1)


if __name__ == "__main__":
    main()
