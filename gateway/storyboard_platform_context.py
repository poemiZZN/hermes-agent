"""Per-request Storyboard/Scriptmaker platform context for the API server.

Each platform calls its own profile-scoped API server (``/p/storyboard/...``,
``/p/scriptmaker/...``) and sends per-user context as request headers:

====================================  ===========  ===========================
Header                                Profile      Field
====================================  ===========  ===========================
X-Hermes-Session-User-Id              both         user_id
X-Hermes-Session-User-Name            both         user_name
X-Platform-Token                      both         storyboard_platform_token
X-Hermes-Storyboard-Script-Name-B64   storyboard   storyboard_script_name
X-Hermes-Storyboard-Cos-Path-B64      storyboard   storyboard_cos_path
X-Hermes-Platform-Turn-Ticket         scriptmaker  platform_turn_ticket
X-Hermes-Platform-Api-Base            scriptmaker  platform_api_base
X-Hermes-Platform-Model-Key           scriptmaker  platform_model_key
====================================  ===========  ===========================

The API server's profile middleware parses them once per request
(:func:`parse_platform_headers`) and binds the result for the request; the
server re-binds the same snapshot inside its executor threads, which
ContextVars do not follow.

None of these values goes into ``gateway.session_context._VAR_MAP``. Entries
there fall back to ``os.environ`` and are copied into every terminal and code
execution subprocess, which for a platform token, turn ticket or model key
would hand the caller's credential to any command the agent runs. Only the
user id and name, which are not secrets, also travel as the ordinary
``HERMES_SESSION_USER_*`` session variables.
"""

from __future__ import annotations

import base64
import re
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Iterator, Mapping, Optional

STORYBOARD_PROFILE = "storyboard"
SCRIPTMAKER_PROFILE = "scriptmaker"

# Control characters would let a value forge a header on any echo path.
_CONTROL_CHARS = re.compile(r"[\r\n\x00]")
# Same cap as the API server's other session headers.
_MAX_SESSION_HEADER_LEN = 256


@dataclass(frozen=True)
class PlatformContext:
    """One request's platform context. Credentials stay out of ``repr``."""

    user_id: str = ""
    user_name: str = ""
    storyboard_platform_token: str = field(default="", repr=False)
    storyboard_script_name: str = ""
    storyboard_cos_path: str = ""
    platform_turn_ticket: str = field(default="", repr=False)
    platform_api_base: str = ""
    platform_model_key: str = field(default="", repr=False)


EMPTY_PLATFORM_CONTEXT = PlatformContext()


class PlatformContextError(ValueError):
    """A platform header the API server rejects with HTTP 400.

    ``code`` selects the response envelope: with a code, the OpenAI error
    envelope carrying it; without one, the bare ``{message, type}`` envelope.
    """

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def _decode_b64(encoded: str, limit: int, message: str) -> str:
    if not encoded:
        return ""
    try:
        value = base64.b64decode(encoded, validate=True).decode("utf-8").strip()
    except (ValueError, UnicodeDecodeError):
        raise PlatformContextError(message, "invalid_session_context") from None
    if len(value) > limit or _CONTROL_CHARS.search(value):
        raise PlatformContextError(message, "invalid_session_context")
    return value


