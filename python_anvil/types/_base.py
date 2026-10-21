"""The base class of the generated models."""

from pydantic import BaseModel, ConfigDict


class GeneratedModel(BaseModel):
    """A generated model.

    Fields are snake_case with camelCase aliases, and can be set by either
    name. Enum fields hold their plain values, so `model_dump` gives JSON.
    Extra fields are kept, so a field the API added that these types don't
    have yet still gets sent.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )
