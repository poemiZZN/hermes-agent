#!/usr/bin/env python3
"""Install or verify the runtime portion of a profile-enabled Hermes fork."""

from __future__ import annotations

import argparse
import hashlib
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
    if path.suffix.lower() in {
        ".example",
        ".json",
        ".md",
        ".py",
        ".template",
        ".toml",
        ".yaml",
        ".yml",
    }:
        try:
            text = data.decode("utf-8")
            data = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        except UnicodeDecodeError:
            pass
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def read_env_values(path: Path) -> dict[str, str]:
    """Read one profile's .env without borrowing or logging process secrets."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        normalized_name = name.strip()
        normalized_value = value.strip()
        if (
            len(normalized_value) >= 2
            and normalized_value[0] == normalized_value[-1]
            and normalized_value[0] in {'"', "'"}
        ):
            normalized_value = normalized_value[1:-1]
        if normalized_name and normalized_value:
            values[normalized_name] = normalized_value
    return values


def read_env_names(path: Path) -> set[str]:
    return set(read_env_values(path))


def yaml_module():
    """Hermes' own YAML policy when run from a fork, else PyYAML.

    Hermes 0.22 parses config with ruamel.yaml (``hermes_yaml``) and no longer
    ships PyYAML, so the fork's own interpreter has only the former. The fork
    root goes last on sys.path: none of its modules may shadow an installed one.
    """
    fork_root = str(Path(__file__).resolve().parents[1])
    if fork_root not in sys.path:
        sys.path.append(fork_root)
    try:
        import hermes_yaml

        return hermes_yaml
    except ImportError:
        pass
    try:
        import yaml

        return yaml
    except ImportError as error:
        fail(f"Hermes' YAML module or PyYAML is required to read profile configuration: {error}")


def load_yaml_mapping(path: Path) -> dict:
    yaml = yaml_module()
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except Exception as error:
        fail(f"Unable to read YAML file {path}: {error}")
    if not isinstance(data, dict):
        fail(f"YAML root must be an object: {path}")
    return data


def write_yaml_mapping(path: Path, data: dict) -> None:
    yaml = yaml_module()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def required_env_names(profile_source: Path) -> set[str]:
    manifest = load_yaml_mapping(profile_source / "distribution.yaml")
    required: set[str] = set()
    for record in manifest.get("env_requires") or []:
        if not isinstance(record, dict) or not record.get("required"):
            continue
        name = str(record.get("name") or "").strip()
        if name:
            required.add(name)
    return required


def assert_core_integration(fork_root: Path) -> None:
    gateway = fork_root / "gateway"
    plugins = fork_root / "plugins"
    checks = {
        gateway / "storyboard_platform_context.py": "def parse_platform_headers(",
        gateway / "platforms" / "api_server.py": "parse_platform_headers(request.headers, profile)",
        gateway / "platforms" / "api_server_runs.py": "platform_context=current_platform_context()",
        gateway / "run.py": "overlay_platform_model_key(secrets)",
        plugins / "storyboard-platform" / "__init__.py": 'TOOLSET = "storyboard"',
        plugins / "storyboard-platform" / "storyboard_api_tool.py": '"name": "canvas_image_generate"',
        plugins / "storyboard-platform" / "zenmux_video_analyze_tool.py": '"name": "zenmux_video_analyze"',
        plugins / "scriptmaker-platform" / "__init__.py": 'TOOLSET = "scriptmaker"',
        plugins / "scriptmaker-platform" / "scriptmaker_agent_tool.py": "for schema in _TOOL_SCHEMAS",
    }
    for path, marker in checks.items():
        if not path.is_file():
            fail(f"Required fork file is missing: {path}")
        source = path.read_text(encoding="utf-8")
        if marker not in source:
            fail(f"Platform integration marker is missing from {path}: {marker}")
        if path.suffix == ".py":
            compile(source, str(path), "exec")
    # Built-in tool discovery imports every tools/*.py into the process-global
    # registry: a leftover pre-plugin copy would expose platform tools to every
    # profile and make the plugins' own registrations shadow a global tool.
    for legacy in ("storyboard_api_tool.py", "zenmux_video_analyze_tool.py", "scriptmaker_agent_tool.py"):
        if (fork_root / "tools" / legacy).exists():
            fail(f"Pre-plugin platform tool must be removed from the fork: tools/{legacy}")


_STORYBOARD_TOOLS = {
    "storyboard_api",
    "ask_question",
    "canvas_image_generate",
    "canvas_video_generate",
    "character_three_view_generate",
    "zenmux_video_analyze",
}

_SCRIPTMAKER_TOOLS = {
    "ask_choice",
    "list_projects",
    "select_project",
    "get_project_status",
    "read_attachment",
    "write_attachment_draft",
    "prepare_script_generation",
    "confirm_script_generation",
    "read_script_artifact",
    "propose_artifact_edit",
    "confirm_artifact_edit",
    "pause_task",
    "resume_task",
    "retry_task",
    "terminate_task",
    "export_project",
    "run_project_doctor",
    "open_feature",
    "read_market_reports",
}

_PROFILE_TOOLS = {"storyboard": _STORYBOARD_TOOLS, "scriptmaker": _SCRIPTMAKER_TOOLS}

# Spill thresholds the platform tools have always run with (12k unless listed).
_RESULT_SIZE_LIMITS = {"zenmux_video_analyze": 24000}

# Local surfaces with no platform identity: the platform toolsets stay off there.
_LOCAL_PLATFORMS = ("cli", "cron", "acp")


def assert_plugin_integration(fork_root: Path, release: dict) -> None:
    """Load this fork's platform plugins per profile in a throwaway HERMES_HOME.

    Hermes loads plugins and registers their tools per profile home. Each
    business profile must resolve exactly its own platform tools, with their
    result limits, on its own entry platforms and not on local surfaces; no
    other profile, the default one included, may resolve them at all.
    """
    import tempfile

    records = {str(record.get("name")): record for record in release.get("profiles") or []}
    sys.path.insert(0, str(fork_root))
    try:
        with tempfile.TemporaryDirectory(prefix="hermes-plugin-check-") as temporary:
            root = Path(temporary)
            (root / "config.yaml").write_text("{}\n", encoding="utf-8")
            for name, record in records.items():
                profile_home = root / "profiles" / name
                profile_home.mkdir(parents=True)
                shutil.copy2(fork_root / str(record["path"]) / "config.yaml", profile_home / "config.yaml")
            homes = [(name, root / "profiles" / name, record) for name, record in records.items()]
            for name, home, record in homes + [("default", root, {})]:
                _assert_profile_plugins(name, home, record, records)
    finally:
        try:
            sys.path.remove(str(fork_root))
        except ValueError:
            pass


def _assert_profile_plugins(name: str, home: Path, record: dict, records: dict) -> None:
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override
    from hermes_cli.config import load_config
    from hermes_cli.plugins import discover_plugins
    from hermes_cli.tools_config import _get_effective_configurable_toolsets, _get_platform_tools
    from tools.registry import registry
    from toolsets import resolve_toolset

    own = {str(item) for item in record.get("toolsets") or []}
    all_toolsets = {str(item) for other in records.values() for item in other.get("toolsets") or []}
    token = set_hermes_home_override(str(home))
    try:
        discover_plugins()
        listed = {key for key, _label, _description in _get_effective_configurable_toolsets()}
        for toolset in sorted(all_toolsets):
            resolved = set(resolve_toolset(toolset))
            if toolset not in own:
                if resolved:
                    fail(f"Profile {name} resolves foreign platform tools: {', '.join(sorted(resolved))}")
                continue
            expected = _PROFILE_TOOLS.get(toolset, set())
            if not expected <= resolved:
                fail(f"Profile {name} is missing {toolset} tools: {', '.join(sorted(expected - resolved))}")
            for tool in sorted(expected):
                limit = _RESULT_SIZE_LIMITS.get(tool, 12000)
                if registry.get_max_result_size(tool) != limit:
                    fail(f"Profile {name}: {tool} result limit is not {limit}")
            if toolset not in listed:
                fail(f"Profile {name} does not list the {toolset} toolset in /v1/toolsets")
        config = load_config()
        entry_platforms = ["api_server", *(str(route.get("platform")) for route in record.get("routes") or [])]
        for platform in entry_platforms:
            enabled = _get_platform_tools(config, platform, include_default_mcp_servers=False)
            if not own <= enabled or (all_toolsets - own) & enabled:
                fail(f"Profile {name} toolset isolation failed on {platform}")
        for platform in _LOCAL_PLATFORMS:
            if own & _get_platform_tools(config, platform, include_default_mcp_servers=False):
                fail(f"Profile {name} enables its platform toolset on {platform}")
    finally:
        reset_hermes_home_override(token)


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


def release_profiles(
    fork_root: Path,
    bundle_root: Path,
    release: dict,
    selected_names: set[str] | None,
) -> list[tuple[dict, Path]]:
    records = release.get("profiles")
    if not isinstance(records, list) or not records:
        fail("Fork release does not declare any profile distributions")

    available: dict[str, tuple[dict, Path]] = {}
    for record in records:
        if not isinstance(record, dict):
            fail("Invalid profile record in Fork release")
        name = str(record.get("name") or "").strip()
        relative = str(record.get("path") or "").strip()
        source = (fork_root / relative).resolve()
        if not name or name in available:
            fail(f"Duplicate or empty profile name in Fork release: {name!r}")
        if bundle_root not in source.parents or not source.is_dir():
            fail(f"Profile source is missing or unsafe: {relative}")
        available[name] = (record, source)

    if selected_names:
        unknown = sorted(selected_names - set(available))
        if unknown:
            fail(f"Unknown profiles requested: {', '.join(unknown)}")
        return [available[name] for name in sorted(selected_names)]
    return [available[name] for name in sorted(available)]


def remove_readonly(func, path: str, _error) -> None:
    """Retry deletion after clearing Windows read-only attributes."""
    os.chmod(path, 0o700)
    func(path)


def backup_file(destination: Path, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(destination, backup_path)


def backup_and_remove_skill(destination: Path, backup_root: Path) -> None:
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_destination = backup_root / destination.name
    if backup_destination.exists():
        shutil.rmtree(backup_destination, onerror=remove_readonly)
    shutil.copytree(destination, backup_destination)
    shutil.rmtree(destination, onerror=remove_readonly)


def install_skill(source: Path, skills_root: Path, backup_root: Path) -> Path:
    destination = (skills_root / source.name).resolve()
    if destination.parent != skills_root.resolve():
        fail(f"Unsafe skill destination: {destination}")
    if destination.exists():
        backup_and_remove_skill(destination, backup_root)
    shutil.copytree(source, destination)
    return destination


def stale_managed_skills(
    state_path: Path,
    skills_root: Path,
    desired_names: set[str],
) -> list[Path]:
    if not state_path.is_file():
        return []
    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"Unable to read previous integration state: {state_path}: {error}")

    resolved_root = skills_root.resolve()
    stale: list[Path] = []
    for raw_path in state.get("skills") or []:
        destination = Path(str(raw_path)).expanduser().resolve()
        if destination.parent != resolved_root:
            fail(f"Unsafe managed skill path in previous integration state: {destination}")
        if destination.name not in desired_names and destination.exists():
            stale.append(destination)
    return sorted(set(stale))


def verify_installed_skill(source: Path, destination: Path) -> None:
    for source_file in sorted(path for path in source.rglob("*") if path.is_file()):
        relative = source_file.relative_to(source)
        target_file = destination / relative
        if not target_file.is_file() or sha256(source_file) != sha256(target_file):
            fail(f"Installed skill differs from Fork bundle: {source.name}/{relative.as_posix()}")


def install_managed_file(
    source: Path,
    destination: Path,
    backup_root: Path,
    *,
    check: bool,
) -> None:
    if check:
        if not destination.is_file() or sha256(source) != sha256(destination):
            fail(f"Installed profile file differs from Fork bundle: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and sha256(source) != sha256(destination):
        backup_file(destination, backup_root / destination.name)
    shutil.copy2(source, destination)


def merge_release_config(
    live: dict, release: dict, prefix: str = ""
) -> tuple[dict, list[str]]:
    """Overlay the release profile config onto the site's copy.

    A preserved config.yaml used to be skipped wholesale, so a release that
    added a section (the scriptmaker ``web`` toolset and its backend) never
    reached an existing install, and ``--check`` passed anyway. The release
    owns every key it ships; the site keeps the ones it does not (model,
    providers, ``agent.max_turns``). Mappings merge per key, release scalars
    win, and lists gain missing release entries while keeping site extras.

    Returns the merged mapping and the dotted paths that changed.
    """
    merged = dict(live)
    changed: list[str] = []
    for key, release_value in release.items():
        path = f"{prefix}{key}"
        live_value = live.get(key)
        if isinstance(release_value, dict) and isinstance(live_value, dict):
            merged[key], nested = merge_release_config(live_value, release_value, f"{path}.")
            changed.extend(nested)
        elif isinstance(release_value, list) and isinstance(live_value, list):
            missing = [item for item in release_value if item not in live_value]
            if missing:
                merged[key] = live_value + missing
                changed.append(path)
        elif key not in live or live_value != release_value:
            merged[key] = release_value
            changed.append(path)
    return merged, changed


def reconcile_profile_config(
    source: Path,
    destination: Path,
    backup_root: Path,
    *,
    check: bool,
) -> None:
    """Bring a preserved profile config.yaml up to the release's sections."""
    live = load_yaml_mapping(destination)
    merged, changed = merge_release_config(live, load_yaml_mapping(source))
    if not changed:
        return
    if check:
        fail(
            f"Installed profile config is missing release settings: {destination} "
            f"({', '.join(changed)}); rerun install_runtime.py without --check"
        )
    backup_file(destination, backup_root / destination.name)
    write_yaml_mapping(destination, merged)
    print(f"Merged release settings into {destination}: {', '.join(changed)}")


