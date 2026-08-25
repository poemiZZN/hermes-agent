"""Scriptmaker platform tools backed by one turn-scoped callback endpoint.

Every tool here is a thin wrapper: the model sees the real per-tool JSON schema,
but execution happens back on the Scriptmaker platform, inside the same
``_execute_tool`` implementation the platform's in-process engines use. That is
deliberate — the confirmation gates that decide whether a paid script-generation
task starts must live on the platform, not in a prompt.

The wrapper carries no identity of its own. The turn ticket and the platform
token both arrive as session context variables bound by the authenticated API
adapter, so concurrent users can never execute against each other's turn.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List

from hermes_constants import get_hermes_home
from tools.registry import registry, tool_error, tool_result


_DEFAULT_TIMEOUT_SECONDS = 180
_MAX_RESULT_CHARS = 12000


def _get_session_value(name: str, default: str = "") -> str:
    """Read a per-request session value bound by the API adapter.

    Session context is task-local, so this is the only safe source for the turn
    ticket and platform token. Never mix it with :func:`_setting`.
    """
    try:
        from gateway.session_context import get_session_env

        return get_session_env(name, default) or default
    except Exception:
        return os.getenv(name, default)


def _setting(name: str, default: str = "") -> str:
    """Read deployment configuration from the process env, then HERMES_HOME/.env."""
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


def _resolve_api_base() -> str:
    """Where the platform callback lives.

    The per-request header wins so one Hermes deployment can serve several
    Scriptmaker environments; the .env value is only a fallback.
    """
    base = _get_session_value("HERMES_PLATFORM_API_BASE").strip()
    if not base:
        base = _setting("SCRIPTMAKER_API_BASE").strip()
    return base.rstrip("/")


def _open_platform_request(
    url: str, data: bytes, headers: Dict[str, str], timeout: int
) -> tuple:
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        context = ssl.create_default_context()
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read()
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = int(exc.code)
    return status, raw.decode("utf-8", errors="replace")


def _parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return text


def _dispatch_platform_tool(tool_name: str, args: Dict[str, Any], call_id: str) -> str:
    ticket = _get_session_value("HERMES_PLATFORM_TURN_TICKET").strip()
    token = _get_session_value("HERMES_STORYBOARD_PLATFORM_TOKEN").strip()
    api_base = _resolve_api_base()
    if not ticket or not api_base or not token:
        # Not a task failure the model should narrate around: the session simply
        # did not come from the Scriptmaker conversation surface.
        return tool_error(
            "平台轮次上下文不可用，请回到剧本平台的对话页面重新发送这条消息。",
            success=False,
            retryable=True,
            status="platform_turn_context_unavailable",
        )

    payload = {"tool": tool_name, "arguments": args if isinstance(args, dict) else {}}
    if call_id:
        payload["action_id"] = call_id
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = f"{api_base}/api/agent/turns/{urllib.parse.quote(ticket, safe='')}/tools"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
    }

    try:
        status, text = _open_platform_request(url, body, headers, _DEFAULT_TIMEOUT_SECONDS)
    except Exception as exc:
        return tool_error(f"剧本平台调用失败：{exc}", success=False, retryable=True)

    parsed = _parse_json(text)
    if status == 404:
        return tool_error(
            "轮次票据已过期，请让用户在剧本平台重新发送这条消息。",
            success=False,
            retryable=True,
            status="turn_ticket_expired",
        )
    if not 200 <= status < 300:
        message = ""
        if isinstance(parsed, dict):
            message = str(parsed.get("message") or parsed.get("error") or "")
        return tool_error(message or f"剧本平台返回 HTTP {status}", success=False)

    # The platform returns the raw _execute_tool dict under "result"; hand it to
    # the model unchanged so ok/error/ui/awaiting_user_input keep their meaning.
    if isinstance(parsed, dict) and isinstance(parsed.get("result"), dict):
        return tool_result(parsed["result"])
    return tool_result(parsed if isinstance(parsed, dict) else {"ok": False, "error": "平台返回了无法解析的结果。"})


def _current_tool_call_id() -> str:
    """Best-effort id for the model's tool call, used for replay protection.

    ``registry.dispatch`` does not forward the tool-call id to handlers, but the
    approval layer binds it to a contextvar for the duration of the call. When
    even that is unavailable the platform derives a deterministic id from the
    ticket and the arguments, so idempotency never depends on this succeeding.
    """
    try:
        from tools.approval import _approval_tool_call_id

        return str(_approval_tool_call_id.get() or "")
    except Exception:
        return ""


def _make_handler(tool_name: str) -> Callable[..., str]:
    """Bind the tool name eagerly so all 13 handlers stay distinct."""

    def handler(args: Dict[str, Any], **kwargs) -> str:
        call_id = str(
            kwargs.get("tool_call_id") or kwargs.get("call_id") or _current_tool_call_id()
        )
        return _dispatch_platform_tool(tool_name, args or {}, call_id)

    handler.__name__ = f"_handle_{tool_name}"
    return handler


# Generated from the platform's TOOL_DEFINITIONS so the parameter contract the
# model sees cannot drift from the contract the platform validates.
_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "ask_choice",
        "description": "只有关键条件无法从用户原话和上下文可靠推断时，向用户展示一个语义化选择卡。一次只问一个问题，不要用它重复询问已知信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "稳定字段名，例如 total_episodes、character_count、execution_scope、target_project"
                },
                "question": {
                    "type": "string",
                    "description": "简短自然的问题"
                },
                "options": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {
                                "type": "string"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "用户选择后作为下一条消息发送的完整语义"
                            },
                            "description": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "label",
                            "prompt"
                        ]
                    }
                },
                "custom_prefix": {
                    "type": "string",
                    "description": "用户自定义答案的可选前缀"
                }
            },
            "required": [
                "field",
                "question",
                "options"
            ]
        }
    },
    {
        "name": "list_projects",
        "description": "列出当前用户最近的专业剧本团队任务。用户问有哪些项目、最近项目时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "返回数量，默认10"
                }
            }
        }
    },
    {
        "name": "select_project",
        "description": "把某个专业剧本团队任务设为当前对话操作对象。",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string"
                }
            },
            "required": [
                "job_id"
            ]
        }
    },
    {
        "name": "get_project_status",
        "description": "查询指定或当前专业剧本团队任务的状态、节点和进度。",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "专业剧本团队任务编号"
                }
            }
        }
    },
    {
        "name": "read_attachment",
        "description": "读取当前会话绑定的剧本文档。支持查看元数据、按字符偏移分块读取和关键词搜索；不会启动专业剧本团队。",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["metadata", "read", "search"],
                    "description": "metadata查看文件信息；read按offset读取；search查找关键词"
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "read的起始字符位置"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 500,
                    "maximum": 8000,
                    "description": "单次最多读取8000字符，默认6000"
                },
                "query": {
                    "type": "string",
                    "description": "search使用的关键词"
                }
            },
            "required": ["operation"]
        }
    },
    {
        "name": "write_attachment_draft",
        "description": "把当前模型直接改编的长篇结果分段保存为草稿并生成DOCX下载，不启动专业剧本团队。短内容应直接回复，不要使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "append", "finish"],
                    "description": "start创建草稿；append追加一段；finish完成并生成下载入口"
                },
                "draft_id": {
                    "type": "string",
                    "description": "append和finish必须传入start返回的draft_id"
                },
                "title": {
                    "type": "string",
                    "description": "start时的改编稿标题"
                },
                "content": {
                    "type": "string",
                    "description": "本次写入的改编正文，可在finish时为空"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "prepare_script_generation",
        "description": "在字段齐全后准备一项专业剧本团队任务，只生成确认卡，不真正启动。",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "剧本标题，可根据需求拟定"
                },
                "user_expectation": {
                    "type": "string",
                    "description": "完整创作要求，包含题材、受众、风格、核心故事与限制"
                },
                "total_episodes": {
                    "type": "integer",
                    "description": "总集数"
                },
                "character_count": {
                    "type": "integer",
                    "description": "主要角色数量"
                },
                "episode_word_count": {
                    "type": "integer",
                    "description": "单集目标字数，默认600"
                },
                "script_format_mode": {
                    "type": "string",
                    "description": "standard或waibao，默认standard"
                },
                "execution_scope": {
                    "type": "string",
                    "enum": [
                        "framework_only",
                        "framework_and_script"
                    ],
                    "description": "用户只要求分析/拆解框架时用framework_only；明确要求生成完整剧本时才用framework_and_script"
                }
            },
            "required": [
                "title",
                "user_expectation",
                "total_episodes",
                "character_count"
            ]
        }
    },
    {
        "name": "confirm_script_generation",
        "description": "用户明确确认后，启动上一项已经准备好的剧本生成任务。",
        "parameters": {
            "type": "object",
            "properties": {
                "confirmed": {
                    "type": "boolean"
                }
            },
            "required": [
                "confirmed"
            ]
        }
    },
    {
        "name": "pause_task",
        "description": "暂停当前或指定任务。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string"
                }
            }
        }
    },
    {
        "name": "resume_task",
        "description": "继续当前或指定任务。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string"
                }
            }
        }
    },
    {
        "name": "retry_task",
        "description": "重试失败的当前或指定任务。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string"
                }
            }
        }
    },
    {
        "name": "terminate_task",
        "description": "终止当前或指定任务，必须得到用户明确确认。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string"
                },
                "confirmed": {
                    "type": "boolean"
                }
            },
            "required": [
                "confirmed"
            ]
        }
    },
    {
        "name": "export_project",
        "description": "为已完成的专业剧本团队任务准备下载文件。",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string"
                }
            }
        }
    },
    {
        "name": "run_project_doctor",
        "description": "对专业剧本团队成品或本轮独立上传的完整剧本附件运行AI剧本医生Skill。",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string"
                },
                "skill": {
                    "type": "string",
                    "enum": [
                        "overall_dispatcher",
                        "character_continuity",
                        "hook_rhythm",
                        "logic_holes",
                        "character_humanity"
                    ]
                },
                "user_goal": {
                    "type": "string"
                }
            },
            "required": [
                "skill"
            ]
        }
    },
    {
        "name": "open_feature",
        "description": "打开专业剧本团队、剧本医生或资产库。",
        "parameters": {
            "type": "object",
            "properties": {
                "feature": {
                    "type": "string",
                    "enum": [
                        "script_team",
                        "script_doctor",
                        "assets"
                    ]
                }
            },
            "required": [
                "feature"
            ]
        }
    }
]


_SCHEMA_BY_NAME: Dict[str, Dict[str, Any]] = {item["name"]: item for item in _TOOL_SCHEMAS}


# Registered with one top-level call per tool on purpose. Hermes discovers tool
# modules by AST-scanning the module body for a direct ``registry.register(...)``
# statement, so a registration loop would leave this file silently unimported by
# the gateway even though it imports fine by hand.
registry.register(
    name="ask_choice",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["ask_choice"],
    handler=_make_handler("ask_choice"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="list_projects",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["list_projects"],
    handler=_make_handler("list_projects"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="select_project",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["select_project"],
    handler=_make_handler("select_project"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="get_project_status",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["get_project_status"],
    handler=_make_handler("get_project_status"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="read_attachment",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["read_attachment"],
    handler=_make_handler("read_attachment"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="write_attachment_draft",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["write_attachment_draft"],
    handler=_make_handler("write_attachment_draft"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="prepare_script_generation",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["prepare_script_generation"],
    handler=_make_handler("prepare_script_generation"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="confirm_script_generation",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["confirm_script_generation"],
    handler=_make_handler("confirm_script_generation"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="pause_task",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["pause_task"],
    handler=_make_handler("pause_task"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="resume_task",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["resume_task"],
    handler=_make_handler("resume_task"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="retry_task",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["retry_task"],
    handler=_make_handler("retry_task"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="terminate_task",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["terminate_task"],
    handler=_make_handler("terminate_task"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="export_project",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["export_project"],
    handler=_make_handler("export_project"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="run_project_doctor",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["run_project_doctor"],
    handler=_make_handler("run_project_doctor"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
registry.register(
    name="open_feature",
    toolset="scriptmaker",
    schema=_SCHEMA_BY_NAME["open_feature"],
    handler=_make_handler("open_feature"),
    emoji="SM",
    max_result_size_chars=_MAX_RESULT_CHARS,
)
