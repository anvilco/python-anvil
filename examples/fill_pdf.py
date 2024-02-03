# Run this from the project root
#
# ANVIL_API_KEY=YOUR_KEY python examples/fill_pdf.py && open ./filled.pdf

import os

from python_anvil.api import Anvil


API_KEY = os.environ.get("ANVIL_API_KEY")
# or set your own key here
# API_KEY = 'my-api-key'

# The PDF template ID to fill. This PDF template ID is a sample template
# available to anyone.
#
# See https://www.useanvil.com/help/tutorials/set-up-a-pdf-template for details
# on setting up your own template
PDF_TEMPLATE_EID = "05xXsZko33JIO6aq5Pnr"

# PDF fill data can be an instance of `FillPDFPayload` or a plain dict.
# `FillPDFPayload` is from `python_anvil.api_resources.payload import FillPDFPayload`.
# If using a plain dict, fill data keys can be either Python snake_case with
# underscores, or in camelCase. Note, though, that the keys in `data` must
# match the keys on the form. This is usually in camelCase.
# If you'd like to use camelCase on all data, you can call `Anvil.fill_pdf()`
# with a full JSON payload instead.
FILL_DATA = {
    "title": "My PDF Title",
    "font_size": 10,
    "text_color": "#333333",
    "data": {
        "shortText": "HELLOO",
        "date": "2022-07-08",
        "name": {
            "firstName": "Robin",
            "mi": "W",
            "lastName": "Smith"
        },
        "email": "testy@example.com",
        "phone": {
            "num": "5554443333",
            "region": "US",
            "baseRegion": "US"
        },
        "usAddress": {
            "street1": "123 Main St #234",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94106",
            "country": "US"
        },
        "ssn": "456454567",
        "ein": "897654321",
        "checkbox": True,
        "radioGroup": "cast68d7e540afba11ecaf289fa5a354293a",
        "decimalNumber": 12345.67,
        "dollar": 123.45,
        "integer": 12345,
        "percent": 50.3,
        "longText": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor.",
        "textPerLine": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor.",
        "textPerLetter": "taH9QGigei6G5BtTUA4",
        "image": "https://placekitten.com/800/495"
    }
}

def main():
    anvil = Anvil(api_key=API_KEY)

    # Fill the provided cast eid (see PDF Templates in your Anvil account)
    # with the data above. This will return bytes for use in directly writing
    # to a file.
    res = anvil.fill_pdf(PDF_TEMPLATE_EID, FILL_DATA)

    # Version number support
    # ----------------------
    # A version number can also be passed in. This will retrieve a specific
    # version of the PDF to be filled if you don't want the current version
    # to be used.
    #
    # You can also use the constant `Anvil.VERSION_LATEST` to fill a PDF with
    # your latest, unpublished changes. Use this if you'd like to fill out a
    # draft version of your template/PDF.
    #
    # res = anvil.fill_pdf('abc123', data, version_number=Anvil.VERSION_LATEST)

    # Write the bytes to disk
    with open('./filled.pdf', 'wb') as f:
        f.write(res)


if __name__ == '__main__':
    main()
