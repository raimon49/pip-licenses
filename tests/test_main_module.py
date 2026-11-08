# tests.test_main_module
#
# MIT License
#
# Copyright (c) 2026 Mr. Walls
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import argparse
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import piplicenses.__main__ as mainmod


class DummyConfig:
    """Simple config stub that stores keyword arguments as attributes."""

    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)


def make_fake_parser(seen: dict[str, Any], values: dict[str, Any]) -> Any:  # noqa: ANN401 -- intentionally dynamically typed
    """Build a parser stub that records CLI args and returns a namespace.

    The stub intentionally keeps the interface minimal and specific to the
    behaviour exercised by the tests.
    """

    class FakeParser:
        """Minimal parser stub used to verify argv handling."""

        def parse_args(self, args: list[str]) -> SimpleNamespace:
            """Record the parsed arguments and return a namespace-like object."""
            seen["args"] = list(args)
            return SimpleNamespace(**values)

    return FakeParser()


def install_main_stubs(
    *,
    parser_values: dict[str, Any] | None = None,
    output_string: str = "output",
    warn_string: str = "",
    saved: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], Any]:
    """Create consistent stubs for the main entry point and configuration.

    Returns a tuple containing the observed argv, the save-state dictionary, and
    a fake parser instance.
    """
    seen: dict[str, Any] = {}
    save_state: dict[str, Any] = {} if saved is None else saved
    values: dict[str, Any] = (
        {} if parser_values is None else dict(parser_values)
    )
    values.setdefault("output_file", None)

    parser = make_fake_parser(seen, values)

    return seen, save_state, parser


class AddOverridesTests(unittest.TestCase):
    """Tests covering `add_overrides()` normalization logic."""

    def test_add_overrides_handles_input_type_None(self) -> None:
        """Ensure overrides accept trivial calls."""
        base = {"base": True}

        self.assertEqual(mainmod.add_overrides({}, None), {})
        self.assertEqual(mainmod.add_overrides(base, None), {"base": True})

    def test_add_overrides_handles_input_type_dict(self) -> None:
        """Ensure overrides accept dicts."""
        base = {"base": True}

        self.assertEqual(mainmod.add_overrides(base, None), {"base": True})

        override_dict = {"flag": "value"}
        self.assertEqual(
            mainmod.add_overrides(base, override_dict),
            {"base": True, "flag": "value"},
        )

    def test_add_overrides_handles_input_type_ns(self) -> None:
        """Ensure overrides accept dicts and namespaces."""
        base = {"base": True}

        self.assertEqual(mainmod.add_overrides(base, None), {"base": True})

        ns = argparse.Namespace(foo="bar", count=3)
        self.assertEqual(
            mainmod.add_overrides(base, ns),
            {"base": True, "foo": "bar", "count": 3},
        )

    def test_add_overrides_handles_supported_input_types(self) -> None:
        """Ensure overrides accept dicts, namespaces, and attribute objects."""
        base = {"base": True}

        self.assertEqual(mainmod.add_overrides({}, None), {})
        self.assertEqual(mainmod.add_overrides(base, None), {"base": True})

        override_dict = {"flag": "value"}
        self.assertEqual(
            mainmod.add_overrides(base, override_dict),
            {"base": True, "flag": "value"},
        )

        ns = argparse.Namespace(foo="bar", count=3)
        # overrides are cumulative
        self.assertEqual(
            mainmod.add_overrides(base, ns),
            {"base": True, "flag": "value", "foo": "bar", "count": 3},
        )

        class Attrs:
            """Simple attribute-based object used for override testing."""

        obj = Attrs()
        obj.answer = 42  # type: ignore[attr-defined]
        # overrides are cumulative
        self.assertEqual(
            mainmod.add_overrides(base, obj),
            {
                "base": True,
                "answer": 42,
                "flag": "value",
                "foo": "bar",
                "count": 3,
            },
        )


