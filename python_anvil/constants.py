"""Basic constants used in the library."""

# GRAPHQL_ENDPOINT: str = "https://graphql.useanvil.com"
GRAPHQL_ENDPOINT: str = "http://localhost:3000/graphql"
REST_ENDPOINT = "https://app.useanvil.com/api/v1/"

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
