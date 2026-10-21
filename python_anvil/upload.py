"""File uploads in GraphQL requests, per the GraphQL multipart request spec.

https://github.com/jaydenseric/graphql-multipart-request-spec

A file can be anywhere in a request's variables. `extract_files` finds them,
replaces each with `None`, and records where it was, which `build_multipart`
turns into the `operations`, `map` and file parts of the request.
"""

from __future__ import annotations

import io
import json
import os
from collections.abc import Mapping
from mimetypes import guess_type
from pathlib import Path
from typing import Any


FileInput = str | os.PathLike | bytes | bytearray | io.IOBase

# The multipart part a file is sent as: the filename, the file contents (bytes
# or a file object) and the mimetype, in the shape `requests` wants
FilePart = tuple[str, Any, str | None]

FILENAME_IGNORE_MESSAGE = (
    "If you think you can ignore this, pass `ignore_filename_validation=True`."
)
# Without a name, the part would have no filename and the API would treat it as text
DEFAULT_FILENAME = "blob"


class UploadWithOptions:
    """A file to upload, with the filename and mimetype to send it with.

    Make these with `prepare_graphql_file`.
    """

    def __init__(
        self,
        file: FileInput,
        filename: str | None = None,
        mimetype: str | None = None,
    ):
        self.file = file
        self.filename = filename
        self.mimetype = mimetype

    @property
    def options(self) -> dict[str, str]:
        return {
            key: value
            for key, value in (("filename", self.filename), ("mimetype", self.mimetype))
            if value
        }

    def __repr__(self) -> str:
        return f"UploadWithOptions({self.file!r}, {self.options!r})"


def prepare_graphql_file(
    path_or_file: FileInput,
    *,
    filename: str | None = None,
    mimetype: str | None = None,
    ignore_filename_validation: bool = False,
) -> UploadWithOptions:
    """Prepare a file for a GraphQL multipart upload, e.g. in `create_etch_packet`.

    :param path_or_file: A path to a file, the file's `bytes`, or an open
        binary file object. A path is opened when the request is sent, and
        opened again if the request is retried; a file object is read from
        its current position, and rewound if the request is retried.
    :param filename: The filename to send. Required for `bytes` and for file
        objects that have no `name`, like a `BytesIO`. A path and a file
        opened from one are sent with their own names unless this is given.
    :param mimetype: The Content-Type to send the file with. Defaults to one
        guessed from the filename.
    :param ignore_filename_validation: Send a file without a filename, as
        "blob". An escape hatch for things we didn't anticipate.
    """
    if not isinstance(path_or_file, (str, os.PathLike)) and not (
        filename or ignore_filename_validation or _own_filename(path_or_file)
    ):
        raise ValueError(
            f"When passing {_describe(path_or_file)} to prepare_graphql_file, "
            f"`filename` must be provided. {FILENAME_IGNORE_MESSAGE}"
        )

    return UploadWithOptions(path_or_file, filename=filename, mimetype=mimetype)


def is_file(value: Any) -> bool:
    """Whether a value in a request's variables is a file to upload.

    Paths given as plain strings aren't, since they can't be told apart from
    other strings: pass those through `prepare_graphql_file`.
    """
    return isinstance(
        value, (UploadWithOptions, bytes, bytearray, io.IOBase, os.PathLike)
    )


def extract_files(value: Any) -> tuple[Any, list[Any], dict[int, list[str]]]:
    """Pull the files out of a request's variables.

    Given the whole operation, `{"query": ..., "variables": ...}`, returns a
    copy with every file replaced by `None`, the files found, and where each
    was found: a map of a file's index to the dotted paths it was at, e.g.
    `variables.files.0.file`.
    """
    files: list[Any] = []
    paths: dict[int, list[str]] = {}

    def walk(node: Any, path: str) -> Any:
        if is_file(node):
            # The same file in two places is sent once, with two paths
            for index, file in enumerate(files):
                if file is node:
                    paths[index].append(path)
                    return None
            files.append(node)
            paths[len(files) - 1] = [path]
            return None
        if isinstance(node, Mapping):
            return {key: walk(child, _join(path, key)) for key, child in node.items()}
        if isinstance(node, (list, tuple)):
            return [walk(child, _join(path, i)) for i, child in enumerate(node)]
        return node

    clone = walk(value, "")
    return clone, files, paths


