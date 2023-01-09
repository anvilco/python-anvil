import copy
import json
import mimetypes
from io import BufferedIOBase
from pathlib import Path
from typing import Any, Callable, Optional, List, Tuple, Union

FileLikeObject = Union[Path, BufferedIOBase]


def get_extractable_files_from_payload(
    variables: Any,
    is_match: Callable = lambda x: x,
    cur_path: Optional[str] = None,
    cur_files: Optional[List] = None,
) -> Tuple[List[Tuple[str, FileLikeObject]], bool]:
    """
    Processes variables bound for a Graphql multipart request and produces
        a mapping for use in the request.

    IMPORTANT: This will __overwrite__ the file-like objects to `None` due to
    the expected request format in the spec.

    Spec: https://github.com/jaydenseric/graphql-multipart-request-spec

    :param variables:
    :param is_match:
    :param cur_path:
    :param cur_files:
    :return: List containing a tuple of (file path string, file path/buffer object)
    :rtype: Tuple[List[Tuple[str, Union[Path, BufferedIOBase]], bool]
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
    elif isinstance(variables, dict):
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


def get_multipart_payload(mutation, variables):
    def is_match(item):
        return isinstance(item, Path) or isinstance(item, BufferedIOBase)

    multipart_map, _ = get_extractable_files_from_payload(variables, is_match=is_match)
    to_upload = {}

    operations = json.dumps(
        {
            "operationName": "CreateEtchPacket",
            "query": mutation.get_mutation(),
            "variables": variables,
        }
    )

    filemap = {}
    for idx, filepath in enumerate(multipart_map):
        filemap[idx] = [filepath[0]]
        to_upload[idx] = filepath[1]

    files = {"operations": (None, operations), "map": (None, json.dumps(filemap))}

    for key, file_or_path in to_upload.items():
        # `key` here is most likely going to be a list index (int), but
        # `requests` will expect an actual string when it constructs the
        # multipart request. We make sure this is a string here.
        actual_key = str(key)

        # This is already a file-like thing, pass it directly to `requests`.
        if isinstance(file_or_path, BufferedIOBase):
            file_part = file_or_path
        elif isinstance(file_or_path, Path):
            file_part = open(file_or_path, "rb")
        else:
            raise AssertionError("File path or file-like object not given")

        mimetype, _ = mimetypes.guess_type(file_part.name)
        files[actual_key] = ('what.pdf', file_part, mimetype)

    return files
