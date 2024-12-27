# pylint: disable=duplicate-code

import os

from python_anvil.api import Anvil
from python_anvil.api_resources.mutations.create_etch_packet import CreateEtchPacket
from python_anvil.api_resources.payload import EtchCastRef, EtchSigner, SignerField


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

    # You can reference an existing PDF Template from your Anvil account
    # instead of uploading a new file.
    # You can find this information by going to the "PDF Templates" section of
    # your Anvil account, choosing a template, and selecting "API Info" at the
    # top-right of the page.
    # Additionally, you can get this information by using the provided CLI by:
    # `anvil cast --list` to list all your available templates, then:
    # `anvil cast [THE_EID_OF_THE_CAST]` to get a listing of data in that
    # template.
    pdf_template = EtchCastRef(
        # The `id` here is what should be used by signer objects.
        # This can be any string, but should be unique if adding multiple files.
        id="introPages",
        # The eid of the cast you want to use from "API Info" or through the CLI.
        # This is a sample PDF anyone can use
        cast_eid="05xXsZko33JIO6aq5Pnr",
    )

    # Gather your signer data
    signer1 = EtchSigner(
        name="Morgan",
        email="morgan@example.com",
        # Fields where the signer needs to sign.
        # Check your cast fields via the CLI (`anvil cast [cast_eid]`) or the
        # PDF Templates section on the Anvil app.
        # This basically says: "In the 'introPages' file (defined as
        # `pdf_template` above), assign the signature field with cast id of
        # 'def456' to this signer." You can add multiple signer fields here.
        fields=[
            SignerField(
                file_id="introPages",
                field_id="def456",
            )
        ],
        # By default, `signer_type` will be "email" which will automatically
        # send emails when this etch packet is created.
        # It can also be set to "embedded" which will _not_ send emails, and
        # you will need to handle sending the signer URLs manually in some way.
        signer_type="email",
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

    # Add your file(s)
    packet.add_file(pdf_template)

    # If needed, you can also override or add additional payload fields this way.
    # This is useful if the Anvil API has new features, but `python-anvil` has not
    # yet been updated to support it.
    # payload = packet.create_payload()
    # payload.aNewFeature = True

    # Create your packet
    # If overriding/adding new fields, use the modified payload from
    # `packet.create_payload()`
    res = anvil.create_etch_packet(payload=packet)
    print(res)


if __name__ == '__main__':
    main()
