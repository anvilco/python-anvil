# pylint: disable=too-many-locals
import click
import os
from csv import DictReader
from logging import getLogger
from tabulate import tabulate
from time import sleep
from typing import List

from python_anvil import utils

from .api import Anvil
from .api_resources.payload import FillPDFPayload


logger = getLogger(__name__)


def get_api_key():
    return os.environ.get("ANVIL_API_KEY")


def contains_headers(res):
    return isinstance(res, dict) and "headers" in res


def process_response(res):
    return res["response"], res["headers"]


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx: click.Context, debug=False):
    ctx.ensure_object(dict)

    key = get_api_key()
    if not key:
        raise ValueError("$ANVIL_API_KEY must be defined in your environment variables")

    anvil = Anvil(key)
    ctx.obj["anvil"] = anvil
    ctx.obj["debug"] = debug


@cli.command("current-user", help="Show details about your API user")
@click.pass_context
def current_user(ctx):
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]
    res = anvil.get_current_user(debug=debug)

    if contains_headers(res):
        res, headers = process_response(res)
        if debug:
            click.echo(headers)

    click.echo(f"User data: \n\n {res}")


@cli.command()
@click.option(
    "-i", "-in", "input_filename", help="Filename of input payload", required=True
)
@click.option(
    "-o",
    "--out",
    "out_filename",
    help="Filename of output PDF",
    required=True,
)
@click.pass_context
def generate_pdf(ctx, input_filename, out_filename):
    """Generate a PDF."""
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]

    with click.open_file(input_filename, "r") as infile:
        res = anvil.generate_pdf(infile.read(), debug=debug)

    if contains_headers(res):
        res, headers = process_response(res)
        if debug:
            click.echo(headers)

    with click.open_file(out_filename, "wb") as file:
        file.write(res)


@cli.command()
@click.option("-l", "--list", "list_all", help="List all available welds", is_flag=True)
@click.argument("eid", default="")
@click.pass_context
def weld(ctx, eid, list_all):
    """Fetch weld info or list of welds."""
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]

    if list_all:
        res = anvil.get_welds(debug=debug)
        if contains_headers(res):
            res, headers = process_response(res)
            if debug:
                click.echo(headers)

        data = [(w["eid"], w.get("slug"), w.get("title")) for w in res]
        click.echo(tabulate(data, tablefmt="pretty", headers=["eid", "slug", "title"]))
        return

    if not eid:
        raise Exception("You need to pass in a weld eid")


@cli.command()
@click.option(
    "-l",
    "--list",
    "list_templates",
    help="List available casts marked as templates",
    is_flag=True,
)
@click.option(
    "-a", "--all", "list_all", help="List all casts, even non-templates", is_flag=True
)
@click.argument("eid", default="")
@click.pass_context
def cast(ctx, eid, list_all, list_templates):
    """Fetch Cast data given a Cast eid."""
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]

    if not eid and not (list_templates or list_all):
        raise AssertionError("Cast eid or --list/--all option required")

    if list_all or list_templates:
        res = anvil.get_casts(debug=debug, show_all=list_all)

        if contains_headers(res):
            res, headers = process_response(res)
            if debug:
                click.echo(headers)

        data = [[c["eid"], c["title"]] for c in res]
        click.echo(tabulate(data, headers=["eid", "title"]))
        return

    if eid:
        click.echo(f"Getting cast with eid '{eid}' \n")
        res = anvil.get_cast(eid, debug=debug)

        if contains_headers(res):
            res, headers = process_response(res)
            if debug:
                click.echo(headers)

        def get_field_info(cc):
            return tabulate(cc.get("fields", []))

        if not res:
            click.echo(f"Cast with eid: {eid} not found")
            return

        table_data = [[res["eid"], res["title"], get_field_info(res["fieldInfo"])]]
        click.echo(tabulate(table_data, tablefmt="pretty", headers=res.keys()))


