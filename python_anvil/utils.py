import re
import uuid
from logging import getLogger
from os import path


logger = getLogger(__name__)


def build_batch_filenames(filename: str, start_idx=0, separator: str = "-"):
    """
    Create a generator for filenames in sequential order.

    Example:
        build_batch_filenames('somefile.pdf') will yield filenames:
        * somefile-1.pdf
        * somefile-2.pdf
        * somefile-3.pdf
    :param filename: Full filename, including extension
    :param start_idx: Starting index number
    :param separator:
    :return:
    """
    idx = start_idx or 0
    sep = separator or "-"
    file_part, ext = path.splitext(filename)

    while True:
        yield f"{file_part}{sep}{idx}{ext}"
        idx += 1


def create_unique_id(prefix: str = "field") -> str:
    """Create a prefixed unique id."""
    return f"{prefix}-{uuid.uuid4().hex}"


def remove_empty_items(dict_obj: dict):
    """Remove null values from a dict."""
    return {k: v for k, v in dict_obj.items() if v is not None}


def camel_to_snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
