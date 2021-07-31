# 0.3.0 (2021-07-31)

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