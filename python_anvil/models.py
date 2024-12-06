from typing import Any
import warnings
from pydantic import BaseModel, ConfigDict
from io import IOBase, BytesIO, BufferedReader

try:    
    from pydantic.version import VERSION as PYDANTIC_VERSION
    IS_V2 = not PYDANTIC_VERSION.startswith('1')
except ImportError:    
    IS_V2 = False

if IS_V2:
    class FileCompatibleBaseModel(BaseModel):
        """
            Patched model_dump to extract file objects from SerializationIterator in V2
            and return as BufferedReader
        """ 
        def model_dump(self, **kwargs):
            
            data = super().model_dump(**kwargs)
            for key, value in data.items():
                if str(type(value).__name__) == 'SerializationIterator' and hasattr(value, '__next__'):
                    content = bytearray()
                    try:
                        while True:
                            content.extend(next(value))
                    except StopIteration:
                        data[key] = BufferedReader(BytesIO(bytes(content)))
            return data

else:
    FileCompatibleBaseModel = BaseModel
