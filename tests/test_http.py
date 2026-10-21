"""The client over a real HTTP connection, to a local server. See tests/server.py."""

from __future__ import annotations

import base64
import contextlib
import io
import threading
import time
from pathlib import Path

import pytest
import requests

from python_anvil import Anvil, AnvilRequestError, __version__


ASSETS = Path(__file__).parent / "assets"
DUMMY_PDF = ASSETS / "dummy.pdf"


def decode_auth(header: str, scheme: str) -> str:
    return base64.b64decode(header.removeprefix(f"{scheme} ")).decode()


def describe_base_url():
    def it_sends_fill_pdf_to_the_rest_api(server, client):
        server.respond(
            {"body": b"%PDF-1.7", "headers": {"content-type": "application/pdf"}}
        )

        data = client.fill_pdf("tpl123", {"data": {"a": 1}})

        assert data == b"%PDF-1.7"
        [request] = server.requests
        assert request.method == "POST"
        assert request.path == "/api/v1/fill/tpl123.pdf"
        assert request.headers["content-type"] == "application/json"
        assert request.json == {"data": {"a": 1}}

    def it_passes_version_latest_through_as_a_query_parameter(server, client):
        server.respond(
            {"body": b"%PDF-1.7", "headers": {"content-type": "application/pdf"}}
        )

        client.fill_pdf(
            "tpl123", {"data": {"a": 1}}, version_number=Anvil.VERSION_LATEST
        )

        assert server.requests[0].path == "/api/v1/fill/tpl123.pdf?versionNumber=-1"

    def it_sends_generate_pdf_to_the_rest_api(server, client):
        server.respond(
            {"body": b"%PDF-1.7", "headers": {"content-type": "application/pdf"}}
        )

        data = client.generate_pdf({"data": [{"content": "hi"}]})

        assert data == b"%PDF-1.7"
        [request] = server.requests
        assert request.path == "/api/v1/generate-pdf"
        assert request.json == {"data": [{"content": "hi"}], "type": "markdown"}

    def it_sends_download_documents_to_the_document_group_zip(server, client):
        server.respond(
            {"body": b"PK\x03\x04", "headers": {"content-type": "application/zip"}}
        )

        data = client.download_documents("dg123")

        assert data == b"PK\x03\x04"
        [request] = server.requests
        assert request.method == "GET"
        assert request.path == "/api/document-group/dg123.zip"

    def it_sends_graphql_requests_to_graphql(server, client):
        server.respond({"json": {"data": {"forgeSubmit": {"eid": "sub1"}}}})

        data = client.forge_submit({"forge_eid": "forge123", "payload": {}})

        assert data == {"forgeSubmit": {"eid": "sub1"}}
        [request] = server.requests
        assert request.path == "/graphql"
        assert request.headers["content-type"] == "application/json"
        body = request.json
        assert "mutation ForgeSubmit" in body["query"]
        assert body["variables"] == {
            "forgeEid": "forge123",
            "payload": {},
            "isTest": True,
        }

    def it_uses_a_full_url_as_is_when_it_is_on_the_base_url(server, client):
        server.respond({"json": {"ok": True}})

        client.request_rest("GET", f"{server.base_url}/api/v1/something")

        assert server.requests[0].path == "/api/v1/something"

    def it_accepts_a_base_url_with_a_trailing_slash(server, make_client):
        client = make_client(base_url=server.base_url + "/")
        server.respond({"json": {"ok": True}})

        client.request_rest("GET", "/api/v1/something")

        assert client.base_url == server.base_url
        assert server.requests[0].path == "/api/v1/something"

    def it_rejects_a_base_url_that_is_not_a_url():
        with pytest.raises(ValueError, match="base_url"):
            Anvil("key", base_url="app.useanvil.com")