@cli.command("fill-pdf")
@click.argument("template_id")
@click.option(
    "-o",
    "--out",
    "out_filename",
    required=True,
    help="Filename of output PDF",
)
@click.option(
    "-i",
    "--input",
    "payload_csv",
    required=True,
    help="Filename of input CSV that provides data",
)
@click.pass_context
def fill_pdf(ctx, template_id, out_filename, payload_csv):
    """Fill PDF template with data."""
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]

    if all([template_id, out_filename, payload_csv]):
        payloads = []  # type: List[FillPDFPayload]
        with click.open_file(payload_csv, "r") as csv_file:
            reader = DictReader(csv_file)
            # NOTE: This is potentially problematic for larger datasets and/or
            # very long csv files, but not sure if the use-case is there yet..
            #
            # Once memory/execution times are a problem for this command, the
            # `progressbar()` can be removed below and we could just work on
            # each csv line individually without loading it all into memory
            # as we are doing here (or with `list()`). But then that removes
            # the nice progress bar, so..trade-offs!
            for row in reader:
                payloads.append(FillPDFPayload(data=dict(row)))

        with click.progressbar(payloads, label="Filling PDFs and saving") as ps:
            indexed_files = utils.build_batch_filenames(out_filename)
            for payload in ps:
                res = anvil.fill_pdf(template_id, payload.to_dict(), debug=debug)

                if contains_headers(res):
                    res, headers = process_response(res)
                    if debug:
                        click.echo(headers)

                next_file = next(indexed_files)
                click.echo(f"\nWriting {next_file}")
                with click.open_file(next_file, "wb") as file:
                    file.write(res)
                sleep(1)


@cli.command("create-etch")
@click.option(
    "-p",
    "--payload",
    "payload",
    type=click.File('rb'),
    required=True,
    help="File that contains JSON payload",
)
@click.pass_context
def create_etch(ctx, payload):
    """Create an etch packet with a JSON file.

    Example usage:
        # For existing files
        > $ ANVIL_API_KEY=mykey anvil create-etch --payload=my_payload_file.json

        # You can also get data from STDIN
        > $ ANVIL_API_KEY=mykey anvil create-etch --payload -
    """
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]
    res = anvil.create_etch_packet(json=payload.read(), debug=debug)

    if contains_headers(res):
        res, headers = process_response(res)
        if debug:
            click.echo(headers)

    if "data" in res:
        click.echo(
            f"Etch packet created with id: {res['data']['createEtchPacket']['eid']}"
        )
    else:
        click.echo(res)


@cli.command("generate-etch-url", help="Generate an etch url for a signer")
@click.option(
    "-c",
    "--client",
    "client_user_id",
    required=True,
    help="The signer's user id in your system belongs here",
)
@click.option(
    "-s",
    "--signer",
    "signer_eid",
    required=True,
    help="The eid of the next signer belongs here. The signer's eid can be "
    "found in the response of the `createEtchPacket` mutation",
)
@click.pass_context
def generate_etch_url(ctx, signer_eid, client_user_id):
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]
    res = anvil.generate_etch_signing_url(
        signer_eid=signer_eid, client_user_id=client_user_id, debug=debug
    )

    if contains_headers(res):
        res, headers = process_response(res)
        if debug:
            click.echo(headers)

    url = res.get("data", {}).get("generateEtchSignURL")
    click.echo(f"Signing URL is: {url}")


@cli.command("download-documents", help="Download etch documents")
@click.option(
    "-d",
    "--document-group",
    "document_group_eid",
    required=True,
    help="The documentGroupEid can be found in the response of the "
    "createEtchPacket or sendEtchPacket mutations.",
)
@click.option(
    "-f", "--filename", "filename", help="Optional filename for the downloaded zip file"
)
@click.option(
    "--stdout/--no-stdout",
    help="Instead of writing to a file, output data to STDOUT",
    default=False,
)
@click.pass_context
def download_documents(ctx, document_group_eid, filename, stdout):
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]
    res = anvil.download_documents(document_group_eid, debug=debug)

    if contains_headers(res):
        res, headers = process_response(res)
        if debug:
            click.echo(headers)

    if not stdout:
        if not filename:
            filename = f"{document_group_eid}.zip"

        with click.open_file(filename, 'wb') as out_file:
            out_file.write(res)
        click.echo(f"Saved as '{click.format_filename(filename)}'")
    else:
        click.echo(res)


@cli.command('gql-query', help="Run a raw graphql query")
@click.option(
    "-q",
    "--query",
    "query",
    required=True,
    help="The query body. This is the 'query' part of the JSON payload",
)
@click.option(
    "-v",
    "--variables",
    "variables",
    help="The query variables. This is the 'variables' part of the JSON payload",
)
@click.pass_context
def gql_query(ctx, query, variables):
    anvil = ctx.obj["anvil"]
    debug = ctx.obj["debug"]
    res = anvil.query(query, variables=variables, debug=debug)

    if contains_headers(res):
        res, headers = process_response(res)
        if debug:
            click.echo(headers)

    click.echo(res)


if __name__ == "__main__":  # pragma: no cover
    cli()  # pylint: disable=no-value-for-parameter
