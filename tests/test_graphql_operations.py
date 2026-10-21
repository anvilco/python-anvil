"""The client's queries and mutations must match the API schema.

The schema is the one @anvilco/types ships, refreshed with `make update-schema`.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest
from graphql import GraphQLSchema, build_schema, parse, validate

from python_anvil import Anvil
from python_anvil.api_resources.mutations import (
    CreateEtchPacket,
    ForgeSubmit,
    GenerateEtchSigningURL,
)
from python_anvil.graphql import mutations, queries


SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "anvil_schema.graphql"


@pytest.fixture(scope="module")
def schema() -> GraphQLSchema:
    return build_schema(SCHEMA_PATH.read_text())


def assert_valid(schema: GraphQLSchema, document: str) -> None:
    errors = validate(schema, parse(document))
    assert not errors, "\n".join(error.message for error in errors)


def describe_the_operations_module():
    @pytest.mark.parametrize(
        "operation",
        [
            queries.etch_packet.generate_query(),
            mutations.create_etch_packet.generate_mutation(),
            mutations.forge_submit.generate_mutation(),
            mutations.generate_etch_sign_url.generate_mutation(),
            mutations.remove_weld_data.generate_mutation(),
        ],
        ids=[
            "etchPacket",
            "createEtchPacket",
            "forgeSubmit",
            "generateEtchSignURL",
            "removeWeldData",
        ],
    )
    def it_matches_the_schema(schema, operation):
        assert_valid(schema, operation)

    def it_accepts_a_response_query(schema):
        assert_valid(schema, queries.etch_packet.generate_query("{ eid name }"))
        assert_valid(schema, mutations.create_etch_packet.generate_mutation("{ eid }"))
        assert_valid(schema, mutations.forge_submit.generate_mutation("{ eid }"))


def describe_the_mutation_builders():
    def it_uses_the_shared_mutations(schema):
        assert (
            CreateEtchPacket(name="x").get_mutation()
            == mutations.create_etch_packet.generate_mutation()
        )
        assert (
            ForgeSubmit({}, forge_eid="x").get_mutation()
            == mutations.forge_submit.generate_mutation()
        )
        assert (
            GenerateEtchSigningURL("s", "c").get_mutation()
            == mutations.generate_etch_sign_url.generate_mutation()
        )
        assert_valid(schema, CreateEtchPacket(name="x").get_mutation("{ eid status }"))


def describe_the_convenience_queries():
    @pytest.fixture
    def sent():
        """Every query the client's convenience methods send, by calling them with the transport mocked."""
        client = Anvil("key")
        documents: list[str] = []

        def capture(query, variables=None, **kwargs):
            documents.append(query)
            return {
                "currentUser": {
                    "organizations": [{"casts": {"items": []}, "welds": {"items": []}}]
                },
                "cast": {},
                "weld": {},
            }

        with mock.patch.object(client, "request_graphql", side_effect=capture):
            client.get_current_user()
            client.get_cast("cast123")
            client.get_cast(
                "cast123",
                fields=["eid", "name"],
                cast_args=[("versionNumber", "-1")],
            )
            client.get_casts()
            client.get_casts(show_all=True)
            client.get_welds()
            client.get_weld("weld123")
        return documents

    def it_matches_the_schema(schema, sent):
        assert len(sent) == 7
        for document in sent:
            assert_valid(schema, document)
