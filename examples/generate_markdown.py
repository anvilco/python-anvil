# Generate a PDF from Markdown-structured data via the Anvil API.
# Docs: https://www.useanvil.com/docs/api/generate-pdf#markdown-to-pdf
#
# Run this from the project root:
# ANVIL_API_KEY=YOUR_KEY python examples/generate_markdown.py
# Then: open ./generate-markdown-output.pdf

import os

from python_anvil.api import Anvil
from python_anvil.api_resources.payload import GeneratePDFPayload


API_KEY = os.environ.get("ANVIL_API_KEY")


def main():
    anvil = Anvil(api_key=API_KEY)

    invoice_rows = [
        ["Description", "Quantity", "Price"],
        ["4x Large Widgets", "4", "$40.00"],
        ["10x Medium Sized Widgets in dark blue", "10", "$100.00"],
        ["10x Small Widgets in white", "6", "$60.00"],
    ]

    payload = GeneratePDFPayload(
        type="markdown",
        title="Example Invoice",
        data=[
            dict(label="Name", content="Sally Jones"),
            dict(
                content=(
                    "Lorem **ipsum** dolor sit _amet_, consectetur "
                    "adipiscing elit, sed "
                    "[do eiusmod](https://www.useanvil.com/docs) "
                    "tempor incididunt ut labore et dolore magna aliqua."
                )
            ),
            dict(
                table=dict(
                    firstRowHeaders=True,
                    rows=invoice_rows,
                )
            ),
        ],
    )

    # Returns the PDF binary
    response = anvil.generate_pdf(payload)

    with open("./generate-markdown-output.pdf", "wb") as f:
        f.write(response)


if __name__ == "__main__":
    main()
