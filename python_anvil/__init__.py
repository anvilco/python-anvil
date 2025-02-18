from importlib.metadata import PackageNotFoundError, version

from python_anvil import api, cli
from python_anvil.models import FileCompatibleBaseModel


try:
    __version__ = version('python_anvil')
except PackageNotFoundError:
    __version__ = '(local)'

__all__ = ['api', 'cli', 'FileCompatibleBaseModel']