def _join(path: str, key: Any) -> str:
    return f"{path}.{key}" if path else str(key)


def validate_upload_schema(
    value: Any, parent: Any = None, key: str | None = None
) -> bool:
    """Whether every file in the variables is where the API expects one: under a `file` key.

    Also checks base64 uploads, `{"data": ..., "filename": ..., "mimetype": ...}`.
    """
    if value is None:
        return True

    if key != "file":
        if isinstance(value, (list, tuple)):
            return all(validate_upload_schema(child, value) for child in value)
        if isinstance(value, Mapping):
            return all(
                validate_upload_schema(child, value, child_key)
                for child_key, child in value.items()
            )
        return not is_file(value)

    # OK, the key is 'file'

    # All flavors should be nested, and not top-level
    if not (isinstance(parent, Mapping) and parent.get("file") is value):
        return False

    # Base64 Upload
    if isinstance(value, Mapping):
        if value.get("data"):
            # Must be a string and also have the provided keys
            return isinstance(value["data"], str) and all(
                value.get(required) for required in ("filename", "mimetype")
            )
        # Another form of the Upload scalar, like {"url": ...}
        return True

    return is_file(value)


class MultipartRequest:
    """The parts of a multipart GraphQL request, built fresh for each attempt.

    Files given as paths are opened when the parts are built, so a retry sends
    them in full again. File objects are rewound for a retry when they can be;
    one that can't be read again fails rather than sending an empty file.
    """

    def __init__(self, operations: Mapping[str, Any]):
        clone, self._files, paths = extract_files(dict(operations))
        self.operations_json = json.dumps(clone)
        self.map_json = json.dumps({str(i + 1): found for i, found in paths.items()})
        self.attempts = 0
        self._opened: list[io.IOBase] = []

    def __bool__(self) -> bool:
        return bool(self._files)

    def build(self) -> list[tuple[str, Any]]:
        """The `files` argument for `requests`: the operations, the map, then each file."""
        self.close()
        self.attempts += 1

        parts: list[tuple[str, Any]] = [
            ("operations", (None, self.operations_json, "application/json")),
            ("map", (None, self.map_json, "application/json")),
        ]
        for index, file in enumerate(self._files):
            parts.append((str(index + 1), self._part(file)))
        return parts

    def close(self) -> None:
        """Close the files this opened for the last attempt."""
        for handle in self._opened:
            handle.close()
        self._opened = []

    def _part(self, file: Any) -> FilePart:
        filename: str | None = None
        mimetype: str | None = None
        if isinstance(file, UploadWithOptions):
            filename, mimetype = file.filename, file.mimetype
            file = file.file

        if isinstance(file, (str, os.PathLike)):
            path = Path(file)
            filename = filename or path.name
            handle = path.open("rb")
            self._opened.append(handle)
            content: Any = handle
        elif isinstance(file, (bytes, bytearray)):
            content = bytes(file)
        elif isinstance(file, io.IOBase) or hasattr(file, "read"):
            filename = filename or _own_filename(file)
            if self.attempts > 1:
                if file.seekable():
                    file.seek(0)
                else:
                    raise ValueError(
                        f"Can't send {filename or 'a file'} again because its "
                        "stream has already been read. To upload a file in a "
                        "request that may be retried, pass a path, a seekable "
                        "file object or bytes."
                    )
            content = file
        else:
            raise TypeError(f"Can't upload {_describe(file)}")

        filename = filename or DEFAULT_FILENAME
        mimetype = mimetype or guess_type(filename)[0]
        return filename, content, mimetype


def _own_filename(file: Any) -> str | None:
    """The name a file object carries, if it has one, like an open file's path."""
    name = getattr(file, "name", None)
    if isinstance(name, (bytes, bytearray)):
        name = name.decode("utf-8", "replace")
    if isinstance(name, str) and name:
        return os.path.basename(name)
    return None


def _describe(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        return "bytes"
    return f"a {type(value).__name__}"
