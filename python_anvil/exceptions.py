"""The exception names from before 6.0.0. New code should import from `python_anvil.errors`."""

from python_anvil.errors import AnvilError, AnvilRequestError


AnvilException = AnvilError
AnvilRequestException = AnvilRequestError

__all__ = ["AnvilException", "AnvilRequestException"]
