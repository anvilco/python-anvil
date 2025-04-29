"""Plugins to extract project metadata from local repositories."""

import configparser
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class Plugin(ABC):
    """Base class for repository plugins."""

    @abstractmethod
    def matches(self, cwd: Path) -> bool:
        """Determine if the current directory contains repository information."""
        raise NotImplementedError

    @abstractmethod
    def get_slug(self, cwd: Path) -> str:
        """Parse the 'owner/project' from the current directory."""
        raise NotImplementedError


def get_slug(cwd: Optional[Path] = None) -> str:
    """Parse the 'owner/project' from the current directory."""
    cwd = cwd or Path.cwd()
    plugin = _find_plugin(cwd)
    return plugin.get_slug(cwd)


def _find_plugin(cwd: Path) -> Plugin:
    """Find an return a matching repository plugin."""
    for cls in Plugin.__subclasses__():
        plugin = cls()  # type: ignore
        if plugin.matches(cwd):
            return plugin

    raise RuntimeError(f"No repository data found: {cwd}")


class Git(Plugin):
    """Metadata extractor for Git repositories."""

    def matches(self, cwd: Path) -> bool:
        return ".git" in os.listdir(cwd)

    def get_slug(self, cwd: Path) -> str:
        config = configparser.ConfigParser()
        config.read(cwd / ".git" / "config")
        try:
            url = config['remote "origin"']["url"]
        except KeyError:
            url = config['branch "main"']["remote"]
        parts = url.replace(".git", "").split("/")
        return "/".join(parts[-2:])
