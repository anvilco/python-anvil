GRAPHQL_ENDPOINT = "https://graphql.useanvil.com"
REST_ENDPOINT = "https://app.useanvil.com/api/v1/"

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
