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
