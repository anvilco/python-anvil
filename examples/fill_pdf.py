from python_anvil.api import Anvil


API_KEY = 'my-api-key'


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

    # Write the bytes to disk
    with open('./file.pdf', 'wb') as f:
        f.write(res)


if __name__ == '__main__':
    main()