class MainFunctionTests(unittest.TestCase):
    """Tests for the `main()` entry-point behaviour and failure handling."""

    def test_main_uses_sys_argv_when_no_explicit_argv(self) -> None:
        """When no argv is provided, the function should read from sys.argv."""
        _seen, save_state, parser = install_main_stubs()
        with (
            patch.object(
                mainmod.sys, "argv", ["piplicenses", "--from", "meta"]
            ),
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod, "create_output_string", return_value="output"
            ),
            patch.object(mainmod, "create_warn_string", return_value=""),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
        ):
            self.assertEqual(mainmod.main(), 0)
            self.assertEqual(_seen["args"], ["--from", "meta"])
            self.assertIsNone(save_state.get("path"))

    def test_main_accepts_single_positional_argv_list(self) -> None:
        """A single positional list/tuple should be accepted as argv."""
        seen, save_state, parser = install_main_stubs()
        with (
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod, "create_output_string", return_value="output"
            ),
            patch.object(mainmod, "create_warn_string", return_value=""),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
        ):
            self.assertEqual(mainmod.main(["--format", "json"]), 0)
            self.assertEqual(seen["args"], ["--format", "json"])

    def test_main_raises_for_invalid_positional_usage(self) -> None:
        """Unsupported positional arguments should raise a `TypeError`."""
        _, save_state, parser = install_main_stubs()
        with (
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod, "create_output_string", return_value="output"
            ),
            patch.object(mainmod, "create_warn_string", return_value=""),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
        ):
            _test_fixture: str = "not-a-list"
            with self.assertRaises(TypeError):
                mainmod.main(_test_fixture)

    def test_main_merges_cli_flags_overrides_and_kwargs(self) -> None:
        """CLI args, flags, overrides, and kwargs should merge in the expected order."""
        seen, save_state, parser = install_main_stubs(
            parser_values={"output_file": "from_cli.txt"},
            output_string="report",
        )
        with (
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod, "create_output_string", return_value="report"
            ),
            patch.object(mainmod, "create_warn_string", return_value=""),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
        ):
            self.assertEqual(
                mainmod.main(
                    argv=["--from", "meta"],
                    flags=["--summary"],
                    overrides={"output_file": "from_override.txt"},
                    ignore_packages=["a", "b"],
                ),
                0,
            )
            self.assertEqual(seen["args"], ["--from", "meta", "--summary"])
            self.assertEqual(save_state["path"], "from_override.txt")
            self.assertEqual(save_state["text"], "report")

    def test_main_prints_output_and_returns_zero_when_no_warning(self) -> None:
        """Successful execution should emit the generated output and return zero."""
        _, save_state, parser = install_main_stubs(
            output_string="report", warn_string=""
        )
        with (
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod, "create_output_string", return_value="report"
            ),
            patch.object(mainmod, "create_warn_string", return_value=""),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(mainmod.main(), 0)
            self.assertIn("report", stdout.getvalue())

    def test_main_rewraps_nonzero_system_exit_with_details(self) -> None:
        """SystemExit from output generation should be re-raised with the original args."""
        _, save_state, parser = install_main_stubs()
        with (
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod,
                "create_output_string",
                side_effect=SystemExit("broken", 7),
            ),
            patch.object(mainmod, "create_warn_string", return_value=""),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
        ):
            with self.assertRaises(SystemExit) as exc_info:
                mainmod.main()
            self.assertEqual(exc_info.exception.args, ("broken", 7))

    def test_main_re_raises_zero_system_exit_from_output_generation(
        self,
    ) -> None:
        """A zero-valued SystemExit should be preserved as a zero exit code."""
        _, save_state, parser = install_main_stubs()
        with (
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod,
                "create_output_string",
                side_effect=SystemExit(0),
            ),
            patch.object(mainmod, "create_warn_string", return_value=""),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
        ):
            with self.assertRaises(SystemExit) as exc_info:
                mainmod.main()
            self.assertEqual(exc_info.exception.code, 0)

    def test_main_warn_string_returns_zero_for_6_x_versions(self) -> None:
        """Warnings should return zero for beta/dev version strings containing `6.0.`."""
        _, save_state, parser = install_main_stubs(warn_string="warning")
        with (
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod, "create_output_string", return_value="report"
            ),
            patch.object(
                mainmod, "create_warn_string", return_value="warning"
            ),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
            patch.object(mainmod, "__version__", "6.0.0b14"),
        ):
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(mainmod.main(), 0)
            self.assertIn("warning", stderr.getvalue())

    def test_main_warn_string_returns_two_for_non_6_x_versions(self) -> None:
        """Warnings should return two for version strings outside the `6.0.*` family."""
        _, save_state, parser = install_main_stubs(warn_string="warning")
        with (
            patch.object(mainmod, "create_parser", return_value=parser),
            patch.object(mainmod, "Configuration", DummyConfig),
            patch.object(
                mainmod, "create_output_string", return_value="report"
            ),
            patch.object(
                mainmod, "create_warn_string", return_value="warning"
            ),
            patch.object(
                mainmod,
                "save_if_needs",
                side_effect=lambda path, text: save_state.update(
                    {"path": path, "text": text}
                ),
            ),
            patch.object(mainmod, "__version__", "7.0.0"),
        ):
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(mainmod.main(), 2)
            self.assertIn("warning", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
