ETCH_TEST_PAYLOAD = dict(
    name="Packet name",
    signature_email_subject="The subject",
    signers=[
        dict(
            name="Joe Doe",
            email="joe@example.com",
            fields=[dict(fileId="existingCast", fieldId="signMe")],
        )
    ],
    files=[
        dict(
            id="someFile",
            title="Sign This",
            file=dict(
                data="Some Base64 Thing",
                filename="someFile.pdf",
                mimetype="application/pdf",
            ),
            fields=[
                dict(
                    id="signField",
                    type="signature",
                    pageNum=0,
                    rect=dict(x=100, y=100, width=100, height=100),
                )
            ],
        )
    ],
)

EXPECTED_FILES = [
    {
        'id': 'someFile',
        'title': 'Sign This',
        'file': {
            'data': 'Some Base64 Thing',
            'filename': 'someFile.pdf',
            'mimetype': 'application/pdf',
        },
        'fields': [
            {
                'id': 'signField',
                'type': 'signature',
                'pageNum': 0,
                'rect': {'x': 100, 'y': 100, 'width': 100, 'height': 100},
            }
        ],
        'fontSize': 14,
        'textColor': '#000000',
    }
]

EXPECTED_ETCH_TEST_PAYLOAD = {
    'name': 'Packet name',
    'signatureEmailSubject': 'The subject',
    'signers': [
        {
            'name': 'Joe Doe',
            'email': 'joe@example.com',
            'fields': [{'fileId': 'existingCast', 'fieldId': 'signMe'}],
            'id': 'signer-mock-generated',
            'routingOrder': 1,
            'signerType': 'email',
        }
    ],
    'isDraft': False,
    'isTest': True,
    'data': {'payloads': {}},
    'signaturePageOptions': {},
    'files': EXPECTED_FILES,
}

EXPECTED_ETCH_TEST_PAYLOAD_JSON = {
    'name': 'Packet name',
    'signatureEmailSubject': 'The subject',
    'signers': [
        {
            'name': 'Joe Doe',
            'email': 'joe@example.com',
            'fields': [{'fileId': 'existingCast', 'fieldId': 'signMe'}],
            'id': '',
            'routingOrder': 1,
            'signerType': 'email',
        }
    ],
    'isDraft': False,
    'isTest': True,
    'data': None,
    'signaturePageOptions': None,
    'files': EXPECTED_FILES,
}
