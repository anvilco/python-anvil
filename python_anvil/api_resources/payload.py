from io import BufferedIOBase
from typing import Any, Literal

from pydantic import (
    ConfigDict,
    Field,
    field_validator,
)

from python_anvil.models import FileCompatibleBaseModel
from python_anvil.types import operations, rest

from .base import BaseModel


class EmbeddedLogo(BaseModel):
    src: str
    max_width: int | None = None
    max_height: int | None = None


class FillPDFPayload(rest.FillPdfRequest):
    """The body of a fill PDF request: `data` and the API's styling options.

    See `python_anvil.types.rest.FillPdfRequest` for every option.
    """

    data: list[dict[str, Any]] | dict[str, Any]
    # As before 6.0.0, any size; the API says what it accepts
    font_size: int | None = Field(None, alias="fontSize")
    # The API defaults this to "pdf"; leave it out rather than always sending it
    output_format: Literal["pdf", "url"] | None = Field(None, alias="outputFormat")

    @field_validator("data")
    @classmethod
    def data_cannot_be_empty(cls, v):
        if isinstance(v, dict) and len(v) == 0:
            raise ValueError("cannot be empty")
        return v


class GeneratePDFPayload(rest.GenerateMarkdownPdfRequest):
    """The body of a generate PDF request, from Markdown (the default) or HTML.

    See `python_anvil.types.rest.GenerateMarkdownPdfRequest` and
    `GenerateHtmlPdfRequest` for every option.
    """

    data: list[dict[str, Any]] | dict[Literal["html", "css"], str]  # type: ignore[assignment]
    logo: EmbeddedLogo | Literal[False] | None = None  # type: ignore[assignment]
    type: Literal["markdown", "html"] | None = "markdown"
    # As before 6.0.0, any size; the API says what it accepts
    font_size: int | None = Field(None, alias="fontSize")
    # The API defaults this to "pdf"; leave it out rather than always sending it
    output_format: Literal["pdf", "url"] | None = Field(None, alias="outputFormat")


class GenerateEtchSigningURLPayload(BaseModel):
    signer_eid: str
    client_user_id: str


class SignerField(BaseModel):
    file_id: str
    field_id: str


class EtchSigner(rest.EtchSigner):
    """A signer of an Etch packet: who signs, which fields, and how.

    See `python_anvil.types.rest.EtchSigner` for every option.
    """

    name: str
    email: str
    fields: list[SignerField]  # type: ignore[assignment]
    signer_type: Literal["email", "embedded", "in-person"] = Field(
        "email", alias="signerType"
    )
    # id will be generated if `None`
    id: str | None = None  # type: ignore[assignment]
    # As before 6.0.0, any order; the API says what it accepts
    routing_order: int | None = Field(None, alias="routingOrder")
    enable_emails: bool | list[str] | None = Field(None, alias="enableEmails")  # type: ignore[assignment]


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


class CreateEtchPacketPayload(FileCompatibleBaseModel, operations.CreateEtchPacketArgs):
    """The variables of the `createEtchPacket` mutation.

    See `python_anvil.types.operations.CreateEtchPacketArgs` for every
    variable, and the full packet payload defined here:
    https://www.useanvil.com/docs/api/e-signatures#tying-it-all-together
    """

    name: str
    signers: list[EtchSigner]  # type: ignore[assignment]
    # NOTE: This is a list of `AttachableEtchFile` objects, but we need to
    # override the default `FileCompatibleBaseModel` to handle multipart/form-data
    # uploads correctly. This field name is referenced in the models.py file.
    files: list["AttachableEtchFile"]  # type: ignore[assignment]
    is_draft: bool | None = Field(False, alias="isDraft")
    is_test: bool | None = Field(True, alias="isTest")
    data: CreateEtchFilePayload | None = None
    signature_page_options: dict[Any, Any] | None = Field(
        None, alias="signaturePageOptions"
    )
    enable_emails: bool | list[str] | None = Field(None, alias="enableEmails")


class ForgeSubmitPayload(operations.ForgeSubmitArgs):
    """The variables of the `forgeSubmit` mutation.

    See `python_anvil.types.operations.ForgeSubmitArgs` for every variable,
    and the full payload defined here:
    https://www.useanvil.com/docs/api/graphql/reference/#operation-forgesubmit-Mutations
    """

    payload: dict[str, Any]
    # Note that if using a development API key, this will be forced to `True`
    # even when `False` is used in the payload.
    is_test: bool | None = Field(True, alias="isTest")


UploadableFile = Base64Upload | BufferedIOBase
AttachableEtchFile = DocumentUpload | EtchCastRef | DocumentMarkup | DocumentMarkdown

# Classes below use types wrapped in quotes avoid a circular dependency/weird
# variable assignment locations with the aliases above. We need to manually
# update the refs for them to point to the right things.
DocumentUpload.model_rebuild()
CreateEtchPacketPayload.model_rebuild()
