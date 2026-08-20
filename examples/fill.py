# Fill a PDF template with your data via the Anvil API.
# Docs: https://www.useanvil.com/docs/api/fill-pdf
#
# Run this from the project root:
# ANVIL_API_KEY=YOUR_KEY python examples/fill.py && open ./fill-output.pdf

import os

from python_anvil.api import Anvil


API_KEY = os.environ.get("ANVIL_API_KEY")

# The PDF template ID to fill. This is a sample template available to anyone.
# See https://www.useanvil.com/help/tutorials/set-up-a-pdf-template for details
# on setting up your own template.
PDF_TEMPLATE_EID = "05xXsZko33JIO6aq5Pnr"

# Fill data can be an instance of `FillPDFPayload` or a plain dict.
# The keys in `data` must match the field IDs on the PDF template,
# which are usually camelCase.
FILL_DATA = {
    "title": "My PDF Title",
    "font_size": 10,
    "text_color": "#333333",
    "data": {
        "shortText": "Hello World!",
        "date": "2024-01-15",
        "name": {"firstName": "Robin", "mi": "W", "lastName": "Smith"},
        "email": "testy@example.com",
        "phone": {"num": "5554443333", "region": "US", "baseRegion": "US"},
        "usAddress": {
            "street1": "123 Main St #234",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94106",
            "country": "US",
        },
        "ssn": "456454567",
        "ein": "897654321",
        "checkbox": True,
        "decimalNumber": 12345.67,
        "dollar": 123.45,
        "integer": 12345,
        "percent": 50.3,
        "longText": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    },
}


def main():
    anvil = Anvil(api_key=API_KEY)

    # Returns the PDF binary
    res = anvil.fill_pdf(PDF_TEMPLATE_EID, FILL_DATA)

    with open("./fill-output.pdf", "wb") as f:
        f.write(res)


if __name__ == "__main__":
    main()
