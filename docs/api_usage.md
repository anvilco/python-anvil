# API Usage

All methods assume that a valid API key is already available. Please take a look
at [Anvil API Basics](https://www.useanvil.com/docs/api/basics) for more details on how to get your key.

### `Anvil` constructor

* `api_key` - Your Anvil API key, either development or production
* `environment` (default: `'dev'`) - The type of key being used. This affects how the library sets rate limits on API
  calls if a rate limit error occurs. Allowed values: `["dev", "prod"]`

Example:

```python
from python_anvil.api import Anvil

anvil = Anvil(api_key="MY_KEY", environment="prod")
```

### Anvil.fill_pdf

Anvil allows you to fill templatized PDFs using the payload provided.

**template_data: str (required)**

The template id that will be filled. The template must already exist in your organization account.

**payload: Optional[Union[dict, AnyStr, FillPDFPayload]]**

Data to embed into the PDF. Supported `payload` types are:

* `dict` - root-level keys should be in snake-case (i.e. some_var_name).
* `str`/JSON - raw JSON string/JSON payload to send to the endpoint. There will be minimal processing of payload. Make
  sure all required data is set.
* `FillPDFPayload` - dataclass (see: [Data Types](#data-types))

Example:

```python
from python_anvil.api import Anvil

anvil = Anvil(api_key="MY KEY")
data = {
    "title": "Some Title",
    "font_size": 10,
    "data": {"textField": "Some data"}
}
response = anvil.fill_pdf("some_template", data)
```

### Anvil.generate_pdf

Anvil allows you to dynamically generate new PDFs using JSON data you provide via the /api/v1/generate-pdf REST
endpoint. Useful for agreements, invoices, disclosures, or any other text-heavy documents.

By default, `generate_pdf` will format data assuming it's in [Markdown](https://daringfireball.net/projects/markdown/).

HTML is another supported input type. This can be used by providing
`"type": "html"` in the payload and making the `data` field a dict containing
keys `"html"` and an optional `"css"`. Example below:

```python
from python_anvil.api import Anvil

anvil = Anvil(api_key="MY KEY")
data = {
    "type": "html",
    "title": "Some Title",
    "data": {
      "html": "<h2>HTML Heading</h2>",
      "css": "h2 { color: red }",
    }
}
response = anvil.generate_pdf(data)
```

See the official [Anvil Docs on HTML to PDF](https://www.useanvil.com/docs/api/generate-pdf#html--css-to-pdf)
for more details.

**payload: Union[dict, AnyStr, GeneratePDFPayload]**

Data to embed into the PDF. Supported `payload` types are:

* `dict` - root-level keys should be in snake-case (i.e. some_var_name).
* `str`/JSON - raw JSON string/JSON payload to send to the endpoint. There will be minimal processing of payload. Make
  sure all required data is set.
* `GeneratePDFPayload` - dataclass (see: [Data Types](#data-types))

### Anvil.get_casts

Queries the GraphQL API and returns a list of available casts.

By default, this will retrieve the `'eid', 'title', 'fieldInfo'` fields for the
casts, but this can be changed with the `fields` argument.

* `fields` - (Optional) list of fields to return for each Cast

### Anvil.get_cast

Queries the GraphQL API for data about a single cast.

By default, this will retrieve the `'eid', 'title', 'fieldInfo'` fields for the
casts, but this can be changed with the `fields` argument.

* `eid` - The eid of the Cast
* `fields` - (Optional) list of fields you want from the Cast instance.

### Anvil.get_welds

Queries the GraphQL API and returns a list of available welds.

Fetching the welds is the best way to fetch the data submitted to a given workflow
(weld). An instances of a workflow is called a weldData.

### Anvil.get_current_user

Returns the currently logged in user. You can generally get a lot of what you
may need from this query.

### Anvil.download_documents

Retrieves zip file data from the API with a given docoument eid.

When all parties have signed an Etch Packet, you can fetch the completed
documents in zip form with this API call.

* `document_group_eid` - The eid of the document group you wish to download.

### Anvil.generate_signing_url

Generates a signing URL for a given signature process.

By default, we will solicit all signatures via email. However, if you'd like
to embed the signature process into one of your own flows we support this as
well.

* `signer_eid` - eid of the signer. This can be found in the response of the
  `createEtchPacket` mutation.
* `client_user_id` - the signer's user id in your system

### Anvil.create_etch_packet

Creates an Anvil Etch E-sign packet.

This is one of the more complex processes due to the different types of data
needed in the final payload. Please take a look at the [advanced section](advanced.md#create-etch-packet)
for more details the creation process.

* `payload` - Payload to use for the packet. Accepted types are `dict`,
  `CreateEtchPacket` and `CreateEtchPacketPayload`.
* `json` - Raw JSON payload of the etch packet

### Anvil.forge_submit

Creates an Anvil submission
object. [See documentation](https://www.useanvil.com/docs/api/graphql/reference/#operation-forgesubmit-Mutations) for
more details.

* `payload` - Payload to use for the submission. Accepted types are `dict`,
  `ForgeSubmit` and `ForgeSubmitPayload`.
* `json` - Raw JSON payload of the `forgeSubmit` mutation.

### Data Types

This package uses `pydantic` heavily to serialize and validate data.
These dataclasses exist in `python_anvil/api_resources/payload.py`.

Please see [pydantic's docs](https://pydantic-docs.helpmanual.io/) for more details on how to use these
dataclass instances.


### Supported kwargs

All API functions also accept arbitrary kwargs which will affect how some underlying functions behave.

* `retry` (default: `True`) - When this is passed as an argument, it will enable/disable request retries due to rate
  limit errors. By default, this library _will_ retry requests for a maximum of 5 times.
* `include_headers` (default: `False`) - When this is passed as an argument, the function's return will be a `dict`
  containing: `{"response": {...data}, "headers": {...data}}`. This is useful if you would like to have more control
  over the response data. Specifically, you can control API retries when used with `retry=False`.

Example:

```python
from python_anvil.api import Anvil

anvil = Anvil(api_key=MY_API_KEY)

# Including headers
res = anvil.fill_pdf("some_template_id", payload, include_headers=True)
response = res["response"]
headers = res["headers"]

# No headers
res = anvil.fill_pdf("some_template_id", payload, include_headers=False)
```

### Using fields that are not yet supported

There may be times when the Anvil API has new features or options, but explicit support hasn't yet been added to this
library. As of version 1.1 of `python-anvil`, extra fields are supported on all model objects.

For example:

```python
from python_anvil.api_resources.payload import EtchSigner, SignerField

# Use `EtchSigner`
signer = EtchSigner(
  name="Taylor Doe",
  email="tdoe@example.com",
  fields=[SignerField(file_id="file1", field_id="sig1")]
)

# Previously, adding this next field would raise an error, or would be removed from the resulting JSON payload, but this
# is now supported.
# NOTE: the field name should be the _exact_ field name needed in JSON. This will usually be camel-case (myVariable) and
# not the typical PEP 8 standard snake case (my_variable).
signer.newFeature = True
```
