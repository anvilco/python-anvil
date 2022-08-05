# pylint: disable=no-self-argument,no-self-use

import sys

# Disabling pylint no-name-in-module because this is the documented way to
# import `BaseModel` and it's not broken, so let's keep it.
from pydantic import (  # pylint: disable=no-name-in-module
    Field,
    HttpUrl,
    root_validator,
    validator,
)
from typing import Any, Dict, List, Optional, Text, Union

from .base import BaseModel


if sys.version_info >= (3, 8):
    from typing import Literal  # pylint: disable=no-name-in-module
else:
    from typing_extensions import Literal


class EmbeddedLogo(BaseModel):
    src: str
    max_width: Optional[int]
    max_height: Optional[int]


class FillPDFPayload(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any]]
    title: Optional[str] = None
    font_size: Optional[int] = None
    text_color: Optional[str] = None

    @validator("data")
    def data_cannot_be_empty(cls, v):
        if isinstance(v, dict) and len(v) == 0:
            raise ValueError("cannot be empty")
        return v


class GeneratePDFPayload(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[Literal["html", "css"], str]]
    logo: Optional[EmbeddedLogo]
    title: Optional[str]
    type: Optional[Literal["markdown", "html"]] = "markdown"

    @validator("data")
    def data_must_match_type(cls, v, values):
        if "type" in values and values["type"] == "html":
            if "html" not in v:
                raise ValueError("must contain HTML if using `html` type")
            if isinstance(v, list):
                raise ValueError("must contain a data dict not a list")
        return v

    @validator("type")
    def type_must_match_data(cls, v, values):
        if v == "html":
            if "data" in values and not isinstance(values["data"], dict):
                raise ValueError("HTML types must used a dict data payload")
        return v


class GenerateEtchSigningURLPayload(BaseModel):
    signer_eid: str
    client_user_id: str


class SignerField(BaseModel):
    file_id: str
    field_id: str


class EtchSigner(BaseModel):
    """Dataclass representing etch signers."""

    name: str
    email: str
    fields: List[SignerField]
    signer_type: str = "email"
    # id will be generated if `None`
    id: Optional[str] = None
    routing_order: Optional[int] = None
    redirect_url: Optional[str] = Field(None, alias="redirectURL")
    accept_each_field: Optional[bool] = None
    enable_emails: Optional[List[str]] = None
    # signature_mode can be "draw" or "text" (default: text)
    signature_mode: Optional[str] = None


class SignatureField(BaseModel):
    id: str
    type: str
    page_num: int
    # Should be in a format similar to:
    # { x: 100.00, y: 121.21, width: 33.00 }
    rect: Dict[str, float]


class Base64Upload(BaseModel):
    data: str
    filename: str
    mimetype: str = "application/pdf"


class DocumentUpload(BaseModel):
    """Dataclass representing an uploaded document."""

    id: str
    title: str
    # A GraphQLUpload or Base64Upload, but using Bas64Upload for now
    file: Base64Upload
    fields: List[SignatureField]
    font_size: int = 14
    text_color: str = "#000000"


class EtchCastRef(BaseModel):
    """Dataclass representing an existing template used as a reference."""

    id: str
    cast_eid: str


class CreateEtchFilePayload(BaseModel):
    payloads: Union[str, Dict[str, FillPDFPayload]]


class CreateEtchPacketPayload(BaseModel):
    """
    Payload for createEtchPacket.

    See the full packet payload defined here:
    https://www.useanvil.com/docs/api/e-signatures#tying-it-all-together
    """

    name: str
    signers: List[EtchSigner]
    files: List[Union[DocumentUpload, EtchCastRef]]
    signature_email_subject: Optional[str] = None
    signature_email_body: Optional[str] = None
    is_draft: Optional[bool] = False
    is_test: Optional[bool] = True
    merge_pdfs: Optional[bool] = Field(None, alias="mergePDFs")
    data: Optional[CreateEtchFilePayload] = None
    signature_page_options: Optional[Dict[Any, Any]] = None
    webhook_url: Optional[str] = Field(None, alias="webhookURL")
    reply_to_name: Optional[Any] = None
    reply_to_email: Optional[Any] = None


class ForgeSubmitPayload(BaseModel):
    """
    Payload for forgeSubmit.

    See full payload defined here:
    https://www.useanvil.com/docs/api/graphql/reference/#operation-forgesubmit-Mutations
    """

    forge_eid: Text
    payload: Dict[Text, Any]
    weld_data_eid: Optional[Text] = None
    submission_eid: Optional[Text] = None
    # Defaults to True when not provided/is None
    enforce_payload_valid_on_create: Optional[bool] = None
    current_step: Optional[int] = None
    complete: Optional[bool] = None
    # Note that if using a development API key, this will be forced to `True`
    # even when `False` is used in the payload.
    is_test: Optional[bool] = True
    timezone: Optional[Text] = None
    webhook_url: Optional[HttpUrl] = Field(None, alias="webhookURL")
    group_array_id: Optional[Text] = None
    group_array_index: Optional[int] = None

    @root_validator
    def wd_submission_both_required(cls, values):
        both_required = ["weld_data_eid", "submission_eid"]
        picked = [k for k in both_required if k in values and values[k] is not None]
        if len(picked) == 1:
            raise ValueError(
                "Both `weld_data_eid` and `submission_eid` are "
                "required if either are provided."
            )
        return values
