from __future__ import annotations

from python_anvil.api_resources.mutations.base import BaseQuery
from python_anvil.api_resources.payload import GenerateEtchSigningURLPayload
from python_anvil.graphql.mutations.generate_etch_sign_url import generate_mutation


class GenerateEtchSigningURL(BaseQuery):
    """Builds a `generateEtchSignURL` mutation and its variables."""

    def __init__(self, signer_eid: str, client_user_id: str):
        self.signer_eid = signer_eid
        self.client_user_id = client_user_id

    def get_mutation(self, response_query: str | None = None) -> str:
        return generate_mutation()

    def create_payload(self) -> GenerateEtchSigningURLPayload:
        return GenerateEtchSigningURLPayload(
            signer_eid=self.signer_eid, client_user_id=self.client_user_id
        )
