"""ZenMux/Qwen video analysis tool with automatic 50 MB compression."""

from __future__ import annotations

import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from hermes_constants import get_hermes_home
from tools.registry import registry, tool_error, tool_result


_DEFAULT_MODEL = "qwen3.7-plus"
_DEFAULT_BASE_URL = "https://zenmux.ai/api/v1"
_DEFAULT_PROMPT = "请帮我详细分析这个视频分镜里发生了什么，给出场景描述。"
_DEFAULT_COS_DIR = "/canvas-agent-video/"
_TARGET_SIZE_MB = 50
_MAX_TARGET_SIZE_MB = 50


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


def _get_api_key() -> str:
    return (
        _setting("ZENMUX_API_KEY")
        or _setting("ZENMUX_OPENAI_API_KEY")
        or _setting("DASHSCOPE_API_KEY")
        or _setting("OPENAI_API_KEY")
    )


def _file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def _resolve_video_path(raw_path: str) -> Path:
    cleaned = str(raw_path or "").strip().strip('"').strip("'")
    if not cleaned:
        raise ValueError("video_path is required")
    if cleaned.lower().startswith(("http://", "https://")):
        raise ValueError("video_path should be a local file path. Use video_url for remote URLs.")
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")
    return path


def _is_remote_video_url(value: str) -> bool:
    return str(value or "").strip().lower().startswith(("http://", "https://"))


def _safe_segment(value: str, fallback: str = "default") -> str:
    cleaned = (
        str(value or "")
        .strip()
        .replace("\\", "_")
        .replace("/", "_")
    )
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in cleaned)
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:80] or fallback


def _find_cos_upload_script() -> Path:
    configured = _setting("ZENMUX_VIDEO_COS_UPLOAD_SCRIPT") or _setting("COS_UPLOAD_SCRIPT")
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())
    current = Path(__file__).resolve()
    candidates.extend(
        [
            Path.cwd() / "tencent-interface" / "cos_upload.py",
            Path("D:/web-prov/storyboard-web/tencent-interface/cos_upload.py"),
        ]
    )
    for candidate in candidates:
        try:
            path = candidate.resolve()
        except Exception:
            continue
        if path.exists() and path.is_file():
            return path
    raise RuntimeError("cos_upload.py was not found; set ZENMUX_VIDEO_COS_UPLOAD_SCRIPT to enable local video URL conversion")


def _cos_upload_dir(args: Dict[str, Any]) -> str:
    configured = str(args.get("cos_dir") or args.get("cosDir") or _setting("ZENMUX_VIDEO_COS_DIR") or _DEFAULT_COS_DIR).strip()
    if not configured.startswith("/"):
        configured = "/" + configured
    if not configured.endswith("/"):
        configured += "/"
    date_segment = datetime.now().strftime("%Y%m%d")
    return f"{configured}{date_segment}/"


