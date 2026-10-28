import base64
import os
from io import BufferedReader, BytesIO
from mimetypes import guess_type
from typing import Any

from pydantic import BaseModel, ConfigDict

from python_anvil.api_resources.base import underscore_to_camel


class FileCompatibleBaseModel(BaseModel):
    """
    Patched model_dump to extract file objects from SerializationIterator.

    Becaus of Pydantic V2. Return as BufferedReader or base64 encoded dict as needed.
    """

    # Allow extra fields even if it is not defined. This will allow models
    # to be more flexible if features are added in the Anvil API, but
    # explicit support hasn't been added yet to this library.
    model_config = ConfigDict(
        alias_generator=underscore_to_camel, populate_by_name=True, extra="allow"
    )

    def _iterator_to_buffered_reader(self, value):
        content = bytearray()
        try:
            while True:
                content.extend(next(value))
        except StopIteration:
            # Create a BytesIO with the content
            bio = BytesIO(bytes(content))
            # Create a BufferedReader with the content
            reader = BufferedReader(bio)  # type: ignore[arg-type]
            return reader

    def _check_if_serialization_iterator(self, value):
        return str(type(value).__name__) == "SerializationIterator" and hasattr(
            value, "__next__"
        )

    def _process_file_data(self, file_obj, original=None):
        """Process file object into base64 encoded dict format."""
        # Read the file data and encode it as base64
        file_content = file_obj.read()

        # The name of the file as it was given; the copy read here has none
        filename = (
            getattr(original, "name", None)
            or getattr(file_obj, "name", None)
            or "document.pdf"
        )
        if isinstance(filename, (bytes, bytearray)):
            filename = filename.decode("utf-8")
        filename = str(filename)

        # manage mimetype based on file extension
        mimetype = guess_type(filename)[0] or "application/pdf"

        return {
            "data": base64.b64encode(file_content).decode("utf-8"),
            "mimetype": mimetype,
            "filename": os.path.basename(filename),
        }

    def _original_file_item(self, index: int) -> Any:
        files = getattr(self, "files", None)
        if not isinstance(files, list) or index >= len(files):
            return None
        return files[index]

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        for key, value in data.items():
            if key == "file" and self._check_if_serialization_iterator(value):
                # Direct file case
                file_obj = self._iterator_to_buffered_reader(value)
                data[key] = self._process_file_data(
                    file_obj, getattr(self, "file", None)
                )
            elif key == "files" and isinstance(value, list):
                # List of objects case
                for index, item in enumerate(value):
                    if (
                        isinstance(item, dict)
                        and "file" in item
                        and self._check_if_serialization_iterator(item["file"])
                    ):
                        file_obj = self._iterator_to_buffered_reader(item["file"])
                        original = getattr(
                            self._original_file_item(index), "file", None
                        )
                        data[key][index]["file"] = self._process_file_data(
                            file_obj, original
                        )
        return data
