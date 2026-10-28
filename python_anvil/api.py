"""The Anvil API client."""

from __future__ import annotations

import json as json_lib
import logging
import warnings
from collections.abc import Mapping
from typing import Any, TypeVar

import requests
from pydantic import BaseModel

from python_anvil.api_resources.mutations import (
    BaseQuery,
    CreateEtchPacket,
    ForgeSubmit,
    GenerateEtchSigningURL,
)
from python_anvil.api_resources.payload import (
    CreateEtchPacketPayload,
    FillPDFPayload,
    ForgeSubmitPayload,
    GeneratePDFPayload,
)
from python_anvil.constants import (
    BINARY_DATA_TYPES,
    DATA_TYPE_BYTES,
    DATA_TYPE_JSON,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_REQUEST_LIMIT_MS,
    DEFAULT_TIMEOUT,
    VERSION_LATEST,
    VERSION_LATEST_PUBLISHED,
)
from python_anvil.graphql import mutations, queries
from python_anvil.http import HTTPClient, process_response
from python_anvil.upload import (
    MultipartRequest,
    UploadWithOptions,
    prepare_graphql_file,
    validate_upload_schema,
)


logger = logging.getLogger(__name__)

# The most casts or welds the API returns per page
PAGE_LIMIT = 500

PayloadModel = TypeVar("PayloadModel", bound=BaseModel)


