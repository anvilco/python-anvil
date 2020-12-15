from dataclasses import dataclass

from dataclasses_json import dataclass_json
from typing import Any, List


@dataclass_json
@dataclass
class CastFields:
    fields: List[Any]


@dataclass_json
@dataclass
class Cast:
    eid: str
    title: str
    fieldInfo: CastFields
