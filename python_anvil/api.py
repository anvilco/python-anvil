from logging import getLogger
from typing import AnyStr, Dict, List, Optional, Union

from .api_resources.mutations import *
from .api_resources.payload import (
    CreateEtchPacketPayload,
    FillPDFPayload,
    GeneratePDFPayload,
)
from .api_resources.requests import GraphqlRequest, PlainRequest, RestRequest
from .http import HTTPClient
from .utils import remove_empty_items


logger = getLogger(__name__)


class Anvil:
    """Main Anvil API class.

    Handles all GraphQL and REST queries.

    Usage:
        >> anvil = Anvil(api_key="my_key")
        >> payload = {}
        >> pdf_data = anvil.fill_pdf("the_template_id", payload)
    """

    def __init__(self, api_key=None):
        self.client = HTTPClient(api_key=api_key)

    def query(self, query: str, variables: Optional[str] = None):
        gql = GraphqlRequest(client=self.client)
        return gql.post(query, variables=variables)

    def mutate(self, query: BaseQuery, variables: dict):
        gql = GraphqlRequest(client=self.client)
        return gql.post(query.get_mutation(), variables)

    def request_rest(self, options: Optional[dict] = None):
        api = RestRequest(self.client, options=options)
        return api

    def fill_pdf(self, template_id: str, payload: Union[dict, AnyStr]):
        """Fills an existing template with provided payload data.

        Use the casts graphql query to get a list of available templates you
        can use for this request.

        :param template_id: eid of an existing template/cast.
        :type template_id: str
        :param payload: payload in the form of a dict or JSON data
        :type payload: dict|str
        """
        data = None
        try:
            if isinstance(payload, dict):
                data = FillPDFPayload.from_dict(payload)
            elif isinstance(payload, str):
                data = FillPDFPayload.from_json(payload)
            elif isinstance(payload, FillPDFPayload):
                data = payload
            else:
                raise ValueError("`payload` must be a valid JSON string or a dict")
        except KeyError as e:
            raise ValueError(
                "`payload` validation failed. Please make sure all required "
                "fields are set. "
            )

        api = RestRequest(client=self.client)
        return api.post(
            f"fill/{template_id}.pdf",
            remove_empty_items(data.to_dict() if data else {}),
        )

    def generate_pdf(self, payload: Union[AnyStr, Dict]):
        if not payload:
            raise ValueError("`payload` must be a valid JSON string or a dict")

        if isinstance(payload, dict):
            data = GeneratePDFPayload.from_dict(payload)
        elif isinstance(payload, str):
            data = GeneratePDFPayload.from_json(payload)
        else:
            raise ValueError("`payload` must be a valid JSON string or a dict")

        # Any data errors would come from here..
        api = RestRequest(client=self.client)
        return api.post("generate-pdf", data=remove_empty_items(data.to_dict()))

    def get_cast(self, eid: str, fields=None):
        if not fields:
            # Use default fields
            fields = ['eid', 'title', 'fieldInfo']

        res = self.query(
            f"""{{
          cast(eid: "{eid}") {{
            {" ".join(fields)}
          }}
        }}"""
        )

        return res["data"]["cast"]

    def get_casts(self, fields=None) -> List:
        if not fields:
            # Use default fields
            fields = ['eid', 'title', 'fieldInfo']

        res = self.query(
            f"""{{
              currentUser {{
                organizations {{
                  casts {{
                    {" ".join(fields)}
                  }}
                }}
              }}
            }}"""
        )

        orgs = res["data"]["currentUser"]["organizations"]
        return [item for org in orgs for item in org["casts"]]

    def get_current_user(self):
        res = self.query(
            """{
              currentUser {
                name
                email
                eid
                role
                organizations {
                  eid
                  name
                  slug
                  casts {
                    eid
                    name
                  }
                }
              }
            }
            """
        )
        user = res["data"]["currentUser"]
        return user

    def get_welds(self) -> list:
        res = self.query(
            """{
              currentUser {
                organizations {
                  welds {
                    eid
                    slug
                    title
                  }
                }
              }
            }"""
        )
        orgs = res["data"]["currentUser"]["organizations"]
        return [item for org in orgs for item in org["welds"]]

    def get_queries(self):
        """
        Gets list of available queries.

        TODO: This is probably going to be removed in the near future
            (in the API).
        :return:
        """
        res = self.query(
            """{
              __schema {
                queryType {
                  fields {
                    name
                    description
                  }
                }
              }
            }"""
        )

        return res["data"]["__schema"]["queryType"]

    def create_etch_packet(
        self,
        payload: Optional[
            Union[dict, CreateEtchPacketPayload, CreateEtchPacket]
        ] = None,
        json=None,
    ):
        """Create etch packet via a graphql mutation."""
        # Create an etch packet payload instance excluding signers and files
        # (if any). We'll need to add those separately. below.
        if not any([payload, json]):
            raise TypeError('One of the arguments `payload` or `json` must exist')

        if json:
            payload = CreateEtchPacketPayload.from_json(json)

        if isinstance(payload, dict):
            mutation = CreateEtchPacket.create_from_dict(payload)
        elif isinstance(payload, CreateEtchPacketPayload):
            mutation = CreateEtchPacket(payload=payload)
        elif isinstance(payload, CreateEtchPacket):
            mutation = payload
        else:
            raise ValueError(
                "`payload` must be a valid CreateEtchPacket instance or dict"
            )

        return self.mutate(mutation, variables=mutation.create_payload().to_dict())

    def generate_etch_signing_url(self, signer_eid: str, client_user_id: str):
        """Generate a signing URL for a given user."""
        mutation = GenerateEtchSigningURL(
            signer_eid=signer_eid,
            client_user_id=client_user_id,
        )
        payload = mutation.create_payload()
        return self.mutate(mutation, variables=payload.to_dict())

    def download_documents(self, document_group_eid: str):
        """Retrieve all completed documents in zip form."""
        api = PlainRequest(client=self.client)
        return api.get(f"document-group/{document_group_eid}.zip")
