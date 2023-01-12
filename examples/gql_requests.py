import os
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport
from requests.auth import HTTPBasicAuth
from aiohttp import BasicAuth

API_KEY = os.environ.get("ANVIL_API_KEY")

HOST = "http://localhost:3000/graphql"


def get_cast(eid, fields):
    query = gql(
        f"""
    query {{
        cast (eid: "{eid}") {{
            {" ".join(fields)}
        }}
    }}
    """
    )

    return query


def get_casts(fields=None, show_all=True):
    if not fields:
        # Use default fields
        fields = ["eid", "title", "fieldInfo"]

    cast_args = "" if show_all else "(isTemplate: true)"

    query = gql(
        f"""{{
      currentUser {{
        organizations {{
          casts {cast_args} {{
            {" ".join(fields)}
          }}
        }}
      }}
    }}"""
    )

    return query


def get_aiohttp_transport():
    auth = BasicAuth(login=API_KEY, password="")
    return AIOHTTPTransport(url=HOST, auth=auth)


def get_requests_transport():
    auth = HTTPBasicAuth(username=API_KEY, password="")
    return RequestsHTTPTransport(url=HOST, auth=auth)


def main():
    # transport = get_requests_transport()
    transport = get_aiohttp_transport()
    client = Client(transport=transport, fetch_schema_from_transport=True)

    eid = "xDBz9Vk0i3grDZJwgm0y"
    fields = ['eid', 'title', 'fieldInfo']

    result = client.execute(get_cast(eid=eid, fields=fields))
    print(result)


if __name__ == "__main__":
    main()
