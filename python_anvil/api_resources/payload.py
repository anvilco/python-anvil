# pylint: disable=no-self-argument,no-self-use

import re

# Disabling pylint no-name-in-module because this is the documented way to
# import `BaseModel` and it's not broken, so let's keep it.
from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel as _BaseModel,
    Extra,
    Field,
    validator,
)
from typing import Any, Dict, List, Literal, Optional, Union


under_pat = re.compile(r"_([a-z])")


def underscore_to_camel(name):
    ret = under_pat.sub(lambda x: x.group(1).upper(), name)
    return ret


class BaseModel(_BaseModel):
    class Config:
        """Config override for all models.

        This override is mainly so everything can go from snake to camel-case.
        """

        alias_generator = underscore_to_camel
        allow_population_by_field_name = True

        # Allow extra fields even if it is not defined. This will allow models
        # to be more flexible if features are added in the Anvil API, but
        # explicit support hasn't been added yet to this library.
        extra = Extra.allow


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
    """Payload for createEtchPacket.

    See the full packet payload defined here:
    https://www.useanvil.com/docs/api/e-signatures#tying-it-all-together
    """

    name: str
    signature_email_subject: str
    signers: List[EtchSigner]
    files: List[Union[DocumentUpload, EtchCastRef]]
    is_draft: Optional[bool] = False
    is_test: Optional[bool] = True
    data: Optional[CreateEtchFilePayload] = None
    signature_page_options: Optional[Dict[Any, Any]] = None
    webhook_url: Optional[str] = Field(None, alias="webhookURL")
