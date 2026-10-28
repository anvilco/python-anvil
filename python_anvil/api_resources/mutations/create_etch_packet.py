import logging
from io import BufferedIOBase
from logging import Logger
from mimetypes import guess_type
from typing import Any

from pydantic import TypeAdapter

from python_anvil.api_resources.mutations.base import BaseQuery
from python_anvil.api_resources.payload import (
    AttachableEtchFile,
    CreateEtchFilePayload,
    CreateEtchPacketPayload,
    DocumentUpload,
    EtchSigner,
)
from python_anvil.graphql.mutations.create_etch_packet import (
    DEFAULT_RESPONSE_QUERY,
    generate_mutation,
)
from python_anvil.utils import camel_to_snake, create_unique_id


logger: Logger = logging.getLogger(__name__)

_ATTACHABLE_FILE: TypeAdapter[AttachableEtchFile] = TypeAdapter(AttachableEtchFile)

# The mutation, under the name it had before 6.0.0
CREATE_ETCH_PACKET = generate_mutation()


class CreateEtchPacket(BaseQuery):
    """Builds a `createEtchPacket` mutation, adding signers and files one at a time.

    Or pass the whole thing as `payload`.
    """

    default_response_query = DEFAULT_RESPONSE_QUERY

    def __init__(
        self,
        name: str | None = None,
        signature_email_subject: str | None = None,
        signature_email_body: str | None = None,
        signers: list[EtchSigner] | None = None,
        files: list[AttachableEtchFile] | None = None,
        file_payloads: dict | None = None,
        signature_page_options: dict[Any, Any] | None = None,
        is_draft: bool = False,
        is_test: bool = True,
        payload: CreateEtchPacketPayload | None = None,
        webhook_url: str | None = None,
        reply_to_name: str | None = None,
        reply_to_email: str | None = None,
        merge_pdfs: bool | None = None,
        enable_emails: bool | list[str] | None = None,
        create_cast_templates_from_uploads: bool | None = None,
        duplicate_casts: bool | None = None,
        organization_eid: str | None = None,
        allow_updates: bool | None = None,
    ):
        # `name` is required when `payload` is not present.
        if not payload and not name:
            raise TypeError("`name` is required")

        self.name = name
        self.signature_email_subject = signature_email_subject
        self.signature_email_body = signature_email_body
        self.signature_page_options = signature_page_options
        self.signers = signers or []
        self.files = files or []
        self.file_payloads = file_payloads or {}
        self.is_draft = is_draft
        self.is_test = is_test
        self.payload = payload
        self.webhook_url = webhook_url
        self.reply_to_name = reply_to_name
        self.reply_to_email = reply_to_email
        self.merge_pdfs = merge_pdfs
        self.enable_emails = enable_emails
        self.create_cast_templates_from_uploads = create_cast_templates_from_uploads
        self.duplicate_casts = duplicate_casts
        self.organization_eid = organization_eid
        self.allow_updates = allow_updates

    def get_mutation(self, response_query: str | None = None) -> str:
        return generate_mutation(self.response_fields(response_query))

    @classmethod
    def create_from_dict(cls, payload: dict) -> "CreateEtchPacket":
        """Create a new instance of `CreateEtchPacket` from a dict payload.

        Keys may be snake_case or camelCase, like the mutation's variables.
        """
        payload = {camel_to_snake(k): v for k, v in payload.items()}
        try:
            mutation = cls(
                **{k: v for k, v in payload.items() if k not in ["signers", "files"]}
            )
        except TypeError as e:
            raise ValueError(
                f"`payload` must be a valid CreateEtchPacket instance or dict. {e}"
            ) from e
        for signer in payload.get("signers") or []:
            mutation.add_signer(signer)

        for file in payload.get("files") or []:
            mutation.add_file(file)

        return mutation

    def add_signer(self, signer: dict | EtchSigner):
        """Add a signer to the mutation payload.

        :param signer: Signer object to add to the payload
        :type signer: dict|EtchSigner
        """
        if isinstance(signer, dict):
            data = EtchSigner(**signer)
        elif isinstance(signer, EtchSigner):
            data = signer
        else:
            raise ValueError("Signer must be either a dict or EtchSigner type")

        if not data.id:
            data.id = create_unique_id("signer")
        if not data.routing_order:
            if self.signers:
                # Basic thing to get the next number
                # But this might not be necessary since API goes by index
                # of signers in the list.
                all_signers = [(s.routing_order or 0) for s in self.signers]
                num = max(all_signers) + 1
            else:
                num = 1
            data.routing_order = num

        self.signers.append(data)

    def add_file(self, file: AttachableEtchFile | dict):
        """Add a file to a pending list of files.

        A `DocumentUpload`, `EtchCastRef`, `DocumentMarkdown` or `DocumentMarkup`,
        or a dict of one of those, with snake_case or camelCase keys. Files
        will not be uploaded when running this method. They will be uploaded
        when the mutation actually runs.
        """
        if isinstance(file, dict):
            file = _ATTACHABLE_FILE.validate_python(file)
        if (
            isinstance(file, DocumentUpload)
            and isinstance(file.file, BufferedIOBase)
            and getattr(file.file, "content_type", None) is None
        ):
            # Don't clobber existing `content_type`s provided.
            content_type, _ = guess_type(file.file.name)  # type: ignore
            logger.debug(
                "File did not have a `content_type`, guessing as '%s'", content_type
            )
            file.file.content_type = content_type  # type: ignore

        self.files.append(file)

    def add_file_payloads(self, file_id: str, fill_payload):
        existing_files = [f.id for f in self.files if f]
        if file_id not in existing_files:
            raise ValueError(
                f"`{file_id}` was not added as a file. Please add "
                f"the file first before adding a fill payload."
            )
        self.file_payloads[file_id] = fill_payload

    def get_file_payloads(self):
        existing_files = [f.id for f in self.files if f]
        for key, _ in self.file_payloads.items():
            if key not in existing_files:
                raise ValueError(
                    f"`{key}` was not added as a file. Please add "
                    f"that file or remove its fill payload before "
                    f"attempting to create an Etch payload."
                )
        return self.file_payloads

    def create_payload(self) -> CreateEtchPacketPayload:
        """Create a payload based on data set on the class instance.

        Check `api_resources.payload.CreateEtchPacketPayload` for full payload
        requirements. Data requirements aren't explicitly enforced here, but
        at the payload class level.
        """
        # If there's an existing payload instance attribute, just return that.
        if self.payload:
            return self.payload

        if not self.name:
            raise TypeError("`name` is required")

        payload = CreateEtchPacketPayload(
            is_test=self.is_test,
            is_draft=self.is_draft,
            name=self.name,
            signers=self.signers,
            files=self.files,
            data=CreateEtchFilePayload(payloads=self.get_file_payloads()),
            signature_email_subject=self.signature_email_subject,
            signature_email_body=self.signature_email_body,
            signature_page_options=self.signature_page_options or {},
            webhook_url=self.webhook_url,
            reply_to_email=self.reply_to_email,
            reply_to_name=self.reply_to_name,
            merge_pdfs=self.merge_pdfs,
            enable_emails=self.enable_emails,
            create_cast_templates_from_uploads=self.create_cast_templates_from_uploads,
            duplicate_casts=self.duplicate_casts,
            organization_eid=self.organization_eid,
            allow_updates=self.allow_updates,
        )

        return payload
