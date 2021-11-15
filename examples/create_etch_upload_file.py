# pylint: disable=duplicate-code
# NOTE: The pylint disable above doesn't actually work (yet?)
# SEE: https://github.com/PyCQA/pylint/issues/214

import base64

from python_anvil.api import Anvil
from python_anvil.api_resources.mutations.create_etch_packet import CreateEtchPacket
from python_anvil.api_resources.payload import (
    Base64Upload,
    DocumentUpload,
    EtchSigner,
    SignatureField,
    SignerField,
)


API_KEY = 'my-api-key'


def main():
    anvil = Anvil(api_key=API_KEY)

    # Create an instance of the builder
    packet = CreateEtchPacket(
        name="Etch packet with uploaded file",
        signature_email_subject="Please sign these forms",
        # URL where Anvil will send POST requests when server events happen.
        # Take a look at https://www.useanvil.com/docs/api/e-signatures#webhook-notifications
        # for other details on how to configure webhooks on your account.
        # You can also use sites like webhook.site, requestbin.com or ngrok to
        # test webhooks.
        # webhook_url="https://my.webhook.example.com/etch-events/
    )

    # Get your file(s) ready to sign.
    # For this example, the PDF hasn't been uploaded to Anvil yet, so we need
    # to: open the file, upload the file as a base64 encoded payload along with
    # some data about where the user should sign.
    b64file = None
    with open("./my_local_file.pdf", "rb") as f:
        b64file = base64.b64encode(f.read())

    if not b64file:
        raise ValueError('base64-encoded file not found')

    # Upload the file and define signer field locations.
    file1 = DocumentUpload(
        id="myNewFile",
        title="Please sign this important form",
        # A base64 encoded pdf should be here.
        # Currently, this library does not do this for you, so make sure that
        # the file data is ready at this point.
        file=Base64Upload(
            data=b64file.decode("utf-8"),
            # This is the filename your user will see after signing and
            # downloading their signature packet
            filename="a_custom_filename.pdf",
        ),
        fields=[
            SignatureField(
                id="sign1",
                type="signature",
                page_num=0,
                # The position and size of the field. The coordinates provided here
                # (x=100, y=100) is the top-left of the rectangle.
                rect=dict(x=183, y=100, width=250, height=50),
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
            )
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
