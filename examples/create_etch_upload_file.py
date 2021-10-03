# pylint: disable=duplicate-code
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
        name="Packet Name",
        signature_email_subject="Please sign these forms",
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
        fields=[
            SignerField(
                # this is the `id` in the `DocumentUpload` object above
                file_id="myNewFile",
                # This is the signing field id in the `SignatureField` above
                field_id="sign1",
            )
        ],
        signer_type="embedded",
    )

    # Add your signer.
    packet.add_signer(signer1)

    # Add files to your payload
    packet.add_file(file1)

    res = anvil.create_etch_packet(payload=packet, include_headers=True)
    print(res)


if __name__ == '__main__':
    main()
