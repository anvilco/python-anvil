"""The generated types, and the payload models built on them."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from python_anvil import types
from python_anvil.api_resources.payload import (
    CreateEtchPacketPayload,
    EtchSigner,
    FillPDFPayload,
    ForgeSubmitPayload,
)
from python_anvil.graphql import mutations, queries
from python_anvil.types import GeneratedModel, graphql, operations, rest


def describe_the_generated_models():
    def they_take_snake_case_and_camel_case_names():
        by_snake = rest.FillPdfRequest(
            data={"a": 1}, font_size=10, use_interactive_fields=True
        )
        by_camel = rest.FillPdfRequest(
            data={"a": 1}, fontSize=10, useInteractiveFields=True
        )
        assert by_snake == by_camel
        assert by_snake.font_size == 10

    def they_dump_camel_case_json():
        request = rest.FillPdfRequest(
            data={"a": 1}, text_color="#333", use_interactive_fields=True
        )
        assert request.model_dump(by_alias=True, exclude_none=True) == {
            "data": {"a": 1},
            "textColor": "#333",
            "useInteractiveFields": True,
            "outputFormat": "pdf",
        }

    def they_keep_extra_fields():
        request = rest.PageOptions(width="8.5in", brandNew=True)  # type: ignore[call-arg]
        assert request.model_dump(by_alias=True, exclude_none=True) == {
            "width": "8.5in",
            "brandNew": True,
        }

    def they_check_enum_values():
        assert rest.EtchSigner(id="s", signature_mode="draw").signature_mode == "draw"
        with pytest.raises(ValidationError):
            rest.EtchSigner(id="s", signature_mode="wave")

    def they_are_all_generated_models():
        for model in (
            rest.FillPdfRequest,
            graphql.EtchFile,
            graphql.EtchPacket,
            operations.CreateEtchPacketArgs,
        ):
            assert issubclass(model, GeneratedModel)

    def the_package_exports_the_useful_ones():
        assert types.FillPdfRequest is rest.FillPdfRequest
        assert types.CreateEtchPacketArgs is operations.CreateEtchPacketArgs
        assert types.EtchPacketArgs is operations.EtchPacketArgs


def describe_the_operation_argument_models():
    def they_have_the_schema_argument_names_as_aliases():
        args = operations.CreateEtchPacketArgs(
            name="x", webhook_url="https://example.com", merge_pdfs=True
        )
        assert args.model_dump(by_alias=True, exclude_none=True) == {
            "name": "x",
            "webhookURL": "https://example.com",
            "mergePDFs": True,
        }

    def they_require_the_required_arguments():
        with pytest.raises(ValidationError):
            operations.ForgeSubmitArgs(payload={})  # type: ignore[call-arg]
        assert operations.ForgeSubmitArgs(forge_eid="f", payload={}).forge_eid == "f"

    def they_type_input_objects_from_the_schema():
        args = operations.CreateEtchPacketArgs(files=[{"id": "f1", "castEid": "cast1"}])
        assert args.files is not None
        assert isinstance(args.files[0], graphql.EtchFile)
        assert args.model_dump(by_alias=True, exclude_none=True)["files"] == [
            {"id": "f1", "castEid": "cast1"}
        ]

    def they_rename_arguments_that_pydantic_uses():
        assert "schema_" in operations.CreateCastArgs.model_fields
        assert operations.CreateCastArgs.model_fields["schema_"].alias == "schema"

    @pytest.mark.parametrize(
        ("operation", "model"),
        [
            (
                mutations.create_etch_packet.generate_mutation(),
                operations.CreateEtchPacketArgs,
            ),
            (mutations.forge_submit.generate_mutation(), operations.ForgeSubmitArgs),
            (
                mutations.generate_etch_sign_url.generate_mutation(),
                operations.GenerateEtchSignURLArgs,
            ),
            (
                mutations.remove_weld_data.generate_mutation(),
                operations.RemoveWeldDataArgs,
            ),
            (queries.etch_packet.generate_query(), operations.EtchPacketArgs),
        ],
        ids=[
            "createEtchPacket",
            "forgeSubmit",
            "generateEtchSignURL",
            "removeWeldData",
            "etchPacket",
        ],
    )
    def the_client_operations_only_use_arguments_the_model_has(operation, model):
        variables = set(re.findall(r"\$(\w+):", operation))
        aliases = {field.alias or name for name, field in model.model_fields.items()}
        assert variables <= aliases


def describe_the_payload_models():
    def fill_pdf_payload_takes_every_fill_option():
        payload = FillPDFPayload(
            data={"a": 1}, font_size=10, use_interactive_fields=True, borderColor="#000"
        )
        assert isinstance(payload, rest.FillPdfRequest)
        assert payload.model_dump(by_alias=True, exclude_none=True) == {
            "data": {"a": 1},
            "fontSize": 10,
            "useInteractiveFields": True,
            "borderColor": "#000",
        }

    def fill_pdf_payload_still_rejects_empty_data():
        with pytest.raises(ValidationError):
            FillPDFPayload(data={})

    def etch_signer_takes_every_signer_option():
        signer = EtchSigner(
            name="Sally",
            email="sally@example.com",
            fields=[{"file_id": "f", "field_id": "sig"}],
            signer_type="embedded",
            signature_mode="draw",
            allow_name_change=True,
            redirect_url="https://example.com/done",
        )
        assert isinstance(signer, rest.EtchSigner)
        assert signer.model_dump(by_alias=True, exclude_none=True) == {
            "name": "Sally",
            "email": "sally@example.com",
            "fields": [{"fileId": "f", "fieldId": "sig"}],
            "signerType": "embedded",
            "signatureMode": "draw",
            "allowNameChange": True,
            "redirectURL": "https://example.com/done",
        }

    def etch_signer_passes_dates_through_as_strings():
        # A datetime object would not survive the JSON encoder, and a date with
        # no timezone must still be the API's call
        for value in ("2030-01-01T00:00:00Z", "2030-01-01T00:00:00"):
            signer = EtchSigner(
                name="S", email="s@example.com", fields=[], tokenValidUntil=value
            )
            dumped = signer.model_dump(by_alias=True, exclude_none=True)
            assert dumped["tokenValidUntil"] == value
            json.dumps(dumped)

    def payloads_keep_accepting_any_font_size_and_routing_order():
        assert (
            FillPDFPayload(data={"a": 1}, font_size=36).model_dump(by_alias=True)[
                "fontSize"
            ]
            == 36
        )
        signer = EtchSigner(name="S", email="s@example.com", fields=[], routing_order=0)
        assert signer.model_dump(by_alias=True, exclude_none=True)["routingOrder"] == 0

    def etch_signer_rejects_an_unknown_signer_type():
        with pytest.raises(ValidationError):
            EtchSigner(
                name="S", email="s@example.com", fields=[], signer_type="carrier pigeon"
            )

    def create_etch_packet_payload_is_the_mutation_arguments():
        payload = CreateEtchPacketPayload(
            name="Packet",
            signers=[],
            files=[],
            allow_updates=True,
            advanced_create=True,
        )
        assert isinstance(payload, operations.CreateEtchPacketArgs)
        assert payload.model_dump(by_alias=True, exclude_none=True) == {
            "name": "Packet",
            "signers": [],
            "files": [],
            "isDraft": False,
            "isTest": True,
            "allowUpdates": True,
            "advancedCreate": True,
        }

    def forge_submit_payload_is_the_mutation_arguments():
        payload = ForgeSubmitPayload(
            forge_eid="f", payload={"a": 1}, group_array_id="g"
        )
        assert isinstance(payload, operations.ForgeSubmitArgs)
        assert payload.model_dump(by_alias=True, exclude_none=True) == {
            "forgeEid": "f",
            "payload": {"a": 1},
            "isTest": True,
            "groupArrayId": "g",
        }


def describe_the_generated_files():
    def they_say_they_are_generated():
        for name in ("rest.py", "graphql.py", "operations.py"):
            source = (Path(types.__file__).parent / name).read_text()
            assert source.startswith("# Generated by dev/generate_types.py")
