"""Scriptmaker platform tools for the scriptmaker profile.

Bundled with the integration fork and enabled only in the scriptmaker
profile's ``plugins.enabled``. Hermes keeps one plugin manager and one
tool-registry scope per profile home, so these tools exist in that profile and
in no other: the storyboard and default profiles never import this package.
"""

from __future__ import annotations

import logging

from tools.registry import registry

logger = logging.getLogger(__name__)

TOOLSET = "scriptmaker"


def register(ctx) -> None:
    from . import scriptmaker_agent_tool

    for spec in scriptmaker_agent_tool.TOOLS:
        ctx.register_tool(
            name=spec["name"],
            toolset=TOOLSET,
            schema=spec["schema"],
            handler=spec["handler"],
            emoji=spec["emoji"],
        )
        # Same as storyboard-platform: ctx.register_tool takes no
        # max_result_size_chars, so the tight spill threshold these tools have
        # always run with is set on this profile's registry entry.
        entry = registry.get_entry(spec["name"])
        if entry is not None and entry.handler is spec["handler"]:
            entry.max_result_size_chars = spec["max_result_size_chars"]
        else:
            logger.warning("scriptmaker-platform: result size limit not applied to %s", spec["name"])
