"""
connectors/dispatcher.py — 平台分发器
=====================================

统一的跨平台入口：
  preflight(platform, ...) → 转发到具体平台
  run_action(platform, ...) → 转发到具体平台
  register_agent(platform, ...) → 转发到具体平台
"""

from __future__ import annotations

from typing import Any, Dict

from connectors.muse import (
    PLATFORM_ID as MUSE_PLATFORM_ID,
    preflight as muse_preflight,
    register_muse_agent,
    run_agent_action as muse_run,
    user_muse_state,
)
from connectors.grok_bot import (
    PLATFORM_ID as GROK_PLATFORM_ID,
    preflight as grok_preflight,
    register_grok_agent,
    run_agent_action as grok_run,
    user_grok_state,
)
from connectors.nvidia import (
    PLATFORM_ID as NVIDIA_PLATFORM_ID,
    preflight as nvidia_preflight,
    register_nvidia_agent,
    run_agent_action as nvidia_run,
    user_nvidia_state,
)

_PLATFORM_PREFLIGHT = {
    MUSE_PLATFORM_ID: muse_preflight,
    GROK_PLATFORM_ID: grok_preflight,
    NVIDIA_PLATFORM_ID: nvidia_preflight,
}

_PLATFORM_RUN = {
    MUSE_PLATFORM_ID: muse_run,
    GROK_PLATFORM_ID: grok_run,
    NVIDIA_PLATFORM_ID: nvidia_run,
}

_PLATFORM_STATE = {
    MUSE_PLATFORM_ID: user_muse_state,
    GROK_PLATFORM_ID: user_grok_state,
    NVIDIA_PLATFORM_ID: user_nvidia_state,
}

# preflight / run 的 kwargs 白名单（三平台签名略有差异：Muse 无 model，Grok 无 bot_id 差异等）
# http_post_mock：离线测试接缝，大陆不可达时注入 mock 验证治理逻辑（不进 MCP schema）
_PREFLIGHT_KWARGS = {
    MUSE_PLATFORM_ID: {"agent_instance_id", "user_id", "prompt", "action", "currency",
                       "amount", "http_post_mock"},
    GROK_PLATFORM_ID: {"agent_instance_id", "user_id", "prompt", "action", "currency",
                       "amount", "http_post_mock"},
    NVIDIA_PLATFORM_ID: {"agent_instance_id", "user_id", "prompt", "action", "currency",
                         "amount", "http_post_mock"},
}

_RUN_KWARGS = {
    MUSE_PLATFORM_ID: {"agent_instance_id", "user_id", "prompt", "action", "bot_id",
                       "currency", "amount", "override", "http_post_mock"},
    GROK_PLATFORM_ID: {"agent_instance_id", "user_id", "prompt", "action", "bot_id",
                       "model", "currency", "amount", "override", "http_post_mock"},
    NVIDIA_PLATFORM_ID: {"agent_instance_id", "user_id", "prompt", "action", "model",
                         "currency", "amount", "override", "http_post_mock"},
}


# 各平台 register 允许的 kwargs（防统一 MCP schema 传入多余参数导致 TypeError）
_REGISTER_KWARGS = {
    MUSE_PLATFORM_ID: {"user_id", "agent_name", "platform_agent_id", "client_id",
                       "tokens", "capabilities", "platform_tier"},
    GROK_PLATFORM_ID: {"user_id", "agent_name", "platform_agent_id", "auth",
                       "credentials", "capabilities", "platform_tier"},
    NVIDIA_PLATFORM_ID: {"user_id", "agent_name", "agent_instance_id",
                         "platform_agent_id", "api_key"},
}


def register_agent(platform: str, **kwargs: Any) -> Dict[str, Any]:
    """统一注册入口。

    按平台过滤 kwargs：MCP 层用同一套 schema（含 nvidia-dev 的 agent_instance_id
    / api_key），Muse/Grok 侧不认识的参数在此剥离，避免 TypeError。
    """
    allowed = _REGISTER_KWARGS.get(platform)
    if not allowed:
        return {"ok": False, "error": f"unsupported platform: {platform}",
                "supported": list(_PLATFORM_RUN.keys())}
    body = {k: v for k, v in kwargs.items() if k in allowed}

    if platform == MUSE_PLATFORM_ID:
        return register_muse_agent(**body)
    if platform == GROK_PLATFORM_ID:
        return register_grok_agent(**body)
    return register_nvidia_agent(**body)


def preflight(platform: str, **kwargs: Any) -> Dict[str, Any]:
    fn = _PLATFORM_PREFLIGHT.get(platform)
    if not fn:
        return {"ok": False, "error": f"unsupported platform: {platform}",
                "supported": list(_PLATFORM_PREFLIGHT.keys())}
    body = {k: v for k, v in kwargs.items() if k in _PREFLIGHT_KWARGS.get(platform, set())}
    return fn(**body)


def run_action(platform: str, **kwargs: Any) -> Dict[str, Any]:
    fn = _PLATFORM_RUN.get(platform)
    if not fn:
        return {"ok": False, "error": f"unsupported platform: {platform}",
                "supported": list(_PLATFORM_RUN.keys())}
    body = {k: v for k, v in kwargs.items() if k in _RUN_KWARGS.get(platform, set())}
    return fn(**body)


def user_state(platform: str, user_id: str) -> Dict[str, Any]:
    fn = _PLATFORM_STATE.get(platform)
    if not fn:
        return {"ok": False, "error": f"unsupported platform: {platform}"}
    return fn(user_id)


def supported_platforms() -> list:
    return sorted(_PLATFORM_RUN.keys())


__all__ = [
    "register_agent", "preflight", "run_action", "user_state",
    "supported_platforms",
    "MUSE_PLATFORM_ID", "GROK_PLATFORM_ID", "NVIDIA_PLATFORM_ID",
]
