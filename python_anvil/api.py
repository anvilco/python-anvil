import logging
from gql import gql
from graphql import DocumentNode
from typing import Any, AnyStr, Callable, Dict, List, Optional, Tuple, Union

from .api_resources.mutations import (
    BaseQuery,
    CreateEtchPacket,
    ForgeSubmit,
    GenerateEtchSigningURL,
)
from .api_resources.payload import (
    CreateEtchPacketPayload,
    FillPDFPayload,
    ForgeSubmitPayload,
    GeneratePDFPayload,
)
from .api_resources.requests import FullyQualifiedRequest, PlainRequest, RestRequest
from .http import GQLClient, HTTPClient


logger = logging.getLogger(__name__)


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

    # Version number to use for latest versions (usually drafts)
    VERSION_LATEST = -1
    # Version number to use for the latest published version.
    # This is the default when a version is not provided.
    VERSION_LATEST_PUBLISHED = -2

    def __init__(
        self,
        api_key: Optional[str] = None,
        environment="dev",
        endpoint_url=None,
    ):
        if not api_key:
            raise ValueError('`api_key` must be a valid string')

        self.client = HTTPClient(api_key=api_key, environment=environment)
        self.gql_client = GQLClient.get_client(
            api_key=api_key,
            environment=environment,
            endpoint_url=endpoint_url,
        )

    def query(
        self,
        query: Union[str, DocumentNode],
        variables: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Execute a GraphQL query.

        :param query:
        :type query: Union[str, DocumentNode]
        :param variables:
        :type variables: Optional[Dict[str, Any]]
        :param kwargs:
        :return:
        """
        # Remove `debug` for now.
        kwargs.pop("debug", None)
        if isinstance(query, str):
            query = gql(query)

        return self.gql_client.execute(query, variable_values=variables, **kwargs)

    def mutate(
        self, query: Union[str, BaseQuery], variables: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation.

        NOTE: Any files attached provided in `variables` will be sent via the
        multipart spec:
        https://github.com/jaydenseric/graphql-multipart-request-spec

        :param query:
        :type query: Union[str, BaseQuery]
        :param variables:
        :type variables: Dict[str, Any]
        :param kwargs:
        :return:
        """
        # Remove `debug` for now.
        kwargs.pop("debug", None)
        if isinstance(query, str):
            use_query = gql(query)
        else:
            mutation = query.get_mutation()
            use_query = gql(mutation)

        return self.gql_client.execute(use_query, variable_values=variables, **kwargs)

    def request_rest(self, options: Optional[dict] = None):
        api = RestRequest(self.client, options=options)
        return api

    def request_fully_qualified(self, options: Optional[dict] = None):
        api = FullyQualifiedRequest(self.client, options=options)
        return api

    def fill_pdf(
        self, template_id: str, payload: Union[dict, AnyStr, FillPDFPayload], **kwargs
    ):
        """Fill an existing template with provided payload data.

        Use the casts graphql query to get a list of available templates you
        can use for this request.

        :param template_id: eid of an existing template/cast
        :type template_id: str
        :param payload: payload in the form of a dict or JSON data
        :type payload: dict|str
        :param kwargs.version_number: specific template version number to use. If
            not provided, the latest _published_ version will be used.
        :type kwargs.version_number: int
        """
        try:
            if isinstance(payload, dict):
                data = FillPDFPayload(**payload)
            elif isinstance(payload, str):
                data = FillPDFPayload.model_validate_json(payload)
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

        version_number = kwargs.pop("version_number", None)
        if version_number:
            kwargs["params"] = dict(versionNumber=version_number)

        api = RestRequest(client=self.client)
        return api.post(
            f"fill/{template_id}.pdf",
            data.model_dump(by_alias=True, exclude_none=True) if data else {},
            **kwargs,
        )

    def generate_pdf(self, payload: Union[AnyStr, Dict, GeneratePDFPayload], **kwargs):
        if not payload:
            raise ValueError("`payload` must be a valid JSON string or a dict")

        if isinstance(payload, dict):
            data = GeneratePDFPayload(**payload)
        elif isinstance(payload, str):
            data = GeneratePDFPayload.model_validate_json(payload)
        elif isinstance(payload, GeneratePDFPayload):
            data = payload
        else:
            raise ValueError("`payload` must be a valid JSON string or a dict")

        # Any data errors would come from here
        api = RestRequest(client=self.client)
        return api.post(
            "generate-pdf",
            data=data.model_dump(by_alias=True, exclude_none=True),
            **kwargs,
        )

    def get_cast(
        self,
        eid: str,
        fields: Optional[List[str]] = None,
        version_number: Optional[int] = None,
        cast_args: Optional[List[Tuple[str, str]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:

        if not fields:
            # Use default fields
            fields = ["eid", "title", "fieldInfo"]

        if not cast_args:
            cast_args = []

        cast_args.append(("eid", f'"{eid}"'))

        # If `version_number` isn't provided, the API will default to the
        # latest published version.
        if version_number:
            cast_args.append(("versionNumber", str(version_number)))

        arg_str = ""
        if len(cast_args):
            joined_args = [(":".join(arg)) for arg in cast_args]
            arg_str = f"({','.join(joined_args)})"

        res = self.query(
            gql(
                f"""{{
              cast {arg_str} {{
                {" ".join(fields)}
              }}
            }}"""
            ),
            **kwargs,
        )

        def get_data(r: dict) -> Dict[str, Any]:
            return r["cast"]

        return _get_return(res, get_data=get_data)

    def get_casts(
        self, fields: Optional[List[str]] = None, show_all: bool = False, **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve all Cast objects for the current user across all organizations.

        :param fields: List of fields to retrieve for each cast object
        :type fields: Optional[List[str]]
        :param show_all: Boolean to show all Cast objects.
            Defaults to showing only templates.
        :type show_all: bool
        :param kwargs:
        :return:
        """
        if not fields:
            # Use default fields
            fields = ["eid", "title", "fieldInfo"]

        cast_args = "" if show_all else "(isTemplate: true)"

        res = self.query(
            gql(
                f"""{{
              currentUser {{
                organizations {{
                  casts {cast_args} {{
                    {" ".join(fields)}
                  }}
                }}
              }}
            }}"""
            ),
            **kwargs,
        )

        def get_data(r: dict):
            orgs = r["currentUser"]["organizations"]
            return [item for org in orgs for item in org["casts"]]

        return _get_return(res, get_data=get_data)

    def get_current_user(self, **kwargs):
        """Retrieve current user data.

        :param kwargs:
        :return:
        """
        res = self.query(
            gql(
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
            }"""
            ),
            **kwargs,
        )

        return _get_return(res, get_data=lambda r: r["currentUser"])

    def get_welds(self, **kwargs) -> Union[List, Tuple[List, Dict]]:
        res = self.query(
            gql(
                """{
              currentUser {
                organizations {
                  welds {
                    eid
                    slug
                    name
                    forges {
                      eid
                      name
                    }
                  }
                }
              }
            }"""
            ),
            **kwargs,
        )

        def get_data(r: dict):
            orgs = r["currentUser"]["organizations"]
            return [item for org in orgs for item in org["welds"]]

        return _get_return(res, get_data=get_data)

    def get_weld(self, eid: str, **kwargs):
        res = self.query(
            gql(
                """
            query WeldQuery(
                #$organizationSlug: String!,
                #$slug: String!
                $eid: String!
            ) {
                weld(
                    #organizationSlug: $organizationSlug,
                    #slug: $slug
                    eid: $eid
                ) {
                    eid
                    slug
                    name
                    forges {
                        eid
                        name
                        slug
                    }
                }
            }"""
            ),
            variables=dict(eid=eid),
            **kwargs,
        )

        def get_data(r: dict):
            return r["weld"]

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
            payload = CreateEtchPacketPayload.model_validate_json(json)

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

        payload = mutation.create_payload()
        variables = payload.model_dump(by_alias=True, exclude_none=True)

        return self.mutate(mutation, variables=variables, upload_files=True, **kwargs)

    def generate_etch_signing_url(self, signer_eid: str, client_user_id: str, **kwargs):
        """Generate a signing URL for a given user."""
        mutation = GenerateEtchSigningURL(
            signer_eid=signer_eid,
            client_user_id=client_user_id,
        )
        payload = mutation.create_payload()
        return self.mutate(
            mutation, variables=payload.model_dump(by_alias=True), **kwargs
        )

    def download_documents(self, document_group_eid: str, **kwargs):
        """Retrieve all completed documents in zip form."""
        api = PlainRequest(client=self.client)
        return api.get(f"document-group/{document_group_eid}.zip", **kwargs)

    def forge_submit(
        self,
        payload: Optional[Union[Dict[str, Any], ForgeSubmitPayload]] = None,
        json=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a Webform (forge) submission via a graphql mutation."""
        if not any([json, payload]):
            raise TypeError('One of arguments `json` or `payload` are required')

        if json:
            payload = ForgeSubmitPayload.model_validate_json(json)

        if isinstance(payload, dict):
            mutation = ForgeSubmit.create_from_dict(payload)
        elif isinstance(payload, ForgeSubmitPayload):
            mutation = ForgeSubmit(payload=payload)
        else:
            raise ValueError(
                "`payload` must be a valid ForgeSubmitPayload instance or dict"
            )

        return self.mutate(
            mutation,
            variables=mutation.create_payload().model_dump(
                by_alias=True, exclude_none=True
            ),
            **kwargs,
        )
