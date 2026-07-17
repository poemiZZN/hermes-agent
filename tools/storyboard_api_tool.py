"""Storyboard platform API tool with session-scoped internal auth."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextvars import copy_context
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from hermes_constants import get_hermes_home
from tools.registry import registry, tool_error, tool_result


_ENDPOINT_RE = re.compile(r"^/api/[A-Za-z0-9_./:-]+$")
_BLOCKED_ENDPOINT_PREFIXES = ("/api/auth", "/api/admin", "/api/hermes/auth")
_DEFAULT_TIMEOUT_SECONDS = 120
_MAX_CANVAS_IMAGE_PROMPTS = 10
_CANVAS_IMAGE_EXTENSION_RE = re.compile(r"\.(?:png|jpe?g|webp|gif|bmp)$", re.IGNORECASE)
_CANVAS_IMAGE_VERSION_RE = re.compile(r"^(?P<stem>.+)_v(?P<version>[1-9]\d*)$", re.IGNORECASE)


class TokenUnavailable(RuntimeError):
    pass


class SilentTokenUnavailable(RuntimeError):
    pass


def _canvas_image_keyword(prompt: str, index: int) -> str:
    cleaned = re.sub(r"[\s\\/:*?\"<>|,，。.!！?？;；:：、()（）\[\]{}]+", "", prompt)
    cleaned = re.sub(r"^(?:请帮我|帮我|请)", "", cleaned)
    cleaned = re.sub(r"^(?:生成|创建|制作|画)", "", cleaned)
    cleaned = re.sub(r"^(?:一张|一个|一幅)", "", cleaned)
    cleaned = re.sub(r"(?:图片|图像|照片)$", "", cleaned)
    return cleaned[:16] or f"image{index + 1}"


def _normalize_canvas_image_file_names(raw_names: Any, prompts: list[str]) -> list[str]:
    if isinstance(raw_names, list):
        candidates = [str(item or "").strip() for item in raw_names]
        if candidates and len(candidates) != len(prompts):
            raise ValueError("file_names must contain exactly one item for every prompt")
    elif isinstance(raw_names, str) and raw_names.strip():
        candidates = [raw_names.strip()]
        if len(prompts) != 1:
            raise ValueError("file_names must be an array with one item for every prompt")
    else:
        candidates = []

    used: set[str] = set()
    normalized_names: list[str] = []
    for index, prompt in enumerate(prompts):
        raw_name = candidates[index] if index < len(candidates) else ""
        raw_name = raw_name.replace("\\", "/").split("/")[-1]
        raw_name = _CANVAS_IMAGE_EXTENSION_RE.sub("", raw_name).strip()
        safe_name = re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", "_", raw_name)
        safe_name = re.sub(r"\s+", "_", safe_name)
        safe_name = re.sub(r"_+", "_", safe_name).strip("._-")
        if not safe_name:
            safe_name = f"img_{_canvas_image_keyword(prompt, index)}_v1"
        elif not safe_name.lower().startswith("img_"):
            safe_name = f"img_{safe_name}"
        if not _CANVAS_IMAGE_VERSION_RE.match(safe_name):
            safe_name = f"{safe_name}_v1"

        match = _CANVAS_IMAGE_VERSION_RE.match(safe_name)
        stem = (match.group("stem") if match else safe_name)[:72].rstrip("._-")
        version = int(match.group("version")) if match else 1
        unique_name = f"{stem}_v{version}"
        while unique_name.casefold() in used:
            version += 1
            unique_name = f"{stem}_v{version}"
        used.add(unique_name.casefold())
        normalized_names.append(unique_name)
    return normalized_names


def _canvas_image_cos_directory(script_name: str, provider: str, provider_subject: str) -> str:
    session_cos_path = _get_session_value("HERMES_STORYBOARD_COS_PATH", "").strip()
    if session_cos_path:
        parts = [
            part.strip()
            for part in session_cos_path.replace("\\", "/").split("/")
            if part.strip() and part.strip() not in {".", ".."}
        ]
        if parts:
            return f"/{'/'.join(parts)}/"

    def safe_segment(value: str, fallback: str) -> str:
        segment = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._-")
        return segment[:80] or fallback

    script_segment = safe_segment(script_name, "default_script")
    identity_segment = safe_segment(
        f"{provider}_{provider_subject}" if provider_subject else provider,
        "default_user",
    )
    return f"/canvas/{script_segment}/{identity_segment}/"


def _get_session_value(name: str, default: str = "") -> str:
    try:
        from gateway.session_context import get_session_env

        return get_session_env(name, default) or default
    except Exception:
        return os.getenv(name, default)


def _current_identity() -> Tuple[str, str]:
    provider = _get_session_value("HERMES_SESSION_PLATFORM", "").strip()
    provider_subject = _get_session_value("HERMES_SESSION_USER_ID", "").strip()
    if not provider_subject:
        session_key = _get_session_value("HERMES_SESSION_KEY", "").strip()
        match = re.search(r"(?:^|:)user:(\d+)(?:$|:)", session_key)
        if match and (not provider or provider == "api_server"):
            provider = provider or "api_server"
            provider_subject = match.group(1)
    return provider, provider_subject


def _is_platform_embedded_identity(provider: str | None = None) -> bool:
    current_provider = (provider if provider is not None else _current_identity()[0]).strip().lower()
    return current_provider == "api_server"


def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    env_path = get_hermes_home() / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, raw = stripped.split("=", 1)
            if key.strip() != name:
                continue
            value = raw.strip().strip('"').strip("'")
            if value:
                return value
    except Exception:
        pass
    return default


def _configured_api_base(default: str = "http://localhost:3004") -> str:
    return (
        _setting("STORYBOARD_API_BASE")
        or _setting("PUBLIC_BASE_URL")
        or _setting("HERMES_STORYBOARD_API_BASE")
        or default
    ).rstrip("/")


def _safe_segment(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(value or ""))[:120]
    return safe or "unknown"


def _cache_path(provider: str, provider_subject: str) -> Path:
    root = _setting("HERMES_STORYBOARD_TOKEN_CACHE_DIR")
    base = Path(root) if root else get_hermes_home() / "cache" / "storyboard-platform-tokens"
    return base / _safe_segment(provider) / f"{_safe_segment(provider_subject)}.json"


def _load_token() -> Tuple[str, str]:
    provider, provider_subject = _current_identity()
    if not provider or not provider_subject:
        raise TokenUnavailable("Missing Hermes session identity for storyboard_api")

    session_token = _get_session_value("HERMES_STORYBOARD_PLATFORM_TOKEN", "").strip()
    if session_token and _is_platform_embedded_identity(provider):
        return session_token, _configured_api_base()

    path = _cache_path(provider, provider_subject)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TokenUnavailable("Storyboard platform token is not available for this session") from exc
    except Exception as exc:
        raise TokenUnavailable("Storyboard platform token cache is unreadable") from exc

    if str(payload.get("provider") or "") != provider:
        raise TokenUnavailable("Storyboard platform token cache provider mismatch")
    if str(payload.get("providerSubject") or "") != provider_subject:
        raise TokenUnavailable("Storyboard platform token cache subject mismatch")

    token = str(payload.get("accessToken") or "").strip()
    if not token:
        raise TokenUnavailable("Storyboard platform token cache has no access token")

    expires_at = str(payload.get("expiresAt") or "").strip()
    if expires_at:
        try:
            expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)
            if expires_dt <= datetime.now(timezone.utc):
                raise TokenUnavailable("Storyboard platform token is expired for this session")
        except TokenUnavailable:
            raise
        except Exception:
            pass

    return token, str(payload.get("apiBase") or _configured_api_base()).strip().rstrip("/")


def _write_token_cache(payload: Dict[str, Any], api_base: str) -> Tuple[str, str]:
    provider, provider_subject = _current_identity()
    token = str(payload.get("accessToken") or "").strip()
    if not provider or not provider_subject:
        raise SilentTokenUnavailable("Missing Hermes session identity for token cache")
    if not token:
        raise SilentTokenUnavailable("Silent token response has no access token")
    cache_payload = {
        "provider": provider,
        "providerSubject": provider_subject,
        "accessToken": token,
        "refreshToken": str(payload.get("refreshToken") or ""),
        "expiresAt": str(payload.get("expiresAt") or ""),
        "refreshExpiresAt": str(payload.get("refreshExpiresAt") or ""),
        "apiBase": api_base.rstrip("/"),
        "source": "storyboard-api-tool-silent-issue",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    path = _cache_path(provider, provider_subject)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return token, api_base.rstrip("/")


def _validate_endpoint(endpoint: str) -> str:
    endpoint = str(endpoint or "").strip()
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    if not _ENDPOINT_RE.match(endpoint):
        raise ValueError("endpoint must be a safe /api/... path")
    if any(endpoint.startswith(prefix) for prefix in _BLOCKED_ENDPOINT_PREFIXES):
        raise ValueError("endpoint is not allowed for storyboard_api")
    return endpoint


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value if value is not None else {}, ensure_ascii=False).encode("utf-8")


def _build_url(api_base: str, endpoint: str, query: Dict[str, Any] | None) -> str:
    url = f"{api_base.rstrip('/')}{endpoint}"
    if query:
        params = {str(k): str(v) for k, v in query.items() if v is not None and isinstance(k, str)}
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
    return url


def _post_json(api_base: str, endpoint: str, body: Dict[str, Any], headers: Dict[str, str], timeout: int) -> Tuple[int, Any]:
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}{endpoint}",
        data=_json_bytes(body),
        headers={**headers, "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        context = ssl.create_default_context()
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read()
            status = int(response.status)
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = int(exc.code)
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
    text = raw.decode("utf-8", errors="replace")
    if "json" in content_type.lower() or text.strip().startswith(("{", "[")):
        try:
            return status, json.loads(text)
        except Exception:
            pass
    return status, text


def _basic_auth_header() -> Dict[str, str]:
    client_id = _setting("HERMES_AGENT_CLIENT_ID")
    client_secret = _setting("HERMES_AGENT_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SilentTokenUnavailable("Hermes agent client credentials are not configured")
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {basic}"}


def _issue_token_for_bound_identity(api_base: str | None = None, timeout: int = _DEFAULT_TIMEOUT_SECONDS) -> Tuple[str, str]:
    provider, provider_subject = _current_identity()
    if not provider or not provider_subject:
        raise SilentTokenUnavailable("Missing Hermes session identity for silent token issuance")
    if _is_platform_embedded_identity(provider):
        raise SilentTokenUnavailable("Platform API server sessions must use the platform-injected token")
    base = (api_base or _configured_api_base()).rstrip("/")
    status, data = _post_json(
        base,
        "/api/hermes/auth/token",
        {"grant_type": "external_identity", "provider": provider, "providerSubject": provider_subject, "scopes": ["platform:api"]},
        _basic_auth_header(),
        timeout,
    )
    if 200 <= status < 300 and isinstance(data, dict) and data.get("accessToken"):
        return _write_token_cache(data, base)
    error = data.get("error") or data.get("message") if isinstance(data, dict) else str(data)
    raise SilentTokenUnavailable(error or f"Silent token issuance failed: HTTP {status}")


def _platform_session_token_unavailable(reason: str) -> str:
    return tool_error(
        "Platform session token is unavailable for storyboard_api. Retry from the logged-in platform page; if it persists, check storyboard web token injection.",
        success=False,
        status="platform_session_token_unavailable",
        needsLogin=False,
        retryable=True,
        reason=reason,
    )


def _login_link_result(reason: str, api_base: str | None = None, timeout: int = _DEFAULT_TIMEOUT_SECONDS) -> str:
    provider, provider_subject = _current_identity()
    if _is_platform_embedded_identity(provider):
        return _platform_session_token_unavailable(reason)
    if not provider or not provider_subject:
        return tool_error("Current Hermes session identity is missing, so a storyboard login link cannot be created.", success=False, needsLogin=True)
    try:
        basic_header = _basic_auth_header()
    except SilentTokenUnavailable:
        return tool_error("Storyboard login link cannot be created because Hermes agent client credentials are not configured.", success=False, needsLogin=True)
    base = (api_base or _configured_api_base()).rstrip("/")
    status, data = _post_json(
        base,
        "/api/hermes/auth/link",
        {"provider": provider, "providerSubject": provider_subject, "scopes": ["platform:api"]},
        basic_header,
        timeout,
    )
    if 200 <= status < 300 and isinstance(data, dict) and data.get("loginUrl"):
        return tool_result(
            success=True,
            status="login_required",
            needsLogin=True,
            loginUrl=data.get("loginUrl"),
            message="授权链接已创建。请让用户打开链接登录并确认授权，完成后再继续原任务。",
            reason=reason,
        )
    error = data.get("error") or data.get("message") if isinstance(data, dict) else str(data)
    return tool_error(f"Storyboard login link creation failed: {error or f'HTTP {status}'}", success=False, needsLogin=True)


def _encode_multipart(form: Dict[str, Any], file_field: str, file_path: str) -> Tuple[bytes, str]:
    boundary = f"----hermes-storyboard-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    def add_text(name: str, value: Any) -> None:
        chunks.append(f"--{boundary}\r\n".encode("ascii"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value if value is not None else "").encode("utf-8"))
        chunks.append(b"\r\n")

    for key, value in (form or {}).items():
        if isinstance(key, str):
            add_text(key, value)

    if file_path:
        path = Path(file_path).expanduser()
        if not path.is_file():
            raise ValueError("file_path does not exist or is not a file")
        name = file_field or "file"
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("ascii"))
        chunks.append((f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\nContent-Type: {content_type}\r\n\r\n').encode("utf-8"))
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("ascii"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _open_platform_request(url: str, data: bytes | None, headers: Dict[str, str], method: str, timeout: int) -> Tuple[int, str, str]:
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        context = ssl.create_default_context()
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read()
            status = int(response.status)
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = int(exc.code)
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
    return status, content_type, raw.decode("utf-8", errors="replace")


def _parse_response_text(text: str, content_type: str) -> Any:
    if "json" in content_type.lower() or text.strip().startswith(("{", "[")):
        try:
            return json.loads(text)
        except Exception:
            return text
    return text


def _request_json(args: Dict[str, Any], **kwargs) -> str:
    endpoint = _validate_endpoint(args.get("endpoint", ""))
    method = str(args.get("method") or ("GET" if endpoint in {"/api/workspaces", "/api/scripts"} else "POST")).upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return tool_error("method must be GET, POST, PUT, PATCH, or DELETE")
    timeout = max(1, min(int(args.get("timeout_seconds") or _DEFAULT_TIMEOUT_SECONDS), 300))

    try:
        token, api_base = _load_token()
    except TokenUnavailable as exc:
        try:
            token, api_base = _issue_token_for_bound_identity(timeout=timeout)
        except SilentTokenUnavailable as silent_exc:
            return _login_link_result(f"{exc}; silent token issuance failed: {silent_exc}", timeout=timeout)

    query = args.get("query") if isinstance(args.get("query"), dict) else None
    url = _build_url(api_base, endpoint, query)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    data = None
    if args.get("multipart"):
        body, content_type = _encode_multipart(
            form=args.get("form") if isinstance(args.get("form"), dict) else {},
            file_field=str(args.get("file_field") or "file"),
            file_path=str(args.get("file_path") or ""),
        )
        headers["Content-Type"] = content_type
        data = body
    elif method != "GET":
        headers["Content-Type"] = "application/json"
        data = _json_bytes(args.get("body") if isinstance(args.get("body"), dict) else {})

    try:
        status, content_type, text = _open_platform_request(url, data, headers, method, timeout)
    except Exception as exc:
        return tool_error(str(exc), success=False)

    if status == 401:
        try:
            token, api_base = _issue_token_for_bound_identity(api_base=api_base, timeout=timeout)
            url = _build_url(api_base, endpoint, query)
            headers["Authorization"] = f"Bearer {token}"
            status, content_type, text = _open_platform_request(url, data, headers, method, timeout)
        except SilentTokenUnavailable as silent_exc:
            return _login_link_result(f"Storyboard platform returned HTTP {status}; silent token issuance failed: {silent_exc}", api_base=api_base, timeout=timeout)
        except Exception as exc:
            return tool_error(str(exc), success=False)

    parsed = _parse_response_text(text, content_type)
    result = {"success": 200 <= status < 300, "status": status, "endpoint": endpoint, "data": parsed}
    if status == 401:
        return _login_link_result(f"Storyboard platform returned HTTP {status}", api_base=api_base, timeout=timeout)
    if not result["success"] and isinstance(parsed, dict):
        result["error"] = parsed.get("error") or parsed.get("message") or f"HTTP {status}"
    elif not result["success"]:
        result["error"] = f"HTTP {status}"
    return tool_result(result)


STORYBOARD_API_SCHEMA = {
    "name": "storyboard_api",
    "description": "Call storyboard platform API endpoints using internal session auth. Do not pass or ask for tokens.",
    "parameters": {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string", "description": "Safe platform endpoint path, e.g. /api/storyboard/text."},
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
            "body": {"type": "object", "description": "JSON request body."},
            "query": {"type": "object", "description": "Optional query parameters."},
            "multipart": {"type": "boolean", "description": "Use multipart/form-data."},
            "form": {"type": "object", "description": "Multipart text fields."},
            "file_field": {"type": "string", "description": "Multipart file field name."},
            "file_path": {"type": "string", "description": "Local file path for upload."},
            "timeout_seconds": {"type": "integer", "description": "Request timeout from 1 to 300 seconds."},
        },
        "required": ["endpoint"],
    },
}


def _canvas_image_generate(args: Dict[str, Any], **kwargs) -> str:
    provider, provider_subject = _current_identity()
    session_script_name = _get_session_value("HERMES_STORYBOARD_SCRIPT_NAME", "").strip()
    requested_script_name = str(args.get("scriptName") or args.get("script_name") or "").strip()
    if _is_platform_embedded_identity(provider):
        if not session_script_name:
            return tool_error("Current platform scriptName is unavailable for this session", success=False)
        script_name = session_script_name
    else:
        script_name = requested_script_name
    raw_prompts = args.get("prompt")
    if isinstance(raw_prompts, list):
        prompts = [str(item or "").strip() for item in raw_prompts]
        prompts = [item for item in prompts if item]
    else:
        legacy_prompt = str(raw_prompts or "").strip()
        prompts = [legacy_prompt] if legacy_prompt else []
    if not script_name:
        return tool_error("scriptName is required", success=False)
    if not prompts:
        return tool_error("prompt must contain at least one non-empty string", success=False)
    if len(prompts) > _MAX_CANVAS_IMAGE_PROMPTS:
        return tool_error(
            f"prompt supports at most {_MAX_CANVAS_IMAGE_PROMPTS} items",
            success=False,
        )

    try:
        file_names = _normalize_canvas_image_file_names(args.get("file_names"), prompts)
    except ValueError as exc:
        return tool_error(str(exc), success=False)
    cos_directory = _canvas_image_cos_directory(script_name, provider, provider_subject)

    reference_images = args.get("reference_images")
    if not isinstance(reference_images, list):
        reference_images = []

    timeout = max(1, min(int(args.get("timeout_seconds") or _DEFAULT_TIMEOUT_SECONDS), 300))
    try:
        _load_token()
    except TokenUnavailable as exc:
        try:
            _issue_token_for_bound_identity(timeout=timeout)
        except SilentTokenUnavailable as silent_exc:
            return _login_link_result(
                f"{exc}; silent token issuance failed: {silent_exc}",
                timeout=timeout,
            )

    common_body = {
        "scriptName": script_name,
        "model": str(args.get("model") or "gpt-2").strip() or "gpt-2",
        "ratio": str(args.get("ratio") or "3:4").strip() or "3:4",
        "resolution": str(args.get("resolution") or "1K").strip() or "1K",
        "quality": "high",
        "output_format": "png",
        "n": 1,
        "reference_images": reference_images,
    }

    def submit_prompt(index: int, prompt: str) -> Dict[str, Any]:
        file_name = file_names[index]
        raw_result = _request_json(
            {
                "endpoint": "/api/canvas/generate",
                "method": "POST",
                "timeout_seconds": timeout,
                "body": {
                    **common_body,
                    "prompt": prompt,
                    "cos_path": f"{cos_directory}{file_name}.png",
                },
            }
        )
        try:
            parsed = json.loads(raw_result)
        except Exception:
            parsed = {"success": False, "error": str(raw_result or "Invalid tool result")}
        if not isinstance(parsed, dict):
            parsed = {"success": False, "data": parsed}
        return {"index": index, "prompt": prompt, "file_name": file_name, **parsed}

    results: list[Dict[str, Any] | None] = [None] * len(prompts)
    with ThreadPoolExecutor(max_workers=len(prompts), thread_name_prefix="canvas-image") as executor:
        futures = {
            executor.submit(copy_context().run, submit_prompt, index, prompt): index
            for index, prompt in enumerate(prompts)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                results[index] = {
                    "index": index,
                    "prompt": prompts[index],
                    "file_name": file_names[index],
                    "success": False,
                    "error": str(exc),
                }

    completed_results = [item for item in results if item is not None]
    success_count = sum(
        1 for item in completed_results
        if item.get("success") and not item.get("needsLogin")
    )
    failed_count = len(completed_results) - success_count
    batch_result = {
        "success": success_count == len(prompts),
        "status": "submitted" if not failed_count else ("partial" if success_count else "failed"),
        "requested_count": len(prompts),
        "submitted_count": success_count,
        "failed_count": failed_count,
        "results": completed_results,
    }
    login_result = next((item for item in completed_results if item.get("needsLogin")), None)
    if login_result:
        batch_result.update({
            "needsLogin": True,
            "loginUrl": login_result.get("loginUrl"),
            "message": login_result.get("message"),
        })
    return tool_result(batch_result)


CANVAS_IMAGE_GENERATE_SCHEMA = {
    "name": "canvas_image_generate",
    "description": (
        "Generate one or more images through the storyboard platform /api/canvas/generate "
        "endpoint using internal session auth. The model only passes business "
        "parameters. Use this instead of image_generate/FAL for storyboard "
        "platform image generation. quality is fixed to high, output_format "
        "to png, and n to 1 per prompt. Submit one concurrent platform request "
        "for every prompt array item. file_names maps one-to-one to prompt and each "
        "name is normalized to img_{keywords}_v{version}. In API-server embedded sessions, the current "
        "page scriptName is injected by the platform and overrides any "
        "model-provided scriptName. After a successful submission, never "
        "mention task IDs, job IDs, request IDs, or model IDs in the assistant "
        "reply; the platform UI tracks and renders task results separately."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scriptName": {
                "type": "string",
                "description": "Optional script name. API-server embedded sessions use the current page scriptName instead.",
            },
            "prompt": {
                "type": "array",
                "description": "One image generation prompt per requested image. All items are submitted concurrently.",
                "items": {"type": "string", "minLength": 1},
                "minItems": 1,
                "maxItems": _MAX_CANVAS_IMAGE_PROMPTS,
            },
            "file_names": {
                "type": "array",
                "description": (
                    "One unique filename base per prompt, in the same order and with the same item count. "
                    "Extract one or two short keywords from each prompt and use img_{keywords}_v{version}, "
                    "for example img_戴墨镜的猫_v1. Do not include directories or extensions."
                ),
                "items": {"type": "string", "minLength": 1},
                "minItems": 1,
                "maxItems": _MAX_CANVAS_IMAGE_PROMPTS,
            },
            "model": {
                "type": "string",
                "description": "Image model. Defaults to gpt-2.",
            },
            "ratio": {
                "type": "string",
                "description": "Aspect ratio. Defaults to 3:4.",
            },
            "resolution": {
                "type": "string",
                "description": "Image resolution. Defaults to 1K.",
            },
            "reference_images": {
                "type": "array",
                "description": "Optional reference image assets/URLs. Defaults to an empty list.",
                "items": {},
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Request timeout from 1 to 300 seconds.",
            },
        },
        "required": ["prompt", "file_names"],
    },
}


registry.register(
    name="storyboard_api",
    toolset="storyboard",
    schema=STORYBOARD_API_SCHEMA,
    handler=_request_json,
    emoji="SB",
    max_result_size_chars=12000,
)

registry.register(
    name="canvas_image_generate",
    toolset="storyboard",
    schema=CANVAS_IMAGE_GENERATE_SCHEMA,
    handler=_canvas_image_generate,
    emoji="IMG",
    max_result_size_chars=12000,
)
