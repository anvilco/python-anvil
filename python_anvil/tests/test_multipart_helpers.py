# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

from python_anvil.multipart_helpers import get_extractable_files_from_payload


def describe_get_extractable_files_from_payload():
    def test_it_works():
        is_match = lambda x: isinstance(x, int)
        variables = {
            "one": [{"f1": "data", "f2": 1}],
            "two": {"s2-1": "more data", "s2-2": "more more data", "s2-3": 2},
            "three": "nothing here",
            "four": 4,
        }

        paths, _ = get_extractable_files_from_payload(
            variables, is_match, cur_path="variables"
        )
        assert len(paths) == 3
        assert ("variables.one.0.f2", 1) in paths
        assert ("variables.two.s2-3", 2) in paths
        assert ("variables.four", 4) in paths

    def test_handles_empty_things():
        payload_expected_pairs = [
            ({}, 0),
            ([], 0),
            ('', 0),
            (' ', 1),
        ]

        for var_input, exp_len in payload_expected_pairs:
            paths, _ = get_extractable_files_from_payload(
                var_input, lambda x: x, cur_path="variables"
            )
            assert len(paths) == exp_len
