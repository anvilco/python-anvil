"""Utilities to detect the environment this program is running on."""

import os
from pathlib import Path

CONTINUOUS_INTEGRATION = [
    # General
    "CI",
    "CONTINUOUS_INTEGRATION",
    "DISABLE_COVERAGE",
    # Travis CI
    "TRAVIS",
    # Appveyor
    "APPVEYOR",
    # CircleCI
    "CIRCLECI",
    # Drone
    "DRONE",
]


def ci():
    return any(name in CONTINUOUS_INTEGRATION for name in os.environ)


def poetry():
    return "POETRY_ACTIVE" in os.environ or Path("poetry.lock").exists()