class Anvil:
    """The Anvil API client.

    Handles all GraphQL and REST requests: authentication, rate limits,
    retries and errors.

    Usage:
        >>> anvil = Anvil(api_key="my_key")
        >>> pdf_bytes = anvil.fill_pdf("the_template_id", {"data": {...}})

    Every method raises an `AnvilRequestError` when the API responds with an
    error, and a `requests` exception when a request can't be made at all.

    :param api_key: Your API key, from your organization's settings.
    :param access_token: An OAuth access token, instead of an API key. If both
        are given, the access token is used.
    :param base_url: Where to send requests. Defaults to production,
        `https://app.useanvil.com`. REST requests go to `{base_url}/api/...`
        and GraphQL requests to `{base_url}/graphql`.
    :param user_agent: Sent as the User-Agent header. Defaults to
        `python-anvil/<version>`.
    :param request_limit: How many requests to allow per `request_limit_ms`
        until the first response from the API tells the client your actual
        limits. Defaults to 1 per second.
    :param request_limit_ms: See `request_limit`.
    :param timeout: Seconds to wait for a connection, and then for each read,
        before a request fails. A `(connect, read)` tuple is also accepted.
        Defaults to 5 minutes; `None` waits forever.
    :param max_retries: How many times to retry a request that got a 500,
        502, 503 or 504, or that couldn't connect, with exponential backoff
        from 100ms. Defaults to 5; `0` disables retries. Mutations are
        retried too, as they were before 6.0.0. A request that was sent but
        got no complete response, like a read timeout, is not retried, since
        the API may have processed it.
    :param session: A `requests.Session` to send requests with, e.g. one
        configured with a proxy. Defaults to a session of the client's own.

    Every client in the process with the same `base_url` and credentials
    shares one rate limiter, and so the limits the API taught it. The
    starting `request_limit` only applies to the first of them.
    """

    # Version number to use for latest versions (usually drafts)
    VERSION_LATEST = VERSION_LATEST
    # Version number to use for the latest published version.
    # This is the default when a version is not provided.
    VERSION_LATEST_PUBLISHED = VERSION_LATEST_PUBLISHED

    def __init__(
        self,
        api_key: str | None = None,
        environment: str | None = None,
        *,
        access_token: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        user_agent: str | None = None,
        request_limit: int = DEFAULT_REQUEST_LIMIT,
        request_limit_ms: int = DEFAULT_REQUEST_LIMIT_MS,
        timeout: float | tuple[float, float] | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        session: requests.Session | None = None,
        endpoint_url: str | None = None,
    ):
        if endpoint_url is not None:
            raise TypeError(
                "`endpoint_url` was removed in 6.0.0. Pass `base_url` instead, "
                "e.g. base_url='https://staging.useanvil.com': GraphQL requests "
                "go to {base_url}/graphql."
            )
        if environment is not None:
            warnings.warn(
                "`environment` does nothing since 6.0.0 and will be removed: the "
                "rate limits now come from the API's responses.",
                DeprecationWarning,
                stacklevel=2,
            )
        if not (api_key or access_token):
            raise ValueError("`api_key` or `access_token` is required")

        self.client = HTTPClient(
            api_key,
            access_token,
            base_url=base_url,
            user_agent=user_agent,
            request_limit=request_limit,
            request_limit_ms=request_limit_ms,
            timeout=timeout,
            max_retries=max_retries,
            session=session,
        )

    @property
    def base_url(self) -> str:
        return self.client.base_url

    # Class methods

    @staticmethod
    def prepare_graphql_file(
        path_or_file: Any,
        *,
        filename: str | None = None,
        mimetype: str | None = None,
        ignore_filename_validation: bool = False,
    ) -> UploadWithOptions:
        """Prepare a file for a GraphQL multipart upload. See `python_anvil.upload.prepare_graphql_file`."""
        return prepare_graphql_file(
            path_or_file,
            filename=filename,
            mimetype=mimetype,
            ignore_filename_validation=ignore_filename_validation,
        )

    # REST

    def request_rest(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
        data_type: str = DATA_TYPE_JSON,
        timeout: float | tuple[float, float] | None = None,
    ) -> Any:
        """Send a REST request. For endpoints without a method of their own.

        :param method: The HTTP method, e.g. `"POST"`.
        :param path: The path from the base URL, e.g. `/api/v1/fill/abc.pdf`.
            A full URL on the base URL is accepted too.
        :param json: A JSON body.
        :param params: Query string parameters.
        :param data: A raw body, e.g. bytes or a file object, instead of `json`.
        :param headers: Extra headers.
        :param data_type: What to return: `"json"` (the default) for the parsed
            JSON, `"bytes"` for the raw body, or `"stream"` for the
            `requests.Response` itself, to stream a large body with
            `iter_content`. Close it when done, or use it as a context manager.
        :param timeout: Overrides the client's timeout for this request.
        """
        response = self.client.request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            stream=data_type == "stream",
            timeout=timeout,
        )
        return process_response(response, data_type)

    def fill_pdf(
        self,
        template_id: str,
        payload: dict | str | bytes | FillPDFPayload,
        *,
        version_number: int | None = None,
        data_type: str = DATA_TYPE_BYTES,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Fill a PDF template with your data. Returns the PDF.

        :param template_id: The eid of the PDF template (cast) to fill.
        :param payload: The fill data: a dict, a JSON string or a `FillPDFPayload`.
            Keys may be snake_case (`font_size`) or camelCase (`fontSize`).
        :param version_number: The template version to fill. By default, the
            latest published version. `Anvil.VERSION_LATEST` fills the most
            recent version, published or not.
        :param data_type: `"bytes"` (the default) or `"stream"`. See `request_rest`.
        :param params: Extra query string parameters.
        """
        data = _parse_payload(payload, FillPDFPayload)
        _check_binary_data_type(data_type)

        query: dict[str, Any] = dict(params or {})
        if version_number is not None:
            query["versionNumber"] = version_number

        return self.request_rest(
            "POST",
            f"/api/v1/fill/{template_id}.pdf",
            json=data.model_dump(by_alias=True, exclude_none=True),
            params=query or None,
            data_type=data_type,
        )

    def generate_pdf(
        self,
        payload: dict | str | bytes | GeneratePDFPayload,
        *,
        data_type: str = DATA_TYPE_BYTES,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Generate a PDF from Markdown or HTML. Returns the PDF.

        :param payload: A dict, a JSON string or a `GeneratePDFPayload`. Markdown
            by default; pass `type: "html"` with `data: {"html": ..., "css": ...}`
            for HTML.
        :param data_type: `"bytes"` (the default) or `"stream"`. See `request_rest`.
        :param params: Extra query string parameters.
        """
        if not payload:
            raise ValueError("`payload` must be a valid JSON string or a dict")
        data = _parse_payload(payload, GeneratePDFPayload)
        _check_binary_data_type(data_type)

        return self.request_rest(
            "POST",
            "/api/v1/generate-pdf",
            json=data.model_dump(by_alias=True, exclude_none=True),
            params=params,
            data_type=data_type,
        )

    def download_documents(
        self, document_group_eid: str, *, data_type: str = DATA_TYPE_BYTES
    ) -> Any:
        """Download the documents of an Etch packet's document group as a zip file.

        :param document_group_eid: The document group's eid, from
            `create_etch_packet` or `get_etch_packet`.
        :param data_type: `"bytes"` (the default) or `"stream"`. See `request_rest`.
        """
        _check_binary_data_type(data_type)
        return self.request_rest(
            "GET",
            f"/api/document-group/{document_group_eid}.zip",
            data_type=data_type,
        )

    # GraphQL

    def request_graphql(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
        *,
        timeout: float | tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        """Send a GraphQL query or mutation. For operations without a method of their own.

        Returns the response's `data`. Files anywhere in `variables` are sent
        as a multipart upload: see `prepare_graphql_file`.

        See the GraphQL reference for every query and mutation:
        https://www.useanvil.com/docs/api/graphql/reference/
        """
        operations = {"query": query, "variables": dict(variables or {})}

        # Checks for both file uploads and base64 uploads
        if not validate_upload_schema(operations["variables"]):
            raise ValueError(
                "Invalid file schema detected: files must be under a `file` key"
            )

        multipart = MultipartRequest(operations)
        try:
            if multipart:
                response = self.client.request(
                    "POST", "/graphql", files=multipart.build, timeout=timeout
                )
            else:
                response = self.client.request(
                    "POST", "/graphql", json=operations, timeout=timeout
                )
        finally:
            multipart.close()

        body = process_response(response, DATA_TYPE_JSON)
        if not isinstance(body, Mapping) or "data" not in body:
            raise ValueError(f"Unexpected GraphQL response: {body!r}")
        return body["data"] or {}

    def query(
        self, query: str, variables: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a GraphQL query. The same as `request_graphql`."""
        return self.request_graphql(query, variables)

    def mutate(
        self, query: str | BaseQuery, variables: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a GraphQL mutation, as a string or a mutation class. The same as `request_graphql`."""
        mutation = query if isinstance(query, str) else query.get_mutation()
        return self.request_graphql(mutation, variables)

    def create_etch_packet(
        self,
        payload: dict | CreateEtchPacketPayload | CreateEtchPacket | None = None,
        json: str | bytes | None = None,
        *,
        response_query: str | None = None,
        mutation: str | None = None,
    ) -> dict[str, Any]:
        """Create an Etch e-sign packet, and send it to the first signer unless it's a draft.

        Returns the response's `data`, with the packet under `createEtchPacket`.

        :param payload: A `CreateEtchPacket` builder, a `CreateEtchPacketPayload`,
            or a dict of the mutation's variables (snake_case or camelCase).
            Files to upload can be base64 dicts or prepared with
            `prepare_graphql_file`.
        :param json: The variables as a JSON string, instead of `payload`.
        :param response_query: The fields to select on the created packet,
            instead of the defaults.
        :param mutation: Your own `createEtchPacket` mutation, with its response
            fields, instead of the client's. `response_query` is then ignored.
        """
        if payload is None and json is None:
            raise TypeError("One of the arguments `payload` or `json` must exist")

        if json is not None:
            payload = CreateEtchPacketPayload.model_validate_json(json)

        if isinstance(payload, dict):
            builder = CreateEtchPacket.create_from_dict(payload)
        elif isinstance(payload, CreateEtchPacketPayload):
            builder = CreateEtchPacket(payload=payload)
        elif isinstance(payload, CreateEtchPacket):
            builder = payload
        else:
            raise ValueError(
                "`payload` must be a valid CreateEtchPacket instance or dict"
            )

        variables = builder.create_payload().model_dump(
            by_alias=True, exclude_none=True
        )
        return self.request_graphql(
            mutation or builder.get_mutation(response_query), variables
        )

    def get_etch_packet(
        self, eid: str, *, response_query: str | None = None
    ) -> dict[str, Any]:
        """Get an Etch packet's details and status. Returns the packet.

        :param eid: The packet's eid.
        :param response_query: The fields to select, instead of the defaults.
        """
        data = self.request_graphql(
            queries.etch_packet.generate_query(response_query), {"eid": eid}
        )
        return data["etchPacket"]

    def generate_etch_signing_url(self, signer_eid: str, client_user_id: str) -> str:
        """Generate the URL an embedded signer signs at. Returns the URL.

        The packet must have been sent, and the signer must be an `embedded` signer.

        :param signer_eid: The signer's eid, from the packet's `documentGroup.signers`.
        :param client_user_id: Your ID for the user who will sign.
        """
        mutation = GenerateEtchSigningURL(
            signer_eid=signer_eid, client_user_id=client_user_id
        )
        data = self.request_graphql(
            mutation.get_mutation(), mutation.create_payload().model_dump(by_alias=True)
        )
        return data["generateEtchSignURL"]

    generate_etch_sign_url = generate_etch_signing_url

    def forge_submit(
        self,
        payload: dict | ForgeSubmitPayload | None = None,
        json: str | bytes | None = None,
        *,
        response_query: str | None = None,
        mutation: str | None = None,
    ) -> dict[str, Any]:
        """Submit data to a webform (forge) in a workflow (weld). Returns the response's `data`.

        :param payload: A `ForgeSubmitPayload` or a dict of the mutation's
            variables (snake_case or camelCase). `forge_eid` and `payload` are
            required; `weld_data_eid` and `submission_eid` update a submission.
        :param json: The variables as a JSON string, instead of `payload`.
        :param response_query: The fields to select on the submission, instead
            of the defaults.
        :param mutation: Your own `forgeSubmit` mutation, instead of the client's.
        """
        if payload is None and json is None:
            raise TypeError("One of arguments `json` or `payload` are required")

        if json is not None:
            payload = ForgeSubmitPayload.model_validate_json(json)

        if isinstance(payload, dict):
            builder = ForgeSubmit.create_from_dict(payload)
        elif isinstance(payload, ForgeSubmitPayload):
            builder = ForgeSubmit(payload=payload)
        else:
            raise ValueError(
                "`payload` must be a valid ForgeSubmitPayload instance or dict"
            )

        variables = builder.create_payload().model_dump(
            by_alias=True, exclude_none=True
        )
        return self.request_graphql(
            mutation or builder.get_mutation(response_query), variables
        )

    def remove_weld_data(self, eid: str, *, mutation: str | None = None) -> bool:
        """Remove a workflow submission's data (a weld data). Returns whether it was removed.

        :param eid: The weld data's eid, from `forge_submit`'s `weldData`.
        :param mutation: Your own `removeWeldData` mutation, instead of the client's.
        """
        data = self.request_graphql(
            mutation or mutations.remove_weld_data.generate_mutation(), {"eid": eid}
        )
        return bool(data["removeWeldData"])

    # Convenience queries

    def get_current_user(self) -> dict[str, Any]:
        """The user the API key belongs to, with their organizations."""
        data = self.request_graphql(
            """{
              currentUser {
                name
                email
                eid
                role
                organizations {
                  eid
                  name
                  slug
                }
              }
            }"""
        )
        return data["currentUser"]

    def get_cast(
        self,
        eid: str,
        fields: list[str] | None = None,
        version_number: int | None = None,
        cast_args: list[tuple[str, str]] | None = None,
    ) -> dict[str, Any]:
        """A PDF template (cast). By default its `eid`, `title` and `fieldInfo`.

        :param eid: The cast's eid.
        :param fields: The fields to select, instead of the defaults.
        :param version_number: A specific version. By default, the latest
            published version.
        :param cast_args: Extra arguments for the `cast` query, as
            `(name, value)` pairs with the value in GraphQL syntax.
        """
        fields = fields or ["eid", "title", "fieldInfo"]
        args = list(cast_args or [])
        args.append(("eid", json_lib.dumps(eid)))
        if version_number is not None:
            args.append(("versionNumber", str(version_number)))

        arg_str = ", ".join(f"{name}: {value}" for name, value in args)
        data = self.request_graphql(
            f"""{{
              cast({arg_str}) {{
                {" ".join(fields)}
              }}
            }}"""
        )
        return data["cast"]

    def get_casts(
        self, fields: list[str] | None = None, show_all: bool = False
    ) -> list[dict[str, Any]]:
        """The PDF templates (casts) in every organization of the current user.

        Up to 500 per organization.

        :param fields: The fields to select, instead of `eid`, `title` and `fieldInfo`.
        :param show_all: Include casts that aren't templates.
        """
        fields = fields or ["eid", "title", "fieldInfo"]
        is_template = "null" if show_all else "true"

        data = self.request_graphql(
            f"""{{
              currentUser {{
                organizations {{
                  casts(isTemplate: {is_template}, limit: {PAGE_LIMIT}) {{
                    items {{
                      {" ".join(fields)}
                    }}
                  }}
                }}
              }}
            }}"""
        )
        return [
            cast
            for org in data["currentUser"]["organizations"]
            for cast in org["casts"]["items"]
        ]

    def get_welds(self) -> list[dict[str, Any]]:
        """The workflows (welds) in every organization of the current user, with their webforms (forges).

        Up to 500 per organization.
        """
        data = self.request_graphql(
            f"""{{
              currentUser {{
                organizations {{
                  welds(limit: {PAGE_LIMIT}) {{
                    items {{
                      eid
                      slug
                      name
                      forges {{
                        eid
                        name
                      }}
                    }}
                  }}
                }}
              }}
            }}"""
        )
        return [
            weld
            for org in data["currentUser"]["organizations"]
            for weld in org["welds"]["items"]
        ]

    def get_weld(self, eid: str) -> dict[str, Any]:
        """A workflow (weld), with its webforms (forges)."""
        data = self.request_graphql(
            """
            query WeldQuery($eid: String!) {
                weld(eid: $eid) {
                    eid
                    slug
                    name
                    forges {
                        eid
                        name
                        slug
                    }
                }
            }""",
            {"eid": eid},
        )
        return data["weld"]

    def close(self) -> None:
        """Close the client's HTTP session."""
        self.client.close()

    def __enter__(self) -> Anvil:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _parse_payload(payload: Any, model: type[PayloadModel]) -> PayloadModel:
    """Validate a dict, JSON string or model instance as `model`."""
    if isinstance(payload, model):
        return payload
    if isinstance(payload, dict):
        return model(**payload)
    if isinstance(payload, (str, bytes)):
        return model.model_validate_json(payload)
    raise ValueError(
        f"`payload` must be a dict, a JSON string or a {model.__name__}, not {type(payload).__name__}"
    )


def _check_binary_data_type(data_type: str) -> None:
    if data_type not in BINARY_DATA_TYPES:
        raise ValueError(f"data_type must be one of: {'|'.join(BINARY_DATA_TYPES)}")
