"""Update project metrics on The Coverage Space.

Usage:
  coveragespace [--verbose]
  coveragespace update <metric> [<value>] [--verbose] [--exit-code]
  coveragespace reset [--verbose]
  coveragespace view [--verbose]
  coveragespace (-h | --help)
  coveragespace (-V | --version)

Options:
  -h --help         Show this help screen.
  -V --version      Show the program version.
  -v --verbose      Always display the coverage metrics.
  -x --exit-code    Return non-zero exit code on failures.

"""

import json
import sys
from shutil import get_terminal_size

import colorama
import log
from docopt import docopt

from . import VERSION, api, coverage, environments, repository


def main():
    """Parse command-line arguments, configure logging, and run the program."""
    colorama.init(autoreset=True)
    arguments = docopt(__doc__, version=VERSION)
    log.init(level=log.DEBUG if arguments["--verbose"] else log.WARNING)

    if environments.ci():
        log.info("Coverage check skipped when running on CI service")
        sys.exit()

    if arguments["view"]:
        success = view()
    else:
        slug = repository.get_slug()
        if arguments["update"]:
            success = call(
                slug,
                arguments["<metric>"],
                arguments["<value>"],
                verbose=arguments["--verbose"],
                hardfail=arguments["--exit-code"],
            )
        elif arguments["reset"]:
            success = call(slug, reset=True)
        else:
            success = call(slug, launch=True)

    if not success and arguments["--exit-code"]:
        sys.exit(1)


def call(
    slug: str,
    metric: str = "overall",
    value: float = 0,
    *,
    reset: bool = False,
    launch: bool = False,
    verbose: bool = False,
    hardfail: bool = False,
):
    """Call the API and display errors."""
    if reset:
        response = api.delete(slug)
    else:
        data = {metric: value or coverage.get_coverage(always=launch)}
        response = api.put(slug, data)

    if response.status_code == 200:
        if verbose or launch:
            display("coverage updated", response.json(), colorama.Fore.GREEN)
        if launch:
            coverage.launch_report(always=True)
        return True

    if response.status_code == 202:
        display("coverage reset", response.json(), colorama.Fore.BLUE)
        return True

    if response.status_code == 422:
        color = colorama.Fore.RED if hardfail else colorama.Fore.YELLOW
        data = response.json()
        prefix = "poetry run " if environments.poetry() else ""
        data["help"] = f"To reset metrics, run: ^{prefix}coveragespace reset$"  # type: ignore
        display("coverage decreased", data, color)
        coverage.launch_report(always=launch)
        return False

    try:
        data = response.json()
        display("coverage unknown", data, colorama.Fore.RED)
    except (TypeError, ValueError) as exc:
        data = response.data.decode("utf-8")
        log.error("%s\n\nwhen decoding response:\n\n%s\n", exc, data)
    return False


def display(title, data, color=""):
    """Write colored text to the console."""
    width, _ = get_terminal_size()
    header = color + "{0:=^{1}}".format(" " + title + " ", width)
    header = header.replace(
        title, colorama.Style.BRIGHT + title + colorama.Style.NORMAL
    )
    body = json.dumps(data, indent=4)
    body = body.replace("^", colorama.Fore.WHITE + colorama.Style.BRIGHT)
    body = body.replace("$", colorama.Style.RESET_ALL)
    footer = color + "=" * width
    print(header)
    print(body)
    print(footer)


def view():
    """View the local coverage report."""
    coverage.launch_report(always=True)
    return True
