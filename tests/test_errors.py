import json

import pytest

from python_anvil.errors import (
    AnvilError,
    AnvilRequestError,
    format_error,
    looks_like_json_error,
    normalize_exception,
    normalize_json_errors,
)
from python_anvil.exceptions import AnvilException, AnvilRequestException


def describe_looks_like_json_error():
    def it_is_true_for_a_graphql_errors_list():
        assert looks_like_json_error({"errors": [{"message": "Nope"}]})

    def it_is_true_for_a_rest_error_with_a_message():
        assert looks_like_json_error({"message": "PDF did not generate"})

    def it_is_true_for_a_rest_error_with_only_a_name():
        assert looks_like_json_error({"name": "ValidationError", "fields": []})

    def it_is_false_for_successful_data():
        assert not looks_like_json_error({"data": {"currentUser": {"eid": "abc"}}})

    def it_is_false_for_an_empty_object_or_no_json():
        assert not looks_like_json_error({})
        assert not looks_like_json_error(None)
        assert not looks_like_json_error([1, 2])


def describe_normalize_json_errors():
    def it_returns_the_graphql_errors_as_they_are():
        errors = [
            {
                "message": "Not Found",
                "path": ["etchPacket"],
                "locations": [{"line": 2, "column": 3}],
            }
        ]
        assert normalize_json_errors({"errors": errors}) == errors

    def it_wraps_a_single_rest_error_in_a_list():
        error = {
            "name": "AssertionError",
            "message": "PDF did not generate properly from given HTML!",
        }
        assert normalize_json_errors(error) == [error]

    def it_keeps_field_level_details_on_validation_errors():
        error = {
            "name": "ValidationError",
            "fields": [{"message": "Required", "property": "data"}],
        }
        assert normalize_json_errors(error) == [error]

    def it_falls_back_to_the_status_text_when_there_is_no_json():
        assert normalize_json_errors(None, "Bad Gateway") == [
            {"name": "Bad Gateway", "message": "Bad Gateway"}
        ]

    def it_falls_back_to_the_status_text_when_the_json_has_no_error_fields():
        assert normalize_json_errors({"foo": "bar"}, "Not Found") == [
            {"name": "Not Found", "message": "Not Found"}
        ]

    def it_defaults_to_unknown_error_without_a_status_text():
        assert normalize_json_errors(None) == [
            {"name": "Unknown Error", "message": "Unknown Error"}
        ]
        assert normalize_json_errors(None, "") == [
            {"name": "Unknown Error", "message": "Unknown Error"}
        ]


def describe_normalize_exception():
    def it_picks_the_name_and_message_off_an_exception():
        try:
            json.loads("")
        except ValueError as e:
            assert normalize_exception(e) == [
                {"name": "JSONDecodeError", "message": str(e)}
            ]

    def it_falls_back_to_the_status_text_when_there_is_no_exception():
        assert normalize_exception(None, "Bad Gateway") == [
            {"name": "Bad Gateway", "message": "Bad Gateway"}
        ]


def describe_anvil_request_error():
    def it_describes_every_error_in_its_message():
        error = AnvilRequestError(
            [{"message": "First"}, {"name": "Second", "message": "thing"}],
            status_code=400,
        )
        assert str(error) == "400: First; Second: thing"
        assert error.message == "First"
        assert error.status_code == 400
        assert error.headers == {}
        assert error.data is None

    def it_includes_validation_fields():
        error = AnvilRequestError(
            [
                {
                    "name": "ValidationError",
                    "fields": [
                        {"message": "Required", "property": "data"},
                        {"message": "Too long"},
                    ],
                }
            ],
            status_code=400,
        )
        assert str(error) == "400: ValidationError (data: Required, Too long)"

    def it_is_an_anvil_error_and_an_exception():
        error = AnvilRequestError([], status_code=500)
        assert isinstance(error, AnvilError)
        assert isinstance(error, Exception)
        assert error.message == "Unknown Error"

    def it_keeps_the_old_exception_names():
        assert AnvilException is AnvilError
        assert AnvilRequestException is AnvilRequestError
        with pytest.raises(AnvilRequestException):
            raise AnvilRequestError([{"message": "x"}], status_code=400)


def describe_describe_error():
    def it_handles_an_error_with_nothing_useful():
        assert format_error({}) == "Unknown Error"
        assert format_error({"fields": "not a list"}) == "Unknown Error"