def enabled_plugins(config: dict) -> set[str]:
    plugins = config.get("plugins") or {}
    return {str(item) for item in plugins.get("enabled") or []} if isinstance(plugins, dict) else set()


def assert_profile_toolset_config(
    config_path: Path,
    profile_name: str,
    expected_toolsets: set[str],
    all_profile_toolsets: set[str],
    expected_plugins: set[str] = frozenset(),
    all_profile_plugins: set[str] = frozenset(),
) -> None:
    config = load_yaml_mapping(config_path)
    # The platform tools exist in a profile only when its plugin is enabled there.
    enabled = enabled_plugins(config)
    if not expected_plugins <= enabled:
        fail(
            f"Profile {profile_name} must enable plugins: "
            f"{', '.join(sorted(expected_plugins - enabled))}"
        )
    foreign_plugins = (all_profile_plugins - expected_plugins) & enabled
    if foreign_plugins:
        fail(f"Profile {profile_name} enables foreign plugins: {', '.join(sorted(foreign_plugins))}")
    platform_toolsets = config.get("platform_toolsets") or {}
    api_toolsets = (
        set(platform_toolsets.get("api_server") or [])
        if isinstance(platform_toolsets, dict)
        else set()
    )
    if not expected_toolsets.issubset(api_toolsets):
        fail(
            f"Profile {profile_name} api_server is missing toolsets: "
            f"{', '.join(sorted(expected_toolsets - api_toolsets))}"
        )
    forbidden = all_profile_toolsets - expected_toolsets
    leaked = forbidden & api_toolsets
    if leaked:
        fail(f"Profile {profile_name} exposes foreign toolsets: {', '.join(sorted(leaked))}")

    agent = config.get("agent") or {}
    disabled = set(agent.get("disabled_toolsets") or []) if isinstance(agent, dict) else set()
    if not forbidden.issubset(disabled):
        fail(
            f"Profile {profile_name} must disable foreign toolsets: "
            f"{', '.join(sorted(forbidden - disabled))}"
        )


