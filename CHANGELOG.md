# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- BREAKING: Drop support for Python 3.8 and 3.9, which are end of life. The minimum supported version is now Python 3.10.
- Add support for Python 3.14 and 3.15 ([#95](https://github.com/anvilco/python-anvil/issues/95)).
- BREAKING: The `anvil` command line tool's dependencies, `click` and `tabulate`, are now the `cli` extra: `pip install 'python-anvil[cli]'` ([#96](https://github.com/anvilco/python-anvil/issues/96)). Importing `python_anvil` no longer imports the CLI.
- BREAKING: One `requests`-based transport replaces `gql` for GraphQL and the `ratelimit` decorators for REST. Both dependencies are dropped.
  - `Anvil(api_key, base_url=...)` sends every request to one host: REST to `{base_url}/api/...`, GraphQL to `{base_url}/graphql`. `base_url` defaults to production. The `endpoint_url` argument is removed, and `environment` does nothing: the rate limits now come from the API.
  - OAuth access tokens are supported: `Anvil(access_token=...)`. JWTs are sent as-is, other tokens base64 encoded, like node-anvil.
  - Rate limits are learned from the first response's `X-RateLimit-Limit` and `X-RateLimit-Interval-Ms` headers. Requests made before that response arrives wait for it. The client counts requests over a sliding window, like the API, and only waits when the limit has been reached. A `429` is retried after its `Retry-After` plus 50ms, for as long as it takes. The `retry` option is removed.
  - API errors raise `AnvilRequestError`, with the normalized `errors` (GraphQL errors, REST errors and validation errors with their `fields`), the `status_code`, the `headers` and any partial `data`. The REST methods used to raise a bare `Exception`; GraphQL methods raised `gql`'s errors. `AnvilRequestException` and `AnvilException` remain as aliases.
  - Methods return the data: the PDF or zip `bytes` for `fill_pdf`, `generate_pdf` and `download_documents`, and the response's `data` dict for the GraphQL methods. The `include_headers` and `debug` options are removed; the headers are on `AnvilRequestError`.
  - `data_type="stream"` on the binary methods returns the `requests.Response`, to stream a large PDF or zip.
  - Requests time out after 5 minutes by default (`timeout`). They never did before.
  - A `requests.Session` can be passed in (`session`), e.g. to use a proxy, and `user_agent`, `request_limit` and `request_limit_ms` match node-anvil's options.
- BREAKING: `request_rest` now sends a request, `request_rest("POST", "/api/v1/...", json=...)`, like node-anvil's `requestREST`. The `RestRequest`, `PlainRequest`, `GraphqlRequest` and `FullyQualifiedRequest` classes and `request_fully_qualified` are removed.
- BREAKING: `generate_etch_signing_url` returns the URL. `get_etch_packet` returns the packet, and `remove_weld_data` whether the data was removed.
- BREAKING: `query` and `mutate` take the operation as a string; `gql` documents and its DSL are gone. `request_graphql` is the same thing with node-anvil's name.
- BREAKING: `get_casts` and `get_welds` query the API's paginated `casts` and `welds` fields, which the old queries no longer matched, and return up to 500 per organization. `get_current_user` no longer selects each organization's casts.
- Add `get_etch_packet` and `remove_weld_data`, and `response_query` and `mutation` options on `create_etch_packet`, `forge_submit` and `get_etch_packet`, matching node-anvil.
- Add `Anvil.prepare_graphql_file` (also `python_anvil.prepare_graphql_file`) for multipart uploads of a path, bytes or a file object, anywhere in a mutation's variables. Files given as open file objects used to be base64 encoded into the JSON; they still are unless prepared this way.
- The `createEtchPacket` mutation gains `organizationEid` and `allowUpdates`, and the mutations and default response fields now match node-anvil's exactly.
- The client's queries and mutations are checked against the API schema in CI, and `make update-schema` refreshes the schema from the published `@anvilco/types` package.
- Add `test-client.py`, which runs every method against a real environment: `ANVIL_API_KEY=... make test-client`.
- Add `python_anvil.types`: pydantic models generated from the API's OpenAPI spec and GraphQL schema, the Python counterpart of `@anvilco/types`. `types.rest` has the REST request bodies, `types.graphql` every type in the schema, and `types.operations` the arguments of every query and mutation, like `CreateEtchPacketArgs`. The client's payload models extend them, so `FillPDFPayload`, `EtchSigner`, `CreateEtchPacketPayload` and `ForgeSubmitPayload` now accept every option the API has, and reject misspelled enum values. `ForgeSubmitPayload.webhook_url` is a plain `str` now, not an `HttpUrl`.
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
