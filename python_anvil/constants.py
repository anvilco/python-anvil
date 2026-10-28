"""Constants used throughout the library."""

# Where requests go unless the client is given another `base_url`
DEFAULT_BASE_URL = "https://app.useanvil.com"

# Version number to use for latest versions (usually drafts)
VERSION_LATEST = -1
# Version number to use for the latest published version.
# This is the default when a version is not provided.
VERSION_LATEST_PUBLISHED = -2

# What a REST request's data comes back as
DATA_TYPE_JSON = "json"
DATA_TYPE_BYTES = "bytes"
DATA_TYPE_STREAM = "stream"
DATA_TYPES = (DATA_TYPE_JSON, DATA_TYPE_BYTES, DATA_TYPE_STREAM)
BINARY_DATA_TYPES = (DATA_TYPE_BYTES, DATA_TYPE_STREAM)

# Until the first response says what the account's rate limit is, the client
# allows this many requests per interval
DEFAULT_REQUEST_LIMIT = 1
DEFAULT_REQUEST_LIMIT_MS = 1000

# Added to every wait for the rate limit, and to a 429's Retry-After, to allow
# for requests that were sent further apart than they arrive
RETRY_BUFFER_MS = 50
# How long to wait before retrying a 429 that has no usable Retry-After header,
# and the most a Retry-After header can make the client wait
DEFAULT_RETRY_AFTER_MS = 1000
MAX_RETRY_AFTER_MS = 60_000

# Seconds to wait for a connection, and then for each read, before giving up
DEFAULT_TIMEOUT = 300

# How many times to retry a request that failed with one of these statuses or
# couldn't connect, and the backoff before the first retry, doubled each time:
# 100ms, 200ms, 400ms, 800ms, 1.6s. The statuses and count are what gql's
# transport retried before 6.0.0. A request that was sent but got no complete
# response (a read timeout, a connection dropped mid-response) is not retried:
# the API may have processed it.
DEFAULT_MAX_RETRIES = 5
RETRY_STATUSES = (500, 502, 503, 504)
RETRY_BACKOFF_MS = 100
