#!/usr/bin/env python3
"""Install or verify the runtime portion of a Storyboard-enabled Hermes fork."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in {".json", ".md", ".py", ".toml", ".yaml", ".yml"}:
        try:
            text = data.decode("utf-8")
            data = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        except UnicodeDecodeError:
            pass
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def read_env_names(path: Path) -> set[str]:
    names = set(os.environ)
    if not path.is_file():
        return names
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        names.add(stripped.split("=", 1)[0].strip())
    return names


def assert_core_integration(fork_root: Path) -> None:
    checks = {
        fork_root / "gateway" / "session_context.py": "HERMES_STORYBOARD_PLATFORM_TOKEN",
        fork_root / "gateway" / "platforms" / "api_server.py": "X-Hermes-Storyboard-Script-Name-B64",
        fork_root / "toolsets.py": '"storyboard": {',
        fork_root / "hermes_cli" / "tools_config.py": '"storyboard",      "Storyboard Platform"',
        fork_root / "tools" / "storyboard_api_tool.py": 'name="canvas_image_generate"',
        fork_root / "tools" / "zenmux_video_analyze_tool.py": 'name="zenmux_video_analyze"',
    }
    for path, marker in checks.items():
        if not path.is_file():
            fail(f"Required fork file is missing: {path}")
        source = path.read_text(encoding="utf-8")
        if marker not in source:
            fail(f"Storyboard integration marker is missing from {path}: {marker}")
        if path.suffix == ".py":
            compile(source, str(path), "exec")


def assert_toolset_integration(fork_root: Path) -> None:
    expected_tools = {
        "storyboard_api",
        "canvas_image_generate",
        "zenmux_video_analyze",
    }
    sys.path.insert(0, str(fork_root))
    try:
        importlib.import_module("tools.storyboard_api_tool")
        importlib.import_module("tools.zenmux_video_analyze_tool")
        from hermes_cli.tools_config import CONFIGURABLE_TOOLSETS, _get_platform_tools
        from tools.registry import registry
        from toolsets import resolve_toolset

        registered = set(registry.get_tool_names_for_toolset("storyboard"))
        if not expected_tools.issubset(registered):
            fail(f"Storyboard registry tools are missing: {', '.join(sorted(expected_tools - registered))}")

        resolved = set(resolve_toolset("storyboard"))
        if not expected_tools.issubset(resolved):
            fail(f"Storyboard toolset resolution is incomplete: {', '.join(sorted(expected_tools - resolved))}")

        configurable = {name for name, _label, _description in CONFIGURABLE_TOOLSETS}
        if "storyboard" not in configurable:
            fail("Storyboard toolset is missing from CONFIGURABLE_TOOLSETS")

        for platform in ("api_server", "wecom", "wecom_callback"):
            enabled = _get_platform_tools({}, platform, include_default_mcp_servers=False)
            if "storyboard" not in enabled:
                fail(f"Storyboard toolset is not enabled for platform: {platform}")
    finally:
        try:
            sys.path.remove(str(fork_root))
        except ValueError:
            pass


def verify_release_files(fork_root: Path, release: dict) -> None:
    for record in release.get("files") or []:
        relative = str(record.get("path") or "")
        path = (fork_root / relative).resolve()
        if fork_root not in path.parents:
            fail(f"Unsafe release file path: {relative}")
        if not path.is_file():
            fail(f"Fork release file is missing: {relative}")
        if sha256(path) != str(record.get("sha256") or ""):
            fail(f"Fork release file hash mismatch: {relative}")


def install_skill(source: Path, skills_root: Path, backup_root: Path) -> Path:
    destination = (skills_root / source.name).resolve()
    if destination.parent != skills_root.resolve():
        fail(f"Unsafe skill destination: {destination}")
    if destination.exists():
        backup_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(destination, backup_root / source.name)
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return destination


def verify_installed_skill(source: Path, destination: Path) -> None:
    for source_file in sorted(path for path in source.rglob("*") if path.is_file()):
        relative = source_file.relative_to(source)
        target_file = destination / relative
        if not target_file.is_file() or sha256(source_file) != sha256(target_file):
            fail(f"Installed skill differs from fork bundle: {source.name}/{relative.as_posix()}")


def current_commit(fork_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=fork_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Skills and verify a Storyboard-enabled Hermes fork.")
    parser.add_argument("--hermes-home", type=Path, help="Defaults to HERMES_HOME or ~/.hermes.")
    parser.add_argument("--check", action="store_true", help="Verify only; do not copy Skills.")
    parser.add_argument("--require-env", action="store_true", help="Require Storyboard API and client credentials.")
    args = parser.parse_args()

    bundle_root = Path(__file__).resolve().parent
    fork_root = bundle_root.parent.resolve()
    release_path = bundle_root / "release.json"
    if not release_path.is_file():
        fail(f"Fork release manifest is missing: {release_path}")
    release = json.loads(release_path.read_text(encoding="utf-8-sig"))
    assert_core_integration(fork_root)
    assert_toolset_integration(fork_root)
    verify_release_files(fork_root, release)

    configured_home = args.hermes_home or os.getenv("HERMES_HOME") or (Path.home() / ".hermes")
    hermes_home = Path(configured_home).expanduser().resolve()
    skills_root = hermes_home / "skills"
    skill_sources = sorted(path for path in (bundle_root / "skills").iterdir() if path.is_dir())
    if not skill_sources:
        fail("Fork bundle does not contain any Skills")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_root = hermes_home / "integration-backups" / f"fork-{timestamp}" / "skills"
    installed: list[Path] = []
    skills_root.mkdir(parents=True, exist_ok=True)
    for source in skill_sources:
        destination = skills_root / source.name
        if not args.check:
            destination = install_skill(source, skills_root, backup_root)
        verify_installed_skill(source, destination)
        installed.append(destination)

    if args.require_env:
        names = read_env_names(hermes_home / ".env")
        required = {
            "STORYBOARD_API_BASE",
            "HERMES_AGENT_CLIENT_ID",
            "HERMES_AGENT_CLIENT_SECRET",
        }
        missing = sorted(required - names)
        if missing:
            fail(f"Required Hermes environment variables are missing: {', '.join(missing)}")

    state_root = hermes_home / "integration-state"
    state_root.mkdir(parents=True, exist_ok=True)
    state = {
        "name": release.get("name"),
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "forkCommit": current_commit(fork_root),
        "releaseTag": release.get("releaseTag"),
        "hermesHome": str(hermes_home),
        "skills": [str(path) for path in installed],
        "checkOnly": bool(args.check),
    }
    (state_root / "storyboard-platform-fork.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Storyboard Hermes fork runtime verification passed.")
    print(f"Fork commit: {state['forkCommit'] or '(not a Git checkout)'}")
    print(f"Hermes home: {hermes_home}")
    print("Restart the Hermes gateway to load the integrated tools and session context.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
