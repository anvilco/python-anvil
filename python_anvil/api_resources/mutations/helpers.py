from typing import List, Type

from python_anvil.api_resources.base import BaseModel


def get_payload_attrs(payload_model: Type[BaseModel]) -> List[str]:
    return list(payload_model.model_fields.keys())
