"""``hermes_cli.stdio._augment_path_with_known_tools`` keeps subprocesses on the running venv.

A canonical install (``%LOCALAPPDATA%\\hermes\\hermes-agent``) and a fork checkout may coexist on
one Windows host. The PATH augmentation must put the RUNNING interpreter's Scripts dir first, so
bare ``python`` / ``pip`` in subprocesses never resolve against the other checkout's venv.
Host-independent: paths are built with ``os.path`` and ``is_windows`` is patched.
"""

from __future__ import annotations

import os


def test_running_venv_precedes_stale_hermes_venv(monkeypatch):
    from hermes_cli import stdio

    own_venv = os.path.join("", "fork", ".venv")
    own_scripts = os.path.join(own_venv, "Scripts")
    stale_scripts = os.path.join("", "stock", "venv", "Scripts")
    system_scripts = os.path.join("", "system", "bin")

    monkeypatch.setattr(stdio, "is_windows", lambda: True)
    monkeypatch.setattr(stdio.sys, "prefix", own_venv)
    monkeypatch.setattr(
        stdio.os.path, "isdir", lambda path: os.path.normpath(path) == os.path.normpath(own_scripts))
    monkeypatch.setenv("LOCALAPPDATA", os.path.join("", "local"))
    monkeypatch.setenv("PATH", os.pathsep.join([stale_scripts, own_scripts, system_scripts]))

    stdio._augment_path_with_known_tools()

    entries = os.environ["PATH"].split(os.pathsep)
    assert entries[0] == os.path.normpath(own_scripts)
    assert entries.count(os.path.normpath(own_scripts)) == 1
    assert entries.index(stale_scripts) > entries.index(own_scripts)


def test_known_tools_still_prepend_without_interpreter_scripts(monkeypatch):
    from hermes_cli import stdio

    local_appdata = os.path.join("", "local")
    git_cmd = os.path.join(local_appdata, "hermes", "git", "cmd")
    system_scripts = os.path.join("", "system", "bin")

    monkeypatch.setattr(stdio, "is_windows", lambda: True)
    monkeypatch.setattr(stdio.sys, "prefix", os.path.join("", "missing"))
    monkeypatch.setattr(
        stdio.os.path, "isdir", lambda path: os.path.normpath(path) == os.path.normpath(git_cmd))
    monkeypatch.setenv("LOCALAPPDATA", local_appdata)
    monkeypatch.setenv("PATH", system_scripts)

    stdio._augment_path_with_known_tools()

    assert os.environ["PATH"].split(os.pathsep) == [git_cmd, system_scripts]


def test_canonical_install_venv_is_not_prepended(monkeypatch):
    from hermes_cli import stdio

    local_appdata = os.path.join("", "local")
    canonical_scripts = os.path.join(local_appdata, "hermes", "hermes-agent", "venv", "Scripts")
    system_scripts = os.path.join("", "system", "bin")

    monkeypatch.setattr(stdio, "is_windows", lambda: True)
    monkeypatch.setattr(stdio.sys, "prefix", os.path.join("", "missing"))
    monkeypatch.setattr(
        stdio.os.path, "isdir",
        lambda path: os.path.normpath(path) == os.path.normpath(canonical_scripts))
    monkeypatch.setenv("LOCALAPPDATA", local_appdata)
    monkeypatch.setenv("PATH", system_scripts)

    stdio._augment_path_with_known_tools()

    assert os.environ["PATH"].split(os.pathsep) == [system_scripts]
