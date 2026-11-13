"""Preflight refusal/nonmutation checks; no Apple or game binary is bundled."""
import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "prepare", Path(__file__).resolve().parents[1] / "prepare_bf6_metalfx.py"
)
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bf6-preflight-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        bottle = self.home / "Library/Application Support/CrossOver/Bottles/Test Bottle"
        bottle.mkdir(parents=True)
        (bottle / "cxbottle.conf").write_text("test fixture")
        self.app = self.root / "CrossOver Test.app"
        base = self.app / "Contents/SharedSupport/CrossOver"
        (base / "bin").mkdir(parents=True)
        (base / "bin/wine").write_text("never executed")
        self.binary = base / "lib/apple_gptk/external/D3DMetal.framework/Versions/A/D3DMetal"
        self.binary.parent.mkdir(parents=True)
        # Synthetic fixture, not executable code or a proprietary binary.
        data = bytearray(max(off + len(old) for off, old, new in prepare.PATCHES))
        for off, old, new in prepare.PATCHES:
            data[off:off + len(old)] = old
        self.data = bytes(data)
        self.binary.write_bytes(self.data)
        self.game = self.root / "Game Folder/bf6.exe"
        self.game.parent.mkdir()
        self.game.write_text("synthetic game fixture")
        self.out = self.root / "output must not be created"
        self.argv = ["prepare_bf6_metalfx.py", "--app", str(self.app),
                     "--bottle", "Test Bottle", "--game", str(self.game),
                     "--out", str(self.out)]

    def invoke(self, extra=(), trust_fixture=True):
        expected = hashlib.sha256(self.data).hexdigest() if trust_fixture else prepare.EXPECTED
        with patch("sys.argv", self.argv + list(extra)), \
                patch.object(prepare.platform, "system", return_value="Darwin"), \
                patch.object(prepare.Path, "home", return_value=self.home), \
                patch.object(prepare, "EXPECTED", expected), \
                contextlib.redirect_stdout(io.StringIO()):
            return prepare.main()

    def assert_untouched(self):
        self.assertFalse(self.out.exists())
        self.assertEqual(self.binary.read_bytes(), self.data)

    def test_unknown_framework_refuses_before_writes(self):
        with self.assertRaisesRegex(SystemExit, "Unsupported D3DMetal"):
            self.invoke(trust_fixture=False)
        self.assert_untouched()

    def test_check_only_is_read_only(self):
        self.invoke(["--check-only"])
        self.assert_untouched()

    def test_unknown_campaign_build_refuses_before_writes(self):
        with self.assertRaisesRegex(SystemExit, "Direct-campaign startup is unverified"):
            self.invoke(["--direct-campaign"])
        self.assert_untouched()

    def test_existing_output_is_never_overwritten(self):
        self.out.mkdir()
        sentinel = self.out / "user-file.txt"
        sentinel.write_text("keep this")
        with self.assertRaisesRegex(SystemExit, "Output folder already exists"):
            self.invoke()
        self.assertEqual(sentinel.read_text(), "keep this")
        self.assertEqual(self.binary.read_bytes(), self.data)

    def test_missing_bottle_is_not_created(self):
        self.argv[self.argv.index("Test Bottle")] = "Missing Bottle"
        with self.assertRaisesRegex(SystemExit, "Existing bottle not found"):
            self.invoke()
        missing = self.home / "Library/Application Support/CrossOver/Bottles/Missing Bottle"
        self.assertFalse(missing.exists())
        self.assert_untouched()


if __name__ == "__main__":
    unittest.main()