def _upload_video_to_url(video_path: Path, args: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    script_path = _find_cos_upload_script()
    python_executable = _setting("PYTHON_EXECUTABLE") or sys.executable or "python"
    suffix = video_path.suffix.lower() or ".mp4"
    object_name = str(args.get("object_name") or args.get("objectName") or "").strip()
    if not object_name:
        object_name = f"{_safe_segment(video_path.stem, 'video')}_{uuid.uuid4().hex[:10]}{suffix}"
    content_type = mimetypes.guess_type(str(video_path))[0] or "video/mp4"
    cos_dir = _cos_upload_dir(args)
    url_expire = int(args.get("url_expire") or args.get("urlExpire") or _setting("ZENMUX_VIDEO_URL_EXPIRE_SECONDS") or 604800)
    url_expire = max(600, min(url_expire, 604800))

    cmd = [
        python_executable,
        "-X",
        "utf8",
        str(script_path),
        "--file",
        str(video_path),
        "--dir",
        cos_dir,
        "--object-name",
        object_name,
        "--kind",
        "video",
        "--content-type",
        content_type,
        "--url-expire",
        str(url_expire),
    ]
    completed = subprocess.run(
        cmd,
        cwd=str(script_path.parent),
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        check=False,
        capture_output=True,
        text=True,
        timeout=900,
    )
    stdout_text = (completed.stdout or "").strip()
    stderr_text = (completed.stderr or "").strip()
    lines = [line.strip() for line in stdout_text.splitlines() if line.strip()]
    payload: Dict[str, Any] = {}
    if lines:
        try:
            payload = json.loads(lines[-1])
        except Exception:
            payload = {}
    if completed.returncode != 0 or payload.get("success") is False:
        detail = "\n".join(part for part in [stdout_text, stderr_text] if part).strip()
        raise RuntimeError(payload.get("error") or detail[-1000:] or "COS video upload failed")

    url = str(payload.get("url") or payload.get("presigned_url") or payload.get("public_url") or "").strip()
    if not _is_remote_video_url(url):
        raise RuntimeError("COS video upload did not return an http(s) URL")
    return url, {
        "uploadedVideoUrl": url,
        "uploadedVideoPublicUrl": payload.get("public_url", ""),
        "uploadedVideoPresignedUrl": payload.get("presigned_url", ""),
        "uploadedVideoKey": payload.get("key", ""),
        "uploadedVideoBucket": payload.get("bucket", ""),
        "uploadedVideoRegion": payload.get("region", ""),
        "uploadedVideoCosDir": cos_dir,
    }


def _compress_video_crf(
    input_path: Path,
    output_path: Path,
    target_size_mb: int = _TARGET_SIZE_MB,
    timeout_seconds: int = 900,
) -> Tuple[Path, int, float]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg was not found on PATH; install ffmpeg before analyzing videos larger than 50 MB")

    crf = 28
    last_size_mb = 0.0
    last_error = ""
    while crf <= 40:
        cmd = [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(input_path),
            "-c:v",
            "libx264",
            "-crf",
            str(crf),
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        if completed.returncode != 0:
            last_error = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(f"ffmpeg compression failed at CRF={crf}: {last_error[:1000]}")

        last_size_mb = _file_size_mb(output_path)
        if last_size_mb <= target_size_mb:
            return output_path, crf, last_size_mb
        crf += 3

    raise RuntimeError(
        f"Could not compress video under {target_size_mb} MB by CRF=40; "
        f"last output size was {last_size_mb:.2f} MB"
    )


def _prepare_video(path: Path, target_size_mb: int, timeout_seconds: int) -> Tuple[Path, Dict[str, Any]]:
    original_size_mb = _file_size_mb(path)
    info: Dict[str, Any] = {
        "originalPath": str(path),
        "originalSizeMb": round(original_size_mb, 2),
        "compressed": False,
    }
    if original_size_mb <= target_size_mb:
        info["analysisPath"] = str(path)
        info["analysisSizeMb"] = round(original_size_mb, 2)
        return path, info

    temp_dir = Path(tempfile.gettempdir()) / "hermes-zenmux-video"
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / f"{path.stem[:40]}-{uuid.uuid4().hex[:10]}-compressed.mp4"
    compressed_path, crf, compressed_size_mb = _compress_video_crf(
        path,
        output_path,
        target_size_mb=target_size_mb,
        timeout_seconds=timeout_seconds,
    )
    info.update(
        {
            "compressed": True,
            "compressionCrf": crf,
            "analysisPath": str(compressed_path),
            "analysisSizeMb": round(compressed_size_mb, 2),
        }
    )
    return compressed_path, info


def _analyze_video_with_openai(video_url: str, prompt: str, model: str, api_key: str, base_url: str, fps: int) -> str:
    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError(
            "openai SDK is not installed or cannot be imported; install/configure it in the Hermes Python environment"
        ) from exc

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": video_url,
                        },
                        "fps": fps,
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )
    try:
        return str(completion.choices[0].message.content or "").strip()
    except Exception as exc:
        raise RuntimeError("ZenMux video analysis response did not contain message content") from exc


