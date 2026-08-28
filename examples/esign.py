# Create an Etch e-sign packet via the Anvil API and send it to a signer.
# Docs: https://www.useanvil.com/docs/api/e-signatures
#
# Run this from the project root:
# ANVIL_API_KEY=YOUR_KEY SIGNER_EMAIL=your.real.email@example.com \
#   python examples/create_etch_packet.py
#
# A signature request email is sent to SIGNER_EMAIL, so use your real email
# address. The new packet also appears in your dashboard's e-sign area.

# pylint: disable=duplicate-code

import os

from python_anvil.api import Anvil
from python_anvil.api_resources.mutations.create_etch_packet import CreateEtchPacket
from python_anvil.api_resources.payload import EtchCastRef, EtchSigner, SignerField


API_KEY = os.environ.get("ANVIL_API_KEY")
SIGNER_NAME = "Testy Signer"
SIGNER_EMAIL = os.environ.get("SIGNER_EMAIL") or ""

# The PDF template to sign. This is a sample template available to anyone.
# See https://www.useanvil.com/help/tutorials/set-up-a-pdf-template for details
# on setting up your own template.
PDF_TEMPLATE_EID = "05xXsZko33JIO6aq5Pnr"


def main():
    anvil = Anvil(api_key=API_KEY)

    # Test packets use development signatures and do not count toward your
    # billed packets (`is_test=True` is the default). Pass `is_draft=True`
    # to review the packet in your dashboard before anything is sent.
    packet = CreateEtchPacket(
        name=f"Test Docs - {SIGNER_NAME}",
        signature_email_subject="Custom email subject",
        signature_email_body="Custom please sign these documents....",
    )

    # Reference an existing PDF template from your Anvil account. The `id` is
    # your own name for this file, used by the signer fields below.
    pdf_template = EtchCastRef(
        id="sampleTemplate",
        cast_eid=PDF_TEMPLATE_EID,
    )
    packet.add_file(pdf_template)

    # Fill the PDF with data before it is sent to any signers. Keys here match
    # the field IDs configured on the PDF template.
    packet.add_file_payloads(
        "sampleTemplate",
        dict(data={"name": SIGNER_NAME, "email": SIGNER_EMAIL}),
    )

    # Signers sign in the order they are added. `signer_type="email"` sends
    # the signature request email automatically.
    signer = EtchSigner(
        name=SIGNER_NAME,
        email=SIGNER_EMAIL,
        signer_type="email",
        fields=[
            SignerField(
                file_id="sampleTemplate",
                field_id="signature",
            )
        ],
    )
    packet.add_signer(signer)

    res = anvil.create_etch_packet(payload=packet)
    print(res)


if __name__ == "__main__":
    main()
