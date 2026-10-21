import json
from unittest import mock

import pytest
from click.testing import CliRunner

from python_anvil.cli import cli
from python_anvil.errors import AnvilRequestError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv("ANVIL_API_KEY", "MY_KEY")
    monkeypatch.delenv("ANVIL_BASE_URL", raising=False)


def describe_cli():
    @mock.patch("python_anvil.api.Anvil.get_current_user")
    def it_requires_an_api_key(get_current_user, runner, monkeypatch):
        monkeypatch.delenv("ANVIL_API_KEY", raising=False)
        res = runner.invoke(cli, ["current-user"])
        assert get_current_user.call_count == 0
        assert isinstance(res.exception, ValueError)

    @mock.patch("python_anvil.api.Anvil.get_current_user")
    def it_sends_requests_to_production_by_default(get_current_user, runner, api_key):
        with mock.patch(
            "python_anvil.cli.Anvil", wraps=lambda *a, **kw: mock.Mock()
        ) as anvil_class:
            runner.invoke(cli, ["current-user"])
        anvil_class.assert_called_once_with(
            "MY_KEY", base_url="https://app.useanvil.com"
        )

    def it_sends_requests_to_anvil_base_url(runner, api_key, monkeypatch):
        monkeypatch.setenv("ANVIL_BASE_URL", "https://staging.useanvil.com")
        with mock.patch(
            "python_anvil.cli.Anvil", wraps=lambda *a, **kw: mock.Mock()
        ) as anvil_class:
            runner.invoke(cli, ["current-user"])
        anvil_class.assert_called_once_with(
            "MY_KEY", base_url="https://staging.useanvil.com"
        )

    @mock.patch("python_anvil.api.Anvil.get_current_user")
    def it_reports_api_errors_in_one_line(get_current_user, runner, api_key):
        get_current_user.side_effect = AnvilRequestError(
            [{"message": "Forbidden"}], status_code=403
        )

        res = runner.invoke(cli, ["current-user"])

        assert res.exit_code == 1
        assert "Error: 403: Forbidden" in res.output

    def describe_current_user():
        @mock.patch("python_anvil.api.Anvil.request_graphql")
        def it_prints_the_user(request_graphql, runner, api_key):
            request_graphql.return_value = {"currentUser": {"name": "Cameron"}}

            res = runner.invoke(cli, ["current-user"])

            assert "{'name': 'Cameron'}" in res.output
            assert "User data:" in res.output
            assert request_graphql.call_count == 1

    def describe_generate_pdf():
        @mock.patch("python_anvil.api.Anvil.generate_pdf")
        def it_writes_the_pdf(generate_pdf, runner, api_key):
            in_data = json.dumps({"data": [{"content": "x"}], "title": "My Title"})
            generate_pdf.return_value = b"Some bytes"
            mock_open = mock.mock_open(read_data=in_data)

            with mock.patch("click.open_file", mock_open) as m:
                res = runner.invoke(
                    cli, ["generate-pdf", "-i", "infile", "-o", "outfile"]
                )

            assert res.exit_code == 0, res.output
            generate_pdf.assert_called_once_with(in_data)
            m().write.assert_called_once_with(b"Some bytes")

    def describe_generate_etch_url():
        @mock.patch("python_anvil.api.Anvil.generate_etch_signing_url")
        def it_prints_the_url(generate, runner, api_key):
            generate.return_value = "https://app.useanvil.com/sign/abc"

            res = runner.invoke(
                cli, ["generate-etch-url", "-c", "user1", "-s", "signer1"]
            )

            assert "Signing URL is: https://app.useanvil.com/sign/abc" in res.output
            generate.assert_called_once_with(
                signer_eid="signer1", client_user_id="user1"
            )

    def describe_create_etch():
        @mock.patch("python_anvil.api.Anvil.create_etch_packet")
        def it_prints_the_packet_eid(create, runner, api_key, tmp_path):
            create.return_value = {"createEtchPacket": {"eid": "packet123"}}
            payload = tmp_path / "payload.json"
            payload.write_text(json.dumps({"name": "x", "signers": [], "files": []}))

            res = runner.invoke(cli, ["create-etch", "-p", str(payload)])

            assert "Etch packet created with id: packet123" in res.output
            create.assert_called_once_with(json=payload.read_bytes())

    def describe_gql_query():
        @mock.patch("python_anvil.api.Anvil.query")
        def it_works_with_a_query_only(query, runner, api_key):
            query.return_value = {"eid": "abc123", "name": "Some User"}
            query_str = "query SomeQuery { someQuery { eid name } }"

            res = runner.invoke(cli, ["gql-query", "-q", query_str])

            query.assert_called_once_with(query_str, variables=None)
            assert json.loads(res.output) == {"eid": "abc123", "name": "Some User"}

        @mock.patch("python_anvil.api.Anvil.query")
        def it_parses_the_variables_as_json(query, runner, api_key):
            query.return_value = {}
            query_str = (
                "query SomeQuery ($eid: String) { someQuery(eid: $eid) { eid name } }"
            )

            runner.invoke(
                cli, ["gql-query", "-q", query_str, "-v", json.dumps({"eid": "abc123"})]
            )

            query.assert_called_once_with(query_str, variables={"eid": "abc123"})