def configure_default_gateway(
    hermes_root: Path,
    all_profile_toolsets: set[str],
    profile_records: list[dict],
    backup_root: Path,
    *,
    check: bool,
) -> None:
    config_path = hermes_root / "config.yaml"
    config = load_yaml_mapping(config_path)
    changed = False

    gateway = config.get("gateway")
    if not isinstance(gateway, dict):
        gateway = {}
        config["gateway"] = gateway
        changed = True
    if gateway.get("multiplex_profiles") is not True:
        gateway["multiplex_profiles"] = True
        changed = True

    top_level_routes = config.get("profile_routes")
    if isinstance(top_level_routes, list):
        profile_routes = top_level_routes
    else:
        nested_routes = gateway.get("profile_routes")
        if not isinstance(nested_routes, list):
            nested_routes = []
            gateway["profile_routes"] = nested_routes
            changed = True
        profile_routes = nested_routes

    route_indexes = {
        str(route.get("name")): index
        for index, route in enumerate(profile_routes)
        if isinstance(route, dict) and route.get("name")
    }
    for profile_record in profile_records:
        for raw_route in profile_record.get("routes") or []:
            if not isinstance(raw_route, dict):
                continue
            route = dict(raw_route)
            route["profile"] = str(profile_record.get("name") or route.get("profile") or "")
            route_name = str(route.get("name") or "")
            if not route_name:
                continue
            existing_index = route_indexes.get(route_name)
            if existing_index is None:
                route_indexes[route_name] = len(profile_routes)
                profile_routes.append(route)
                changed = True
            elif profile_routes[existing_index] != route:
                profile_routes[existing_index] = route
                changed = True

    platform_toolsets = config.get("platform_toolsets")
    if isinstance(platform_toolsets, dict):
        for platform, raw_toolsets in list(platform_toolsets.items()):
            if not isinstance(raw_toolsets, list):
                continue
            filtered = [item for item in raw_toolsets if str(item) not in all_profile_toolsets]
            if filtered != raw_toolsets:
                platform_toolsets[platform] = filtered
                changed = True

    agent = config.get("agent")
    if not isinstance(agent, dict):
        agent = {}
        config["agent"] = agent
        changed = True
    disabled = [str(item) for item in agent.get("disabled_toolsets") or []]
    for toolset in sorted(all_profile_toolsets):
        if toolset not in disabled:
            disabled.append(toolset)
            changed = True
    agent["disabled_toolsets"] = disabled

    # The default profile serves the management API: it must never load a
    # business plugin, which would put platform tools in its registry scope.
    business_plugins = {
        str(item) for record in profile_records for item in record.get("plugins") or []
    }
    plugins = config.get("plugins")
    if isinstance(plugins, dict) and business_plugins & enabled_plugins(config):
        plugins["enabled"] = [
            item for item in plugins.get("enabled") or [] if str(item) not in business_plugins
        ]
        changed = True

    if check and changed:
        fail(
            "Default profile is not migrated: enable gateway.multiplex_profiles, "
            "remove business toolsets and plugins, and disable the toolsets in the default profile"
        )
    if not check and changed:
        if config_path.is_file():
            backup_file(config_path, backup_root / "default-config.yaml")
        write_yaml_mapping(config_path, config)


