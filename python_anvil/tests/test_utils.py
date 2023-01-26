# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

from python_anvil.utils import build_batch_filenames, camel_to_snake, create_unique_id


def describe_build_batch_filenames():
    def test_with_normal_filename():
        gen = build_batch_filenames("somefile.txt")
        assert next(gen) == "somefile-0.txt"
        assert next(gen) == "somefile-1.txt"

    def test_with_start_index():
        gen = build_batch_filenames("somefile.txt", start_idx=100)
        assert next(gen) == "somefile-100.txt"
        assert next(gen) == "somefile-101.txt"

    def test_with_separator():
        gen = build_batch_filenames("somefile.txt", separator=":::")
        assert next(gen) == "somefile:::0.txt"

    def test_with_all():
        gen = build_batch_filenames("somefile.txt", start_idx=555, separator=":::")
        assert next(gen) == "somefile:::555.txt"


def describe_create_unique_id():
    def test_no_prefix():
        assert create_unique_id().startswith("field-")

    def test_prefix():
        prefix = "somePrefix+++--"
        assert create_unique_id(prefix).startswith(prefix)


def describe_camel_to_snake():
    def test_it():
        assert camel_to_snake('oneToTwo') == 'one_to_two'
        assert camel_to_snake('one') == 'one'
        assert camel_to_snake('TwoTwo') == 'two_two'
