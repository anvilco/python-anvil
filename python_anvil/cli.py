"""The `anvil` command line tool. Needs the `cli` extra: pip install 'python-anvil[cli]'."""

from __future__ import annotations

import json
import logging
import os
import sys
from csv import DictReader
from time import sleep

from python_anvil import utils
from python_anvil.api import Anvil
from python_anvil.api_resources.payload import FillPDFPayload
from python_anvil.constants import DEFAULT_BASE_URL
from python_anvil.errors import AnvilRequestError


try:
    import click
    from tabulate import tabulate
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "The anvil command line tool needs the `cli` extra: "
        "pip install 'python-anvil[cli]'"
    ) from e


logger = logging.getLogger(__name__)


def get_api_key() -> str | None:
    return os.environ.get("ANVIL_API_KEY")


def get_base_url() -> str:
    return os.environ.get("ANVIL_BASE_URL") or DEFAULT_BASE_URL


class AnvilGroup(click.Group):
    """Reports API errors in one line, instead of a traceback."""

    def invoke(self, ctx: click.Context):  # type: ignore[no-untyped-def]
        try:
            return super().invoke(ctx)
        except AnvilRequestError as e:
            click.echo(f"Error: {e}", err=True)
            if ctx.obj and ctx.obj.get("debug"):
                click.echo(json.dumps(e.errors, indent=2), err=True)
            sys.exit(1)


@click.group(cls=AnvilGroup)
@click.option("--debug/--no-debug", default=False, help="Log every request")
@click.pass_context
def cli(ctx: click.Context, debug: bool = False):
    """Anvil API command line tool.

    Set $ANVIL_API_KEY to your API key. Set $ANVIL_BASE_URL to send requests
    somewhere other than production.
    """
    ctx.ensure_object(dict)

    key = get_api_key()
    if not key:
        raise ValueError("$ANVIL_API_KEY must be defined in your environment variables")

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    ctx.obj["anvil"] = Anvil(key, base_url=get_base_url())
    ctx.obj["debug"] = debug


@cli.command("current-user", help="Show details about your API user")
@click.pass_context
def current_user(ctx):
    anvil: Anvil = ctx.obj["anvil"]
    res = anvil.get_current_user()
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
    anvil: Anvil = ctx.obj["anvil"]

    with click.open_file(input_filename) as infile:
        res = anvil.generate_pdf(infile.read())

    with click.open_file(out_filename, "wb") as file:
        file.write(res)


@cli.command()
@click.option("-l", "--list", "list_all", help="List all available welds", is_flag=True)
@click.argument("eid", default="")
@click.pass_context
def weld(ctx, eid, list_all):
    """Fetch weld info or list of welds."""
    anvil: Anvil = ctx.obj["anvil"]

    if list_all:
        res = anvil.get_welds()
        data = [(w["eid"], w.get("slug"), w.get("name"), w.get("forges")) for w in res]
        click.echo(
            tabulate(
                data, tablefmt="pretty", headers=["eid", "slug", "title", "forges"]
            )
        )
        return

    if not eid:
        raise click.UsageError("You need to pass in a weld eid")

    click.echo(anvil.get_weld(eid))


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
@click.option(
    "--version_number", type=int, help="Get the specified version of this cast"
)
@click.argument("eid", default="")
@click.pass_context
def cast(ctx, eid, version_number, list_all, list_templates):
    """Fetch Cast data given a Cast eid."""
    anvil: Anvil = ctx.obj["anvil"]

    if not eid and not (list_templates or list_all):
        raise click.UsageError("Cast eid or --list/--all option required")

    if list_all or list_templates:
        casts = anvil.get_casts(show_all=list_all)
        data = [[c["eid"], c["title"]] for c in casts]
        click.echo(tabulate(data, headers=["eid", "title"]))
        return

    click.echo(f"Getting cast with eid '{eid}' \n")
    res = anvil.get_cast(eid, version_number=version_number)

    if not res:
        click.echo(f"Cast with eid: {eid} not found")
        return

    def get_field_info(cc):
        return tabulate(cc.get("fields", []))

    table_data = [[res["eid"], res["title"], get_field_info(res["fieldInfo"])]]
    click.echo(tabulate(table_data, tablefmt="pretty", headers=list(res.keys())))


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
    """Fill PDF template with data, once per row of a CSV file."""
    anvil: Anvil = ctx.obj["anvil"]

    payloads: list[FillPDFPayload] = []
    with click.open_file(payload_csv) as csv_file:
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
            res = anvil.fill_pdf(template_id, payload)

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
    type=click.File("rb"),
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
    anvil: Anvil = ctx.obj["anvil"]
    res = anvil.create_etch_packet(json=payload.read())
    click.echo(f"Etch packet created with id: {res['createEtchPacket']['eid']}")


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
    anvil: Anvil = ctx.obj["anvil"]
    url = anvil.generate_etch_signing_url(
        signer_eid=signer_eid, client_user_id=client_user_id
    )
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
    anvil: Anvil = ctx.obj["anvil"]
    res = anvil.download_documents(document_group_eid)

    if stdout:
        click.echo(res)
        return

    if not filename:
        filename = f"{document_group_eid}.zip"

    with click.open_file(filename, "wb") as out_file:
        out_file.write(res)
    click.echo(f"Saved as '{click.format_filename(filename)}'")


@cli.command("gql-query", help="Run a raw graphql query")
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
    help="The query variables, as JSON. This is the 'variables' part of the JSON payload",
)
@click.pass_context
def gql_query(ctx, query, variables):
    anvil: Anvil = ctx.obj["anvil"]
    res = anvil.query(query, variables=json.loads(variables) if variables else None)
    click.echo(json.dumps(res, indent=2))


if __name__ == "__main__":  # pragma: no cover
    cli()
