"""Exercise the CI entry point, including its failure exit code."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECK = Path(__file__).resolve().parents[1] / "check_alembic_heads.py"


class MigrationHeadCheckTests(unittest.TestCase):
    def test_empty_single_multiple_and_merged_heads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            versions = root / "versions"
            versions.mkdir()
            config = root / "alembic.ini"
            config.write_text(f"[alembic]\nscript_location = {root}\n", encoding="utf-8")

            def run():
                return subprocess.run(
                    [sys.executable, str(CHECK), str(config)],
                    capture_output=True,
                    text=True,
                )

            def revision(name, parent):
                (versions / f"{name}.py").write_text(
                    f"revision = {name!r}\ndown_revision = {parent!r}\n",
                    encoding="utf-8",
                )

            self.assertEqual(run().returncode, 1)
            revision("base", None)
            self.assertEqual(run().returncode, 0)
            revision("left", "base")
            revision("right", "base")
            result = run()
            self.assertEqual(result.returncode, 1)
            self.assertIn("found 2", result.stderr)
            revision("merged", ("left", "right"))
            self.assertEqual(run().returncode, 0)


if __name__ == "__main__":
    unittest.main()
