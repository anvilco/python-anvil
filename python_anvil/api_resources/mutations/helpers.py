from typing import List, Text
from python_anvil.api_resources.base import BaseModel


def get_payload_attrs(payload_model: BaseModel) -> List[Text]:
    return list(payload_model.__fields__.keys())
