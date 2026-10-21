import base64

import pytest

from python_anvil.auth import build_auth_header, is_jwt


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


JWT_HEADER = b64url(b'{"alg":"HS256","typ":"JWT"}')
JWT_PAYLOAD = b64url(b'{"sub":"123"}')
JWT = f"{JWT_HEADER}.{JWT_PAYLOAD}.c2ln"


def describe_build_auth_header():
    def it_builds_basic_auth_with_a_trailing_colon_after_the_api_key():
        header = build_auth_header(api_key="my-api-key")
        assert header == "Basic " + base64.b64encode(b"my-api-key:").decode()

    def it_builds_bearer_auth_with_a_base64_encoded_access_token():
        header = build_auth_header(access_token="my-access-token")
        assert header == "Bearer " + base64.b64encode(b"my-access-token").decode()

    def it_does_not_put_a_trailing_colon_after_the_access_token():
        header = build_auth_header(access_token="tok")
        assert base64.b64decode(header.removeprefix("Bearer ")) == b"tok"

    def it_sends_a_jwt_access_token_as_is():
        assert build_auth_header(access_token=JWT) == f"Bearer {JWT}"

    def it_sends_an_unsigned_jwt_as_is():
        unsigned = JWT.rsplit(".", 1)[0] + "."
        assert build_auth_header(access_token=unsigned) == f"Bearer {unsigned}"

    def it_base64_encodes_a_token_that_only_looks_like_a_jwt():
        token = "aaa.bbb.ccc"
        assert (
            build_auth_header(access_token=token)
            == "Bearer " + base64.b64encode(token.encode()).decode()
        )

    def it_prefers_the_access_token_when_both_are_given():
        assert build_auth_header(api_key="key", access_token="tok").startswith(
            "Bearer "
        )

    def it_requires_one_of_them():
        with pytest.raises(ValueError, match="`api_key` or `access_token` is required"):
            build_auth_header()
        with pytest.raises(ValueError):
            build_auth_header(api_key="", access_token="")


def describe_is_jwt():
    def it_is_true_for_three_base64url_segments_with_a_json_header_and_payload():
        assert is_jwt(JWT)

    def it_is_false_without_an_alg_in_the_header():
        header = b64url(b'{"typ":"JWT"}')
        assert not is_jwt(f"{header}.{b64url(b'{}')}.sig")

    def it_is_false_when_a_segment_is_not_json():
        assert not is_jwt("aaa.bbb.ccc")
        assert not is_jwt(f"{b64url(b'[1]')}.{b64url(b'{}')}.sig")

    def it_is_false_for_the_wrong_shape():
        assert not is_jwt("one.two")
        assert not is_jwt("")
        assert not is_jwt(None)
        assert not is_jwt("has spaces.in it.x")
