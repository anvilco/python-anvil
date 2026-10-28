![Horizontal Lockupblack](https://user-images.githubusercontent.com/293079/169453889-ae211c6c-7634-4ccd-8ca9-8970c2621b6f.png#gh-light-mode-only)
![Horizontal Lockup copywhite](https://user-images.githubusercontent.com/293079/169453892-895f637b-4633-4a14-b997-960c9e17579b.png#gh-dark-mode-only)

# Anvil API Client for Python

[![PyPI Version](https://img.shields.io/pypi/v/python-anvil.svg)](https://pypi.org/project/python-anvil)
[![PyPI License](https://img.shields.io/pypi/l/python-anvil.svg)](https://pypi.org/project/python-anvil)

This library will allow you to interact with the [Anvil API](https://www.useanvil.com/developers) in Python.

[Anvil](https://www.useanvil.com/developers/) provides easy APIs for all things paperwork.

1. [PDF filling API](https://www.useanvil.com/products/pdf-filling-api/) - fill out a PDF template with a web request and structured JSON data.
2. [PDF generation API](https://www.useanvil.com/products/pdf-generation-api/) - send markdown or HTML and Anvil will render it to a PDF.
3. [Etch e-sign with API](https://www.useanvil.com/products/etch/) - customizable, embeddable, e-signature platform with an API to control the signing process end-to-end.
4. [Anvil Workflows (w/ API)](https://www.useanvil.com/products/workflows/) - Webforms + PDF + e-sign with a powerful no-code builder. Easily collect structured data, generate PDFs, and request signatures.

Learn more on our [Anvil developer page](https://www.useanvil.com/developers/). See the [API guide](https://www.useanvil.com/docs) and the [GraphQL reference](https://www.useanvil.com/docs/api/graphql/reference/) for full documentation.

## Usage

Requires Python 3.10 or later.

```sh
pip install python-anvil
```

Or with Poetry, uv or another tool, add the `python-anvil` package. The `anvil` command line tool is an optional extra:

```sh
pip install 'python-anvil[cli]'
```

A basic example converting your JSON to a filled PDF, then saving the PDF to a file:

```python
from python_anvil import Anvil

# The ID of the PDF template to fill
pdf_template_id = "kA6Da9CuGqUtc6QiBDRR"
# Your API key from your Anvil organization settings
api_key = "7j2JuUWmN4fGjBxsCltWaybHOEy3UEtt"

# JSON data to fill the PDF
example_data = {
    "title": "My PDF Title",
    "fontSize": 10,
    "textColor": "#CC0000",
    "data": {
        "someFieldId": "Hello World!",
    },
}
anvil = Anvil(api_key)
pdf_bytes = anvil.fill_pdf(pdf_template_id, example_data)

# By default, if the PDF has been published then the published version is what will
# be filled. If the PDF has not been published, then the most recent version will
# be filled.
#
# However, a version number can also be passed in that will be used to retrieve and
# fill a specific version of the PDF.
# You can also use the constant `Anvil.VERSION_LATEST` (or `-1`) to fill the most
# recent version of your PDF, whether that version has been published or not.
# Use this if you'd like to fill out a draft version of your template/PDF.
pdf_bytes = anvil.fill_pdf(pdf_template_id, example_data, version_number=Anvil.VERSION_LATEST)

# The filled PDF's raw bytes
with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Types

The client's request types are generated from the Anvil API's GraphQL schema and OpenAPI spec, as [pydantic](https://docs.pydantic.dev/) models in `python_anvil.types`, the Python counterpart of [`@anvilco/types`](https://www.npmjs.com/package/@anvilco/types). Field names are snake_case with camelCase aliases, and either works. The payload models the client's methods take extend them, so a misspelled option or enum value is a validation error:

```python
from python_anvil.api_resources.payload import FillPDFPayload

payload = FillPDFPayload(data={"someFieldId": "Hello"}, font_size=10, use_interactive_fields=True)
pdf_bytes = anvil.fill_pdf(pdf_template_id, payload)
```

* `python_anvil.types.rest`: the REST request bodies, like `FillPdfRequest`, `GenerateMarkdownPdfRequest` and `EtchSigner`.
* `python_anvil.types.graphql`: every type in the GraphQL schema, by name: objects like `EtchPacket`, inputs like `EtchFile`.
* `python_anvil.types.operations`: the arguments of every query and mutation, like `CreateEtchPacketArgs` and `ForgeSubmitArgs`.

A plain `dict` works everywhere a model does, and extra fields are kept, so a feature the API added that this library doesn't know about yet still gets sent.

## API

* [Constructor](#anvilapi_key-options)
* [fill_pdf(template_id, payload, ...)](#fill_pdftemplate_id-payload-version_number-data_type)
* [generate_pdf(payload, ...)](#generate_pdfpayload-data_type)
* [create_etch_packet(payload, ...)](#create_etch_packetpayload-json-response_query-mutation)
* [get_etch_packet(eid, ...)](#get_etch_packeteid-response_query)
* [generate_etch_signing_url(signer_eid, client_user_id)](#generate_etch_signing_urlsigner_eid-client_user_id)
* [download_documents(document_group_eid, ...)](#download_documentsdocument_group_eid-data_type)
* [forge_submit(payload, ...)](#forge_submitpayload-json-response_query-mutation)
* [remove_weld_data(eid)](#remove_weld_dataeid-mutation)
* [request_graphql(query, variables)](#request_graphqlquery-variables)
* [request_rest(method, path, ...)](#request_restmethod-path-json-params-data_type)
* [Anvil.prepare_graphql_file(path_or_file, ...)](#anvilprepare_graphql_filepath_or_file-filename-mimetype)
* [Other queries](#other-queries)
* [Options](#options), including [authentication](#authentication) and [base_url](#base_url)
* [Constants](#constants)
* [Errors](#errors)
* [Rate limits](#rate-limits)
* [Retries](#retries)
* [Command line tool](#command-line-tool)

### Instance methods

##### Anvil(api_key, **options)

Creates an Anvil client instance.

* `api_key` (str) - Your API key. Or pass `access_token=` instead; see [Authentication](#authentication).
* `**options` - [Options](#options) for the client, as keyword arguments.

```python
from python_anvil import Anvil

anvil = Anvil("abc123")
```

The client can also be used as a context manager, which closes its HTTP session when done.

##### fill_pdf(template_id, payload[, version_number, data_type])

Fills a PDF template with your JSON data.

First, you will need to have [uploaded a PDF to Anvil](https://useanvil.com/docs/api/fill-pdf#creating-a-pdf-template). You can find the PDF template's ID on the PDF template's page. If you already have the URL to the page in Anvil, the ID is there as well: `https://app.useanvil.com/org/<your-org-slug>/pdf/<pdf-template-id>`

```python
# PDF template you uploaded to Anvil
pdf_template_id = "kA6Da9CuGqUtc6QiBDRR"

# JSON data to fill the PDF
payload = {
    "title": "My PDF Title",
    "fontSize": 10,
    "textColor": "#CC0000",
    "data": {
        "someFieldId": "Hello World!",
    },
}
pdf_bytes = anvil.fill_pdf(pdf_template_id, payload)

# Be sure to write the file as raw bytes
with open("filled.pdf", "wb") as f:
    f.write(pdf_bytes)
```

* `template_id` (str) - The id of your PDF template from the Anvil UI
* `payload` (dict | str | `FillPDFPayload`) - The JSON data that will fill the PDF template, as a dict, a JSON string, or a `FillPDFPayload`. Keys may be snake_case or camelCase.
  * `title` (str) - _optional_ Set the title encoded into the PDF document
  * `font_size` (int) - _optional_ Set the font size of all filled text. Default is 10.
  * `text_color` (str) - _optional_ Set the text color of all filled text. Default is dark blue.
  * `data` (dict) - The data to fill the PDF. The keys in this object will correspond to a field's ID in the PDF. These field IDs and their types are available on the PDF template's page in the Anvil dashboard.
    * For example `{"someFieldId": "Hello World!"}`
  * See `python_anvil.types.rest.FillPdfRequest` for every option.
* `version_number` (int) - _optional_ The version of the PDF template to fill. Defaults to the latest published version, or the latest version if the template has never been published. See [Constants](#constants).
* `data_type` (str) - _optional_ What to return. `"bytes"` (the default) returns the PDF's bytes; `"stream"` returns the `requests.Response`, to stream a large PDF with `iter_content`. See [request_rest](#request_restmethod-path-json-params-data_type).
* Returns the filled PDF's raw bytes, or raises an [`AnvilRequestError`](#errors).

##### generate_pdf(payload[, data_type])

Dynamically generate a new PDF from your HTML and CSS or markdown.

Useful for agreements, invoices, disclosures, or any other text-heavy documents. This does not require you do anything in the Anvil UI other than setup your API key, just send it data, get a PDF. See [the generate PDF docs](https://useanvil.com/api/generate-pdf) for full details.

* [HTML to PDF docs](https://www.useanvil.com/docs/api/generate-pdf#html--css-to-pdf)
* [Markdown to PDF docs](https://www.useanvil.com/docs/api/generate-pdf#markdown-to-pdf)

Check out our [HTML invoice template](https://github.com/anvilco/html-pdf-invoice-template) for a complete HTML to PDF example.

```python
# An example using an HTML to PDF payload
payload = {
    "title": "Example",
    "type": "html",
    "data": {
        "html": """
            <h1 class='header-one'>What is Lorem Ipsum?</h1>
            <p>
              Lorem Ipsum is simply dummy text...
            </p>
        """,
        "css": """
            body { font-size: 14px; color: #171717; }
            .header-one { text-decoration: underline; }
        """,
    },
}

# An example using a Markdown payload
payload = {
    "title": "Example Invoice",
    "data": [
        {"label": "Name", "content": "Sally Jones"},
        {"content": "Lorem **ipsum** dolor sit _amet_"},
        {
            "table": {
                "firstRowHeaders": True,
                "rows": [
                    ["Description", "Quantity", "Price"],
                    ["4x Large Widgets", "4", "$40.00"],
                    ["10x Medium Sized Widgets in dark blue", "10", "$100.00"],
                    ["10x Small Widgets in white", "6", "$60.00"],
                ],
            },
        },
    ],
}
pdf_bytes = anvil.generate_pdf(payload)

# Be sure to write the file as raw bytes
with open("generated.pdf", "wb") as f:
    f.write(pdf_bytes)
```

* `payload` (dict | str | `GeneratePDFPayload`) - The JSON data that will generate the PDF
  * `title` (str) - _optional_ Set the title encoded into the PDF document
  * `type` (str) - _optional_ `"markdown"` (the default) or `"html"`
  * `data` (list | dict) - The data that generates the PDF: a list of content blocks for Markdown, or `{"html": ..., "css": ...}` for HTML. See [the docs](https://useanvil.com/docs/api/generate-pdf#supported-format-of-data) for all supported objects.
* `data_type` (str) - _optional_ `"bytes"` (the default) or `"stream"`, like [fill_pdf](#fill_pdftemplate_id-payload-version_number-data_type).
* Returns the generated PDF's raw bytes, or raises an [`AnvilRequestError`](#errors).

##### create_etch_packet(payload[, json, response_query, mutation])

Creates an Etch Packet and optionally sends it to the first signer.

```python
from python_anvil import Anvil

anvil = Anvil(api_key)

data = anvil.create_etch_packet({
    "name": "Example packet",
    # Test packets use development signatures and are not billed
    "is_test": True,
    # Send it to the first signer right away
    "is_draft": False,
    "files": [{
        "id": "uploadedNDA",
        "title": "Demo NDA",
        "file": Anvil.prepare_graphql_file("./nda.pdf"),
        "fields": [{
            "id": "signatureOne",
            "type": "signature",
            "pageNum": 0,
            "rect": {"x": 100, "y": 100, "width": 150, "height": 30},
        }],
    }],
    "signers": [{
        "id": "signerOne",
        "name": "Sally Signer",
        "email": "sally@example.com",
        # 'embedded' signers sign in your app with a URL from generate_etch_signing_url.
        # The default, 'email', sends them an email.
        "signerType": "embedded",
        "fields": [{"fileId": "uploadedNDA", "fieldId": "signatureOne"}],
    }],
})

etch_packet = data["createEtchPacket"]
signer_eid = etch_packet["documentGroup"]["signers"][0]["eid"]
```

* `payload` (dict | `CreateEtchPacket` | `CreateEtchPacketPayload`) - The mutation's variables. See the [API Documentation](#api-documentation) for details, and the [`CreateEtchPacket` builder](#the-createetchpacket-builder) below for building a packet step by step. Files to upload can be base64 dicts, or prepared with [prepare_graphql_file](#anvilprepare_graphql_filepath_or_file-filename-mimetype).
* `json` (str) - _optional_ The variables as a JSON string, instead of `payload`.
* `response_query` (str) - _optional_ A GraphQL Query compliant query to use for the data desired in the mutation response. Can be left out to use default.
* `mutation` (str) - _optional_ If you'd like complete control of the GraphQL mutation, you can pass in a GraphQL Mutation compliant string that will be used in the mutation call. This string should also include your response query, as the `response_query` param is ignored if `mutation` is passed. Example:
  ```graphql
    mutation CreateEtchPacket (
      $name: String,
      ...
    ) {
      createEtchPacket (
        name: $name,
        ...
      ) {
        id
        eid
        ...
      }
    }
  ```
* Returns the response's `data`, with the packet under `createEtchPacket`, or raises an [`AnvilRequestError`](#errors).

###### The `CreateEtchPacket` builder

Instead of a dict, `create_etch_packet` takes a `CreateEtchPacket`, a builder that collects the packet's files and signers, generates signer IDs and routing orders, and lets you pre-fill the PDFs:

```python
from python_anvil import Anvil
from python_anvil.api_resources.mutations import CreateEtchPacket
from python_anvil.api_resources.payload import (
    DocumentUpload,
    EtchCastRef,
    EtchSigner,
    FillPDFPayload,
    SignatureField,
    SignerField,
)

anvil = Anvil(api_key)

packet = CreateEtchPacket(
    name="Packet Name",
    signature_email_subject="Please sign these forms",
    # Test packets use development signatures and are not billed
    is_test=True,
)

# A PDF to upload. `prepare_graphql_file` takes a path, bytes or an open file.
packet.add_file(
    DocumentUpload(
        id="myNewFile",
        title="Please sign this important form",
        file=Anvil.prepare_graphql_file("./important-form.pdf"),
        fields=[
            SignatureField(
                id="firstSignature",
                type="signature",
                page_num=0,
                # The position and size of the field
                rect={"x": 100, "y": 100, "width": 100, "height": 100},
            )
        ],
    )
)

# Or a PDF template from your Anvil account. Find its eid under "API Info"
# on the template's page, or with the CLI: `anvil cast --list`
packet.add_file(EtchCastRef(id="fileAlias", cast_eid="CAST_EID_GOES_HERE"))

# Pre-fill the template, with the same payload shape `fill_pdf` takes
packet.add_file_payloads("fileAlias", FillPDFPayload(data={"aTextFieldId": "This is pre-filled."}))

packet.add_signer(
    EtchSigner(
        name="Jackie",
        email="jackie@example.com",
        # Which fields this signer signs: the file ids and field ids above
        fields=[
            SignerField(file_id="myNewFile", field_id="firstSignature"),
            SignerField(file_id="fileAlias", field_id="signOne"),
        ],
        # "email" (the default) emails the signer; "embedded" doesn't, and you
        # send them to a URL from `generate_etch_signing_url` instead
        signer_type="email",
        # "draw" lets the signer draw their signature; "text" types their name
        signature_mode="draw",
        # Where the signer is sent after signing
        redirect_url="https://app.useanvil.com",
    )
)

data = anvil.create_etch_packet(packet)
```

`EtchSigner`, `DocumentUpload` and the other payload models extend the generated [types](#types), so every option the API has is available on them.

##### get_etch_packet(eid[, response_query])

Gets the details of an Etch Packet.

```python
packet = anvil.get_etch_packet(etch_packet_eid)
status, document_group = packet["status"], packet["documentGroup"]
```

* `eid` (str) - your Etch Packet eid
* `response_query` (str) - _optional_ A GraphQL Query compliant query to use for the data desired in the query response. Can be left out to use default.
* Returns the packet, or raises an [`AnvilRequestError`](#errors).

##### generate_etch_signing_url(signer_eid, client_user_id)

Generates an Etch sign URL for an Etch Packet signer. The Etch Packet and its signers must have already been created, the packet must have been sent, and the signer must be an `embedded` signer.

```python
url = anvil.generate_etch_signing_url(
    signer_eid,
    # Your ID for the user who will be signing
    client_user_id="user-123",
)
# Send your user to `url` to sign
```

* `signer_eid` (str) - the eid of the Etch Packet signer, found in the response of the `create_etch_packet` instance method
* `client_user_id` (str) - your ID for the user who will sign
* Returns the signing URL, or raises an [`AnvilRequestError`](#errors).

Also available as `generate_etch_sign_url`, node-anvil's name for it.

##### download_documents(document_group_eid[, data_type])

Returns the document group specified by the `document_group_eid` in Zip file format.

```python
zip_bytes = anvil.download_documents(document_group_eid)
with open("documents.zip", "wb") as f:
    f.write(zip_bytes)

# Or stream it
with anvil.download_documents(document_group_eid, data_type="stream") as response, open("documents.zip", "wb") as f:
    for chunk in response.iter_content(chunk_size=64 * 1024):
        f.write(chunk)
```

* `document_group_eid` (str) - the eid of the document group to download
* `data_type` (str) - _optional_ `"bytes"` (the default) or `"stream"`, like [fill_pdf](#fill_pdftemplate_id-payload-version_number-data_type).
* Returns the zip file's raw bytes, or raises an [`AnvilRequestError`](#errors).

##### forge_submit(payload[, json, response_query, mutation])

Creates or updates a submission to a webform in a Workflow, the same as someone filling in and submitting that webform. Webforms are called Forges in the API.

```python
data = anvil.forge_submit({
    # The webform's eid
    "forge_eid": "your-forge-eid",
    # Keys are the IDs of the webform's fields
    "payload": {
        "name": "Sally Jones",
        "email": "sally@example.com",
    },
    "is_test": True,
})
submission = data["forgeSubmit"]
weld_data_eid = submission["weldData"]["eid"]
```

* `payload` (dict | `ForgeSubmitPayload`) - Requires `forge_eid` and `payload`. Pass `weld_data_eid` and `submission_eid` to update an existing submission. See the [GraphQL reference](https://www.useanvil.com/docs/api/graphql/reference/) for all variables.
* `json` (str) - _optional_ The variables as a JSON string, instead of `payload`.
* `response_query` (str) - _optional_ A GraphQL Query compliant query to use for the data desired in the mutation response. Can be left out to use default.
* `mutation` (str) - _optional_ Your own complete GraphQL mutation. `response_query` is ignored if this is passed.
* Returns the response's `data`, like [request_graphql](#request_graphqlquery-variables).

##### remove_weld_data(eid[, mutation])

Deletes a Workflow submission (a `WeldData`) and everything in it.

```python
removed = anvil.remove_weld_data(weld_data_eid)  # True
```

* `eid` (str) - the eid of the WeldData to remove
* `mutation` (str) - _optional_ Your own complete GraphQL mutation.
* Returns whether it was removed, or raises an [`AnvilRequestError`](#errors).

##### request_graphql(query[, variables])

A fallback function for queries and mutations without a specialized function in this client.

See the [GraphQL reference](https://www.useanvil.com/docs/api/graphql/reference/) for a listing on all possible queries

```python
data = anvil.request_graphql(
    """
    query WeldDataQuery ($eid: String!) {
      weldData (eid: $eid) {
        eid
        isComplete
        isTest
      }
    }
    """,
    {"eid": "nxflNZqxDUbltLUbYWK"},
)
weld_data = data["weldData"]
```

* `query` (str) - GraphQL query or mutation to run. See the [GraphQL reference](https://www.useanvil.com/docs/api/graphql/reference/) for a listing on all possible queries
* `variables` (dict) - _optional_ GraphQL variables for the query. Files to upload can be anywhere in here; see [prepare_graphql_file](#anvilprepare_graphql_filepath_or_file-filename-mimetype).
* Returns the response's `data`: use the query or mutation name to reference the data that you requested. Raises an [`AnvilRequestError`](#errors) for GraphQL errors (which come with a `200` status) and HTTP errors alike.

`query(query, variables)` and `mutate(query, variables)` are the same method, under the names earlier versions used.

##### request_rest(method, path[, json, params, data_type])

A fallback function for REST endpoints without a specialized function in this client.

```python
pdf_bytes = anvil.request_rest(
    "POST",
    f"/api/v1/fill/{pdf_template_id}.pdf",
    json=payload,
    data_type="bytes",
)
```

* `method` (str) - The HTTP method, e.g. `"POST"`
* `path` (str) - Path from the `base_url`, e.g. `/api/v1/fill/abc.pdf`
* `json` (Any) - _optional_ A JSON body
* `params` (dict) - _optional_ Query string parameters
* `data` (Any) - _optional_ A raw body, e.g. bytes or a file object, instead of `json`
* `headers` (dict) - _optional_ Extra headers
* `data_type` (str) - _optional_ What to return. `"json"` (the default) returns the parsed JSON, `"bytes"` the raw body, and `"stream"` the [`requests.Response`](https://requests.readthedocs.io/en/latest/api/#requests.Response) itself, to stream a large body with `iter_content`. Close it when done, or use it as a context manager.
* `timeout` (float) - _optional_ Overrides the client's `timeout` for this request
* Returns the data, or raises an [`AnvilRequestError`](#errors).

### Class methods

##### Anvil.prepare_graphql_file(path_or_file[, filename, mimetype])

Prepares a file for a GraphQL multipart upload, e.g. in `create_etch_packet`'s `files`. A file can be anywhere in a mutation's variables, under a `file` key. Also available as `python_anvil.prepare_graphql_file`.

```python
# A path. The file is opened when the request is sent.
file = Anvil.prepare_graphql_file("./nda.pdf")

# Bytes, which need a filename
file = Anvil.prepare_graphql_file(pdf_bytes, filename="nda.pdf")

# An open binary file object. One with a name, like an open file, is sent with it.
with open("./nda.pdf", "rb") as f:
    file = Anvil.prepare_graphql_file(f)
    data = anvil.create_etch_packet({..., "files": [{"id": "nda", "title": "NDA", "file": file, "fields": [...]}]})
```

* `path_or_file` (str | Path | bytes | file object) - The file to upload
* `filename` (str) - _optional_ The filename to send. Required for `bytes` and for file objects with no `name`, like a `BytesIO`.
* `mimetype` (str) - _optional_ The Content-Type to send the file with. Defaults to one guessed from the filename.
* `ignore_filename_validation` (bool) - _optional_ Send a file without a filename, as `blob`. An escape hatch for things we didn't anticipate.
* Returns an `UploadWithOptions`, which the client recognizes in the variables.

A request that gets rate limited is retried: a file given as a path is opened again, and a file object is rewound. A file object that can't be read again fails with an error rather than sending an empty file. Files can also be passed as a base64 dict, `{"data": "...", "filename": "nda.pdf", "mimetype": "application/pdf"}`, which is sent as plain JSON; `DocumentUpload` encodes an open file this way unless it was prepared with `prepare_graphql_file`.

### Other queries

A few queries have methods of their own, for exploring your account. They return the query's data directly.

* `get_current_user()` - The user the API key belongs to, with their organizations.
* `get_casts(fields=None, show_all=False)` - The PDF templates (casts) in every organization, up to 500 each. By default their `eid`, `title` and `fieldInfo`; `show_all` includes casts that aren't templates.
* `get_cast(eid, fields=None, version_number=None)` - One PDF template.
* `get_welds()` - The workflows (welds) in every organization, with their webforms (forges), up to 500 each.
* `get_weld(eid)` - One workflow, with its webforms.

### Options

Options for the Anvil client, as keyword arguments. Defaults are shown after each option.

```python
Anvil(
    # One of api_key or access_token is required. See Authentication.
    api_key="<your_api_key>",
    access_token="<oauth_access_token>",

    # Where to send requests. See base_url.
    base_url="https://app.useanvil.com",

    # Sent as the User-Agent header
    user_agent="python-anvil/<version>",

    # How many requests to allow per request_limit_ms until the first response from
    # the API tells the client your actual limits. See Rate limits.
    request_limit=1,
    request_limit_ms=1000,

    # Seconds to wait for a connection, and then for each read, before a request
    # fails with a requests.Timeout. A (connect, read) tuple works too; None waits forever.
    timeout=300,

    # How many times to retry a request that got a 500, 502, 503 or 504, or a
    # connection error. See Retries. 0 turns retries off.
    max_retries=5,

    # A requests.Session to send requests with, e.g. one configured with a proxy.
    # Defaults to a session of the client's own.
    session=None,
)
```

##### Authentication

Authenticate with either an API key or an OAuth access token.

**API key:** Find your API keys in your Anvil organization's settings. Requests use HTTP Basic auth: `Basic base64(api_key + ':')`.

```python
anvil = Anvil(api_key="your-api-key")
```

**OAuth access token:** Requests use Bearer auth. Anvil's access tokens are JWTs, which are sent as-is: `Bearer <access_token>`. Any other kind of token is base64 encoded: `Bearer base64(access_token)`.

```python
anvil = Anvil(access_token="your-oauth-access-token")
```

If you pass both, the `access_token` is used.

##### base_url

By default, requests go to production, `https://app.useanvil.com`. Set `base_url` to send them somewhere else. All requests go to that host:

* REST: `{base_url}/api/v1/...`
* GraphQL: `{base_url}/graphql`
* Document downloads: `{base_url}/api/document-group/{eid}.zip`

```python
anvil = Anvil(
    api_key="your-api-key",
    base_url="https://anvil.example.com",
)
```

### Constants

* `Anvil.VERSION_LATEST` (`-1`) - With `fill_pdf`'s `version_number` option, fills the most recent version of a PDF template, published or not. Use it to fill drafts.
* `Anvil.VERSION_LATEST_PUBLISHED` (`-2`) - Fills the latest published version. Unlike leaving `version_number` out, this returns an error if the template has never been published.

Both are also importable from `python_anvil`.

### Errors

When the API responds with an error, the client's methods raise an `AnvilRequestError`. It has the `status_code`, the response `headers`, any partial `data` a GraphQL response came with, and `errors`: a list of dicts that each have a `message`, a `name`, or both.

```python
from python_anvil import Anvil, AnvilRequestError

try:
    pdf_bytes = anvil.fill_pdf(pdf_template_id, payload)
except AnvilRequestError as e:
    print(e.status_code, e.errors)
    print(e)  # e.g. "400: ValidationError (data: Required)"
```

`errors` looks like one of these:

* **GraphQL errors**, as returned by the API, often with a `200` `status_code`:
  ```python
  [{"message": "Not Found", "path": ["etchPacket"], "locations": [{"line": 2, "column": 3}]}]
  ```
* **A REST error.** Validation errors have no `message`, but list each problem field:
  ```python
  [{"name": "AssertionError", "message": "PDF did not generate properly from given HTML!"}]
  [{"name": "ValidationError", "status": 400, "fields": [{"message": "Required", "property": "data"}]}]
  ```
* **A response that isn't JSON**, like a `502` from a proxy. The `name` and `message` are the HTTP status text:
  ```python
  [{"name": "Bad Gateway", "message": "Bad Gateway"}]
  ```
* **A JSON response that couldn't be parsed.** The parsing error's `name` and `message`:
  ```python
  [{"name": "JSONDecodeError", "message": "Expecting value: line 1 column 1 (char 0)"}]
  ```

When a request can't be made at all, e.g. because of a network error or a timeout, the methods raise the [`requests` exception](https://requests.readthedocs.io/en/latest/api/#exceptions), such as `requests.ConnectionError` or `requests.Timeout`. Invalid arguments, like an unsupported `data_type` or a payload that fails validation, raise a `ValueError` (pydantic's `ValidationError` is one) before anything is sent.

`AnvilRequestError` and its base class `AnvilError` are also importable under their old names, `AnvilRequestException` and `AnvilException`, from `python_anvil.exceptions`.

### Rate limits

Our API has request rate limits in place. The initial request made by this client will parse the limits for your account from the `X-RateLimit-Limit` and `X-RateLimit-Interval-Ms` response headers, and then handle the throttling of subsequent requests for you automatically. Any requests made while waiting for that first response will wait for it before being sent.

The limit is your account's, so every client in the process with the same `base_url` and credentials shares one limiter, and the limits it learned. An app that makes a new client for each request is limited as a whole, and the client is thread-safe, so requests from several threads share the limit too. The `request_limit` and `request_limit_ms` options are the starting limits until the first response, and only apply to the first client made for those credentials. Separate processes, like web server workers, each learn the limits for themselves.

Like the API, the client counts requests over a sliding window: it only holds a request back when `X-RateLimit-Limit` requests have already been sent in the last `X-RateLimit-Interval-Ms`. A request counts from when it is sent until an interval after its response arrives. The API counts from when the request reached it, which is somewhere in between, so it never sees more requests in its window than the client allowed.

In the event that this client still receives a `429 Too Many Requests` error response, it will wait for the number of seconds in the `Retry-After` header, plus 50ms, then retry the request. Without a `Retry-After` it waits a second.

See the [Anvil API docs](https://www.useanvil.com/docs/api/getting-started/#rate-limits) for more information on the specifics of the rate limits.

### Retries

A request that gets a `500`, `502`, `503` or `504`, or that can't connect, is retried up to `max_retries` times (5 by default) with exponential backoff: 100ms before the first retry, then 200ms, 400ms, and so on, or a `503`'s `Retry-After` when it has one. Retries wait for the rate limit like any request, and an upload is sent in full again. Mutations are retried as well, so a request the API processed but answered with a `5xx` could be sent twice; pass `max_retries=0` to turn retries off for a client that must not do that. A request that still fails raises an [`AnvilRequestError`](#errors) with the last response, or the `requests.ConnectionError`.

## Command line tool

The `anvil` command, installed with the `cli` extra, is a quick way to try the API from a shell. It uses the `ANVIL_API_KEY` environment variable, and `ANVIL_BASE_URL` to send requests somewhere other than production. Add `--help` after a command for its options.

```sh
$ pip install 'python-anvil[cli]'
$ export ANVIL_API_KEY=MY_GENERATED_KEY

$ anvil
Usage: anvil [OPTIONS] COMMAND [ARGS]...

Commands:
  cast                Fetch Cast data given a Cast eid.
  create-etch         Create an etch packet with a JSON file.
  current-user        Show details about your API user
  download-documents  Download etch documents
  fill-pdf            Fill PDF template with data, once per row of a CSV file.
  generate-etch-url   Generate an etch url for a signer
  generate-pdf        Generate a PDF
  gql-query           Run a raw graphql query
  weld                Fetch weld info or list of welds

# Fill a sample PDF template with each row of a CSV file
$ anvil fill-pdf -o test.pdf -i examples/cli/fill_pdf.csv 05xXsZko33JIO6aq5Pnr
```

## API Documentation

Our general API Documentation can be found [here](https://www.useanvil.com/api/). It's the best resource for up-to-date information about our API and its capabilities.

See the [PDF filling API docs](https://useanvil.com/docs/api/fill-pdf) for more information about the `fill_pdf` method.

## Examples

The [examples](https://github.com/anvilco/python-anvil/tree/master/examples) folder has complete, runnable examples: filling a PDF, generating a PDF from Markdown or HTML, e-signing with a template or an uploaded PDF, embedded signing, workflow submissions, and your own GraphQL queries. Each takes your API key from `ANVIL_API_KEY`.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to run the tests, test against a real environment, regenerate the types, and publish a release.
