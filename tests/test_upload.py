from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

from python_anvil import Anvil, UploadWithOptions, prepare_graphql_file
from python_anvil.upload import (
    MultipartRequest,
    extract_files,
    is_file,
    validate_upload_schema,
)


DUMMY_PDF = Path(__file__).parent / "assets" / "dummy.pdf"


def describe_prepare_graphql_file():
    def it_requires_a_filename_for_bytes():
        with pytest.raises(
            ValueError,
            match=r"When passing bytes to prepare_graphql_file, `filename` must be provided",
        ):
            prepare_graphql_file(b"test")

    def it_accepts_bytes_with_a_filename():
        upload = prepare_graphql_file(b"test", filename="test.pdf")
        assert isinstance(upload, UploadWithOptions)
        assert upload.file == b"test"
        assert upload.options == {"filename": "test.pdf"}

    def it_accepts_bytes_without_a_filename_when_told_to_ignore_validation():
        upload = prepare_graphql_file(b"test", ignore_filename_validation=True)
        assert upload.options == {}

    def it_accepts_a_path_without_a_filename():
        assert prepare_graphql_file(str(DUMMY_PDF)).file == str(DUMMY_PDF)
        assert prepare_graphql_file(DUMMY_PDF).file == DUMMY_PDF

    def it_accepts_an_open_file_without_a_filename():
        with DUMMY_PDF.open("rb") as file:
            assert prepare_graphql_file(file).file is file

    def it_requires_a_filename_for_file_objects_with_no_name():
        with pytest.raises(
            ValueError, match="When passing a BytesIO to prepare_graphql_file"
        ):
            prepare_graphql_file(io.BytesIO(b"test"))

    def it_passes_the_filename_and_mimetype_through():
        upload = prepare_graphql_file(
            b"test",
            filename="test.pdf",
            mimetype="application/pdf",
            ignore_filename_validation=True,
        )
        assert upload.options == {"filename": "test.pdf", "mimetype": "application/pdf"}
        assert "test.pdf" in repr(upload)

    def it_is_also_a_static_method_on_the_client():
        assert Anvil.prepare_graphql_file(b"x", filename="x.pdf").filename == "x.pdf"


def describe_is_file():
    def it_is_true_for_the_things_that_can_be_uploaded():
        assert is_file(prepare_graphql_file(b"x", filename="x"))
        assert is_file(b"bytes")
        assert is_file(bytearray(b"bytes"))
        assert is_file(io.BytesIO())
        assert is_file(DUMMY_PDF)

    def it_is_false_for_strings_and_plain_data():
        assert not is_file("a/path.pdf")
        assert not is_file({"data": "base64"})
        assert not is_file(None)
        assert not is_file(1)


def describe_extract_files():
    def it_replaces_files_with_none_and_records_their_paths():
        file_a = prepare_graphql_file(b"a", filename="a.pdf")
        file_b = io.BytesIO(b"b")
        variables = {
            "files": [{"id": "a", "file": file_a}, {"id": "b", "file": file_b}],
            "name": "x",
        }

        clone, files, paths = extract_files({"variables": variables})

        assert clone == {
            "variables": {
                "files": [{"id": "a", "file": None}, {"id": "b", "file": None}],
                "name": "x",
            }
        }
        assert files == [file_a, file_b]
        assert paths == {0: ["variables.files.0.file"], 1: ["variables.files.1.file"]}

    def it_sends_the_same_file_in_two_places_once():
        file = prepare_graphql_file(b"a", filename="a.pdf")

        _, files, paths = extract_files(
            {"variables": {"one": {"file": file}, "two": {"file": file}}}
        )

        assert files == [file]
        assert paths == {0: ["variables.one.file", "variables.two.file"]}

    def it_leaves_variables_without_files_alone():
        variables = {
            "name": "x",
            "signers": [{"email": "a@example.com"}],
            "nested": {"deep": [1, 2]},
        }
        clone, files, paths = extract_files({"variables": variables})
        assert clone == {"variables": variables}
        assert files == []
        assert paths == {}


