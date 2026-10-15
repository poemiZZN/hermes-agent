"""Storyboard platform tools for the storyboard profile.

Bundled with the integration fork and enabled only in the storyboard profile's
``plugins.enabled``. Hermes keeps one plugin manager and one tool-registry
scope per profile home, so these tools exist in that profile and in no other:
the scriptmaker and default profiles never import this package.
"""

from __future__ import annotations

import logging

from tools.registry import registry

logger = logging.getLogger(__name__)

TOOLSET = "storyboard"


def register(ctx) -> None:
    from . import storyboard_api_tool, zenmux_video_analyze_tool

    for spec in (*storyboard_api_tool.TOOLS, *zenmux_video_analyze_tool.TOOLS):
        ctx.register_tool(
            name=spec["name"],
            toolset=TOOLSET,
            schema=spec["schema"],
            handler=spec["handler"],
            emoji=spec["emoji"],
        )
        # ctx.register_tool takes no max_result_size_chars, and the 100k
        # default would put whole platform payloads into the conversation;
        # these tools have always run with a tight spill threshold. get_entry
        # resolves the active profile's scope, the one the plugin manager just
        # registered the tool under; the handler check keeps a foreign entry
        # untouched.
        entry = registry.get_entry(spec["name"])
        if entry is not None and entry.handler is spec["handler"]:
            entry.max_result_size_chars = spec["max_result_size_chars"]
        else:
            logger.warning("storyboard-platform: result size limit not applied to %s", spec["name"])
