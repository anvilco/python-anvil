from pydantic import BaseModel


def get_payload_attrs(payload_model: type[BaseModel]) -> list[str]:
    return list(payload_model.model_fields.keys())
