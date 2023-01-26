# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned

import pytest
from click.testing import CliRunner

from python_anvil.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def describe_cli():
    def describe_conversion():
        def when_integer(runner):
            result = runner.invoke(cli, ['42'])
            assert result
