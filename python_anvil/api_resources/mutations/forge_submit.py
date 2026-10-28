from typing import Any

from python_anvil.api_resources.mutations.base import BaseQuery
from python_anvil.api_resources.mutations.helpers import get_payload_attrs
from python_anvil.api_resources.payload import ForgeSubmitPayload
from python_anvil.graphql.mutations.forge_submit import (
    DEFAULT_RESPONSE_QUERY,
    generate_mutation,
)


class ForgeSubmit(BaseQuery):
    """Builds a `forgeSubmit` mutation and its variables."""

    default_response_query = DEFAULT_RESPONSE_QUERY

    def get_mutation(self, response_query: str | None = None) -> str:
        return generate_mutation(self.response_fields(response_query))

    def __init__(
        self,
        payload: dict[str, Any] | ForgeSubmitPayload,
        forge_eid: str | None = None,
        weld_data_eid: str | None = None,
        submission_eid: str | None = None,
        is_test: bool | None = None,
        **kwargs,
    ):
        """
        Create a forgeSubmit query.

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
    def create_from_dict(cls, payload: dict[str, Any]):
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
