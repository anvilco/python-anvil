from python_anvil.api import Anvil
from python_anvil.api_resources.payload import GeneratePDFPayload


API_KEY = 'my-api-key'


def main():
    anvil = Anvil(api_key=API_KEY)
    data = GeneratePDFPayload(
        type="html",
        title="Some Title",
        data=dict(
            html="<h2>HTML Heading</h2>",
            css="h2 { color: red }",
        ),
    )
    response = anvil.generate_pdf(data)

    # Write the bytes to disk
    with open('./generated.pdf', 'wb') as f:
        f.write(response)


if __name__ == '__main__':
    main()
