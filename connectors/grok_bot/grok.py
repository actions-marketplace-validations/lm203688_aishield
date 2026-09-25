"""
connectors/grok_bot/grok.py — xAI Grok Bot Agent 接入
======================================================

**平台**：xAI Grok Bot（SuperGrok Heavy 起，2026-08-11）
**OpenAI 兼容 API**：https://api.x.ai/v1
**MCP 支持**：是（推荐路径，见 connectors/grok_bot/README.md）

**大陆访问状态（2026-09-24 实测）**：
- api.x.ai — **连接超时**
- grok.com / x.com — **连接超时**
- 需要用户配置 HTTPS_PROXY 环境变量走海外代理

**认证**：
- Personal Access Token (PAT) —— xAI 官方推荐
- OAuth 2.0 —— 企业版场景

**API 风格**：OpenAI 兼容（`POST /v1/chat/completions`），本模块直接支持。
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import eco.personal_agent as pa
from connectors.base import (
    HTTPPost,
    build_authorize_url,
    detect_sensitive_triggers,
    exchange_code_for_token,
    extract_amount,
    get_access_token,
    get_client_secret,
    http_post,
    load_state,
    prompt_fingerprint,
    proxy_env_summary,
    refresh_access_token,
    register_token_endpoint,
    save_state,
    store_access_token,
)

# ============================================================
# xAI API 端点
# ============================================================

PLATFORM_ID = "xai-grok-bot"
PROVIDER = "grok-bot"

XAI_BASE = os.environ.get("AISHIELD_XAI_BASE", "https://api.x.ai")
XAI_API_BASE = os.environ.get("AISHIELD_XAI_API_BASE", "https://api.x.ai/v1")
XAI_AUTH_BASE = os.environ.get("AISHIELD_XAI_AUTH_BASE", "https://console.x.ai")

# OAuth 2.0 端点（xAI 企业版）
XAI_AUTHORIZE_URL = XAI_AUTH_BASE + "/oauth/authorize"
XAI_TOKEN_URL = XAI_AUTH_BASE + "/oauth/token"

# Grok Bot agent API（OpenAI 兼容 + Grok 专用扩展）
GROK_CHAT_URL = XAI_API_BASE + "/chat/completions"
GROK_AGENTS_URL = XAI_API_BASE + "/agents"

# OAuth scopes（xAI 官方）
DEFAULT_SCOPES = [
    "grok:chat",
    "grok:agent",
    "grok:tool_call",
    "user:read",
]

DEFAULT_REDIRECT_URI = os.environ.get(
    "AISHIELD_XAI_REDIRECT_URI",
    "https://aishield.local/callback/xai",
)

register_token_endpoint("grok", XAI_TOKEN_URL)

_ACTION_ENDPOINTS = {
    "chat": GROK_CHAT_URL,
    "chat_completions": GROK_CHAT_URL,
    "get_agent": "/agents/{agent_id}",
    "run_task": "/agents/{agent_id}/tasks",
}

_ACTION_RISK_HINT = {
    "chat": 0.1,
    "chat_completions": 0.1,
    "get_agent": 0.0,
    "run_task": 0.3,
    "tool_call": 0.5,
}


# ============================================================
# PAT 支持（xAI 官方推荐）
# ============================================================


def store_pat(agent_instance_id: str, pat: str) -> Dict[str, Any]:
    """把 PAT 存入本地（不落盘到 git；仅本用户 home 目录）"""
    if not (agent_instance_id and pat):
        return {"ok": False, "error": "agent_instance_id and pat required"}
    state = load_state("grok")
    state.setdefault("tokens", {})[agent_instance_id] = {
        "auth_type": "pat",
        "access_token": pat,  # PAT 直接当 Bearer token
        "refresh_token": None,
        "expires_at": 0,  # 不过期（PAT 常驻）
        "refresh_expires_at": 0,
        "scope": "pat",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    save_state("grok", state)
    return {"ok": True, "agent_instance_id": agent_instance_id, "auth_type": "pat"}


def get_pat_or_token(agent_instance_id: str, http_post_mock: HTTPPost = None) -> Dict[str, Any]:
    """兼容 PAT 与 OAuth token：PAT 不需要 refresh，直接返回"""
    state = load_state("grok")
    entry = state.get("tokens", {}).get(agent_instance_id)
    if not entry:
        return {"ok": False, "error": "no credentials stored", "agent_instance_id": agent_instance_id}

    if entry.get("auth_type") == "pat":
        return {"ok": True, "access_token": entry["access_token"], "auth_type": "pat"}

    # OAuth 走通用 refresh 逻辑
    return get_access_token("grok", agent_instance_id, http_post_mock=http_post_mock)


# ============================================================
# OAuth 便捷封装
# ============================================================


def build_authorize_url_xai(
    client_id: str,
    redirect_uri: str = DEFAULT_REDIRECT_URI,
    scopes: Optional[List[str]] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    return build_authorize_url(
        authorize_endpoint=XAI_AUTHORIZE_URL,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scopes=scopes or DEFAULT_SCOPES,
        state=state,
    )


def exchange_xai_code(
    code: str,
    client_id: str,
    redirect_uri: str = DEFAULT_REDIRECT_URI,
    client_secret: Optional[str] = None,
    http_post_mock: HTTPPost = None,
) -> Dict[str, Any]:
    secret = client_secret or get_client_secret("grok")
    if not secret:
        return {"ok": False, "error": "client_secret not configured (set AISHIELD_XAI_SECRET_KEY)"}
    return exchange_code_for_token(
        XAI_TOKEN_URL, code, client_id, secret, redirect_uri,
        http_post_mock=http_post_mock,
    )


# ============================================================
# Agent 注册
# ============================================================


def register_grok_agent(
    user_id: str,
    agent_name: str,
    platform_agent_id: str,
    auth: str = "pat",
    credentials: Optional[Dict[str, Any]] = None,
    capabilities: Optional[List[str]] = None,
    platform_tier: Optional[str] = None,
) -> Dict[str, Any]:
    """
    把 Grok Bot Agent 登记为 PAI Agent 实例。

    auth: "pat" | "oauth"
    credentials: {"pat": "***"} 或 {"access_token":..., "refresh_token":..., ...}
    """
    if not (user_id and agent_name and platform_agent_id):
        return {"ok": False, "error": "user_id, agent_name, platform_agent_id required"}
    if auth not in ("pat", "oauth"):
        return {"ok": False, "error": "auth must be 'pat' or 'oauth'"}

    r = pa.register_agent_instance(
        user_id=user_id,
        agent_name=agent_name,
        provider=PROVIDER,
        platform=PLATFORM_ID,
        platform_tier=platform_tier,
        capabilities=capabilities or ["grok.chat", "grok.tool_call"],
    )
    instance_id = r.get("instance_id") if isinstance(r, dict) else None
    if not instance_id:
        return {"ok": False, "error": "register failed", "detail": r}

    # 存凭证
    if credentials:
        if auth == "pat" and credentials.get("pat"):
            store_pat(instance_id, credentials["pat"])
        elif auth == "oauth" and credentials.get("access_token"):
            client_id = credentials.get("client_id", "grok-client")
            store_access_token("grok", instance_id, client_id, credentials)

    return {
        "ok": True,
        "agent_instance_id": instance_id,
        "parent_did": r.get("parent_did"),
        "platform": PLATFORM_ID,
        "auth_type": auth,
        "platform_agent_id": platform_agent_id,
    }


# ============================================================
# Preflight
# ============================================================


def preflight(
    agent_instance_id: str,
    user_id: str,
    prompt: str,
    action: str = "chat",
    currency: str = "USD",  # Grok 海外场景默认 USD
    amount: Optional[float] = None,
    http_post_mock: HTTPPost = None,
) -> Dict[str, Any]:
    """Grok Bot 敏感动作前置检查"""
    if not (agent_instance_id and user_id):
        return {"ok": False, "error": "agent_instance_id and user_id required"}

    amount_detected = amount if amount is not None else extract_amount(prompt)
    triggers = detect_sensitive_triggers(prompt)
    payload = {
        "action": action,
        "prompt_fingerprint": prompt_fingerprint(prompt),
        "prompt_preview": (prompt or "")[:120],
        "target_url": f"https://x.ai/agents/{agent_instance_id}",
        "sensitive_triggers": triggers,
    }

    verdict_r = pa.check_budget_and_risk(
        user_id=user_id,
        action=f"grok.{action}",
        amount=amount_detected if amount_detected > 0 else None,
        currency=currency,
        target_url="https://api.x.ai",
        category="chat" if action in ("chat", "chat_completions") else action,
        payload=payload,
    )
    if not verdict_r.get("success") and "verdict" not in verdict_r:
        return {"ok": False, "error": "preflight failed", "detail": verdict_r}

    raw_verdict = verdict_r.get("verdict") or "allow"
    raw_reason = verdict_r.get("verdict_reason") or verdict_r.get("reason") or ""
    risk = verdict_r.get("risk") or {}
    budget_info = verdict_r.get("budget") or {}

    final = raw_verdict
    final_reason = ""
    if raw_verdict == "denied" and raw_reason == "invalid_amount" and amount_detected <= 0:
        final = "allow"
        final_reason = "no_amount_chat_action"
    if raw_verdict in ("allow", "confirm", "denied") and triggers:
        final = "block"
        final_reason = "sensitive_triggers"
    elif raw_verdict == "denied" and raw_reason != "invalid_amount":
        final = "denied"
        final_reason = raw_reason

    verdict_out = {
        "verdict": final,
        "grok_sensitive_triggers": triggers,
        "grok_action": action,
        "final_reason": final_reason,
        "raw_verdict": raw_verdict,
        "raw_reason": raw_reason,
    }

    return {
        "ok": True,
        "verdict": verdict_out,
        "risk": risk,
        "budget": budget_info,
        "amount_detected": amount_detected,
        "currency": currency,
        "target_domain": "api.x.ai",
        "agent_instance_id": agent_instance_id,
        "user_id": user_id,
        "prompt_fingerprint": prompt_fingerprint(prompt),
        "sensitive_triggers": triggers,
        "reason": raw_reason,
        "raw_verdict": verdict_r,
    }


# ============================================================
# 执行 Grok Bot 动作（OpenAI 兼容 chat + task API）
# ============================================================


def run_agent_action(
    agent_instance_id: str,
    user_id: str,
    prompt: str,
    action: str = "chat",
    bot_id: Optional[str] = None,
    model: str = "grok-3",
    currency: str = "USD",
    amount: Optional[float] = None,
    override: bool = False,
    http_post_mock: HTTPPost = None,
) -> Dict[str, Any]:
    """Grok Bot 全流程：preflight → token → 真实 API → record_action"""
    pf = preflight(
        agent_instance_id=agent_instance_id,
        user_id=user_id,
        prompt=prompt,
        action=action,
        currency=currency,
        amount=amount,
        http_post_mock=http_post_mock,
    )
    if not pf.get("ok"):
        return pf

    verdict = pf["verdict"].get("verdict")
    verdict_data = pf["verdict"]

    if verdict == "denied":
        reason = pf.get("reason") or pf.get("detail", {}).get("reason") or "budget_exceeded"
        if reason == "invalid_amount" and pf.get("amount_detected", 0) <= 0:
            verdict = "allow"
            verdict_data = {**verdict_data, "verdict": "allow", "reason": "no_amount_chat_action"}
        else:
            return {"ok": False, "error": f"budget hard-cap exceeded: {reason}",
                    "verdict": verdict_data, "risk": pf.get("risk"),
                    "note": "hard cap, override NOT allowed"}
    if verdict == "block" and not override:
        return {"ok": False, "error": "risk block; use override=true",
                "verdict": verdict_data, "risk": pf.get("risk"),
                "sensitive_triggers": pf.get("sensitive_triggers", [])}
    if verdict == "confirm" and not override:
        return {"ok": False, "error": "requires user confirmation",
                "verdict": verdict_data, "risk": pf.get("risk"),
                "action": "confirm_and_retry"}

    tk = get_pat_or_token(agent_instance_id, http_post_mock=http_post_mock)
    if not tk.get("ok"):
        return {"ok": False, "error": "no valid credentials",
                "action": tk.get("action", "re_authorize"), "preflight": pf}

    # 组 URL + body
    template = _ACTION_ENDPOINTS.get(action)
    if not template:
        return {"ok": False, "error": f"unknown action: {action}",
                "supported": list(_ACTION_ENDPOINTS.keys())}
    if template.startswith("/"):
        url = XAI_API_BASE + template.format(agent_id=bot_id or agent_instance_id)
    else:
        url = template

    # OpenAI 兼容 chat body
    if action in ("chat", "chat_completions"):
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
    else:
        body = {"prompt": prompt, "user_id": user_id}

    status, resp = http_post(url, body, token=tk["access_token"], http_post_mock=http_post_mock)
    if status != 200 or (isinstance(resp, dict) and resp.get("error")):
        return {
            "ok": False,
            "error": f"xai api failed: HTTP {status}",
            "status": status, "response": resp, "preflight": pf,
        }

    # 解析响应（OpenAI 兼容）
    choices = resp.get("choices") or []
    answer = ""
    completion_id = None
    usage = {}
    if choices and isinstance(choices[0], dict):
        msg = choices[0].get("message") or {}
        answer = msg.get("content", "")
    completion_id = resp.get("id")
    usage = resp.get("usage", {}) or {}

    action_payload = {
        "action": action,
        "model": model,
        "session_id": completion_id,
        "prompt_fp": pf["prompt_fingerprint"],
        "override_used": bool(override),
        "amount": pf.get("amount_detected", 0),
        "currency": currency,
        "target_url": "https://api.x.ai",
        "sensitive_triggers": pf.get("sensitive_triggers", []),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }
    rec = pa.record_action(
        user_id=user_id,
        action=f"grok.{action}",
        instance_id=agent_instance_id,
        verdict=verdict,
        payload=action_payload,
        note=json.dumps({
            "completion_id": completion_id, "override_used": bool(override),
            "action": action, "model": model,
        }, ensure_ascii=False),
    )

    # 计费类预算记账
    budget_result = None
    if pf.get("amount_detected", 0) > 0:
        order_id = f"grok-{user_id}-{completion_id or pf['prompt_fingerprint']}"
        res = pa.reserve_budget(user_id=user_id, order_id=order_id,
                                amount=pf["amount_detected"], currency=currency)
        if res.get("success"):
            budget_result = pa.commit_budget(
                reservation_id=res.get("reservation_id"), order_id=order_id,
                user_id=user_id, amount=pf["amount_detected"], currency=currency,
            )

    return {
        "ok": True,
        "verdict": verdict,
        "override_used": bool(override),
        "risk": pf.get("risk"),
        "completion_id": completion_id,
        "answer": answer,
        "usage": usage,
        "recorded_action": rec if isinstance(rec, dict) else {"ok": True, "detail": rec},
        "budget": budget_result,
        "response": resp,
    }


# ============================================================
# 状态 + 自检
# ============================================================


def user_grok_state(user_id: str) -> Dict[str, Any]:
    if not user_id:
        return {"ok": False, "error": "user_id required"}
    instances = pa.list_instances_by_platform(user_id=user_id, platform_id=PLATFORM_ID)
    state = load_state("grok")
    tokens_info = []
    for inst in instances:
        iid = inst.get("instance_id")
        entry = state.get("tokens", {}).get(iid)
        if entry:
            now = int(time.time())
            tokens_info.append({
                "agent_instance_id": iid,
                "agent_name": inst.get("agent_name"),
                "auth_type": entry.get("auth_type", "oauth"),
                "token_expires_in_s": max(0, entry.get("expires_at", 0) - now) if entry.get("expires_at") else None,
                "refresh_available": bool(entry.get("refresh_token")) and entry.get("refresh_expires_at", 0) > now,
                "scope": entry.get("scope", ""),
            })
    return {
        "ok": True,
        "user_id": user_id,
        "platform": PLATFORM_ID,
        "platform_reachable": False,  # 大陆默认不通
        "agents": instances,
        "tokens": tokens_info,
        "proxy_env": proxy_env_summary(),
        "note": "需要 HTTPS_PROXY 走海外代理才能直连 api.x.ai",
    }


def self_check() -> Dict[str, Any]:
    import urllib.request
    result = {"ok": True, "checks": {}}
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler())
        req = urllib.request.Request(XAI_BASE + "/v1/models", method="GET")
        with opener.open(req, timeout=5) as r:
            result["checks"]["xai_reachable"] = {"ok": True, "status": r.status}
    except Exception as e:
        result["checks"]["xai_reachable"] = {"ok": False, "error": str(e)[:200]}

    result["checks"]["client_secret_configured"] = bool(get_client_secret("grok"))
    result["checks"]["governance_available"] = pa is not None
    state = load_state("grok")
    result["checks"]["credentials_stored"] = len(state.get("tokens", {}))
    result["checks"]["proxy_env"] = proxy_env_summary()
    return result


__all__ = [
    "PLATFORM_ID", "PROVIDER",
    "XAI_BASE", "XAI_API_BASE", "XAI_AUTH_BASE",
    "XAI_AUTHORIZE_URL", "XAI_TOKEN_URL", "GROK_CHAT_URL",
    "DEFAULT_SCOPES", "DEFAULT_REDIRECT_URI",
    "store_pat", "get_pat_or_token",
    "build_authorize_url_xai", "exchange_xai_code",
    "register_grok_agent", "preflight", "run_agent_action",
    "user_grok_state", "self_check",
]
