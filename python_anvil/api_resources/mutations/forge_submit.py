from typing import AnyStr, Dict, Text

from python_anvil.api_resources.mutations.base import BaseQuery
from python_anvil.api_resources.payload import ForgeSubmitPayload


DEFAULT_RESPONSE_QUERY = """
{
  id
  eid
  payloadValue
  currentStep
  completedAt
  createdAt
  updatedAt
  signer {
    name
    email
    status
    routingOrder
  }
  weldData {
    id
    eid
    isTest
    isComplete
    agents
  }
}
"""

# NOTE: Since the below will be used as a formatted string (this also applies
#   to f-strings) any literal curly braces need to be doubled, else they'll be
#   interpreted as string replacement tokens.
FORGE_SUBMIT = """
mutation ForgeSubmit(
    $forgeEid: String!,
    $weldDataEid: String,
    $submissionEid: String,
    $payload: JSON!,
    $currentStep: Int,
    $complete: Boolean,
    $isTest: Boolean,
    $timezone: String,
    $groupArrayId: String,
    $groupArrayIndex: Int,
    $errorType: String,
) {{
    forgeSubmit (
        forgeEid: $forgeEid,
        weldDataEid: $weldDataEid,
        submissionEid: $submissionEid,
        payload: $payload,
        currentStep: $currentStep,
        complete: $complete,
        isTest: $isTest,
        timezone: $timezone,
        groupArrayId: $groupArrayId,
        groupArrayIndex: $groupArrayIndex,
        errorType: $errorType
    ) {query}
}}
"""


class ForgeSubmit(BaseQuery):
    mutation = FORGE_SUBMIT
    mutation_res_query = DEFAULT_RESPONSE_QUERY

    def __init__(self, forge_eid: Text, payload: Dict[Text, Text]):
        self.forge_eid = forge_eid
        self.payload = payload

    @classmethod
    def create_from_json(cls, json: AnyStr):
        # Parse the data through the model class to validate and pass it back
        # as variables in this class.
        data = ForgeSubmitPayload.parse_raw(json, content_type="application/json")
        return cls(**data.dict())

    def create_payload(self):
        return ForgeSubmitPayload(forge_eid=self.forge_eid, payload=self.payload)