def parse_platform_headers(headers: Mapping[str, str], profile: Optional[str]) -> PlatformContext:
    """Validate one request's platform headers for the profile it was routed to.

    A product's private headers sent to the other product's profile are
    rejected rather than ignored, so a misrouted integration finds out at once
    instead of acting — or billing — under the wrong profile.
    """

    def header(name: str) -> str:
        return str(headers.get(name, "") or "").strip()

    model_key = header("X-Hermes-Platform-Model-Key")
    if model_key:
        # Profile-scoped like the turn ticket: a credential meant for one
        # platform must not be accepted, let alone spent, by another.
        if profile != SCRIPTMAKER_PROFILE:
            raise PlatformContextError(
                "Scriptmaker context is not valid for this profile", "profile_context_mismatch")
        if _CONTROL_CHARS.search(model_key):
            raise PlatformContextError("Invalid platform model key")
        if len(model_key) > _MAX_SESSION_HEADER_LEN:
            raise PlatformContextError("Platform model key too long")

    user_id = header("X-Hermes-Session-User-Id")
    user_name = header("X-Hermes-Session-User-Name")
    platform_token = header("X-Platform-Token")
    encoded_script_name = header("X-Hermes-Storyboard-Script-Name-B64")
    encoded_cos_path = header("X-Hermes-Storyboard-Cos-Path-B64")
    turn_ticket = header("X-Hermes-Platform-Turn-Ticket")
    api_base = header("X-Hermes-Platform-Api-Base")

    for label, value, limit in (
        ("session user ID", user_id, _MAX_SESSION_HEADER_LEN),
        ("session user name", user_name, _MAX_SESSION_HEADER_LEN),
        ("platform token", platform_token, 8192),
        ("encoded script name", encoded_script_name, 4096),
        ("encoded COS path", encoded_cos_path, 4096),
        ("platform turn ticket", turn_ticket, 256),
        ("platform API base", api_base, 512),
    ):
        if len(value) > limit or _CONTROL_CHARS.search(value):
            raise PlatformContextError(f"Invalid {label}", "invalid_session_context")

    if profile == STORYBOARD_PROFILE and (turn_ticket or api_base):
        raise PlatformContextError(
            "Scriptmaker context is not valid for storyboard profile", "profile_context_mismatch")
    if profile == SCRIPTMAKER_PROFILE and (encoded_script_name or encoded_cos_path):
        raise PlatformContextError(
            "Storyboard context is not valid for scriptmaker profile", "profile_context_mismatch")

    return PlatformContext(
        user_id=user_id,
        user_name=user_name,
        storyboard_platform_token=platform_token,
        storyboard_script_name=_decode_b64(encoded_script_name, 512, "Invalid storyboard script name"),
        storyboard_cos_path=_decode_b64(encoded_cos_path, 2048, "Invalid storyboard COS path"),
        platform_turn_ticket=turn_ticket,
        platform_api_base=api_base,
        platform_model_key=model_key,
    )


_PLATFORM_CONTEXT: ContextVar[PlatformContext] = ContextVar(
    "storyboard_platform_context", default=EMPTY_PLATFORM_CONTEXT)


def current_platform_context() -> PlatformContext:
    """The platform context bound for this request or run; empty when none was sent."""
    return _PLATFORM_CONTEXT.get()


def current_platform_model_key() -> str:
    """The caller's own upstream model key for this request, or "" when none was sent."""
    return _PLATFORM_CONTEXT.get().platform_model_key


def bind_platform_context(context: Optional[PlatformContext]) -> Token:
    """Bind *context*; pair with :func:`reset_platform_context` in a ``finally``."""
    return _PLATFORM_CONTEXT.set(context or EMPTY_PLATFORM_CONTEXT)


def reset_platform_context(token: Token) -> None:
    _PLATFORM_CONTEXT.reset(token)


@contextmanager
def bound_platform_context(context: Optional[PlatformContext]) -> Iterator[None]:
    """Bind *context* for one block.

    Executor threads are pooled: a context left bound would make the next turn
    that reuses the thread act, and pay, as this caller.
    """
    token = bind_platform_context(context)
    try:
        yield
    finally:
        reset_platform_context(token)


def _profile_model_key_env() -> str:
    """The env var the active profile's ``model.api_key`` placeholder names.

    Read from the profile's own config rather than hard-coded, so changing
    provider or renaming the key needs no change here. A literal ``api_key``
    (no ``${VAR}`` placeholder) has nothing to override and yields "".
    """
    try:
        from hermes_cli.config import read_raw_config_readonly

        model = read_raw_config_readonly().get("model")
        api_key = model.get("api_key") if isinstance(model, dict) else ""
        text = str(api_key or "").strip()
    except Exception:
        return ""
    if text.startswith("${") and text.endswith("}"):
        return text[2:-1].strip()
    return ""


def overlay_platform_model_key(secrets: Mapping[str, str]) -> Mapping[str, str]:
    """*secrets* with the caller's model key in place of the profile's own.

    Called by ``gateway.run._profile_runtime_scope`` inside the profile's
    HERMES_HOME override. The key replaces the variable the profile's
    ``model.api_key`` placeholder names, so whatever resolves the model
    credential through the scope during the turn, auxiliary calls included,
    meters the caller rather than the profile's shared account. Always a copy:
    the profile scope must never carry one caller's key into another turn.
    """
    key = current_platform_model_key()
    if not key:
        return secrets
    env_name = _profile_model_key_env()
    if not env_name:
        return secrets
    return {**secrets, env_name: key}
