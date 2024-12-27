<h1>CLI Usage</h1>

Also provided in this package is a CLI to quickly interact with the Anvil API.

As with the API library, the CLI commands assume that you have a valid API key. Please take a look
at [Anvil API Basics](https://www.useanvil.com/docs/api/basics) for more details on how to get your key.

### Quickstart

In general, adding `--help` after a command will display more information on how to use the command.

<strong>Running the command</strong>

```shell
# The CLI commands will use the environment variable "ANVIL_API_KEY" for all
# Anvil API requests.
$ ANVIL_API_KEY=MY_GENERATED_KEY anvil
Usage: anvil [OPTIONS] COMMAND [ARGS]...

Options:
  --debug / --no-debug
  --help                Show this message and exit.

Commands:
  cast                Fetch Cast data given a Cast eid.
  create-etch         Create an etch packet with a JSON file.
  current-user        Show details about your API user
  download-documents  Download etch documents
  fill-pdf            Fill PDF template with data
  generate-etch-url   Generate an etch url for a signer
  generate-pdf        Generate a PDF
  gql-query           Run a raw graphql query
  weld                Fetch weld info or list of welds

$ ANVIL_API_KEY=MY_GENERATED_KEY anvil fill-pdf --help
Usage: anvil fill-pdf [OPTIONS] TEMPLATE_ID

  Fill PDF template with data

Options:
  -o, --out TEXT    Filename of output PDF  [required]
  -i, --input TEXT  Filename of input CSV that provides data  [required]
  --help            Show this message and exit.
```

For example, you can fill a sample PDF template with the following command

```shell
$ ANVIL_API_KEY=MY_GENERATED_KEY anvil fill-pdf -o test.pdf -i examples/cli/fill_pdf.csv 05xXsZko33JIO6aq5Pnr
```
