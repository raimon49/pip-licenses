"""Tests package for pip-licenses."""

# ruff: file-ignore[F401,]
import unittest

from ._examples import (
    ExampleOutput,
    ExampleRunner,
    ExampleScript,
)
from ._output_validator import OutputValidator
from .test_readme_examples import (
    discover_examples,
    load_readme,
)
