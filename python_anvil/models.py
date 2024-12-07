from typing import Any
from io import BytesIO, BufferedReader

try:        
    from pydantic import BaseModel
    from pydantic.version import VERSION as PYDANTIC_VERSION
    IS_V2 = not PYDANTIC_VERSION.startswith('1')
except ImportError:    
    from pydantic.v1 import BaseModel
    IS_V2 = False

if IS_V2:
    class FileCompatibleBaseModel(BaseModel):
        """
            Patched model_dump to extract file objects from SerializationIterator in V2
            and return as BufferedReader
        """ 

        def _iterator_to_buffered_reader(self, value):
            content = bytearray()
            try:
                while True:
                    content.extend(next(value))
            except StopIteration:
                # Create a BytesIO with the content
                bio = BytesIO(bytes(content))
                # Get the total length
                bio.seek(0, 2)  # Seek to end
                total_length = bio.tell()
                bio.seek(0)  # Reset to start
                
                # Create a BufferedReader with the content
                reader = BufferedReader(bio)
                # Add a length attribute that requests_toolbelt can use
                reader.len = total_length
                return reader
        
        def _check_if_serialization_iterator(self, value):
            return str(type(value).__name__) == 'SerializationIterator' and hasattr(value, '__next__')

        def model_dump(self, **kwargs):
            data = super().model_dump(**kwargs)
            for key, value in data.items():
                if key == 'file' and self._check_if_serialization_iterator(value):
                    # Direct file case
                    data[key] = self._iterator_to_buffered_reader(value)
                elif key == 'files' and isinstance(value, list):
                    # List of objects case
                    for index, item in enumerate(value):
                        if isinstance(item, dict) and 'file' in item:
                            if self._check_if_serialization_iterator(item['file']):
                                data[key][index]['file'] = self._iterator_to_buffered_reader(item['file'])
            return data

else:
    FileCompatibleBaseModel = BaseModel
