"""Temporary, synthetic fixtures only. CC BY 4.0; see LICENSE.md."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import harness


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.artifact = self.root / "dummy.txt"
        self.artifact.write_bytes(b"fictional evidence\n")
        self.config_path = self.root / "config.json"
        self.config = {
            "schema_version": 1, "workspace": ".", "report_dir": "reports",
            "blender_executable": None,
            "artifacts": [{"path": "dummy.txt", "sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest()}],
        }
        self.save_config()

    def save_config(self):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")

    def result(self, report, check_id):
        return next(c for c in report["checks"] if c["id"] == check_id)

    def test_dry_run_hashes_without_writing_or_claiming_engine_success(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        report, code = harness.run(self.config_path)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "not_run")
        item = self.result(report, "artifact_1")
        self.assertEqual(item["status"], "passed")
        self.assertEqual(item["sha256"], self.config["artifacts"][0]["sha256"])
        self.assertEqual(item["size_bytes"], len(self.artifact.read_bytes()))
        self.assertEqual(self.result(report, "engine_validation")["status"], "not_run")
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        self.assertNotIn(str(self.root), json.dumps(report))

    def test_preflight_does_not_read_artifacts(self):
        self.artifact.unlink()
        report, code = harness.run(self.config_path, mode="preflight")
        self.assertEqual(code, 0)
        self.assertEqual(self.result(report, "artifacts")["status"], "not_run")

    def test_missing_artifact_failure_is_saved(self):
        self.artifact.unlink()
        report, code = harness.run(self.config_path, write_report=True)
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "failed")
        saved = json.loads((self.root / report["report_path"]).read_text(encoding="utf-8"))
        self.assertEqual(saved, report)
        self.assertEqual(self.result(saved, "artifact_1")["reason"], "missing_or_not_regular_file")

    def test_bad_hash_and_empty_artifact_fail(self):
        for content, reason in [(b"changed", "sha256_mismatch"), (b"", "empty_artifact")]:
            with self.subTest(reason=reason):
                self.artifact.write_bytes(content)
                report, code = harness.run(self.config_path)
                self.assertEqual(code, 1)
                self.assertEqual(self.result(report, "artifact_1")["reason"], reason)

    def test_misconfiguration_blocks_and_writes_no_files(self):
        for field, value in [("workspace", "missing"), ("workspace", str(harness.REPO)),
                             ("report_dir", "../escape"), ("report_dir", str(self.root)),
                             ("schema_version", True), ("artifacts", []),
                             ("artifacts", [{"path": "../escape.txt"}]),
                             ("artifacts", [{"path": "dummy.txt", "sha256": "bad"}]),
                             ("artifacts", [{"path": "dummy.txt"}, {"path": "dummy.txt"}])]:
            with self.subTest(field=field, value=value):
                original = self.config[field]
                self.config[field] = value
                self.save_config()
                report, code = harness.run(self.config_path, write_report=True)
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "blocked")
                self.assertFalse(report["report_saved"])
                self.assertFalse((self.root / "reports").exists())
                self.config[field] = original

    def test_unavailable_blender_is_not_a_pass(self):
        self.config["blender_executable"] = "missing-blender"
        self.save_config()
        report, code = harness.run(self.config_path, write_report=True)
        self.assertEqual(code, 2)
        self.assertEqual(self.result(report, "blender_path")["status"], "blocked")
        self.assertTrue(report["report_saved"])

    def test_reports_do_not_overwrite(self):
        first, _ = harness.run(self.config_path, write_report=True)
        original = (self.root / first["report_path"]).read_bytes()
        second, _ = harness.run(self.config_path, write_report=True)
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual((self.root / first["report_path"]).read_bytes(), original)

    def test_report_name_collision_preserves_existing_file(self):
        with patch.object(harness.uuid, "uuid4", return_value=SimpleNamespace(hex="fixed-id")):
            first, _ = harness.run(self.config_path, write_report=True)
            target = self.root / first["report_path"]
            original = target.read_bytes()
            second, code = harness.run(self.config_path, write_report=True)
        self.assertEqual(code, 2)
        self.assertFalse(second["report_saved"])
        self.assertEqual(target.read_bytes(), original)

    def test_available_executable_is_only_a_file_check(self):
        candidate = self.root / "fake-blender;not-a-command"
        candidate.write_text("FICTIONAL EXECUTABLE PLACEHOLDER", encoding="utf-8")
        candidate.chmod(0o700)
        self.config["blender_executable"] = candidate.name
        self.save_config()
        report, code = harness.run(self.config_path)
        self.assertEqual(code, 0)
        self.assertEqual(self.result(report, "blender_path")["reason"], "file_available_not_executed")
        self.assertEqual(self.result(report, "engine_validation")["status"], "not_run")
        self.assertEqual(report["status"], "not_run")

    def test_changed_file_is_not_accepted(self):
        real_fstat = os.fstat
        calls = 0
        def changed_fstat(fd):
            nonlocal calls
            calls += 1
            result = real_fstat(fd)
            fields = {key: getattr(result, key) for key in
                      ["st_dev", "st_ino", "st_size", "st_mtime_ns"]}
            if calls == 2:
                fields["st_size"] += 1
            return SimpleNamespace(**fields)
        with patch.object(harness.os, "fstat", changed_fstat):
            report, code = harness.run(self.config_path)
        self.assertEqual(code, 1)
        self.assertEqual(self.result(report, "artifact_1")["reason"], "artifact_changed_during_read")

    def test_report_write_failure_is_in_stdout_result(self):
        original_open = Path.open
        def fail_report(path, *args, **kwargs):
            if args and args[0] == "x":
                raise PermissionError("private path must not be echoed")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", fail_report):
            report, code = harness.run(self.config_path, write_report=True)
        self.assertEqual(code, 2)
        self.assertFalse(report["report_saved"])
        self.assertEqual(self.result(report, "report_write")["reason"], "report_not_saved")
        self.assertNotIn("private path", json.dumps(report))

    def test_invalid_json_and_duplicate_keys(self):
        for content in ["not json", '{"workspace":".","workspace":"elsewhere"}']:
            self.config_path.write_text(content, encoding="utf-8")
            report, code = harness.run(self.config_path)
            self.assertEqual(code, 2)
            self.assertEqual(report["status"], "blocked")

    def test_symlink_escape_is_blocked(self):
        with tempfile.TemporaryDirectory() as other:
            link = self.root / "outside"
            try:
                link.symlink_to(other, target_is_directory=True)
            except OSError:
                self.skipTest("OS does not permit unprivileged symlinks")
            self.config["report_dir"] = "outside/reports"
            self.save_config()
            report, code = harness.run(self.config_path, write_report=True)
            self.assertEqual(code, 2)
            self.assertFalse((Path(other) / "reports").exists())

    def test_cli_emits_parseable_json_on_failure(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = harness.main(["run", "--config", str(self.root / "absent.json")])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
