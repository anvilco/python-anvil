import os
from gql.dsl import DSLQuery, dsl_gql

from python_anvil.api import Anvil
from python_anvil.http import get_gql_ds


API_KEY = os.environ.get("ANVIL_API_KEY")
# or set your own key here
# API_KEY = 'my-api-key'


def call_current_user_query(anvil: Anvil) -> dict:
    """Get the user data attached to the current API key.

    :param anvil:
    :type anvil: Anvil
    :return:
    """
    # See the reference docs for examples of all queries and mutations:
    # https://www.useanvil.com/docs/api/graphql/reference/
    # pylint: disable=unused-variable
    user_query = """
        query CurrentUser {
          currentUser {
            eid
            name
            organizations {
              eid
              slug
              name
              casts {
                eid
                name
              }
              welds {
                eid
                name
              }
            }
          }
        }
    """

    # You can also use `gql`'s query builder. Below is the equivalent of the
    # string above, but can potentially be a better interface if you're
    # building a query in multiple steps. See the official `gql` docs for more
    # details: https://gql.readthedocs.io/en/stable/advanced/dsl_module.html

    # Use `ds` to create your queries
    ds = get_gql_ds(anvil.gql_client)
    ds_user_query_builder = ds.Query.currentUser.select(
        ds.User.eid,
        ds.User.name,
        ds.User.organizations.select(
            ds.Organization.eid,
            ds.Organization.slug,
            ds.Organization.name,
            ds.Organization.casts.select(
                ds.Cast.eid,
                ds.Cast.name,
            ),
            ds.Organization.welds.select(
                ds.Weld.eid,
                ds.Weld.name,
            ),
        ),
    )

    ds_query = dsl_gql(DSLQuery(ds_user_query_builder))

    res = anvil.query(query=ds_query, variables=None)
    return res["currentUser"]


def call_weld_query(anvil: Anvil, weld_eid: str):
    """Call the weld query.

    The weld() query is an example of a query that takes variables.
    :param anvil:
    :type anvil: Anvil
    :param weld_eid:
    :type weld_eid: str
    :return:
    """

    # pylint: disable=unused-variable
    weld_query = """
        query WeldQuery (
          $eid: String,
        ) {
          weld (
            eid: $eid,
          ) {
            eid
            name
            forges {
              eid
              slug
              name
            }
          }
        }
    """
    variables = {"eid": weld_eid}

    # You can also use `gql`'s query builder. Below is the equivalent of the
    # string above, but can potentially be a better interface if you're
    # building a query in multiple steps. See the official `gql` docs for more
    # details: https://gql.readthedocs.io/en/stable/advanced/dsl_module.html

    # Use `ds` to create your queries
    ds = get_gql_ds(anvil.gql_client)
    ds_weld_query_builder = ds.Query.weld.args(eid=weld_eid).select(
        ds.Weld.eid,
        ds.Weld.name,
        ds.Weld.forges.select(
            ds.Forge.eid,
            ds.Forge.slug,
            ds.Forge.name,
        ),
    )

    ds_query = dsl_gql(DSLQuery(ds_weld_query_builder))

    # You can call the query with the string literal and variables like usual
    # res = anvil.query(query=weld_query, variables=variables)

    # Or, use only the `dsl_gql` query. `variables` not needed as it was
    # already used in `.args()`.
    res = anvil.query(query=ds_query)
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
