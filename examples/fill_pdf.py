import os

from python_anvil.api import Anvil


API_KEY = os.environ.get("ANVIL_API_KEY")
# or set your own key here
# API_KEY = 'my-api-key'


def main():
    anvil = Anvil(api_key=API_KEY)

    # Your fill payload. A number of things can be styled at the
    # document-level, and each field can also be styled individually with the
    # same styling options.
    data = {
        "title": "My document title",
        "font_size": 12,
        "text_color": "#00FF00",
        "data": {
            # cast field id as the key, and either an object containing
            # styling options, or a string containing text to fill the
            # field with.
            "cast123": {
                "textColor": "#0000FF",
                "fontSize": 24,
                "value": "Double-sized text",
            },
            "cast456": "Normal text",
            "cast789": "Normal text 2",
            "cast011": "Normal text 3",
        },
    }

    # Fill the provided cast eid (see PDF Templates in your Anvil account)
    # with the data above. This will return bytes for use in directly writing
    # to a file.
    res = anvil.fill_pdf('abc123', data)

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
    with open('./file.pdf', 'wb') as f:
        f.write(res)


if __name__ == '__main__':
    main()