def install_profile(
    record: dict,
    source: Path,
    hermes_root: Path,
    release: dict,
    all_profile_toolsets: set[str],
    backup_root: Path,
    *,
    check: bool,
    require_env: bool,
    force_profile_config: bool,
) -> dict:
    name = str(record["name"])
    profiles_root = (hermes_root / "profiles").resolve()
    profile_home = (profiles_root / name).resolve()
    if profile_home.parent != profiles_root:
        fail(f"Unsafe profile destination: {profile_home}")

    declared_skills = [str(item) for item in record.get("skills") or []]
    skill_sources = sorted(path for path in (source / "skills").iterdir() if path.is_dir())
    actual_skill_names = [path.name for path in skill_sources]
    if sorted(declared_skills) != actual_skill_names:
        fail(
            f"Profile {name} release Skills differ from bundle: "
            f"declared={sorted(declared_skills)}, actual={actual_skill_names}"
        )

    if not check:
        for directory in (
            "memories",
            "sessions",
            "skills",
            "skins",
            "logs",
            "plans",
            "workspace",
            "cron",
            "home",
            "integration-state",
        ):
            (profile_home / directory).mkdir(parents=True, exist_ok=True)
    elif not profile_home.is_dir():
        fail(f"Profile {name} is not installed: {profile_home}")

    profile_backup = backup_root / "profiles" / name
    install_managed_file(
        source / "distribution.yaml",
        profile_home / "distribution.yaml",
        profile_backup,
        check=check,
    )
    install_managed_file(
        source / "SOUL.md",
        profile_home / "SOUL.md",
        profile_backup,
        check=check,
    )
    install_managed_file(
        source / ".env.template",
        profile_home / ".env.EXAMPLE",
        profile_backup,
        check=check,
    )
    if force_profile_config or not (profile_home / "config.yaml").exists():
        install_managed_file(
            source / "config.yaml",
            profile_home / "config.yaml",
            profile_backup,
            check=check,
        )
    else:
        reconcile_profile_config(
            source / "config.yaml",
            profile_home / "config.yaml",
            profile_backup,
            check=check,
        )

    expected_toolsets = {str(item) for item in record.get("toolsets") or []}
    all_profile_plugins = {
        str(item)
        for profile_record in release.get("profiles") or [record]
        for item in profile_record.get("plugins") or []
    }
    assert_profile_toolset_config(
        profile_home / "config.yaml",
        name,
        expected_toolsets,
        all_profile_toolsets,
        {str(item) for item in record.get("plugins") or []},
        all_profile_plugins,
    )

    skills_root = profile_home / "skills"
    state_path = profile_home / "integration-state" / "platform-profile-fork.json"
    stale_skills = stale_managed_skills(state_path, skills_root, set(actual_skill_names))
    if check and stale_skills:
        fail(
            f"Profile {name} has stale managed Skills: "
            + ", ".join(path.name for path in stale_skills)
        )
    if not check:
        for destination in stale_skills:
            backup_and_remove_skill(destination, profile_backup / "skills")

    installed: list[Path] = []
    for skill_source in skill_sources:
        destination = skills_root / skill_source.name
        if not check:
            destination = install_skill(skill_source, skills_root, profile_backup / "skills")
        verify_installed_skill(skill_source, destination)
        installed.append(destination)

    if require_env:
        required = required_env_names(source)
        configured = read_env_names(profile_home / ".env")
        missing = sorted(required - configured)
        if missing:
            fail(
                f"Profile {name} is missing required .env values: "
                + ", ".join(missing)
            )

    state = {
        "name": release.get("name"),
        "profile": name,
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "releaseTag": release.get("releaseTag"),
        "hermesHome": str(profile_home),
        "skills": [str(path) for path in installed],
    }
    if not check:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return state


