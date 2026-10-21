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

from python_anvil import Anvil, AnvilRequestError
from python_anvil.api_resources.mutations import CreateEtchPacket
from python_anvil.api_resources.payload import (
    DocumentUpload,
    EtchSigner,
    SignatureField,
    SignerField,
)


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
    except AnvilRequestError as e:
        results.append((method, "FAIL"))
        print(f"  FAIL  {method}: {e}")
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


def main() -> None:
    if not API_KEY:
        print(
            "ANVIL_API_KEY is required. Usage: ANVIL_API_KEY=<your API key> make test-client",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Testing the Anvil Python client against {BASE_URL}\n")

    client = Anvil(API_KEY, base_url=BASE_URL)

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

    def request_graphql() -> str:
        data = client.request_graphql(
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
            cast_data = client.request_graphql(
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

    check("request_graphql", request_graphql)

    def request_rest() -> str:
        data = client.request_rest(
            "POST",
            "/api/v1/generate-pdf",
            json={
                "title": "request_rest",
                "data": [{"content": "Sent with request_rest"}],
            },
            data_type="bytes",
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

    def fill_pdf_stream() -> str:
        skip_unless(
            state["cast_eid"],
            "No PDF template with example data found. Set ANVIL_PDF_TEMPLATE_ID.",
        )
        with client.fill_pdf(
            str(state["cast_eid"]),
            {"data": state["cast_data"] or {}},
            data_type="stream",
        ) as response:
            data = b"".join(response.iter_content(chunk_size=64 * 1024))
        return assert_pdf(data)

    check("fill_pdf (stream)", fill_pdf_stream)

    def create_etch_packet() -> str:
        packet = CreateEtchPacket(
            name="Anvil Python client test",
            is_test=True,
            # Send it right away, so it has signers that can sign
            is_draft=False,
        )
        packet.add_file(
            DocumentUpload(
                id="testFile",
                title="Test File",
                file=Anvil.prepare_graphql_file(PDF_TO_SIGN),
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

    def create_etch_packet_base64() -> str:
        packet = CreateEtchPacket(
            name="Anvil Python client test (base64 upload)", is_test=True, is_draft=True
        )
        # An open file that wasn't prepared with `prepare_graphql_file` is base64
        # encoded into the mutation's variables, as it always was
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
                    signer_type="embedded",
                    fields=[SignerField(file_id="testFile", field_id="signature")],
                )
            )
            data = client.create_etch_packet(packet)
        return f"draft {data['createEtchPacket']['eid']}"

    check("create_etch_packet (base64 upload)", create_etch_packet_base64)

    def get_etch_packet() -> str:
        skip_unless(state["etch_packet_eid"], "create_etch_packet failed")
        packet = client.get_etch_packet(str(state["etch_packet_eid"]))
        if packet["eid"] != state["etch_packet_eid"]:
            raise AssertionError("Got a different packet back")
        return str(packet["status"])

    check("get_etch_packet", get_etch_packet)

    def generate_etch_signing_url() -> str:
        skip_unless(state["signer_eid"], "create_etch_packet failed")
        url = client.generate_etch_signing_url(
            signer_eid=str(state["signer_eid"]),
            client_user_id="anvil-python-test-client",
        )
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
        removed = client.remove_weld_data(str(state["weld_data_eid"]))
        if removed is not True:
            raise AssertionError("Expected True")
        return f"removed {state['weld_data_eid']}"

    check("remove_weld_data", remove_weld_data)

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
