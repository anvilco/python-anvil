from typing import Any, List

from .base import BaseModel


class CastFields:
    fields: List[Any]


class Cast(BaseModel):
    eid: str
    title: str
    fieldInfo: CastFields
