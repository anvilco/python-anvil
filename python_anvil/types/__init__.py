"""Types generated from the Anvil API's OpenAPI spec and GraphQL schema.

The Python counterpart of `@anvilco/types`: pydantic models, regenerated
from the API with `make update-schema generate`.

- `python_anvil.types.rest`: the REST API's request bodies, like
  `FillPdfRequest` and `GenerateMarkdownPdfRequest`.
- `python_anvil.types.graphql`: every type in the GraphQL schema, by name:
  objects like `EtchPacket` and inputs like `EtchFile`.
- `python_anvil.types.operations`: the arguments of every query and
  mutation, like `CreateEtchPacketArgs` and `ForgeSubmitArgs`.

Field names are snake_case with camelCase aliases, and either works when
constructing a model. `model_dump(by_alias=True, exclude_none=True)` gives
the camelCase JSON the API wants. The client's own payload models in
`python_anvil.api_resources.payload` extend these.

The named request models and the schema's types are stable names. The REST
module also has models for the spec's unnamed nested objects, like `Fields1`
and `Data2`, named by position; those can change when the spec does.
"""

from python_anvil.types import graphql, operations, rest
from python_anvil.types._base import GeneratedModel
from python_anvil.types.operations import (
    CreateEtchPacketArgs,
    EtchPacketArgs,
    ForgeSubmitArgs,
    GenerateEtchSignURLArgs,
    RemoveWeldDataArgs,
)
from python_anvil.types.rest import (
    EtchFinishPageOptions,
    EtchSignaturePageOptions,
    FillPdfRequest,
    GenerateHtmlPdfRequest,
    GenerateMarkdownPdfRequest,
    PageOptions,
)


__all__ = [
    "CreateEtchPacketArgs",
    "EtchFinishPageOptions",
    "EtchPacketArgs",
    "EtchSignaturePageOptions",
    "FillPdfRequest",
    "ForgeSubmitArgs",
    "GenerateEtchSignURLArgs",
    "GenerateHtmlPdfRequest",
    "GenerateMarkdownPdfRequest",
    "GeneratedModel",
    "PageOptions",
    "RemoveWeldDataArgs",
    "graphql",
    "operations",
    "rest",
]
