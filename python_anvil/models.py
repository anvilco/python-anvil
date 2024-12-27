import base64
import os
from io import BufferedReader, BytesIO
from mimetypes import guess_type
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
        return str(type(value).__name__) == 'SerializationIterator' and hasattr(
            value, '__next__'
        )

    def _process_file_data(self, file_obj):
        """Process file object into base64 encoded dict format."""
        # Read the file data and encode it as base64
        file_content = file_obj.read()

        # Get filename - handle both regular files and BytesIO objects
        filename = getattr(file_obj, 'name', "document.pdf")

        if isinstance(filename, (bytes, bytearray)):
            filename = filename.decode('utf-8')

        # manage mimetype based on file extension
        mimetype = guess_type(filename)[0] or 'application/pdf'

        return {
            'data': base64.b64encode(file_content).decode('utf-8'),
            'mimetype': mimetype,
            'filename': os.path.basename(filename),
        }

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        for key, value in data.items():
            if key == 'file' and self._check_if_serialization_iterator(value):
                # Direct file case
                file_obj = self._iterator_to_buffered_reader(value)
                data[key] = self._process_file_data(file_obj)
            elif key == 'files' and isinstance(value, list):
                # List of objects case
                for index, item in enumerate(value):
                    if isinstance(item, dict) and 'file' in item:
                        if self._check_if_serialization_iterator(item['file']):
                            file_obj = self._iterator_to_buffered_reader(item['file'])
                            data[key][index]['file'] = self._process_file_data(file_obj)
        return data
