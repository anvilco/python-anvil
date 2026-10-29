# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v6.0.1] - 2026-10-29

- `query`, `mutate` and `request_graphql` given a `gql` document raise a `TypeError` that says to pass the query string, instead of `Object of type DocumentNode is not JSON serializable`.

## [v6.0.0] - 2026-10-28

- BREAKING: Drop support for Python 3.8 and 3.9, which are end of life. The minimum supported version is now Python 3.10.
- Add support for Python 3.14 and 3.15 ([#95](https://github.com/anvilco/python-anvil/issues/95)).
- BREAKING: The `anvil` command line tool's dependencies, `click` and `tabulate`, are now the `cli` extra: `pip install 'python-anvil[cli]'` ([#96](https://github.com/anvilco/python-anvil/issues/96)). Importing `python_anvil` no longer imports the CLI.
- BREAKING: One `requests`-based transport replaces `gql` for GraphQL and the `ratelimit` decorators for REST. Both dependencies are dropped.
  - `Anvil(api_key, base_url=...)` sends every request to one host: REST to `{base_url}/api/...`, GraphQL to `{base_url}/graphql`. `base_url` defaults to production. The `endpoint_url` argument is removed, and `environment` does nothing: the rate limits now come from the API.
  - OAuth access tokens are supported: `Anvil(access_token=...)`. JWTs are sent as-is, other tokens base64 encoded, like node-anvil.
  - Rate limits are learned from the first response that carries the `X-RateLimit-Limit` and `X-RateLimit-Interval-Ms` headers. Requests made before the first response arrives wait for it. The client counts requests over a sliding window, like the API, and only waits when the limit has been reached. A request counts from when it is sent until an interval after its response arrives, so the API, which counts from when the request reached it, never sees more in its window than the client allowed. Every client in the process with the same `base_url` and credentials shares one limiter, and so the limits the API taught it; the starting `request_limit` only applies to the first of them. A `429` is retried after its `Retry-After` plus 50ms, or after a second when there is no usable `Retry-After`, for as long as it takes. The `retry` option is removed.
  - Every request, REST included, is retried on `500`, `502`, `503` and `504`, and when it couldn't connect, up to `max_retries` times (5) with exponential backoff from 100ms, the statuses and count `gql`'s transport retried for GraphQL requests before. Mutations are retried too, as before. A request that was sent but got no complete response, like a read timeout, is not retried, since the API may have processed it; `gql` retried those too. `max_retries=0` turns it off.
  - API errors raise `AnvilRequestError`, with the normalized `errors` (GraphQL errors, REST errors and validation errors with their `fields`), the `status_code`, the `headers` and any partial `data`. An error is any status outside 2xx, or a 2xx GraphQL response with `errors`; a non-JSON error, like a `502` from a proxy, keeps the start of its body. The REST methods used to raise a bare `Exception`; GraphQL methods raised `gql`'s errors. `AnvilRequestException` and `AnvilException` remain as aliases, and still accept a plain message, but their base class is now `Exception` rather than `BaseException`, so `except Exception` catches them.
  - Methods return the data: the PDF or zip `bytes` for `fill_pdf`, `generate_pdf` and `download_documents`, and the response's `data` dict for the GraphQL methods. A JSON response to a binary method, like `fill_pdf` with `outputFormat: "url"`, is returned parsed. The `include_headers`, `debug` and `retry` keyword arguments are removed and now raise `TypeError`, as do the `gql` options `query` and `mutate` used to pass through; the headers are on `AnvilRequestError`.
  - `data_type="stream"` on the binary methods returns the `requests.Response`, to stream a large PDF or zip.
  - Requests time out after 5 minutes by default (`timeout`). They never did before.
  - A `requests.Session` can be passed in (`session`), e.g. to use a proxy, and `user_agent`, `request_limit` and `request_limit_ms` match node-anvil's options.
- BREAKING: `request_rest` now sends a request, `request_rest("POST", "/api/v1/...", json=...)`, like node-anvil's `requestREST`. A full URL is accepted if it is on the client's `base_url`, and refused otherwise. The `python_anvil.api_resources.requests` module with `RestRequest`, `PlainRequest`, `GraphqlRequest` and `FullyQualifiedRequest`, and `request_fully_qualified`, are removed.
- BREAKING: Removed with `gql`: `python_anvil.http.GQLClient`, `get_local_schema` and `get_gql_ds`, `Anvil.gql_client`, and `HTTPClient`'s old signature and `(content, status_code, headers)` return. `python_anvil.constants` loses `GRAPHQL_ENDPOINT`, `REST_ENDPOINT`, `ANVIL_HOST`, `VALID_HOSTS`, `RETRIES_LIMIT`, `REQUESTS_LIMIT` and `RATELIMIT_ENV`; `DEFAULT_BASE_URL` is the one host now. The mutation builders' `mutation` template attribute is gone (pass `mutation=` to the method instead); `mutation_res_query` still selects a builder's default response fields.
- BREAKING: `generate_etch_signing_url` returns the URL. `get_etch_packet` returns the packet, and `remove_weld_data` whether the data was removed.
- BREAKING: `query` and `mutate` take the operation as a string; `gql` documents and its DSL are gone. `request_graphql` is the same thing with node-anvil's name.
- BREAKING: `get_casts` and `get_welds` query the API's paginated `casts` and `welds` fields, which the old queries no longer matched, and return up to 500 per organization. `get_current_user` no longer selects each organization's casts.
- Add `get_etch_packet` and `remove_weld_data`, and `response_query` and `mutation` options on `create_etch_packet`, `forge_submit` and `get_etch_packet`, matching node-anvil.
- Add `Anvil.prepare_graphql_file` (also `python_anvil.prepare_graphql_file`) for multipart uploads of a path, bytes or a file object, anywhere in a mutation's variables. Files given as open file objects used to be base64 encoded into the JSON; they still are unless prepared this way.
- The `createEtchPacket` mutation gains `organizationEid` and `allowUpdates`, and the mutations and default response fields now match node-anvil's exactly. `forgeSubmit`'s default fields drop `resolvedPayload` and `weldData.status`, and gain `continueURL` and `payloadValue`; pass `response_query` to select others.
- `forge_submit` with a `webhook_url` works. `ForgeSubmitPayload.webhook_url` was a pydantic `HttpUrl`, which the JSON encoder rejected, so it failed before sending; it is a `str` now.
- `fill_pdf` sends `version_number=0` (it used to drop it), and `generate_etch_signing_url` is also available as `generate_etch_sign_url`.
- `Anvil()` with no key reads `ANVIL_API_KEY` from the environment, the way the examples and the CLI do. The client keeps `api_key` and `access_token` as attributes.
- Every method takes a `timeout` keyword argument, overriding the client's timeout for that request.
- `create_etch_packet` and `forge_submit` take the payload as a JSON string too, like `fill_pdf` and `generate_pdf`, and their dicts may hold any kind of file (a template reference, Markdown, HTML or an upload) or model instances, with snake_case or camelCase keys. `query` and `mutate` take `variables` as a JSON string. A `response_query` may be given with or without braces. An `in-person` signer is accepted. An uploaded open file is sent under its own filename rather than `document.pdf`.
- `GeneratePDFPayload` extends the generated request type like the other payload models, so `page`, `logo`, `include_timestamp` and `output_format` are typed. `utils.camel_to_snake` keeps acronyms whole now (`webhookURL` -> `webhook_url`; it gave `webhook_u_r_l`). The CLI's `cast` and `weld` without an eid exit with a usage error (code 2) instead of a traceback. `CREATE_ETCH_PACKET` and `FORGE_SUBMIT` are still exported from the builder modules; a `BaseQuery` subclass with its own `mutation` template still works.
- The client's queries and mutations are checked against the API schema in CI, and `make update-schema` refreshes the schema from the published `@anvilco/types` package.
- Add `test-client.py`, which runs every method against a real environment: `ANVIL_API_KEY=... make test-client`.
- Add `python_anvil.types`: pydantic models generated from the API's OpenAPI spec and GraphQL schema, the Python counterpart of `@anvilco/types`. `types.rest` has the REST request bodies, `types.graphql` every type in the schema, and `types.operations` the arguments of every query and mutation, like `CreateEtchPacketArgs`. The client's payload models extend them, so `FillPDFPayload`, `EtchSigner`, `CreateEtchPacketPayload` and `ForgeSubmitPayload` now accept every option the API has. BREAKING: they also validate those options the way the API documents them: an enum value the API doesn't accept (like `signature_mode="wave"`), or a number out of its documented range (like `token_valid_for_minutes` above a day), is a `ValidationError` before anything is sent, where 5.x passed it through for the API to reject. `font_size` and `routing_order` keep accepting any value, as they did. `ForgeSubmitPayload.webhook_url` is a plain `str` now, not an `HttpUrl`.
- The README now documents every method, option and error, and the `docs/` folder and mkdocs are gone. CONTRIBUTING.md covers development, the integration test script, the generated types and publishing.
- A Sync API Types workflow refreshes `schema/` and regenerates `python_anvil/types` after each production deploy, opening a PR when anything changed. `make update-schema generate` does the same by hand.

## [v5.0.3] - 2025-02-24

- Package import now uses `importlib.metadata` to get the version and throws `PackageNotFoundError` if the package is not
  installed.

## [v5.0.2] - 2025-01-14

- `gql` requirement is now `3.6.0b2`

## [v5.0.1] - 2025-01-06

- Python requirement is now `>= 3.8.0,<3.13`.
- Updated `pylint` to `^3.0` in support of the above.

## [v5.0.0] - 2024-12-27

- **[BREAKING CHANGE]** Python requirement is now `>= 3.8.0,<3.12`.
- Unpegged `urllib3`.
- Utilizing pydantic v2 syntax and best practices.
- Improves file handling with `FileCompatibleBaseModel` (Thanks @cyrusradfar!)

## [v4.0.0] - 2024-07-23

- Updated `pydantic` package dependency to `v2`, but still using `v1` internally.
- **[BREAKING CHANGE]** Python requirement is now `>= 3.8.0`, up from `>= 3.7.2`.

## [v3.0.1] - 2023-06-28

- Fixed issue with `requests_toolbelt` (`gql` dependency) using an incompatible version of `urllib3`.
  This caused an error of `ImportError: cannot import name 'appengine'` to be thrown.

## [v3.0.0] - 2023-02-17

- **[BREAKING CHANGE]** [`graphql-python/gql`](https://github.com/graphql-python/gql) is now the main GraphQL client
  implementation. All functions should still work the same as before. If there are any issues please let us know
  in `python-anvil` GitHub issues.
- Updated examples to reflect new GraphQL implementation and added `examples/make_graphql_request.py` example.

## [v2.0.0] - 2023-01-26

- **[BREAKING CHANGE]** Minimum required Python version updated to `>=3.7.2`

## [v1.9.0] - 2023-01-26

- Clearer version number support
- Add additional variables for `CreateEtchPacket` mutation
- Add missing `webhookURL` variable in `ForgeSubmit` mutation
- Add `forgeSubmit` example

## [v1.8.0] - 2023-01-10

- Added support for multipart uploads on `CreateEtchPacket` requests.
- New example for multipart uploads in `examples/create_etch_upload_file_multipart.py`
- Added environment variable usage in all `examples/` files for easier usage.
- Updated a few minor development packages.

## [v1.7.0] - 2022-09-09

- Added support for `version_number` in PDF Fill requests.

## [v1.6.0] - 2022-09-07

- Added support for HTML/CSS and Markdown in `CreateEtchPacket`. [See examples here](https://www.useanvil.com/docs/api/e-signatures#generating-a-pdf-from-html-and-css).

## [v1.5.0] - 2022-08-05

- Added support for `ForgeSubmit` mutation.

## [v1.4.1] - 2022-05-11

- Updated `mkdocs` dependency to fix issue with Read the Docs.

## [v1.4.0] - 2022-05-10

- Updated a number of packages to fix linter and pre-commit issues
- Added support for `CreateEtchPacket.merge_pdfs`.

## [v1.3.1] - 2022-03-18

- Updated `click` package dependency to `^8.0`
- Update other minor dependencies. [See full list here](https://github.com/anvilco/python-anvil/pull/31).

## [v1.3.0] - 2022-03-04

- Fixed optional field `CreateEtchPacket.signature_email_subject` being required. This is now truly optional.
- Added support for `CreateEtchPacket.signature_email_body`.
- Added support for `CreateEtchPacket.replyToName` and `CreateEtchPacket.replyToEmail` which customizes the "Reply-To"
  header in Etch packet emails.

## [v1.2.1] - 2022-01-03

- Fixed issue with Etch packet `is_test` and `is_draft` options not properly applying to the final GraphQL mutation when
  using `CreateEtchPacket.create_payload`.

## [v1.2.0] - 2021-12-15

- Added `py.typed` for better mypy support.
- Updated a number of dev dependencies.

## [v1.1.0] - 2021-11-15

- Added support for `webhook_url` on Etch packets. Please see the `CreateEtchPacketPayload` class
  and [Anvil API docs](https://www.useanvil.com/docs/api/e-signatures#webhook-notifications) for more info.
- Better support for extra (unsupported) fields in all models. Previously fields not defined in models would be
  stripped, or would raise a runtime error. Additional fields will no longer be stripped and will be used in JSON
  payloads as you may expect. Note that, though this is now supported, the Anvil API will return an error for any
  unsupported fields.
- Updated documentation.

## [v1.0.0] - 2021-10-14

- **[BREAKING CHANGE]** `dataclasses-json` library removed and replaced
  with [pydantic](https://github.com/samuelcolvin/pydantic/).
  This should not affect any users who only use the CLI and API methods, but if you are using any models directly
  from `api_resources/payload.py`, you will likely need to update all usages. Please
  see [pydantic's docs](https://pydantic-docs.helpmanual.io/usage/models/) for more details.
- **[BREAKING CHANGE]** Increased minimum required Python version to 3.6.2.
- Updated `EtchSigner` model to be more in sync with new official documentation.
  See `create_etch_existing_cast.py` file for examples and `api_resources/payload.py` for `EtchSigner` changes.
- Updated CLI command `anvil cast --list` to only return casts that are templates.
  Use `anvil cast --all` if you'd like the previous behavior.
- Updated a number of dependencies, the vast majority being dev-dependencies.

## [v0.3.0] - 2021-08-03

- Fixed API ratelimit not being set correctly
- Added support for setting API key environment which sets different API rate limits
- Added support for `--include-headers` in all API methods which includes HTTP response headers in function returns
- Added support for `--retry` in all API methods which enables/disables automatic retries
- Added support for `--debug` flag in CLI which outputs headers from HTTP responses

## [v0.2.0] - 2021-05-05

- Added support for HTML to PDF on `generate_pdf`

## [v0.1.1] - 2021-02-16

- Fixed for REST API calls failing

## [v0.1.0] - 2021-01-30

#### Initial public release

- Added GraphQL queries
  - Raw queries
  - casts
  - etchPackets
  - currentUser
  - availableQueries
  - welds
  - weldData
- Added GraphQL mutations
  - TODO: sendEtchPacket
  - createEtchPacket
  - generateEtchSignURL
- Added other requests
  - Fill PDF
  - Generate PDF
  - Download Documents
