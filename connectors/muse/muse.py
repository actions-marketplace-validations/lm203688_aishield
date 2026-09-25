"""
connectors/muse/muse.py — Meta Muse Agent 接入
==============================================

**平台**：Meta Muse (https://muse.ai)
**定位**：给 Muse Agent 加装独立的个人身份 + 预算守护 + 行动溯源层

**大陆访问状态（2026-09-24 实测）**：
- muse.ai 首次可达（HTTP 307 → auth.muse.ai），但 CDN 抖动，多数请求超时
- 需要用户配置 HTTPS_PROXY 环境变量走海外代理

**接入路径**（3 条，按优先级）：
1. MCP（推荐，零平台改动）—— 见 connectors/muse/README.md
2. OAuth + REST API —— 本模块实现
3. Muse 官方 Connector 审核 —— 见 connectors/muse/openapi.yaml

**治理模型**（与 eco/personal_agent.py 强绑定）：
- PAI DID：跨平台可验证的个人 Agent 身份
- Capability Ticket：HMAC 签名授权凭证
- 4-tier verdict：allow / confirm / block / denied
- 8 因素风险评分
- HMAC 行动链 + 90 天离线可验证
- Connector 独立 8 规则审核
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
    detect_sensitive_triggers,
    extract_amount,
    exchange_code_for_token,
    get_access_token,
    get_client_secret,
    build_authorize_url,
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
# Muse API 端点
# ============================================================

PLATFORM_ID = "meta-muse"
PROVIDER = "muse"

MUSE_BASE = os.environ.get("AISHIELD_MUSE_BASE", "https://muse.ai")
MUSE_AUTH_BASE = os.environ.get("AISHIELD_MUSE_AUTH_BASE", "https://auth.muse.ai")
MUSE_API_BASE = os.environ.get("AISHIELD_MUSE_API_BASE", "https://api.muse.ai/v1")

MUSE_AUTHORIZE_URL = MUSE_AUTH_BASE + "/oauth/authorize"
MUSE_TOKEN_URL = MUSE_AUTH_BASE + "/oauth/token"

# 默认 OAuth scopes（Muse 官方开放能力）
DEFAULT_SCOPES = [
    "agent:chat",           # 对话
    "agent:run",            # 执行任务
    "agent:tool_call",      # 调用工具
    "user:read",            # 读取用户资料
]

DEFAULT_REDIRECT_URI = os.environ.get(
    "AISHIELD_MUSE_REDIRECT_URI",
    "https://aishield.local/callback/muse",
)

# 登记到 registry 的 token 端点
register_token_endpoint("muse", MUSE_TOKEN_URL)

# Action → API path 映射（Muse Agent 能力）
_ACTION_ENDPOINTS = {
    "chat": "/agents/{agent_id}/messages",
    "run_task": "/agents/{agent_id}/tasks",
    "tool_call": "/agents/{agent_id}/tools",
    "get_state": "/agents/{agent_id}/state",
}

# Action 类型 → 敏感程度（影响 preflight 风险评分）
_ACTION_RISK_HINT = {
    "chat": 0.1,
    "run_task": 0.3,
    "tool_call": 0.5,
    "get_state": 0.0,
}


# ============================================================
# OAuth 便捷封装
# ============================================================


def build_authorize_url_muse(
    client_id: str,
    redirect_uri: str = DEFAULT_REDIRECT_URI,
    scopes: Optional[List[str]] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """生成 Muse OAuth 授权 URL（用户浏览器访问；授权后回跳 redirect_uri?code=...&state=...）"""
    return build_authorize_url(
        authorize_endpoint=MUSE_AUTHORIZE_URL,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scopes=scopes or DEFAULT_SCOPES,
        state=state,
    )


def exchange_muse_code(
    code: str,
    client_id: str,
    redirect_uri: str = DEFAULT_REDIRECT_URI,
    client_secret: Optional[str] = None,
    http_post_mock: HTTPPost = None,
) -> Dict[str, Any]:
    secret = client_secret or get_client_secret("muse")
    if not secret:
        return {"ok": False, "error": "client_secret not configured (set AISHIELD_MUSE_SECRET_KEY or place at ~/.aishield/muse/client_secret.txt)"}
    return exchange_code_for_token(
        MUSE_TOKEN_URL, code, client_id, secret, redirect_uri,
        http_post_mock=http_post_mock,
    )


# ============================================================
# Agent 注册（PAI DID + Muse 元数据）
# ============================================================


def register_muse_agent(
    user_id: str,
    agent_name: str,
    platform_agent_id: str,
    client_id: str,
    tokens: Optional[Dict[str, Any]] = None,
    capabilities: Optional[List[str]] = None,
    platform_tier: Optional[str] = None,
) -> Dict[str, Any]:
    """把 Muse Agent 登记为 PAI Agent 实例（platform=meta-muse）"""
    if not (user_id and agent_name and platform_agent_id and client_id):
        return {"ok": False, "error": "user_id, agent_name, platform_agent_id, client_id required"}

    r = pa.register_agent_instance(
        user_id=user_id,
        agent_name=agent_name,
        provider=PROVIDER,
        platform=PLATFORM_ID,
        platform_tier=platform_tier,
        capabilities=capabilities or ["muse.chat", "muse.run_task", "muse.tool_call"],
    )
    instance_id = r.get("instance_id") if isinstance(r, dict) else None
    if not instance_id:
        return {"ok": False, "error": "register failed", "detail": r}

    if tokens:
        store_access_token("muse", instance_id, client_id, tokens)

    return {
        "ok": True,
        "agent_instance_id": instance_id,
        "parent_did": r.get("parent_did"),
        "platform": PLATFORM_ID,
        "client_id": client_id,
        "platform_agent_id": platform_agent_id,
    }


# ============================================================
# Preflight（预算 + 风险 + 敏感词升级）
# ============================================================


def preflight(
    agent_instance_id: str,
    user_id: str,
    prompt: str,
    action: str = "chat",
    currency: str = "CNY",
    amount: Optional[float] = None,
    http_post_mock: HTTPPost = None,
) -> Dict[str, Any]:
    """Muse Agent 敏感动作前置检查"""
    if not (agent_instance_id and user_id):
        return {"ok": False, "error": "agent_instance_id and user_id required"}

    amount_detected = amount if amount is not None else extract_amount(prompt)
    triggers = detect_sensitive_triggers(prompt)
    payload = {
        "action": action,
        "prompt_fingerprint": prompt_fingerprint(prompt),
        "prompt_preview": (prompt or "")[:120],
        "target_url": f"https://muse.ai/agents/{agent_instance_id}",
        "sensitive_triggers": triggers,
    }

    verdict_r = pa.check_budget_and_risk(
        user_id=user_id,
        action=f"muse.{action}",
        amount=amount_detected if amount_detected > 0 else None,
        currency=currency,
        target_url="https://muse.ai",
        category="chat" if action == "chat" else action,
        payload=payload,
    )
    if not verdict_r.get("success") and "verdict" not in verdict_r:
        return {"ok": False, "error": "preflight failed", "detail": verdict_r}

    raw_verdict = verdict_r.get("verdict") or "allow"
    raw_reason = verdict_r.get("verdict_reason") or verdict_r.get("reason") or ""
    risk = verdict_r.get("risk") or {}
    budget_info = verdict_r.get("budget") or {}

    # 决策流水线（顺序不可变）：
    # 1) invalid_amount 且 amount<=0 → 视为非支付类动作，降级为 allow
    # 2) 有敏感词 → 升级为 block（除非已经是 denied 或 invalid_amount 已降级）
    final = raw_verdict
    final_reason = ""
    if raw_verdict == "denied" and raw_reason == "invalid_amount" and amount_detected <= 0:
        final = "allow"
        final_reason = "no_amount_chat_action"
    if raw_verdict in ("allow", "confirm", "denied") and triggers:
        if raw_verdict != "denied":
            final = "block"
            final_reason = "sensitive_triggers"
        else:
            # 敏感词触发 + 预算原因 denied → 仍为 block（敏感词才是主原因）
            final = "block"
            final_reason = "sensitive_triggers"
    elif raw_verdict == "denied" and raw_reason != "invalid_amount":
        final = "denied"
        final_reason = raw_reason

    verdict_out = {
        "verdict": final,
        "muse_sensitive_triggers": triggers,
        "muse_action": action,
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
        "target_domain": "muse.ai",
        "agent_instance_id": agent_instance_id,
        "user_id": user_id,
        "prompt_fingerprint": prompt_fingerprint(prompt),
        "sensitive_triggers": triggers,
        "reason": raw_reason,
        "raw_verdict": verdict_r,
    }


# ============================================================
# 执行 Muse Agent 动作
# ============================================================


def run_agent_action(
    agent_instance_id: str,
    user_id: str,
    prompt: str,
    action: str = "chat",
    bot_id: Optional[str] = None,
    currency: str = "CNY",
    amount: Optional[float] = None,
    override: bool = False,
    http_post_mock: HTTPPost = None,
) -> Dict[str, Any]:
    """Muse Agent 全流程：
      1. preflight（预算+风险+敏感词）
      2. override 处理（denied 硬拒 / block-需 override / confirm-需 override）
      3. 取 access_token（自动 refresh；fail-closed）
      4. 真实调 Muse API
      5. record_action（含 verdict + risk + prompt 指纹）
    """
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
        # 非支付类动作且 amount=0 时，denied 原因可能是 invalid_amount；应改为 allow 继续
        if reason == "invalid_amount" and pf.get("amount_detected", 0) <= 0:
            verdict = "allow"
            verdict_data = {**verdict_data, "verdict": "allow", "reason": "no_amount_chat_action"}
        else:
            return {
                "ok": False, "error": f"budget hard-cap exceeded: {reason}",
                "verdict": verdict_data, "risk": pf.get("risk"),
                "note": "hard cap, override NOT allowed",
            }
    if verdict == "block" and not override:
        return {
            "ok": False, "error": "risk block; use override=true to force",
            "verdict": verdict_data, "risk": pf.get("risk"),
            "sensitive_triggers": pf.get("sensitive_triggers", []),
        }
    if verdict == "confirm" and not override:
        return {
            "ok": False, "error": "requires user confirmation",
            "verdict": verdict_data, "risk": pf.get("risk"),
            "action": "confirm_and_retry",
        }

    # 取 token
    tk = get_access_token("muse", agent_instance_id, http_post_mock=http_post_mock)
    if not tk.get("ok"):
        return {
            "ok": False, "error": "no valid access token",
            "action": tk.get("action", "re_authorize"),
            "preflight": pf,
        }

    # 组 URL
    template = _ACTION_ENDPOINTS.get(action)
    if not template:
        return {"ok": False, "error": f"unknown action: {action}", "supported": list(_ACTION_ENDPOINTS.keys())}
    url = MUSE_API_BASE + template.format(agent_id=bot_id or agent_instance_id)

    body = {
        "content": prompt,
        "content_type": "text",
        "user_id": user_id,
    }
    if action == "run_task":
        body["stream"] = False

    status, resp = http_post(url, body, token=tk["access_token"], http_post_mock=http_post_mock)
    if status != 200 or (isinstance(resp, dict) and resp.get("error")):
        return {
            "ok": False,
            "error": f"muse api failed: HTTP {status}",
            "status": status, "response": resp, "preflight": pf,
        }

    data = resp.get("data") if isinstance(resp.get("data"), dict) else resp
    message_id = data.get("id") or data.get("message_id") or data.get("task_id")
    session_id = data.get("session_id")

    # 记录 action
    action_payload = {
        "action": action,
        "platform_agent_id": bot_id or agent_instance_id,
        "session_id": session_id,
        "message_id": message_id,
        "prompt_fp": pf["prompt_fingerprint"],
        "override_used": bool(override),
        "amount": pf.get("amount_detected", 0),
        "currency": currency,
        "target_url": "https://muse.ai",
        "sensitive_triggers": pf.get("sensitive_triggers", []),
    }
    rec = pa.record_action(
        user_id=user_id,
        action=f"muse.{action}",
        instance_id=agent_instance_id,
        verdict=verdict,
        payload=action_payload,
        note=json.dumps({
            "message_id": message_id, "session_id": session_id,
            "override_used": bool(override), "action": action,
        }, ensure_ascii=False),
    )

    # 支付类预算记账
    budget_result = None
    if pf.get("amount_detected", 0) > 0:
        order_id = f"muse-{user_id}-{session_id or message_id or pf['prompt_fingerprint']}"
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
        "session_id": session_id,
        "message_id": message_id,
        "recorded_action": rec if isinstance(rec, dict) else {"ok": True, "detail": rec},
        "budget": budget_result,
        "response": data,
    }


# ============================================================
# 用户 Muse 状态 + 自检
# ============================================================


def user_muse_state(user_id: str) -> Dict[str, Any]:
    """用户在 Muse 平台上的所有注册 agent + token 状态"""
    if not user_id:
        return {"ok": False, "error": "user_id required"}
    instances = pa.list_instances_by_platform(user_id=user_id, platform_id=PLATFORM_ID)
    state = load_state("muse")
    tokens_info = []
    for inst in instances:
        iid = inst.get("instance_id")
        entry = state.get("tokens", {}).get(iid)
        if entry:
            now = int(time.time())
            tokens_info.append({
                "agent_instance_id": iid,
                "agent_name": inst.get("agent_name"),
                "token_expires_in_s": max(0, entry.get("expires_at", 0) - now),
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
        "note": "需要 HTTPS_PROXY 走海外代理才能直连 muse.ai",
    }


def self_check() -> Dict[str, Any]:
    """自检：可达性 + 密钥 + 治理层"""
    import urllib.request
    result = {"ok": True, "checks": {}}

    # 1. muse.ai 可达性
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler())
        req = urllib.request.Request(MUSE_BASE, method="HEAD")
        with opener.open(req, timeout=5) as r:
            result["checks"]["muse_reachable"] = {"ok": True, "status": r.status}
    except Exception as e:
        result["checks"]["muse_reachable"] = {"ok": False, "error": str(e)[:200]}

    result["checks"]["client_secret_configured"] = bool(get_client_secret("muse"))
    result["checks"]["governance_available"] = pa is not None
    state = load_state("muse")
    result["checks"]["tokens_stored"] = len(state.get("tokens", {}))
    result["checks"]["proxy_env"] = proxy_env_summary()

    return result


__all__ = [
    "PLATFORM_ID", "PROVIDER",
    "MUSE_BASE", "MUSE_AUTH_BASE", "MUSE_API_BASE",
    "MUSE_AUTHORIZE_URL", "MUSE_TOKEN_URL",
    "DEFAULT_SCOPES", "DEFAULT_REDIRECT_URI",
    "build_authorize_url_muse", "exchange_muse_code",
    "register_muse_agent", "preflight", "run_agent_action",
    "user_muse_state", "self_check",
]
