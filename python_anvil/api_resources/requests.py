from python_anvil.http import HTTPClient


class AnvilRequest:
    show_headers = False
    _client: HTTPClient

    def get_url(self):
        raise NotImplementedError

    def _request(self, method, url, **kwargs):
        if not self._client:
            raise AssertionError(
                "Client has not been initialized. Please use the constructors "
                "provided by the other request implementations."
            )

        if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]:
            raise ValueError("Invalid HTTP method provided")

        full_url = "/".join([self.get_url(), url]) if len(url) > 0 else self.get_url()

        return self._client.request(method, full_url, **kwargs)

    def handle_error(self, response, status_code, headers):
        extra = None
        if self.show_headers:
            extra = headers

        if hasattr(response, "decode"):
            message = f"Error: {status_code}: {response.decode()} {extra}"
        else:
            message = f"Error: {status_code}: {response} {extra}"

        raise Exception(message)

    def process_response(self, response, status_code, headers, **kwargs):
        res = response
        if not 200 <= status_code < 300:
            self.handle_error(response, status_code, headers)

        debug = kwargs.pop("debug", False)

        # Include headers alongside the response.
        # This is useful for figuring out rate limits outside of this library's
        # scope and to manage waiting.
        include_headers = kwargs.pop("include_headers", False)
        if debug or include_headers:
            return {"response": res, "headers": headers}

        return res


class BaseAnvilHttpRequest(AnvilRequest):
    def __init__(self, client, options=None):
        self._client = client
        self._options = options

    def get_url(self):
        raise NotImplementedError

    def get(self, url, params=None, **kwargs):
        retry = kwargs.pop("retry", True)
        content, status_code, headers = self._request(
            "GET", url, params=params, retry=retry
        )
        return self.process_response(content, status_code, headers, **kwargs)

    def post(self, url, data=None, **kwargs):
        retry = kwargs.pop("retry", True)
        content, status_code, headers = self._request(
            "POST", url, json=data, retry=retry
        )
        return self.process_response(content, status_code, headers, **kwargs)


class GraphqlRequest(AnvilRequest):
    API_HOST = "https://graphql.useanvil.com"

    def __init__(self, client: HTTPClient):
        self._client = client

    def get_url(self):
        return f"{self.API_HOST}"

    def post(self, query, variables=None, **kwargs):
        return self.run_query("POST", query, variables=variables, **kwargs)

    def run_query(self, method, query, variables=None, **kwargs):
        data = {"query": query}
        if variables:
            data["variables"] = variables

        # Optional debug kwargs.
        # At this point, only the CLI will pass this in as a
        # "show me everything" sort of switch.
        debug = kwargs.pop("debug", False)
        include_headers = kwargs.pop("include_headers", False)

        content, status_code, headers = self._request(
            method,
            # URL blank here since graphql requests don't append to url
            '',
            # Queries need to be wrapped by curly braces(?) based on the
            # current API implementation.
            # The current library for graphql query generation doesn't do this(?)
            json=data,
            parse_json=True,
            **kwargs,
        )

        return self.process_response(
            content,
            status_code,
            headers,
            debug=debug,
            include_headers=include_headers,
            **kwargs,
        )


class RestRequest(BaseAnvilHttpRequest):
    API_HOST = "https://app.useanvil.com"
    API_BASE = "api"
    API_VERSION = "v1"

    def get_url(self):
        return f"{self.API_HOST}/{self.API_BASE}/{self.API_VERSION}"


class PlainRequest(BaseAnvilHttpRequest):
    API_HOST = "https://app.useanvil.com"
    API_BASE = "api"

    def get_url(self):
        return f"{self.API_HOST}/{self.API_BASE}"
