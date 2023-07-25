# pylint: disable=no-self-argument
import re

# Disabling pylint no-name-in-module because this is the documented way to
# import `BaseModel` and it's not broken, so let's keep it.
from pydantic import ConfigDict, BaseModel as _BaseModel  # pylint: disable=no-name-in-module


under_pat = re.compile(r"_([a-z])")


def underscore_to_camel(name):
    ret = under_pat.sub(lambda x: x.group(1).upper(), name)
    return ret


class BaseModel(_BaseModel):
    model_config = ConfigDict(alias_generator=underscore_to_camel, populate_by_name=True, extra="allow")
