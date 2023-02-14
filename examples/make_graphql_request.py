import os

from python_anvil.api import Anvil

API_KEY = os.environ.get("ANVIL_API_KEY")


def call_current_user_query(anvil: Anvil) -> dict:
    """
    Gets the user data attached to the current API key.
    :param anvil:
    :type anvil: Anvil
    :return:
    """
    # See the reference docs for examples of all queries and mutations:
    # https://www.useanvil.com/docs/api/graphql/reference/
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
    res = anvil.query(query=user_query, variables=None)
    return res["currentUser"]


def call_weld_query(anvil: Anvil, weld_eid: str):
    """
    Call the weld query.
    The weld() query is an example of a query that takes variables.
    :param anvil:
    :type anvil: Anvil
    :param weld_eid:
    :type weld_eid: str
    :return:
    """
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
    res = anvil.query(query=weld_query, variables=variables)
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