def describe_headers():
    def it_sends_basic_auth_with_the_api_key_and_a_trailing_colon(server, make_client):
        client = make_client(api_key="my-api-key")

        client.request_rest("GET", "/api/v1/x")

        auth = server.requests[0].headers["authorization"]
        assert auth.startswith("Basic ")
        assert decode_auth(auth, "Basic") == "my-api-key:"

    def it_sends_bearer_auth_with_the_access_token(server, make_client):
        client = make_client(api_key=None, access_token="my-access-token")

        client.request_rest("GET", "/api/v1/x")

        auth = server.requests[0].headers["authorization"]
        assert auth.startswith("Bearer ")
        assert decode_auth(auth, "Bearer") == "my-access-token"

    def it_sends_a_jwt_access_token_as_is(server, make_client):
        header = (
            base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}')
            .decode()
            .rstrip("=")
        )
        payload = base64.urlsafe_b64encode(b'{"sub":"user1"}').decode().rstrip("=")
        jwt = f"{header}.{payload}.signature"
        client = make_client(api_key=None, access_token=jwt)

        client.request_rest("GET", "/api/v1/x")

        assert server.requests[0].headers["authorization"] == f"Bearer {jwt}"

    def it_sends_the_default_user_agent(server, client):
        client.request_rest("GET", "/api/v1/x")

        assert server.requests[0].headers["user-agent"] == f"python-anvil/{__version__}"

    def it_sends_a_custom_user_agent(server, make_client):
        client = make_client(user_agent="my-app/1.0")

        client.request_rest("GET", "/api/v1/x")

        assert server.requests[0].headers["user-agent"] == "my-app/1.0"

    def it_sends_extra_headers(server, client):
        client.request_rest("GET", "/api/v1/x", headers={"X-Extra": "yes"})

        assert server.requests[0].headers["x-extra"] == "yes"


