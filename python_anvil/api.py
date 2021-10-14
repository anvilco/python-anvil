from logging import getLogger
from typing import AnyStr, Callable, Dict, List, Optional, Tuple, Union

from .api_resources.mutations import *
from .api_resources.payload import (
    CreateEtchPacketPayload,
    FillPDFPayload,
    GeneratePDFPayload,
)
from .api_resources.requests import GraphqlRequest, PlainRequest, RestRequest
from .http import HTTPClient


logger = getLogger(__name__)


def _get_return(res: Dict, get_data: Callable[[Dict], Union[Dict, List]]):
    """Process response and get data from path if provided."""
    _res = res
    if "response" in res and "headers" in res:
        _res = res["response"]
        return {"response": get_data(_res), "headers": res["headers"]}
    return get_data(_res)


class Anvil:
    """Main Anvil API class.

    Handles all GraphQL and REST queries.

    Usage:
        >> anvil = Anvil(api_key="my_key")
        >> payload = {}
        >> pdf_data = anvil.fill_pdf("the_template_id", payload)
    """

    def __init__(self, api_key=None, environment='dev'):
        self.client = HTTPClient(api_key=api_key, environment=environment)

    def query(self, query: str, variables: Optional[str] = None, **kwargs):
        gql = GraphqlRequest(client=self.client)
        return gql.post(query, variables=variables, **kwargs)

    def mutate(self, query: BaseQuery, variables: dict, **kwargs):
        gql = GraphqlRequest(client=self.client)
        return gql.post(query.get_mutation(), variables, **kwargs)

    def request_rest(self, options: Optional[dict] = None):
        api = RestRequest(self.client, options=options)
        return api

    def fill_pdf(
        self, template_id: str, payload: Union[dict, AnyStr, FillPDFPayload], **kwargs
    ):
        """Fill an existing template with provided payload data.

        Use the casts graphql query to get a list of available templates you
        can use for this request.

        :param template_id: eid of an existing template/cast.
        :type template_id: str
        :param payload: payload in the form of a dict or JSON data
        :type payload: dict|str
        """
        try:
            if isinstance(payload, dict):
                data = FillPDFPayload(**payload)
            elif isinstance(payload, str):
                data = FillPDFPayload.parse_raw(
                    payload, content_type="application/json"
                )
            elif isinstance(payload, FillPDFPayload):
                data = payload
            else:
                raise ValueError("`payload` must be a valid JSON string or a dict")
        except KeyError as e:
            logger.exception(e)
            raise ValueError(
                "`payload` validation failed. Please make sure all required "
                "fields are set. "
            ) from e

        api = RestRequest(client=self.client)
        return api.post(
            f"fill/{template_id}.pdf",
            data.dict(by_alias=True, exclude_none=True) if data else {},
            **kwargs,
        )

    def generate_pdf(self, payload: Union[AnyStr, Dict], **kwargs):
        if not payload:
            raise ValueError("`payload` must be a valid JSON string or a dict")

        if isinstance(payload, dict):
            data = GeneratePDFPayload(**payload)
        elif isinstance(payload, str):
            data = GeneratePDFPayload.parse_raw(
                payload, content_type="application/json"
            )
        else:
            raise ValueError("`payload` must be a valid JSON string or a dict")

        # Any data errors would come from here..
        api = RestRequest(client=self.client)
        return api.post(
            "generate-pdf", data=data.dict(by_alias=True, exclude_none=True), **kwargs
        )

    def get_cast(self, eid: str, fields=None, **kwargs):
        if not fields:
            # Use default fields
            fields = ['eid', 'title', 'fieldInfo']

        res = self.query(
            f"""{{
              cast(eid: "{eid}") {{
                {" ".join(fields)}
              }}
            }}""",
            **kwargs,
        )

        def get_data(r):
            return r["data"]["cast"]

        return _get_return(res, get_data=get_data)

    def get_casts(
        self, fields=None, show_all=False, **kwargs
    ) -> Union[List, Tuple[List, Dict]]:
        if not fields:
            # Use default fields
            fields = ["eid", "title", "fieldInfo"]

        cast_args = "" if show_all else "(isTemplate: true)"

        res = self.query(
            f"""{{
              currentUser {{
                organizations {{
                  casts {cast_args} {{
                    {" ".join(fields)}
                  }}
                }}
              }}
            }}""",
            **kwargs,
        )

        def get_data(r):
            orgs = r["data"]["currentUser"]["organizations"]
            return [item for org in orgs for item in org["casts"]]

        return _get_return(res, get_data=get_data)

    def get_current_user(self, **kwargs):
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
            """,
            **kwargs,
        )

        return _get_return(res, get_data=lambda r: r["data"]["currentUser"])

    def get_welds(self, **kwargs) -> Union[List, Tuple[List, Dict]]:
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
            }""",
            **kwargs,
        )

        def get_data(r):
            orgs = r["data"]["currentUser"]["organizations"]
            return [item for org in orgs for item in org["welds"]]

        return _get_return(res, get_data=get_data)

    def create_etch_packet(
        self,
        payload: Optional[
            Union[
                dict,
                CreateEtchPacketPayload,
                CreateEtchPacket,
                AnyStr,
            ]
        ] = None,
        json=None,
        **kwargs,
    ):
        """Create etch packet via a graphql mutation."""
        # Create an etch packet payload instance excluding signers and files
        # (if any). We'll need to add those separately. below.
        if not any([payload, json]):
            raise TypeError('One of the arguments `payload` or `json` must exist')

        if json:
            payload = CreateEtchPacketPayload.parse_raw(
                json, content_type="application/json"
            )

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
        return self.mutate(
            mutation,
            variables=mutation.create_payload().dict(by_alias=True, exclude_none=True),
            **kwargs,
        )

    def generate_etch_signing_url(self, signer_eid: str, client_user_id: str, **kwargs):
        """Generate a signing URL for a given user."""
        mutation = GenerateEtchSigningURL(
            signer_eid=signer_eid,
            client_user_id=client_user_id,
        )
        payload = mutation.create_payload()
        return self.mutate(mutation, variables=payload.dict(by_alias=True), **kwargs)

    def download_documents(self, document_group_eid: str, **kwargs):
        """Retrieve all completed documents in zip form."""
        api = PlainRequest(client=self.client)
        return api.get(f"document-group/{document_group_eid}.zip", **kwargs)
