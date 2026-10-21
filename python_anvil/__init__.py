from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("python_anvil")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "(local)"

from python_anvil.api import Anvil
from python_anvil.constants import VERSION_LATEST, VERSION_LATEST_PUBLISHED
from python_anvil.errors import AnvilError, AnvilRequestError
from python_anvil.models import FileCompatibleBaseModel
from python_anvil.upload import UploadWithOptions, prepare_graphql_file


__all__ = [
    "VERSION_LATEST",
    "VERSION_LATEST_PUBLISHED",
    "Anvil",
    "AnvilError",
    "AnvilRequestError",
    "FileCompatibleBaseModel",
    "UploadWithOptions",
    "__version__",
    "prepare_graphql_file",
]