def describe_rate_limiting():
    def it_updates_the_limiter_from_the_first_response_headers(server, make_client):
        client = make_client(request_limit=1, request_limit_ms=1000)
        server.respond(
            {
                "json": {},
                "headers": {
                    "x-ratelimit-limit": "7",
                    "x-ratelimit-interval-ms": "3000",
                },
            }
        )

        client.request_rest("GET", "/api/v1/x")

        limiter = client.client.rate_limiter
        assert limiter.has_set_from_response
        assert (limiter.limit, limiter.interval_ms) == (7, 3000)

    def it_only_reads_the_limits_from_the_first_response(server, client):
        server.respond_in_turn(
            {
                "json": {},
                "headers": {
                    "x-ratelimit-limit": "7",
                    "x-ratelimit-interval-ms": "3000",
                },
            },
            {
                "json": {},
                "headers": {"x-ratelimit-limit": "2", "x-ratelimit-interval-ms": "100"},
            },
        )

        client.request_rest("GET", "/api/v1/x")
        client.request_rest("GET", "/api/v1/x")

        limiter = client.client.rate_limiter
        assert (limiter.limit, limiter.interval_ms) == (7, 3000)

    def it_keeps_the_starting_limits_when_the_response_has_no_rate_limit_headers(
        server, make_client
    ):
        client = make_client(request_limit=4, request_limit_ms=500)
        server.respond(
            {
                "json": {},
                "headers": {"x-ratelimit-limit": "", "x-ratelimit-interval-ms": ""},
            }
        )

        client.request_rest("GET", "/api/v1/x")

        limiter = client.client.rate_limiter
        assert limiter.has_set_from_response
        assert (limiter.limit, limiter.interval_ms) == (4, 500)

    def it_holds_concurrent_requests_until_the_first_response_sets_the_limits(
        server, client
    ):
        server.respond_in_turn(
            {"json": {}, "delay": 0.2, "headers": {"x-ratelimit-limit": "10"}},
            {"json": {}},
        )

        threads = [
            threading.Thread(target=client.request_rest, args=("GET", "/api/v1/x"))
            for _ in range(3)
        ]
        for thread in threads:
            thread.start()
            time.sleep(0.01)
        for thread in threads:
            thread.join()

        first, *rest = server.requests
        assert len(rest) == 2
        for request in rest:
            assert request.received_at >= first.responded_at

    def it_never_sends_more_requests_in_any_interval_than_the_server_allows(
        server, make_client
    ):
        client = make_client(request_limit=2, request_limit_ms=200)
        server.respond(
            {
                "json": {},
                "headers": {"x-ratelimit-limit": "2", "x-ratelimit-interval-ms": "200"},
            }
        )

        threads = [
            threading.Thread(target=client.request_rest, args=("GET", "/api/v1/x"))
            for _ in range(6)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        times = sorted(request.received_at for request in server.requests)
        assert len(times) == 6
        for i in range(len(times) - 2):
            # The third request after any one must be at least an interval later
            assert times[i + 2] - times[i] >= 0.2

    def it_sends_the_first_request_right_away(server, make_client):
        client = make_client(request_limit=1, request_limit_ms=1000)

        started = time.monotonic()
        client.request_rest("GET", "/api/v1/x")

        assert time.monotonic() - started < 0.5

    def it_does_not_hold_back_requests_that_are_within_the_limit(server, make_client):
        client = make_client(request_limit=5, request_limit_ms=1000)
        server.respond(
            {
                "json": {},
                "headers": {
                    "x-ratelimit-limit": "5",
                    "x-ratelimit-interval-ms": "1000",
                },
            }
        )

        started = time.monotonic()
        for _ in range(5):
            client.request_rest("GET", "/api/v1/x")

        assert time.monotonic() - started < 0.5

    def it_lets_waiting_requests_go_ahead_when_the_first_request_fails(
        server, make_client
    ):
        # A port nothing listens on, then the real server
        client = make_client(request_limit=10)
        client.client.base_url = "http://127.0.0.1:1"

        def first_fails():
            with contextlib.suppress(requests.ConnectionError):
                client.request_rest("GET", "/api/v1/x")

        failing = threading.Thread(target=first_fails)
        failing.start()
        failing.join()

        client.client.base_url = server.base_url
        client.request_rest("GET", "/api/v1/x")

        assert len(server.requests) == 1
        assert client.client.rate_limiter.has_set_from_response

    def it_falls_back_to_one_request_per_second_when_the_starting_limits_are_invalid():
        client = Anvil("key", request_limit=0, request_limit_ms=-5)
        limiter = client.client.rate_limiter
        assert (limiter.limit, limiter.interval_ms) == (1, 1000)

    def it_retries_a_429_after_retry_after_seconds_plus_a_buffer(server, client):
        server.respond_in_turn(
            {
                "status": 429,
                "json": {"message": "Too many"},
                "headers": {"retry-after": "0.2"},
            },
            {"json": {"ok": True}},
        )

        data = client.request_rest("GET", "/api/v1/x")

        assert data == {"ok": True}
        first, second = server.requests
        assert second.received_at - first.responded_at >= 0.25

    def it_retries_a_429_after_only_the_buffer_when_there_is_no_retry_after(
        server, client
    ):
        server.respond_in_turn({"status": 429, "body": b""}, {"json": {"ok": True}})

        data = client.request_rest("GET", "/api/v1/x")

        assert data == {"ok": True}
        first, second = server.requests
        assert 0.05 <= second.received_at - first.responded_at < 0.5

    def it_keeps_retrying_until_the_request_is_not_rate_limited(server, client):
        server.respond_in_turn(
            {"status": 429, "body": b"", "headers": {"retry-after": "0"}},
            {"status": 429, "body": b"", "headers": {"retry-after": "0"}},
            {"json": {"ok": True}},
        )

        assert client.request_rest("GET", "/api/v1/x") == {"ok": True}
        assert len(server.requests) == 3


def describe_errors():
    def it_raises_graphql_errors_from_a_200_response(server, client):
        server.respond(
            {
                "json": {
                    "data": {"etchPacket": None},
                    "errors": [{"message": "Not Found", "path": ["etchPacket"]}],
                }
            }
        )

        with pytest.raises(AnvilRequestError) as excinfo:
            client.get_etch_packet("nope")

        error = excinfo.value
        assert error.status_code == 200
        assert error.errors == [{"message": "Not Found", "path": ["etchPacket"]}]
        assert error.data == {"etchPacket": None}
        assert error.headers["x-ratelimit-limit"] == "10"
        assert str(error) == "200: Not Found"

    def it_raises_a_rest_validation_error_with_its_fields(server, client):
        server.respond(
            {
                "status": 400,
                "json": {
                    "name": "ValidationError",
                    "status": 400,
                    "fields": [{"message": "Required", "property": "data"}],
                },
            }
        )

        with pytest.raises(AnvilRequestError) as excinfo:
            client.generate_pdf({"data": [{"content": "x"}]})

        error = excinfo.value
        assert error.status_code == 400
        assert error.errors[0]["name"] == "ValidationError"
        assert error.errors[0]["fields"] == [
            {"message": "Required", "property": "data"}
        ]
        assert str(error) == "400: ValidationError (data: Required)"

    def it_raises_a_rest_error_with_a_message(server, client):
        server.respond(
            {
                "status": 500,
                "json": {
                    "name": "AssertionError",
                    "message": "PDF did not generate properly from given HTML!",
                },
            }
        )

        with pytest.raises(
            AnvilRequestError, match=r"500: AssertionError: PDF did not generate"
        ):
            client.generate_pdf({"type": "html", "data": {"html": "<p>"}})

    def it_uses_the_status_text_for_a_non_json_error_response(server, client):
        server.respond(
            {
                "status": 502,
                "body": b"<html>Bad Gateway</html>",
                "headers": {"content-type": "text/html"},
            }
        )

        with pytest.raises(AnvilRequestError) as excinfo:
            client.request_rest("GET", "/api/v1/x")

        assert excinfo.value.status_code == 502
        assert excinfo.value.errors == [
            {"name": "Bad Gateway", "message": "Bad Gateway"}
        ]

    def it_uses_the_status_text_for_an_empty_error_response(server, client):
        server.respond({"status": 500, "body": b""})

        with pytest.raises(AnvilRequestError) as excinfo:
            client.request_rest("GET", "/api/v1/x")

        assert excinfo.value.errors == [
            {"name": "Internal Server Error", "message": "Internal Server Error"}
        ]

    def it_raises_a_parsing_error_for_an_empty_json_response(server, client):
        server.respond(
            {
                "status": 200,
                "body": b"",
                "headers": {"content-type": "application/json"},
            }
        )

        with pytest.raises(AnvilRequestError) as excinfo:
            client.request_rest("GET", "/api/v1/x")

        [error] = excinfo.value.errors
        assert error["name"] == "JSONDecodeError"
        assert excinfo.value.status_code == 200

    def it_raises_when_the_server_cannot_be_reached():
        client = Anvil("key", base_url="http://127.0.0.1:1", timeout=1)

        with pytest.raises(requests.ConnectionError):
            client.request_rest("GET", "/api/v1/x")

    def it_treats_a_json_error_as_an_error_even_when_bytes_were_asked_for(
        server, client
    ):
        server.respond(
            {"status": 403, "json": {"message": "Forbidden", "name": "Forbidden"}}
        )

        with pytest.raises(AnvilRequestError, match="403: Forbidden"):
            client.download_documents("dg123")


def describe_file_uploads():
    def it_sends_prepared_bytes_as_a_multipart_graphql_upload(server, client):
        file = Anvil.prepare_graphql_file(
            b"%PDF-1.7 bytes", filename="from-bytes.pdf", mimetype="application/pdf"
        )

        client.create_etch_packet(
            {
                "name": "Packet",
                "files": [{"id": "file1", "title": "File", "file": file, "fields": []}],
            }
        )

        [request] = server.requests
        assert request.path == "/graphql"
        parts = request.multipart_parts()

        operations = parts["operations"].json
        assert operations["variables"]["files"][0]["file"] is None
        assert operations["variables"]["files"][0]["id"] == "file1"
        assert "createEtchPacket" in operations["query"]

        assert parts["map"].json == {"1": ["variables.files.0.file"]}

        file_part = parts["1"]
        assert file_part.filename == "from-bytes.pdf"
        assert file_part.content_type == "application/pdf"
        assert file_part.body == b"%PDF-1.7 bytes"

    def it_sends_a_file_object_using_its_own_filename(server, client):
        with DUMMY_PDF.open("rb") as file:
            client.request_graphql(
                "mutation Upload($file: Upload!) { upload(file: $file) }",
                {"input": {"file": file}},
            )

        parts = server.requests[0].multipart_parts()
        assert parts["map"].json == {"1": ["variables.input.file"]}
        assert parts["1"].filename == "dummy.pdf"
        assert parts["1"].content_type == "application/pdf"
        assert parts["1"].body == DUMMY_PDF.read_bytes()

    def it_sends_several_files_with_one_map_entry_each(server, client):
        client.request_graphql(
            "mutation Upload($files: [EtchFile!]) { createEtchPacket(files: $files) { eid } }",
            {
                "files": [
                    {
                        "id": "a",
                        "file": Anvil.prepare_graphql_file(b"a", filename="a.pdf"),
                    },
                    {
                        "id": "b",
                        "file": Anvil.prepare_graphql_file(b"b", filename="b.pdf"),
                    },
                ]
            },
        )

        parts = server.requests[0].multipart_parts()
        assert parts["map"].json == {
            "1": ["variables.files.0.file"],
            "2": ["variables.files.1.file"],
        }
        assert parts["1"].filename == "a.pdf"
        assert parts["2"].filename == "b.pdf"

    def it_sends_a_file_from_a_path_using_its_own_filename(server, client):
        client.request_graphql(
            "mutation { x }",
            {"input": {"file": Anvil.prepare_graphql_file(str(DUMMY_PDF))}},
        )

        parts = server.requests[0].multipart_parts()
        assert parts["1"].filename == "dummy.pdf"
        assert parts["1"].body == DUMMY_PDF.read_bytes()

    def it_sends_a_path_object_directly(server, client):
        client.request_graphql("mutation { x }", {"input": {"file": DUMMY_PDF}})

        parts = server.requests[0].multipart_parts()
        assert parts["1"].filename == "dummy.pdf"

    def it_sends_a_file_object_with_no_name_using_the_given_filename(server, client):
        file = Anvil.prepare_graphql_file(io.BytesIO(b"hello"), filename="given.pdf")

        client.request_graphql("mutation { x }", {"input": {"file": file}})

        parts = server.requests[0].multipart_parts()
        assert parts["1"].filename == "given.pdf"
        assert parts["1"].body == b"hello"

    def it_names_a_file_with_no_filename_blob(server, client):
        file = Anvil.prepare_graphql_file(b"hello", ignore_filename_validation=True)

        client.request_graphql("mutation { x }", {"input": {"file": file}})

        assert server.requests[0].multipart_parts()["1"].filename == "blob"

    def it_sends_a_base64_upload_as_plain_json(server, client):
        client.request_graphql(
            "mutation { x }",
            {
                "input": {
                    "file": {
                        "data": "aGVsbG8=",
                        "filename": "hello.pdf",
                        "mimetype": "application/pdf",
                    }
                }
            },
        )

        request = server.requests[0]
        assert request.headers["content-type"] == "application/json"
        assert request.json["variables"]["input"]["file"]["data"] == "aGVsbG8="

    def it_rejects_a_file_that_is_not_under_a_file_key(client):
        with pytest.raises(ValueError, match="Invalid file schema"):
            client.request_graphql(
                "mutation { x }",
                {"document": Anvil.prepare_graphql_file(b"x", filename="x.pdf")},
            )

    def describe_when_the_upload_is_retried_after_a_429():
        def it_sends_a_file_from_a_path_in_full_again(server, client):
            server.respond_in_turn({"status": 429, "body": b""}, {"json": {"data": {}}})

            client.request_graphql(
                "mutation { x }",
                {"input": {"file": Anvil.prepare_graphql_file(str(DUMMY_PDF))}},
            )

            first, second = server.requests
            assert first.multipart_parts()["1"].body == DUMMY_PDF.read_bytes()
            assert second.multipart_parts()["1"].body == DUMMY_PDF.read_bytes()

        def it_sends_a_seekable_file_object_in_full_again(server, client):
            server.respond_in_turn({"status": 429, "body": b""}, {"json": {"data": {}}})
            file = Anvil.prepare_graphql_file(
                io.BytesIO(b"hello again"), filename="again.pdf"
            )

            client.request_graphql("mutation { x }", {"input": {"file": file}})

            first, second = server.requests
            assert first.multipart_parts()["1"].body == b"hello again"
            assert second.multipart_parts()["1"].body == b"hello again"

        def it_fails_rather_than_sending_an_empty_file_for_a_file_object_that_cannot_be_read_again(
            server, client
        ):
            server.respond_in_turn({"status": 429, "body": b""}, {"json": {"data": {}}})

            class OnceOnly(io.BytesIO):
                def seekable(self) -> bool:
                    return False

            file = Anvil.prepare_graphql_file(OnceOnly(b"once"), filename="once.pdf")

            with pytest.raises(ValueError, match=r"Can't send once\.pdf again"):
                client.request_graphql("mutation { x }", {"input": {"file": file}})

            assert len(server.requests) == 1


def describe_responses():
    def it_returns_parsed_json_by_default_from_request_rest(server, client):
        server.respond({"json": {"hello": "world"}})

        assert client.request_rest("GET", "/api/v1/x") == {"hello": "world"}

    def it_returns_bytes_when_asked(server, client):
        server.respond(
            {"body": b"raw", "headers": {"content-type": "application/octet-stream"}}
        )

        assert client.request_rest("GET", "/api/v1/x", data_type="bytes") == b"raw"

    def it_returns_the_response_to_stream(server, client):
        server.respond(
            {
                "body": b"%PDF-1.7 " + b"x" * 1000,
                "headers": {"content-type": "application/pdf"},
            }
        )

        with client.fill_pdf("tpl", {"data": {"a": 1}}, data_type="stream") as response:
            assert isinstance(response, requests.Response)
            data = b"".join(response.iter_content(chunk_size=100))

        assert data.startswith(b"%PDF-1.7")
        assert len(data) == 1009

    def it_rejects_an_unknown_data_type(client):
        with pytest.raises(ValueError, match="data_type must be one of"):
            client.request_rest("GET", "/api/v1/x", data_type="buffer")

    def it_rejects_json_for_the_binary_methods(client):
        with pytest.raises(
            ValueError, match=r"data_type must be one of: bytes\|stream"
        ):
            client.download_documents("dg", data_type="json")

    def it_sends_a_raw_body_passed_to_request_rest(server, client):
        server.respond({"json": {}})

        client.request_rest(
            "POST",
            "/api/v1/x",
            data=b"raw body",
            headers={"Content-Type": "text/plain"},
        )

        assert server.requests[0].body == b"raw body"

    def it_sends_requests_with_the_given_session(server, make_client):
        session = requests.Session()
        session.headers["X-From-Session"] = "yes"
        client = make_client(session=session)
        server.respond({"json": {}})

        client.request_rest("GET", "/api/v1/x")

        assert server.requests[0].headers["x-from-session"] == "yes"

    def it_closes_the_session_as_a_context_manager(make_client):
        with make_client() as client:
            session = client.client.session
        assert isinstance(session, requests.Session)
