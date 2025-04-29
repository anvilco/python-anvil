"""Basic constants used in the library."""

GRAPHQL_ENDPOINT: str = "https://graphql.useanvil.com"
REST_ENDPOINT = "https://app.useanvil.com/api/v1"
ANVIL_HOST = "https://app.useanvil.com"

VALID_HOSTS = [
    ANVIL_HOST,
    REST_ENDPOINT,
    GRAPHQL_ENDPOINT,
]

RETRIES_LIMIT = 5
REQUESTS_LIMIT = {
    "dev": {
        "calls": 2,
        "seconds": 1,
    },
    "prod": {
        "calls": 40,
        "seconds": 1,
    },
}

RATELIMIT_ENV = "dev"