def migrate_legacy_default_skills(
    hermes_root: Path,
    backup_root: Path,
    profile_names: list[str],
    *,
    check: bool,
) -> None:
    state_path = hermes_root / "integration-state" / "storyboard-platform-fork.json"
    skills_root = hermes_root / "skills"
    stale = stale_managed_skills(state_path, skills_root, set())
    if check and stale:
        fail(
            "Legacy managed Skills are still installed in the default profile: "
            + ", ".join(path.name for path in stale)
        )
    if check or not state_path.is_file():
        return
    for destination in stale:
        backup_and_remove_skill(destination, backup_root / "default-skills")

    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"Unable to update legacy integration state: {error}")
    state["skills"] = []
    state["migratedAt"] = datetime.now(timezone.utc).isoformat()
    state["migratedToProfiles"] = profile_names
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def assert_profile_api_keys(hermes_root: Path, profile_names: list[str]) -> None:
    """Require strong, distinct API keys for profiles checked together."""
    owners_by_key: dict[str, list[str]] = {}
    for profile_name in profile_names:
        key = read_env_values(
            hermes_root / "profiles" / profile_name / ".env"
        ).get("API_SERVER_KEY", "")
        if len(key) < 16:
            fail(
                f"Profile {profile_name} API_SERVER_KEY must contain at least 16 characters"
            )
        owners_by_key.setdefault(key, []).append(profile_name)

    duplicate_groups = [
        sorted(owners)
        for owners in owners_by_key.values()
        if len(owners) > 1
    ]
    if duplicate_groups:
        fail(
            "Named profiles must use distinct API_SERVER_KEY values: "
            + "; ".join(", ".join(group) for group in duplicate_groups)
        )


