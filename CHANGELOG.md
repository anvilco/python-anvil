# 5.0.3 (2025-02-24)

- Package import now uses `importlib.metadata` to get the version and throws `PackageNotFoundError` if the package is not
  installed.

# 5.0.2 (2025-01-14)

- `gql` requirement is now `3.6.0b2`

# 5.0.1 (2025-01-06)

- Python requirement is now `>= 3.8.0,<3.13`.
- Updated `pylint` to `^3.0` in support of the above.

# 5.0.0 (2024-12-27)

- **[BREAKING CHANGE]** Python requirement is now `>= 3.8.0,<3.12`.
- Unpegged `urllib3`.
- Utilizing pydantic v2 syntax and best practices.
- Improves file handling with `FileCompatibleBaseModel` (Thanks @cyrusradfar!)

# 4.0.0 (2024-07-23)

- Updated `pydantic` package dependency to `v2`, but still using `v1` internally.
- **[BREAKING CHANGE]** Python requirement is now `>= 3.8.0`, up from `>= 3.7.2`.

# 3.0.1 (2023-06-28)

- Fixed issue with `requests_toolbelt` (`gql` dependency) using an incompatible version of `urllib3`.
  This caused an error of `ImportError: cannot import name 'appengine'` to be thrown.

# 3.0.0 (2023-02-17)

- **[BREAKING CHANGE]** [`graphql-python/gql`](https://github.com/graphql-python/gql) is now the main GraphQL client
  implementation. All functions should still work the same as before. If there are any issues please let us know
  in `python-anvil` GitHub issues.
- Updated examples to reflect new GraphQL implementation and added `examples/make_graphql_request.py` example.

# 2.0.0 (2023-01-26)

- **[BREAKING CHANGE]** Minimum required Python version updated to `>=3.7.2`

# 1.9.0 (2023-01-26)

- Clearer version number support
- Add additional variables for `CreateEtchPacket` mutation
- Add missing `webhookURL` variable in `ForgeSubmit` mutation
- Add `forgeSubmit` example

# 1.8.0 (2023-01-10)

- Added support for multipart uploads on `CreateEtchPacket` requests.
- New example for multipart uploads in `examples/create_etch_upload_file_multipart.py`
- Added environment variable usage in all `examples/` files for easier usage.
- Updated a few minor development packages.

# 1.7.0 (2022-09-09)

- Added support for `version_number` in PDF Fill requests.

# 1.6.0 (2022-09-07)

- Added support for HTML/CSS and Markdown in `CreateEtchPacket`. [See examples here](https://www.useanvil.com/docs/api/e-signatures#generating-a-pdf-from-html-and-css).

# 1.5.0 (2022-08-05)

- Added support for `ForgeSubmit` mutation.

# 1.4.1 (2022-05-11)

- Updated `mkdocs` dependency to fix issue with Read the Docs.

# 1.4.0 (2022-05-10)

- Updated a number of packages to fix linter and pre-commit issues
- Added support for `CreateEtchPacket.merge_pdfs`.

# 1.3.1 (2022-03-18)

- Updated `click` package dependency to `^8.0`
- Update other minor dependencies. [See full list here](https://github.com/anvilco/python-anvil/pull/31).

# 1.3.0 (2022-03-04)

- Fixed optional field `CreateEtchPacket.signature_email_subject` being required. This is now truly optional.
- Added support for `CreateEtchPacket.signature_email_body`.
- Added support for `CreateEtchPacket.replyToName` and `CreateEtchPacket.replyToEmail` which customizes the "Reply-To"
  header in Etch packet emails.

# 1.2.1 (2022-01-03)

- Fixed issue with Etch packet `is_test` and `is_draft` options not properly applying to the final GraphQL mutation when
  using `CreateEtchPacket.create_payload`.

# 1.2.0 (2021-12-15)

- Added `py.typed` for better mypy support.
- Updated a number of dev dependencies.

# 1.1.0 (2021-11-15)

- Added support for `webhook_url` on Etch packets. Please see the `CreateEtchPacketPayload` class
  and [Anvil API docs](https://www.useanvil.com/docs/api/e-signatures#webhook-notifications) for more info.
- Better support for extra (unsupported) fields in all models. Previously fields not defined in models would be
  stripped, or would raise a runtime error. Additional fields will no longer be stripped and will be used in JSON
  payloads as you may expect. Note that, though this is now supported, the Anvil API will return an error for any
  unsupported fields.
- Updated documentation.

# 1.0.0 (2021-10-14)

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

# 0.3.0 (2021-08-03)

- Fixed API ratelimit not being set correctly
- Added support for setting API key environment which sets different API rate limits
- Added support for `--include-headers` in all API methods which includes HTTP response headers in function returns
- Added support for `--retry` in all API methods which enables/disables automatic retries
- Added support for `--debug` flag in CLI which outputs headers from HTTP responses

# 0.2.0 (2021-05-05)

- Added support for HTML to PDF on `generate_pdf`

# 0.1.1 (2021-02-16)

- Fixed for REST API calls failing

# 0.1.0 (2021-01-30)

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
