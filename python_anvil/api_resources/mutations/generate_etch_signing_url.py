from python_anvil.api_resources.mutations.base import BaseQuery
from python_anvil.api_resources.payload import GenerateEtchSigningURLPayload


class GenerateEtchSigningURL(BaseQuery):
    """Query class to handle retrieving a signing URL."""

    mutation = """
        mutation ($signerEid: String!, $clientUserId: String!) {
            generateEtchSignURL (signerEid: $signerEid, clientUserId: $clientUserId)
        }
    """

    def __init__(self, signer_eid: str, client_user_id: str):
        self.signer_eid = signer_eid
        self.client_user_id = client_user_id

    def create_payload(self):
        return GenerateEtchSigningURLPayload(
            signer_eid=self.signer_eid, client_user_id=self.client_user_id
        )