def describe_validate_upload_schema():
    def it_accepts_files_under_a_file_key():
        assert validate_upload_schema({"files": [{"file": b"x"}]})
        assert validate_upload_schema({"input": {"file": io.BytesIO()}})
        assert validate_upload_schema(
            {"file": prepare_graphql_file(b"x", filename="x")}
        )

    def it_accepts_base64_uploads_with_a_filename_and_mimetype():
        assert validate_upload_schema(
            {
                "files": [
                    {
                        "file": {
                            "data": "aGk=",
                            "filename": "hi.pdf",
                            "mimetype": "application/pdf",
                        }
                    }
                ]
            }
        )

    def it_rejects_base64_uploads_missing_a_filename_or_mimetype():
        assert not validate_upload_schema(
            {"files": [{"file": {"data": "aGk=", "filename": "hi.pdf"}}]}
        )
        assert not validate_upload_schema(
            {
                "files": [
                    {
                        "file": {
                            "data": 1,
                            "filename": "hi.pdf",
                            "mimetype": "application/pdf",
                        }
                    }
                ]
            }
        )

    def it_accepts_other_upload_forms_like_a_url():
        assert validate_upload_schema(
            {"files": [{"file": {"url": "https://example.com/x.pdf"}}]}
        )

    def it_rejects_files_anywhere_else():
        assert not validate_upload_schema({"document": b"x"})
        assert not validate_upload_schema({"files": [b"x"]})

    def it_accepts_no_variables():
        assert validate_upload_schema(None)
        assert validate_upload_schema({})


def describe_multipart_request():
    def it_is_falsy_without_files():
        assert not MultipartRequest({"query": "{ x }", "variables": {"a": 1}})

    def it_builds_the_operations_map_and_file_parts():
        file = prepare_graphql_file(
            b"%PDF", filename="x.pdf", mimetype="application/pdf"
        )
        request = MultipartRequest(
            {"query": "mutation { x }", "variables": {"input": {"file": file}}}
        )

        assert request
        parts = dict(request.build())
        assert json.loads(parts["operations"][1]) == {
            "query": "mutation { x }",
            "variables": {"input": {"file": None}},
        }
        assert parts["operations"][2] == "application/json"
        assert json.loads(parts["map"][1]) == {"1": ["variables.input.file"]}
        assert parts["1"] == ("x.pdf", b"%PDF", "application/pdf")

    def it_guesses_the_mimetype_from_the_filename():
        request = MultipartRequest(
            {
                "query": "",
                "variables": {"file": prepare_graphql_file(b"x", filename="x.png")},
            }
        )
        assert dict(request.build())["1"][2] == "image/png"

    def it_opens_a_path_for_each_attempt_and_closes_it_after():
        request = MultipartRequest(
            {"query": "", "variables": {"file": prepare_graphql_file(str(DUMMY_PDF))}}
        )

        first = dict(request.build())["1"]
        assert first[0] == "dummy.pdf"
        assert first[1].read() == DUMMY_PDF.read_bytes()

        second = dict(request.build())["1"]
        assert first[1].closed
        assert second[1].read() == DUMMY_PDF.read_bytes()

        request.close()
        assert second[1].closed

    def it_rewinds_a_seekable_file_object_for_a_retry():
        file = io.BytesIO(b"hello")
        request = MultipartRequest(
            {
                "query": "",
                "variables": {"file": prepare_graphql_file(file, filename="h.txt")},
            }
        )

        assert dict(request.build())["1"][1].read() == b"hello"
        assert dict(request.build())["1"][1].read() == b"hello"

    def it_refuses_to_resend_a_file_object_that_cannot_be_read_again():
        class OnceOnly(io.BytesIO):
            def seekable(self) -> bool:
                return False

        request = MultipartRequest(
            {
                "query": "",
                "variables": {
                    "file": prepare_graphql_file(OnceOnly(b"x"), filename="o.txt")
                },
            }
        )
        request.build()
        with pytest.raises(ValueError, match=r"Can't send o\.txt again"):
            request.build()

    def it_rejects_things_that_are_not_files():
        not_a_file: Any = 123
        request = MultipartRequest(
            {
                "query": "",
                "variables": {"file": UploadWithOptions(not_a_file, filename="x")},
            }
        )
        with pytest.raises(TypeError, match="Can't upload a int"):
            request.build()
