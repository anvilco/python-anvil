from io import BufferedIOBase
from typing import Any, Literal

from pydantic import (
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)

from python_anvil.models import FileCompatibleBaseModel

from .base import BaseModel


class EmbeddedLogo(BaseModel):
    src: str
    max_width: int | None = None
    max_height: int | None = None


class FillPDFPayload(BaseModel):
    data: list[dict[str, Any]] | dict[str, Any]
    title: str | None = None
    font_size: int | None = None
    text_color: str | None = None

    @field_validator("data")
    @classmethod
    def data_cannot_be_empty(cls, v):
        if isinstance(v, dict) and len(v) == 0:
            raise ValueError("cannot be empty")
        return v


class GeneratePDFPayload(BaseModel):
    data: list[dict[str, Any]] | dict[Literal["html", "css"], str]
    logo: EmbeddedLogo | None = None
    title: str | None = None
    type: Literal["markdown", "html"] | None = "markdown"
    page: dict[str, Any] | None = None
    font_size: int | None = None
    font_family: str | None = None
    text_color: str | None = None


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
    fields: list[SignerField]
    signer_type: str = "email"
    # id will be generated if `None`
    id: str | None = None
    routing_order: int | None = None
    redirect_url: str | None = Field(None, alias="redirectURL")
    accept_each_field: bool | None = None
    enable_emails: list[str] | None = None
    # signature_mode can be "draw" or "text" (default: text)
    signature_mode: str | None = None


class SignatureField(BaseModel):
    id: str
    type: str
    page_num: int
    # Should be in a format similar to:
    # { x: 100.00, y: 121.21, width: 33.00 }
    rect: dict[str, float]


class Base64Upload(BaseModel):
    data: str
    filename: str
    mimetype: str = "application/pdf"


class TableColumnAlignment(BaseModel):
    align: Literal["left", "center", "right"] | None = None
    width: str | None = None


# https://www.useanvil.com/docs/api/generate-pdf#table
class MarkdownTable(BaseModel):
    rows: list[list[str]]

    # defaults to `True` if not provided.
    # set to false for no header row on the table
    first_row_headers: bool | None = None

    # defaults to `False` if not provided.
    # set to true to display gridlines in-between rows or columns
    row_grid_lines: bool | None = True
    column_grid_lines: bool | None = False

    # defaults to 'top' if not provided.
    # adjust vertical alignment of table text
    # accepts 'top', 'center', or 'bottom'
    vertical_align: Literal["top", "center", "bottom"] | None = "center"

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
    column_options: list[TableColumnAlignment] | None = None


# https://www.useanvil.com/docs/api/object-references/#verbatimfield
class MarkdownContent(BaseModel):
    label: str | None = None
    heading: str | None = None
    content: str | None = None
    table: MarkdownTable | None = None
    font_size: int = 14
    text_color: str = "#000000"


class DocumentMarkup(BaseModel):
    """Dataclass representing a document with HTML/CSS markup."""

    id: str
    filename: str
    markup: dict[Literal["html", "css"], str]
    fields: list[SignatureField] | None = None
    title: str | None = None
    font_size: int = 14
    text_color: str = "#000000"


class DocumentMarkdown(BaseModel):
    """Dataclass representing a document with Markdown."""

    id: str
    filename: str
    # NOTE: Order matters here in the Union[].
    # If `SignatureField` is not first, the types are similar enough that it
    # will use `MarkdownContent` instead.
    fields: list[SignatureField | MarkdownContent] | None = None
    title: str | None = None
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
    fields: list[SignatureField]
    font_size: int = 14
    text_color: str = "#000000"
    model_config = ConfigDict(arbitrary_types_allowed=True)


class EtchCastRef(BaseModel):
    """Dataclass representing an existing template used as a reference."""

    id: str
    cast_eid: str


class CreateEtchFilePayload(BaseModel):
    payloads: str | dict[str, FillPDFPayload]


class CreateEtchPacketPayload(FileCompatibleBaseModel):
    """
    Payload for createEtchPacket.

    See the full packet payload defined here:
    https://www.useanvil.com/docs/api/e-signatures#tying-it-all-together
    """

    name: str
    signers: list[EtchSigner]
    # NOTE: This is a list of `AttachableEtchFile` objects, but we need to
    # override the default `FileCompatibleBaseModel` to handle multipart/form-data
    # uploads correctly. This field name is referenced in the models.py file.
    files: list["AttachableEtchFile"]
    signature_email_subject: str | None = None
    signature_email_body: str | None = None
    is_draft: bool | None = False
    is_test: bool | None = True
    merge_pdfs: bool | None = Field(None, alias="mergePDFs")
    data: CreateEtchFilePayload | None = None
    signature_page_options: dict[Any, Any] | None = None
    webhook_url: str | None = Field(None, alias="webhookURL")
    reply_to_name: Any | None = None
    reply_to_email: Any | None = None
    enable_emails: bool | list[str] | None = None
    create_cast_templates_from_uploads: bool | None = None
    duplicate_casts: bool | None = None


class ForgeSubmitPayload(BaseModel):
    """
    Payload for forgeSubmit.

    See full payload defined here:
    https://www.useanvil.com/docs/api/graphql/reference/#operation-forgesubmit-Mutations
    """

    forge_eid: str
    payload: dict[str, Any]
    weld_data_eid: str | None = None
    submission_eid: str | None = None
    # Defaults to True when not provided/is None
    enforce_payload_valid_on_create: bool | None = None
    current_step: int | None = None
    complete: bool | None = None
    # Note that if using a development API key, this will be forced to `True`
    # even when `False` is used in the payload.
    is_test: bool | None = True
    timezone: str | None = None
    webhook_url: HttpUrl | None = Field(None, alias="webhookURL")
    group_array_id: str | None = None
    group_array_index: int | None = None


UploadableFile = Base64Upload | BufferedIOBase
AttachableEtchFile = DocumentUpload | EtchCastRef | DocumentMarkup | DocumentMarkdown

# Classes below use types wrapped in quotes avoid a circular dependency/weird
# variable assignment locations with the aliases above. We need to manually
# update the refs for them to point to the right things.
DocumentUpload.model_rebuild()
CreateEtchPacketPayload.model_rebuild()
