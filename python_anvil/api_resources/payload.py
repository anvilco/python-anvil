from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin, LetterCase, dataclass_json
from typing import Any, Dict, List, Optional, Union


# NOTE: All dataclasses here have a, probably excessive, `DataClassJsonMixin`
# mixin in order to keep mypy happy for now. When using serializations methods
# you would get an error such as:
# `error: "FillPDFPayload" has no attribute "to_dict"`
# when running mypy.


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class EmbeddedLogo(DataClassJsonMixin):
    src: str
    max_width: Optional[int]
    max_height: Optional[int]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class FillPDFPayload(DataClassJsonMixin):
    data: Dict[str, Any]
    title: Optional[str] = None
    font_size: Optional[int] = None
    text_color: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class GeneratePDFPayload(DataClassJsonMixin):
    data: List[Dict[str, Any]]
    logo: Optional[EmbeddedLogo] = None
    title: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class GenerateEtchSigningURLPayload(DataClassJsonMixin):
    signer_eid: str
    client_user_id: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SignerField(DataClassJsonMixin):
    file_id: str
    field_id: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class EtchSigner(DataClassJsonMixin):
    """Dataclass representing etch signers."""

    name: str
    email: str
    fields: List[SignerField]
    signer_type: str = "email"
    # Will be generated if `None`
    id: Optional[str] = ""
    routing_order: Optional[int] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SignatureField(DataClassJsonMixin):
    id: str
    type: str
    page_num: int
    # Should be in a format similar to:
    # { x: 100.00, y: 121.21, width: 33.00 }
    rect: Dict[str, float]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Base64Upload(DataClassJsonMixin):
    data: str
    filename: str
    mimetype: str = "application/pdf"


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class DocumentUpload(DataClassJsonMixin):
    """Dataclass representing an uploaded document."""

    id: str
    title: str
    # A GraphQLUpload or Base64Upload, but using Bas64Upload for now
    file: Base64Upload
    fields: List[SignatureField]
    font_size: int = 14
    text_color: str = "#000000"


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class EtchCastRef(DataClassJsonMixin):
    """Dataclass representing an existing template used as a reference."""

    id: str
    cast_eid: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CreateEtchFilePayload(DataClassJsonMixin):
    payloads: Union[str, Dict[str, FillPDFPayload]]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CreateEtchPacketPayload(DataClassJsonMixin):
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
