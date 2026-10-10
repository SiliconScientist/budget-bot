"""Exercise the privacy guard against a real Git index."""
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_privacy.py"


class PrivacyCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True)

    def stage(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self.git("add", "--", name)

    def check(self):
        return subprocess.run([sys.executable, str(SCRIPT)], cwd=self.root,
                              capture_output=True, text=True)

    def test_source_is_allowed(self):
        self.stage("src/example.py", "print('hello')\n")
        self.assertEqual(self.check().returncode, 0)

    def test_private_paths_are_blocked_even_when_force_added(self):
        for path in ("config.toml", "category.toml", "data/raw/a.txt",
                     "exports/year.txt", ".env.production", "budget.xlsx",
                     "statement.csv", "backup.bundle", ".private/backup.txt"):
            with self.subTest(path=path):
                self.stage(path, "private\n")
                self.assertNotEqual(self.check().returncode, 0)
                self.git("rm", "--cached", "--", path)

    def test_uses_staged_content_and_does_not_print_secret(self):
        secret = "gh" + "p_" + "A" * 36
        self.stage("src/example.py", "token = '" + secret + "'\n")
        (self.root / "src/example.py").write_text("# clean working copy\n")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(secret, result.stdout + result.stderr)

    def test_account_suffix_in_source_is_blocked(self):
        self.stage("example.txt", "debit" + "1234")
        self.assertNotEqual(self.check().returncode, 0)

    def test_only_approved_fixture_bytes_are_allowed(self):
        name = "tests/fixtures/demo.csv"
        content = "description,amount\nExample,10.00\n"
        self.stage(name, content)
        self.stage("tests/fixtures/synthetic-manifest.json", json.dumps({
            name: hashlib.sha256(content.encode()).hexdigest()
        }))
        self.assertEqual(self.check().returncode, 0)
        self.stage(name, content + "Private,99.00\n")
        self.assertNotEqual(self.check().returncode, 0)

    def test_symlink_is_blocked(self):
        (self.root / "example.txt").symlink_to("/tmp/private-data")
        self.git("add", "example.txt")
        self.assertNotEqual(self.check().returncode, 0)


if __name__ == "__main__":
    unittest.main()
