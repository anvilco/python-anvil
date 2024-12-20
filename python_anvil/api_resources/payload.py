# pylint: disable=no-self-argument

import sys
from io import BufferedIOBase

# Disabling pylint no-name-in-module because this is the documented way to
# import `BaseModel` and it's not broken, so let's keep it.
from pydantic import (  # pylint: disable=no-name-in-module
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)
from typing import Any, Dict, List, Optional, Union

from python_anvil.models import FileCompatibleBaseModel

from .base import BaseModel


if sys.version_info >= (3, 8):
    from typing import Literal  # pylint: disable=no-name-in-module
else:
    from typing_extensions import Literal


class EmbeddedLogo(BaseModel):
    src: str
    max_width: Optional[int] = None
    max_height: Optional[int] = None


class FillPDFPayload(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any]]
    title: Optional[str] = None
    font_size: Optional[int] = None
    text_color: Optional[str] = None

    @field_validator("data")
    @classmethod
    def data_cannot_be_empty(cls, v):
        if isinstance(v, dict) and len(v) == 0:
            raise ValueError("cannot be empty")
        return v


class GeneratePDFPayload(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[Literal["html", "css"], str]]
    logo: Optional[EmbeddedLogo] = None
    title: Optional[str] = None
    type: Optional[Literal["markdown", "html"]] = "markdown"
    page: Optional[Dict[str, Any]] = None
    font_size: Optional[int] = None
    font_family: Optional[str] = None
    text_color: Optional[str] = None


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


class TableColumnAlignment(BaseModel):
    align: Optional[Literal["left", "center", "right"]] = None
    width: Optional[str] = None


# https://www.useanvil.com/docs/api/generate-pdf#table
class MarkdownTable(BaseModel):
    rows: List[List[str]]

    # defaults to `True` if not provided.
    # set to false for no header row on the table
    first_row_headers: Optional[bool] = None

    # defaults to `False` if not provided.
    # set to true to display gridlines in-between rows or columns
    row_grid_lines: Optional[bool] = True
    column_grid_lines: Optional[bool] = False

    # defaults to 'top' if not provided.
    # adjust vertical alignment of table text
    # accepts 'top', 'center', or 'bottom'
    vertical_align: Optional[Literal["top", "center", "bottom"]] = "center"

    # (optional) columnOptions - An array of columnOption objects.
    # You do not need to specify all columns. Accepts an
    # empty object indicating no overrides on the
    # specified column.
    #
    # Supported keys for columnOption:
    # align (optional) - adjust horizontal alignment of table text
    # accepts 'left', 'center', or 'right'; defaults to 'left'
    # width (optional) - adjust the width of the column
    # accepts width in pixels or as percentage of the table width
    column_options: Optional[List[TableColumnAlignment]] = None


# https://www.useanvil.com/docs/api/object-references/#verbatimfield
class MarkdownContent(BaseModel):
    label: Optional[str] = None
    heading: Optional[str] = None
    content: Optional[str] = None
    table: Optional[MarkdownTable] = None
    font_size: int = 14
    text_color: str = "#000000"


class DocumentMarkup(BaseModel):
    """Dataclass representing a document with HTML/CSS markup."""

    id: str
    filename: str
    markup: Dict[Literal["html", "css"], str]
    fields: Optional[List[SignatureField]] = None
    title: Optional[str] = None
    font_size: int = 14
    text_color: str = "#000000"


class DocumentMarkdown(BaseModel):
    """Dataclass representing a document with Markdown."""

    id: str
    filename: str
    # NOTE: Order matters here in the Union[].
    # If `SignatureField` is not first, the types are similar enough that it
    # will use `MarkdownContent` instead.
    fields: Optional[List[Union[SignatureField, MarkdownContent]]] = None
    title: Optional[str] = None
    font_size: int = 14
    text_color: str = "#000000"


class DocumentUpload(FileCompatibleBaseModel):
    """Dataclass representing an uploaded document."""

    id: str
    title: str
    # Previously "UploadableFile", however, that seems to cause weird upload
    # issues where a PDF file would have its first few bytes removed.
    # We're now relying on the backend to validate this property instead of on
    # the client library side.
    # This might be a bug on the `pydantic` side(?) when this object gets
    # converted into a dict.

    # NOTE: This field name is referenced in the models.py file, if you change it you
    #   must change the reference
    file: Any = None
    fields: List[SignatureField]
    font_size: int = 14
    text_color: str = "#000000"
    model_config = ConfigDict(arbitrary_types_allowed=True)


class EtchCastRef(BaseModel):
    """Dataclass representing an existing template used as a reference."""

    id: str
    cast_eid: str


class CreateEtchFilePayload(BaseModel):
    payloads: Union[str, Dict[str, FillPDFPayload]]


class CreateEtchPacketPayload(FileCompatibleBaseModel):
    """
    Payload for createEtchPacket.

    See the full packet payload defined here:
    https://www.useanvil.com/docs/api/e-signatures#tying-it-all-together
    """

    name: str
    signers: List[EtchSigner]
    # NOTE: This is a list of `AttachableEtchFile` objects, but we need to
    # override the default `FileCompatibleBaseModel` to handle multipart/form-data
    # uploads correctly. This field name is referenced in the models.py file.
    files: List["AttachableEtchFile"]
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
    enable_emails: Optional[Union[bool, List[str]]] = None
    create_cast_templates_from_uploads: Optional[bool] = None
    duplicate_casts: Optional[bool] = None


class ForgeSubmitPayload(BaseModel):
    """
    Payload for forgeSubmit.

    See full payload defined here:
    https://www.useanvil.com/docs/api/graphql/reference/#operation-forgesubmit-Mutations
    """

    forge_eid: str
    payload: Dict[str, Any]
    weld_data_eid: Optional[str] = None
    submission_eid: Optional[str] = None
    # Defaults to True when not provided/is None
    enforce_payload_valid_on_create: Optional[bool] = None
    current_step: Optional[int] = None
    complete: Optional[bool] = None
    # Note that if using a development API key, this will be forced to `True`
    # even when `False` is used in the payload.
    is_test: Optional[bool] = True
    timezone: Optional[str] = None
    webhook_url: Optional[HttpUrl] = Field(None, alias="webhookURL")
    group_array_id: Optional[str] = None
    group_array_index: Optional[int] = None


UploadableFile = Union[Base64Upload, BufferedIOBase]
AttachableEtchFile = Union[
    DocumentUpload, EtchCastRef, DocumentMarkup, DocumentMarkdown
]

# Classes below use types wrapped in quotes avoid a circular dependency/weird
# variable assignment locations with the aliases above. We need to manually
# update the refs for them to point to the right things.
DocumentUpload.model_rebuild()
CreateEtchPacketPayload.model_rebuild()
