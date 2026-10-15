"""Local file evidence only; no engine, shell, network, or AI execution.

Copyright 2026 KOUSHIROU WORKS. CC BY 4.0; see LICENSE.md.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import uuid


REPO = Path(__file__).resolve().parent
STATES = {"passed", "failed", "blocked", "not_run"}


class ConfigError(ValueError):
    pass


def relative_path(value):
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise ConfigError("invalid_relative_path")
    value = value.replace("\\", "/")
    if PureWindowsPath(value).drive or value.startswith("/") or ":" in value:
        raise ConfigError("absolute_path_not_allowed")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ConfigError("invalid_relative_path")
    return Path(value)


def inside(root, relative):
    target = (root / relative).resolve()
    if target == root or not target.is_relative_to(root):
        raise ConfigError("path_outside_workspace")
    return target


def load_config(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ConfigError("duplicate_config_key")
            result[key] = value
        return result

    try:
        config = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ConfigError("config_unreadable_or_invalid_json") from None
    required = {"schema_version", "workspace", "report_dir", "blender_executable", "artifacts"}
    if not isinstance(config, dict) or set(config) != required:
        raise ConfigError("invalid_config_fields")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ConfigError("unsupported_schema_version")
    work = config["workspace"]
    if not isinstance(work, str) or not work.strip() or any(ord(c) < 32 for c in work):
        raise ConfigError("invalid_workspace")
    root = (path.resolve().parent / work).resolve()
    if not root.is_dir():
        raise ConfigError("workspace_not_directory")
    if root.is_relative_to(REPO) or REPO.is_relative_to(root):
        raise ConfigError("workspace_must_be_outside_repository")
    report_relative = relative_path(config["report_dir"])
    output = inside(root, report_relative)
    if output.exists() and not output.is_dir():
        raise ConfigError("report_dir_not_directory")
    if path.resolve().is_relative_to(output):
        raise ConfigError("config_inside_report_dir")
    blender = config["blender_executable"]
    if blender is not None and (not isinstance(blender, str) or not blender.strip()
                                or any(ord(c) < 32 for c in blender)):
        raise ConfigError("invalid_blender_path")
    artifacts = config["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ConfigError("artifacts_must_be_nonempty_list")
    seen = set()
    for item in artifacts:
        if not isinstance(item, dict) or set(item) - {"path", "sha256"} or "path" not in item:
            raise ConfigError("invalid_artifact_fields")
        rel = relative_path(item["path"])
        target = inside(root, rel)
        key = rel.as_posix().casefold()
        if key in seen:
            raise ConfigError("duplicate_artifact")
        seen.add(key)
        if target.is_relative_to(output) or output.is_relative_to(target):
            raise ConfigError("artifact_overlaps_report_dir")
        if "sha256" in item and (not isinstance(item["sha256"], str)
                                  or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])):
            raise ConfigError("invalid_expected_sha256")
    return config, root, report_relative


def check(check_id, status, reason, **fields):
    assert status in STATES
    return {"id": check_id, "status": status, "reason": reason, **fields}


def summarize(checks):
    return next(state for state in ("failed", "blocked", "not_run", "passed")
                if any(c["status"] == state for c in checks))


def inspect_artifact(root, item, index):
    check_id = "artifact_" + str(index)
    rel = relative_path(item["path"])
    fields = {"path": rel.as_posix()}
    try:
        target = inside(root, rel)
        if not target.is_file():
            return check(check_id, "failed", "missing_or_not_regular_file", **fields)
        digest = hashlib.sha256()
        size = 0
        with target.open("rb") as source:
            before = os.fstat(source.fileno())
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
            after = os.fstat(source.fileno())
        current = target.stat()
        # Windows stat/fstat can expose different ctime semantics. Compare
        # identity, size and modification time, not creation/change time.
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        if signature(before) != signature(after) or signature(after) != signature(current):
            return check(check_id, "failed", "artifact_changed_during_read", **fields)
        fields.update(size_bytes=size, sha256=digest.hexdigest())
        if not size:
            return check(check_id, "failed", "empty_artifact", **fields)
        if "sha256" in item and fields["sha256"] != item["sha256"]:
            return check(check_id, "failed", "sha256_mismatch", **fields)
        return check(check_id, "passed", "file_evidence_only", **fields)
    except (OSError, ValueError, RuntimeError):
        return check(check_id, "blocked", "artifact_unreadable_or_unsafe", **fields)


def run(config_path, mode="run", write_report=False):
    """Return JSON-compatible evidence and an exit code, without launching apps."""
    report = {
        "schema_version": 1,
        "tool_version": "0.1.0",
        "run_id": uuid.uuid4().hex,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "dry_run": not write_report,
        "scope": "local_file_evidence",
        "checks": [],
        "report_saved": False,
    }
    checks = report["checks"]
    root = report_relative = None
    try:
        config, root, report_relative = load_config(Path(config_path))
        report["config_sha256"] = hashlib.sha256(
            json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        checks.append(check("config", "passed", "paths_and_schema_checked"))
        blender = config["blender_executable"]
        if blender is None:
            checks.append(check("blender_path", "not_run", "not_configured"))
        else:
            executable = (Path(config_path).resolve().parent / blender).resolve()
            present = executable.is_file() and os.access(executable, os.X_OK)
            checks.append(check("blender_path", "passed" if present else "blocked",
                                "file_available_not_executed" if present else "executable_unavailable"))
        if mode == "run":
            checks.extend(inspect_artifact(root, item, i)
                          for i, item in enumerate(config["artifacts"], 1))
        else:
            checks.append(check("artifacts", "not_run", "preflight_only"))
    except (OSError, ValueError, RuntimeError) as exc:
        # Never echo raw configuration, absolute paths, or exception text.
        reason = str(exc) if isinstance(exc, ConfigError) else "config_path_unavailable"
        checks.append(check("config", "blocked", reason))
        root = None
    checks.append(check("engine_validation", "not_run", "no_blender_unity_or_device_execution"))
    report["status"] = summarize(checks)
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    if write_report:
        if root is None:
            checks.append(check("report_write", "blocked", "no_validated_destination"))
        else:
            target = None
            created = False
            try:
                output = inside(root, report_relative)
                output.mkdir(parents=True, exist_ok=True)
                output = inside(root, report_relative)
                target = output / (report["run_id"] + ".json")
                # Exclusive creation: a previous report is never replaced.
                with target.open("x", encoding="utf-8", newline="\n") as stream:
                    created = True
                    report["report_saved"] = True
                    report["report_path"] = (report_relative / target.name).as_posix()
                    json.dump(report, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
            except (OSError, ValueError, RuntimeError):
                report["report_saved"] = False
                report.pop("report_path", None)
                if created:
                    try:
                        target.unlink()
                    except OSError:
                        pass
                checks.append(check("report_write", "blocked", "report_not_saved"))
    report["status"] = summarize(checks)
    # 0 means requested checks completed, never that engine validation passed.
    code = 2 if any(c["status"] == "blocked" for c in checks) else (
        1 if any(c["status"] == "failed" for c in checks) else 0)
    return report, code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "run"))
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--write-report", action="store_true",
                        help="Explicitly save a new report in the configured private workspace")
    args = parser.parse_args(argv)
    report, code = run(args.config, args.mode, args.write_report)
    # ASCII escapes keep JSON readable by machines on legacy Windows consoles.
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
