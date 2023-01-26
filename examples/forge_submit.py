import os

from python_anvil.api import Anvil
from python_anvil.api_resources.payload import ForgeSubmitPayload


API_KEY = os.environ.get("ANVIL_API_KEY")
# or set your own key here
# API_KEY = 'my-api-key'


def main():
    anvil = Anvil(api_key=API_KEY)

    # Your ForgeSubmit payload.
    # In this example, we have a basic Webform containing a name and email field.
    # For both fields, we are using the field's eid which can be found in the
    # weld or forge GraphQL query.
    # More info here: https://www.useanvil.com/docs/api/graphql/reference/#definition-Forge
    payload = ForgeSubmitPayload(
        forge_eid="myForgeEidHere",
        payload=dict(
            forge16401fc09c3e11ed85f5a91873b464b4="FirstName LastName",
            forge1b57aeb09c3e11ed85f5a91873b464b4="myemail@example.com",
        ),
    )

    # Submit the above payload
    res = anvil.forge_submit(payload)
    print(res)


if __name__ == '__main__':
    main()
