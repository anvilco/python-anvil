import copy
import json
import mimetypes
from io import BufferedIOBase
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from python_anvil.api_resources.mutations import BaseQuery


FileLikeObject = Union[Path, BufferedIOBase]


def get_extractable_files_from_payload(
    variables: Any,
    is_match: Callable,
    cur_path: Optional[str] = None,
    cur_files: Optional[List] = None,
) -> Tuple[List[Tuple[str, FileLikeObject]], bool]:
    """Process variables bound for a Graphql multipart request.

    IMPORTANT: This will __overwrite__ the file-like objects to `None` due to
    the expected request format in the spec.

    Spec: https://github.com/jaydenseric/graphql-multipart-request-spec

    :param variables:
    :param is_match:
    :param cur_path:
    :param cur_files:
    :return: List containing a tuple of (file path string, file path/buffer object)
    :rtype: Tuple[List[Tuple[str, Union[Path, BufferedIOBase]], bool, List]
    """

    if cur_path is None:
        cur_path = "variables"
    if cur_files is None:
        cur_files = []
    if not variables:
        return [], False

    if is_match(variables):
        cur_files.append((cur_path, copy.deepcopy(variables)))
        return cur_files, True

    if isinstance(variables, dict):
        to_remove = []
        for key in variables:
            _, remove = get_extractable_files_from_payload(
                variables[key],
                is_match=is_match,
                cur_path=f"{cur_path}.{key}",
                cur_files=cur_files,
            )
            if remove:
                to_remove.append(key)

        for key in to_remove:
            variables[key] = None

    elif isinstance(variables, list):
        to_remove = []
        for idx, item in enumerate(variables):
            _, remove = get_extractable_files_from_payload(
                item,
                is_match=is_match,
                cur_path=f"{cur_path}.{idx}",
                cur_files=cur_files,
            )
            if remove:
                to_remove.append(idx)

        for idx in to_remove:
            variables[idx] = None

    return cur_files, False


def get_multipart_payload(mutation: BaseQuery):  # pylint: disable=too-many-locals
    def is_match(item):
        return isinstance(item, (BufferedIOBase, Path))

    payload, to_upload = mutation.create_payload()
    variables = payload.dict(by_alias=True, exclude_none=True)
    multipart_map, _ = get_extractable_files_from_payload(variables, is_match=is_match)

    operations = json.dumps(
        {
            "query": mutation.get_mutation(),
            "variables": variables,
        }
    )

    filemap = {}
    for idx, filepath in enumerate(multipart_map):
        filemap[idx] = [filepath[0]]

    files = {
        "operations": (None, operations),
        "map": (None, json.dumps(filemap)),
    }  # type: Dict[str, Union[Tuple[None, str], Tuple[Any, Any, Optional[str]]]]

    for idx, file_or_path in enumerate(to_upload):
        # `key` here is most likely going to be a list index (int), but
        # `requests` will expect an actual string when it constructs the
        # multipart request. We make sure this is a string here.
        actual_key = str(idx)

        # This is already a file-like object, pass it directly to `requests`.
        if isinstance(file_or_path, Callable):  # type: ignore
            # If you have a `ValueError` here, make sure your callable returns
            # a tuple of the file and filename:
            # Example: (open(file, "rb"), "file.pdf"))
            file_part, name_part = file_or_path()
        elif isinstance(file_or_path, Path):
            file_part = open(file_or_path, "rb")  # pylint: disable=consider-using-with
            name_part = file_or_path.parts[-1]
        else:
            raise AssertionError("File path or file-like object not given")

        mimetype, _ = mimetypes.guess_type(file_part.name)
        files[actual_key] = (name_part, file_part, mimetype)

    return files
