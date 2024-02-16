# Run this from the project root
#
# ANVIL_API_KEY=YOUR_KEY python examples/generate_pdf.py && open ./generated.pdf

import os

from python_anvil.api import Anvil
from python_anvil.api_resources.payload import GeneratePDFPayload


API_KEY = os.environ.get("ANVIL_API_KEY")
# or set your own key here
# API_KEY = 'my-api-key'


def main():
    anvil = Anvil(api_key=API_KEY)

    data = html_data()

    # You can specify data in literal dict form
    # data = html_data_literal()

    # Or you can generate from markdown
    # data = markdown_data()

    response = anvil.generate_pdf(data)

    # Write the bytes to disk
    with open('./generated.pdf', 'wb') as f:
        f.write(response)

def html_data():
  return GeneratePDFPayload(
      type="html",
      title="Some Title",
      data=dict(
          html="<h2>HTML Heading</h2>",
          css="h2 { color: red }",
      ),

      # Optional page configuration
      # page=dict(
      #     width="8.5in",
      #     height="11in",
      # ),
  )


def html_data_literal():
  return {
      "type": "html",
      "title": "Some Title",
      "data": {
          "html": "<h2>HTML Heading</h2>",
          "css": "h2 { color: blue }",
      }
  }


def markdown_data():
  return GeneratePDFPayload(
      type="markdown",
      title="Some Title",
      data=[dict(
          label="Test",
          content="Lorem __Ipsum__"
      )],

      # Optional args
      # font_size=10,
      # font_family="Lobster",
      # text_color="#cc0000",
  )




if __name__ == '__main__':
    main()
