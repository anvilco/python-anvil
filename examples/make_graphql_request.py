# Send your own GraphQL queries with the Anvil API client.
# Reference: https://www.useanvil.com/docs/api/graphql/reference/
#
# Run this from the project root:
# ANVIL_API_KEY=YOUR_KEY python examples/make_graphql_request.py

import os

from python_anvil.api import Anvil


API_KEY = os.environ.get("ANVIL_API_KEY")
# or set your own key here
# API_KEY = 'my-api-key'


def call_current_user_query(anvil: Anvil) -> dict:
    """Get the user data attached to the current API key."""
    # `request_graphql` (or its alias `query`) takes the query as a string and
    # returns the response's `data`. It raises an `AnvilRequestError` if the
    # API returns any errors.
    res = anvil.request_graphql(
        """
        query CurrentUser {
            currentUser {
                eid
                name
                organizations {
                    eid
                    slug
                    name
                    casts { eid name }
                    welds { eid name }
                }
            }
        }
        """
    )
    return res["currentUser"]


def call_weld_query(anvil: Anvil, weld_eid: str) -> dict:
    """Call the weld query, an example of a query that takes variables."""
    res = anvil.request_graphql(
        """
        query WeldQuery($eid: String!) {
            weld(eid: $eid) {
                eid
                name
                forges { eid slug name }
            }
        }
        """,
        variables={"eid": weld_eid},
    )
    return res["weld"]


def call_queries():
    anvil = Anvil(api_key=API_KEY)
    current_user = call_current_user_query(anvil)

    first_weld = current_user["organizations"][0]["welds"][0]
    weld_data = call_weld_query(anvil, weld_eid=first_weld["eid"])

    print("currentUser: ", current_user)
    print("First weld details: ", weld_data)


if __name__ == "__main__":
    call_queries()
