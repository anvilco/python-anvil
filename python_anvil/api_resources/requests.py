from python_anvil.http import HTTPClient


class AnvilRequest:
    show_headers = False

    def get_url(self):
        raise NotImplementedError

    def handle_error(self, response, status_code, headers):
        extra = None
        if self.show_headers:
            extra = headers

        if hasattr(response, 'decode'):
            message = f"Error: {status_code}: {response.decode()} {extra}"
        else:
            message = f"Error: {status_code}: {response} {extra}"

        raise Exception(message)

    def process_response(self, response, status_code, headers, **kwargs):
        res = response
        if not 200 <= status_code < 300:
            self.handle_error(response, status_code, headers)

        # Include headers alongside the response.
        # This is useful for figuring out rate limits outside of this library's
        # scope and to manage waiting.
        include_headers = kwargs.get('include_headers', False)
        if include_headers:
            return res, headers

        return res


class GraphqlRequest(AnvilRequest):
    API_HOST = "https://graphql.useanvil.com"

    def __init__(self, client: HTTPClient):
        self._client = client

    def get_url(self):
        return f"{self.API_HOST}"

    def post(self, query, variables=None):
        return self.run_query("POST", query, variables=variables)

    def run_query(self, method, query, variables=None, **kwargs):
        data = {"query": query}
        if variables:
            data["variables"] = variables

        content, status_code, headers = self._client.request(
            method,
            self.get_url(),
            # Queries need to be wrapped by curly braces(?) based on the
            # current API implementation.
            # The current library for graphql query generation doesn't do this(?)
            json=data,
            parse_json=True,
        )

        return self.process_response(content, status_code, headers, **kwargs)


class RestRequest(AnvilRequest):
    API_HOST = "https://app.useanvil.com"
    API_BASE = "api"
    API_VERSION = "v1"

    def __init__(self, client, options=None):
        self._client = client
        self._options = options

    def get_url(self):
        return f"{self.API_HOST}/{self.API_BASE}/{self.API_VERSION}"

    def get(self, url, params=None, **kwargs):
        content, status_code, headers = self._client.request(
            "GET", f"{self.get_url()}/{url}", params=params
        )
        return self.process_response(content, status_code, headers, **kwargs)

    def post(self, url, data=None, **kwargs):
        content, status_code, headers = self._client.request(
            "POST",
            f"{self.get_url()}/{url}",
            json=data,
        )
        return self.process_response(content, status_code, headers, **kwargs)


class PlainRequest(AnvilRequest):
    API_HOST = "https://app.useanvil.com"
    API_BASE = "api"

    def __init__(self, client, options=None):
        self._client = client
        self._options = options

    def get_url(self):
        return f"{self.API_HOST}/{self.API_BASE}"

    def get(self, url, params=None, **kwargs):
        content, status_code, headers = self._client.request(
            "GET", f"{self.get_url()}/{url}", params=params
        )
        return self.process_response(content, status_code, headers, **kwargs)

    def post(self, url, data=None, **kwargs):
        content, status_code, headers = self._client.request(
            "POST",
            f"{self.get_url()}/{url}",
            json=data,
        )
        return self.process_response(content, status_code, headers, **kwargs)
