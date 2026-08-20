# Generate a PDF from HTML and CSS via the Anvil API.
# Docs: https://www.useanvil.com/docs/api/generate-pdf#html--css-to-pdf
#
# Run this from the project root:
# ANVIL_API_KEY=YOUR_KEY python examples/generate_html.py
# Then: open ./generate-html-output.pdf

import os

from python_anvil.api import Anvil
from python_anvil.api_resources.payload import GeneratePDFPayload


API_KEY = os.environ.get("ANVIL_API_KEY")

HTML = """
<h1 class='header-one'>What is Lorem Ipsum?</h1>
<p>
  Lorem Ipsum is simply dummy text of the printing and typesetting
  industry. Lorem Ipsum has been the industry's standard dummy text
  ever since the <strong>1500s</strong>, when an unknown printer took
  a galley of type and scrambled it to make a type specimen book.
</p>
<h3 class='header-two'>Where does it come from?</h3>
<p>
  Contrary to popular belief, Lorem Ipsum is not simply random text.
  It has roots in a piece of classical Latin literature from
  <i>45 BC</i>, making it over <strong>2000</strong> years old.
</p>
"""

CSS = """
body { font-size: 14px; color: #171717; }
.header-one { text-decoration: underline; }
.header-two { font-style: italic; }
"""


def main():
    anvil = Anvil(api_key=API_KEY)

    payload = GeneratePDFPayload(
        type="html",
        title="Example HTML to PDF",
        data=dict(html=HTML, css=CSS),
    )

    # Returns the PDF binary
    response = anvil.generate_pdf(payload)

    with open("./generate-html-output.pdf", "wb") as f:
        f.write(response)


if __name__ == "__main__":
    main()