def current_commit(fork_root: Path) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={fork_root}", "rev-parse", "HEAD"],
        cwd=fork_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install or verify Storyboard and Scriptmaker Hermes profiles."
    )
    parser.add_argument(
        "--hermes-home",
        type=Path,
        help="Default Hermes root containing profiles/; defaults to HERMES_HOME or ~/.hermes.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Install one named profile; repeat to select several. Defaults to all release profiles.",
    )
    parser.add_argument("--check", action="store_true", help="Verify only; do not write files.")
    parser.add_argument(
        "--require-env",
        action="store_true",
        help="Require every profile's mandatory values in its own .env file.",
    )
    parser.add_argument(
        "--force-profile-config",
        action="store_true",
        help="Replace existing profile config.yaml files with the release versions.",
    )
    parser.add_argument(
        "--migrate-default-skills",
        action="store_true",
        help="Back up and remove Skills managed by the legacy single-profile installer.",
    )
    args = parser.parse_args()

    bundle_root = Path(__file__).resolve().parent
    fork_root = bundle_root.parent.resolve()
    release_path = bundle_root / "release.json"
    if not release_path.is_file():
        fail(f"Fork release manifest is missing: {release_path}")
    release = json.loads(release_path.read_text(encoding="utf-8-sig"))
    if int(release.get("schemaVersion") or 0) < 2:
        fail("Fork release predates profile distributions; prepare a schemaVersion 2 release")

    assert_core_integration(fork_root)
    assert_plugin_integration(fork_root, release)
    verify_release_files(fork_root, release)

    configured_home = args.hermes_home or os.getenv("HERMES_HOME") or (Path.home() / ".hermes")
    hermes_root = Path(configured_home).expanduser().resolve()
    selected_names = {str(name).strip() for name in args.profiles or [] if str(name).strip()}
    profiles = release_profiles(
        fork_root,
        bundle_root,
        release,
        selected_names or None,
    )
    all_profile_toolsets = {
        str(toolset)
        for record in release.get("profiles") or []
        for toolset in record.get("toolsets") or []
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    backup_root = hermes_root / "integration-backups" / f"fork-{timestamp}"
    configure_default_gateway(
        hermes_root,
        all_profile_toolsets,
        list(release.get("profiles") or []),
        backup_root,
        check=args.check,
    )

    states: list[dict] = []
    for record, source in profiles:
        states.append(
            install_profile(
                record,
                source,
                hermes_root,
                release,
                all_profile_toolsets,
                backup_root,
                check=args.check,
                require_env=args.require_env,
                force_profile_config=args.force_profile_config,
            )
        )

    if args.require_env:
        assert_profile_api_keys(
            hermes_root,
            [state["profile"] for state in states],
        )

    if args.migrate_default_skills:
        migrate_legacy_default_skills(
            hermes_root,
            backup_root,
            [state["profile"] for state in states],
            check=args.check,
        )

    print("Hermes platform profile verification passed.")
    print(f"Fork commit: {current_commit(fork_root) or '(not a Git checkout)'}")
    print(f"Hermes root: {hermes_root}")
    print("Profiles: " + ", ".join(state["profile"] for state in states))
    if not args.check:
        print("Restart the Hermes gateway, then use /p/<profile>/... API routes.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