def _handle_zenmux_video_analyze(args: Dict[str, Any], **kwargs) -> str:
    prompt = str(args.get("prompt") or args.get("question") or _DEFAULT_PROMPT).strip() or _DEFAULT_PROMPT
    model = str(args.get("model") or _setting("ZENMUX_VIDEO_MODEL") or _DEFAULT_MODEL).strip() or _DEFAULT_MODEL
    base_url = (
        str(
            args.get("base_url")
            or _setting("ZENMUX_OPENAI_BASE_URL")
            or _setting("ZENMUX_API_BASE_URL")
            or _setting("ZENMUX_BASE_URL")
            or _DEFAULT_BASE_URL
        )
        .strip()
        or _DEFAULT_BASE_URL
    )
    target_size_mb = int(args.get("target_size_mb") or _TARGET_SIZE_MB)
    target_size_mb = max(1, min(target_size_mb, _MAX_TARGET_SIZE_MB))
    timeout_seconds = int(args.get("compression_timeout_seconds") or 900)
    timeout_seconds = max(30, min(timeout_seconds, 3600))
    fps = int(args.get("fps") or 2)
    fps = max(1, min(fps, 10))
    keep_compressed = bool(args.get("keep_compressed"))

    api_key = _get_api_key()
    if not api_key:
        return tool_error(
            "ZENMUX_API_KEY is not configured for Hermes",
            success=False,
            needsConfig=True,
            env="ZENMUX_API_KEY",
        )

    analysis_path: Optional[Path] = None
    metadata: Dict[str, Any] = {}
    try:
        raw_video_url = str(args.get("video_url") or args.get("url") or "").strip()
        if raw_video_url:
            if not _is_remote_video_url(raw_video_url):
                raise ValueError("video_url must be an http(s) URL")
            metadata = {
                "source": "remote_url",
                "analysisUrl": raw_video_url,
                "compressed": False,
            }
            analysis_url = raw_video_url
        else:
            source_path = _resolve_video_path(str(args.get("video_path") or args.get("path") or ""))
            analysis_path, metadata = _prepare_video(source_path, target_size_mb, timeout_seconds)
            analysis_url, upload_metadata = _upload_video_to_url(analysis_path, args)
            metadata.update(upload_metadata)
            metadata["source"] = "local_file_uploaded_url"
            metadata["analysisUrl"] = analysis_url

        text = _analyze_video_with_openai(analysis_url, prompt, model, api_key, base_url, fps)
        return tool_result(
            success=True,
            text=text,
            model=model,
            baseUrl=base_url,
            prompt=prompt,
            fps=fps,
            **metadata,
        )
    except Exception as exc:
        return tool_error(str(exc), success=False)
    finally:
        if analysis_path and metadata.get("compressed") and not keep_compressed:
            try:
                analysis_path.unlink(missing_ok=True)
            except Exception:
                pass


ZENMUX_VIDEO_ANALYZE_SCHEMA = {
    "name": "zenmux_video_analyze",
    "description": (
        "Analyze a local video file or remote video URL through ZenMux OpenAI-compatible "
        "Chat Completions with qwen3.7-plus. If a local file is larger than 50 MB, "
        "compress it with ffmpeg/libx264 CRF, upload it to COS, then send the "
        "resulting http(s) URL as video_url content. "
        "Use this for storyboard video parsing and scene analysis."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "video_path": {
                "type": "string",
                "description": "Local video file path to analyze. Use this for platform-uploaded videos.",
            },
            "video_url": {
                "type": "string",
                "description": "Remote http(s) video URL to analyze. Local files should use video_path.",
            },
            "prompt": {
                "type": "string",
                "description": "Prompt/question for the video analysis.",
            },
            "model": {
                "type": "string",
                "description": "ZenMux/OpenAI-compatible video model. Defaults to qwen3.7-plus.",
            },
            "fps": {
                "type": "integer",
                "description": "Video sampling fps for the model. Defaults to 2.",
            },
            "target_size_mb": {
                "type": "integer",
                "description": "Compression target in MB. Capped at 50. Defaults to 50.",
            },
            "cos_dir": {
                "type": "string",
                "description": "Optional COS upload directory for local videos. Defaults to /canvas-agent-video/<date>/.",
            },
            "url_expire": {
                "type": "integer",
                "description": "Presigned video URL expiry in seconds. Defaults to 604800.",
            },
            "keep_compressed": {
                "type": "boolean",
                "description": "Keep the temporary compressed mp4 for debugging. Defaults to false.",
            },
        },
        "required": ["prompt"],
    },
}


registry.register(
    name="zenmux_video_analyze",
    toolset="storyboard",
    schema=ZENMUX_VIDEO_ANALYZE_SCHEMA,
    handler=_handle_zenmux_video_analyze,
    emoji="VID",
    max_result_size_chars=24000,
)
