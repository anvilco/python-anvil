# 1.0.0 (2021-10-08)

- **[BREAKING CHANGE]** `dataclasses-json` library removed and replaced
  with [pydantic](https://github.com/samuelcolvin/pydantic/).
  This should not affect any users who only use the CLI and API methods, but if you are using any models directly
  from `api_resources/payload.py`, you will likely need to update all usages. Please
  see [pydantic's docs](https://pydantic-docs.helpmanual.io/usage/models/) for more details.
- **[BREAKING CHANGE]** Increased minimum required Python version to 3.6.2.
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
