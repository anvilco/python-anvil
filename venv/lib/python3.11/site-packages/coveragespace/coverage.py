"""Plugins to extract coverage data from various formats."""

import os
import time
import webbrowser
from abc import ABC, abstractmethod

import coverage
import log

from .cache import Cache

cache = Cache()


class BasePlugin(ABC):  # pylint: disable=no-init
    """Base class for coverage plugins."""

    @abstractmethod
    def matches(self, cwd):
        """Determine if the current directory contains coverage data.

        :return bool: Indicates that the current directory should be processed.

        """
        raise NotImplementedError

    @abstractmethod
    def get_coverage(self, cwd):
        """Extract the coverage data from the current directory.

        :return float: Percentage of lines covered.

        """
        raise NotImplementedError

    @abstractmethod
    def get_report(self, cwd):
        """Get the path to the coverage report.

        :return str: Path to coverage report or `None` if not available.

        """
        raise NotImplementedError


def get_coverage(cwd=None, *, always=False) -> float:
    """Extract the current coverage data."""
    cwd = cwd or os.getcwd()

    plugin = _find_plugin(cwd, allow_missing=always)
    if plugin is None:
        return 0.0

    percentage = plugin.get_coverage(cwd)
    return round(percentage, 1)


def launch_report(cwd=None, *, always=False):
    """Open the generated coverage report in a web browser."""
    cwd = cwd or os.getcwd()

    plugin = _find_plugin(cwd, allow_missing=True)

    if plugin:
        report = plugin.get_report(cwd)

        if report and (not _launched_recently(report) or always):
            log.info("Launching report: %s", report)
            webbrowser.open("file://" + report, new=2, autoraise=True)
        elif always:
            log.error("No coverage report found")


def _find_plugin(cwd, allow_missing=False):
    """Find an return a matching coverage plugin."""
    for cls in BasePlugin.__subclasses__():  # pylint: disable=no-member
        plugin = cls()  # type: ignore
        if plugin.matches(cwd):
            return plugin

    msg = "No coverage data found: {}".format(cwd)
    log.info(msg)

    if allow_missing:
        return None

    raise RuntimeError(msg)


def _launched_recently(path):
    now = time.time()
    then = cache.get(path, default=0)
    elapsed = round(now - then, 1)
    log.info("Report last launched %s seconds ago", elapsed)
    cache.set(path, now)
    return elapsed < 60 * 60  # 1 hour


class CoveragePy(BasePlugin):  # pylint: disable=no-init
    """Coverage extractor for the coverage.py format."""

    def matches(self, cwd):
        return any((".coverage" in os.listdir(cwd), ".coveragerc" in os.listdir(cwd)))

    def get_coverage(self, cwd):
        os.chdir(cwd)

        cov = coverage.Coverage()
        cov.load()

        with open(os.devnull, "w") as ignore:
            total = cov.report(file=ignore)

        return total

    def get_report(self, cwd):
        for root, _, _ in os.walk(cwd):
            path = os.path.join(root, "htmlcov", "index.html")

            if os.path.isfile(path):
                log.info("Found coverage report: %s", path)
                return path

        log.info("No coverage report found: %s", cwd)
        return None
