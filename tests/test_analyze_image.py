"""Tests for analyze_image.py.

The script runs entirely at module import time, so we exercise it via
subprocess to keep the tests honest. Network paths are not invoked here —
those would require either real keys or a local HTTP fake.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "analyze_image.py"


def _run(args, env=None):
    """Run the script with a fresh, controlled environment."""
    base_env = {"PATH": os.environ.get("PATH", "")}
    if env:
        base_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=base_env,
        timeout=15,
    )


class CliArgumentTests(unittest.TestCase):
    def test_no_args_prints_usage_and_exits_nonzero(self):
        result = _run([])
        self.assertNotEqual(result.returncode, 0)
        # Usage string from the module docstring.
        self.assertIn("Usage", result.stdout + result.stderr)

    def test_help_flag_prints_usage(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                result = _run([flag])
                self.assertNotEqual(result.returncode, 0)
                combined = result.stdout + result.stderr
                self.assertIn("Usage", combined)
                self.assertIn("ANTHROPIC_API_KEY", combined)


class ApiKeyTests(unittest.TestCase):
    def test_missing_api_key_errors_out(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as f:
            # Strip ANTHROPIC_API_KEY by passing a minimal env.
            result = _run([f.name])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ANTHROPIC_API_KEY", result.stdout + result.stderr)


class FormatValidationTests(unittest.TestCase):
    def test_unsupported_extension_errors_out(self):
        with tempfile.NamedTemporaryFile(suffix=".bmp") as f:
            result = _run([f.name], env={"ANTHROPIC_API_KEY": "fake-key"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported format", result.stdout + result.stderr)

    def test_extension_lookup_is_case_insensitive(self):
        # Upper-case .JPG should not be reported as unsupported. We can't fully
        # run the script (no network/key), but we can confirm that the script
        # gets past the extension check by giving a missing file: it should
        # then fail trying to open the file rather than rejecting the format.
        with tempfile.TemporaryDirectory() as d:
            ghost = Path(d) / "ghost.JPG"  # uppercase, doesn't exist
            result = _run([str(ghost)], env={"ANTHROPIC_API_KEY": "fake-key"})
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertNotIn("unsupported format", combined)
        # Should fail on file open instead.
        self.assertTrue(
            "No such file" in combined
            or "FileNotFoundError" in combined
            or "Errno 2" in combined,
            msg=f"unexpected output: {combined!r}",
        )


class MediaMapTests(unittest.TestCase):
    """Sanity check that the supported-format table matches docs."""

    EXPECTED = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    def test_readme_supported_formats_match_script(self):
        text = SCRIPT.read_text()
        for ext, mime in self.EXPECTED.items():
            self.assertIn(ext, text)
            self.assertIn(mime, text)


if __name__ == "__main__":
    unittest.main()
