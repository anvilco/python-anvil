from typing import Any, Dict, Optional, Text, Union

from python_anvil.api_resources.mutations.base import BaseQuery
from python_anvil.api_resources.mutations.helpers import get_payload_attrs
from python_anvil.api_resources.payload import ForgeSubmitPayload


DEFAULT_RESPONSE_QUERY = """
{
  id
  eid
  status
  resolvedPayload
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
    status
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

    def __init__(
        self,
        payload: Union[Dict[Text, Any], ForgeSubmitPayload],
        forge_eid: Optional[Text] = None,
        weld_data_eid: Optional[Text] = None,
        submission_eid: Optional[Text] = None,
        is_test: Optional[bool] = None,
        **kwargs,
    ):
        """
        :param forge_eid:
        :param payload:
        :param weld_data_eid:
        :param submission_eid:
        :param is_test:
        :param kwargs: kwargs may contain other fields defined in
              `ForgeSubmitPayload` if not explicitly in the `__init__` args.
        """
        if not forge_eid and not isinstance(payload, ForgeSubmitPayload):
            raise ValueError(
                "`forge_eid` is required if `payload` is not a "
                "`ForgeSubmitPayload` instance"
            )

        self.payload = payload
        self.forge_eid = forge_eid
        self.weld_data_eid = weld_data_eid
        self.submission_eid = submission_eid
        self.is_test = is_test

        # Get other attrs from the model and set on the instance
        model_attrs = get_payload_attrs(ForgeSubmitPayload)
        for attr in model_attrs:
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])

    @classmethod
    def create_from_dict(cls, payload: Dict[Text, Any]):
        # Parse the data through the model class to validate and pass it back
        # as variables in this class.
        return cls(**payload)

    def create_payload(self):
        # If provided a payload and no forge_eid, we'll assume that it's the
        # full thing. Return that instead.
        if not self.forge_eid and self.payload:
            return self.payload

        model_attrs = get_payload_attrs(ForgeSubmitPayload)

        for_payload = {}
        for attr in model_attrs:
            obj = getattr(self, attr, None)
            if obj is not None:
                for_payload[attr] = obj

        return ForgeSubmitPayload(**for_payload)
