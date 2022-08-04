from python_anvil.api import Anvil
from datetime import datetime
from python_anvil.api_resources.payload import ForgeSubmitPayload

API_KEY = 'my-api-key'


def main():
    # Use https://app.useanvil.com/org/YOUR_ORG_HERE/w/WORKFLOW_NAME/api
    # to get a detailed list and description of which fields, eids, etc.
    # are available to use.
    forge_eid = ""

    anvil = Anvil(api_key=API_KEY)

    # Create a payload with the payload model.
    payload = ForgeSubmitPayload(
        forge_eid=forge_eid, payload=dict(field1="Initial forgeSubmit")
    )

    res = anvil.forge_submit(payload=payload)

    data = res["data"]["forgeSubmit"]

    print(data)

    # Get submission and weld_data eids from the initial response
    submission_eid = data["eid"]
    weld_data_eid = data["weldData"]["eid"]

    payload = ForgeSubmitPayload(
        forge_eid=forge_eid,
        # If submission and weld_data eids are provided, you will be _editing_
        # an existing submission.
        submission_eid=submission_eid,
        weld_data_eid=weld_data_eid,
        # NOTE: If using a development key, this will `is_test` will always
        # be `True` even if it's set as `False` here.
        is_test=False,
        payload=dict(
            field1=f"Edited this field {datetime.now()}",
        ),
    )

    res = anvil.forge_submit(payload=payload)

    data = res["data"]["forgeSubmit"]
    print(data)


if __name__ == "__main__":
    main()
