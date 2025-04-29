# pylint: disable=unused-variable,unused-argument,expression-not-assigned,singleton-comparison,redefined-outer-name

import os
import time
from unittest.mock import Mock, patch

import pytest

from ..coverage import _launched_recently, cache, get_coverage


class MockCoverage(Mock):
    @staticmethod
    def report(*args, **kwargs):
        return 42.456


@pytest.fixture
def coveragepy_data(tmpdir):
    cwd = tmpdir.chdir()
    with open("foobar.py", "w") as stream:
        pass
    with open(".coverage", "w") as stream:
        stream.write(
            """
            !coverage.py: This is a private format, don\'t read it directly!
            {"arcs":{"foobar.py": [[-1, 2]]}}
            """
        )


@pytest.fixture
def coveragepy_data_custom(tmpdir):
    cwd = tmpdir.chdir()
    with open("foobar.py", "w") as stream:
        pass
    with open(".coveragerc", "w") as stream:
        stream.write(
            """
            [run]
            data_file = .cache/coverage
            """
        )
    os.makedirs(".cache")
    with open(".cache/coverage", "w") as stream:
        stream.write(
            """
            !coverage.py: This is a private format, don\'t read it directly!
            {"arcs":{"foobar.py": [[-1, 3]]}}
            """
        )


def describe_get_coverage():
    @patch("coverage.Coverage", MockCoverage)
    def it_supports_coveragepy(expect, coveragepy_data):
        expect(get_coverage()) == 42.5

    @patch("coverage.Coverage", MockCoverage)
    def it_supports_coveragepy_with_custom_location(expect, coveragepy_data_custom):
        expect(get_coverage()) == 42.5


def describe_launched_recently():
    def when_never_launched(expect):
        cache.set("mock/path", 0)
        expect(_launched_recently("mock/path")) == False

    def when_just_launched(expect):
        cache.set("mock/path", time.time())
        expect(_launched_recently("mock/path")) == True

    def when_launched_59_minutes_ago(expect):
        cache.set("mock/path", time.time() - 60 * 59)
        expect(_launched_recently("mock/path")) == True

    def when_launched_61_minutes_ago(expect):
        cache.set("mock/path", time.time() - 60 * 61)
        expect(_launched_recently("mock/path")) == False
