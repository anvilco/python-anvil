# pylint: disable=duplicate-code

import os

from python_anvil.api import Anvil
from python_anvil.api_resources.mutations.create_etch_packet import CreateEtchPacket
from python_anvil.api_resources.payload import (
    DocumentMarkup,
    EtchSigner,
    SignatureField,
    SignerField,
)


API_KEY = os.environ.get("ANVIL_API_KEY")
# or set your own key here
# API_KEY = 'my-api-key'


def main():
    anvil = Anvil(api_key=API_KEY)

    # Create an instance of the builder
    packet = CreateEtchPacket(
        name="Etch packet with existing template",
        #
        # Optional changes to email subject and body content
        signature_email_subject="Please sign these forms",
        signature_email_body="This form requires information from your driver's "
        "license. Please have that available.",
        #
        # URL where Anvil will send POST requests when server events happen.
        # Take a look at https://www.useanvil.com/docs/api/e-signatures#webhook-notifications
        # for other details on how to configure webhooks on your account.
        # You can also use sites like webhook.site, requestbin.com or ngrok to
        # test webhooks.
        # webhook_url="https://my.webhook.example.com/etch-events/",
        #
        # Email overrides for the "reply-to" email header for signer emails.
        # If used, both `reply_to_email` and `reply_to_name` are required.
        # By default, this will point to your organization support email.
        # reply_to_email="my-org-email@example.com",
        # reply_to_name="My Name",
        #
        # Merge all PDFs into one. Use this if you have many PDF templates
        # and/or files, but want the final downloaded package to be only
        # 1 PDF file.
        # merge_pdfs=True,
    )

    # Get your file(s) ready to sign.
    # For this example, a PDF will not be uploaded. We'll create and style the
    # document with HTML and CSS and add signing fields based on coordinates.

    # Define the document with HTML/CSS
    file1 = DocumentMarkup(
        id="myNewFile",
        title="Please sign this important form",
        filename="markup.pdf",
        markup={
            "html": """
                <div class="first">This document is created with HTML.</div>
                <br />
                <br />
                <br />
                <div>We can also define signing fields with text tags</div>
                <div>{{ signature : First signature : textTag : textTag }}</div>
            """,
            "css": """"body{ color: red; }  div.first { color: blue; } """,
        },
        fields=[
            SignatureField(
                id="sign1",
                type="signature",
                page_num=0,
                # The position and size of the field. The coordinates provided here
                # (x=300, y=300) is the top-left of the rectangle.
                rect=dict(x=300, y=300, width=250, height=30),
            )
        ],
    )

    # Gather your signer data
    signer1 = EtchSigner(
        name="Jackie",
        email="jackie@example.com",
        # Fields where the signer needs to sign.
        # Check your cast fields via the CLI (`anvil cast [cast_eid]`) or the
        # PDF Templates section on the Anvil app.
        # This basically says: "In the 'myNewFile' file (defined in
        # `file1` above), assign the signature field with cast id of
        # 'sign1' to this signer." You can add multiple signer fields here.
        fields=[
            SignerField(
                # this is the `id` in the `DocumentUpload` object above
                file_id="myNewFile",
                # This is the signing field id in the `SignatureField` above
                field_id="sign1",
            ),
            SignerField(
                # this is the `id` in the `DocumentUpload` object above
                file_id="myNewFile",
                # This is the signing field id in the `SignatureField` above
                field_id="textTag",
            ),
        ],
        signer_type="embedded",
        #
        # You can also change how signatures will be collected.
        # "draw" will allow the signer to draw their signature
        # "text" will insert a text version of the signer's name into the
        # signature field.
        # signature_mode="draw",
        #
        # Whether or not to the signer is required to click each signature
        # field manually. If `False`, the PDF will be signed once the signer
        # accepts the PDF without making the user go through the PDF.
        # accept_each_field=False,
        #
        # URL of where the signer will be redirected after signing.
        # The URL will also have certain URL params added on, so the page
        # can be customized based on the signing action.
        # redirect_url="https://www.google.com",
    )

    # Add your signer.
    packet.add_signer(signer1)

    # Add files to your payload
    packet.add_file(file1)

    # If needed, you can also override or add additional payload fields this way.
    # This is useful if the Anvil API has new features, but `python-anvil` has not
    # yet been updated to support it.
    # payload = packet.create_payload()
    # payload.aNewFeature = True

    # Create your packet
    # If overriding/adding new fields, use the modified payload from
    # `packet.create_payload()`
    res = anvil.create_etch_packet(payload=packet, include_headers=True)
    print(res)


if __name__ == '__main__':
    main()
