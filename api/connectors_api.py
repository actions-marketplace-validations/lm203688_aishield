"""
api/connectors_api.py — 平台接入层 API 路由
===========================================

统一入口 /api/v1/connectors/{platform}/...
支持平台：meta-muse / xai-grok-bot / nvidia-dev
另含 agent 基础设施开源扫描管道：/api/v1/agent-infra/...
"""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from connectors.dispatcher import (
    GROK_PLATFORM_ID,
    MUSE_PLATFORM_ID,
    NVIDIA_PLATFORM_ID,
    register_agent,
    run_action,
    supported_platforms,
    user_state,
)
from connectors.muse import self_check as muse_self_check
from connectors.grok_bot import self_check as grok_self_check
from connectors.nvidia import self_check as nvidia_self_check
from connectors.agent_infra import scan_pipeline as agent_infra_scan


def _plat(path: str) -> str | None:
    m = re.search(r"/api/v1/connectors/([^/]+)(?:/.*)?$", path)
    return m.group(1) if m else None


def handle_get(path: str, query: Dict[str, list]) -> Tuple[Dict[str, Any], int]:
    """GET 路由"""
    # ── Agent 基础设施开源扫描管道（无需 platform 前缀，GET 仅列目标）──
    if path == "/api/v1/agent-infra/targets":
        import eco.platform_registry as reg
        infra = [p for p in reg.list_platforms() if p.get("family") in ("infrastructure", "developer")]
        return {"ok": True, "targets": infra, "count": len(infra)}, 200

    if path.startswith("/api/v1/agent-infra"):
        return {"ok": False, "error": f"unknown GET route: {path}"}, 404

    plat = _plat(path)

    if path == "/api/v1/connectors":
        return {"ok": True, "platforms": supported_platforms(), "count": len(supported_platforms())}, 200

    if not plat:
        return {"ok": False, "error": "platform required"}, 400

    if path == f"/api/v1/connectors/{plat}/self-check":
        if plat == MUSE_PLATFORM_ID:
            return {"ok": True, "platform": plat, **muse_self_check()}, 200
        if plat == GROK_PLATFORM_ID:
            return {"ok": True, "platform": plat, **grok_self_check()}, 200
        if plat == NVIDIA_PLATFORM_ID:
            return {"ok": True, "platform": plat, **nvidia_self_check()}, 200
        return {"ok": False, "error": f"unknown platform: {plat}"}, 400

    if path == f"/api/v1/connectors/{plat}/state" or path.endswith(f"/connectors/{plat}/users/{plat}/state"):
        m = re.search(r"/connectors/([^/]+)/users/([^/]+)/state$", path)
        if m:
            r = user_state(m.group(1), m.group(2))
            return {"ok": r.get("ok"), **r}, 200 if r.get("ok") else 404
        # fallback：无 user_id
        q = query.get("user_id", [""])[0]
        r = user_state(plat, q) if q else {"ok": False, "error": "user_id required"}
        return {"ok": r.get("ok"), **r}, 200 if r.get("ok") else 400

    return {"ok": False, "error": f"unknown GET route: {path}"}, 404


def handle_post(path: str, body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """POST 路由"""
    if not isinstance(body, dict):
        body = {}

    # ── Agent 基础设施开源扫描管道（无需 platform 前缀）──
    if path == "/api/v1/agent-infra/scan":
        spec = {
            k: body.get(k)
            for k in ("name", "repo_url", "local_path", "files", "platform_id", "tool_type")
            if body.get(k) is not None
        }
        if not spec:
            return {"ok": False, "error": "empty scan spec; provide name + (repo_url|local_path|files)"}, 400
        res = agent_infra_scan.scan_target(spec)
        if res.get("error"):
            return {"ok": False, "error": res["error"], "target": res.get("target")}, 400
        out = dict(res)
        out["ok"] = True
        out["mcp_adapter_skeleton"] = agent_infra_scan.build_mcp_adapter_skeleton(res)
        out["secondary_rd_checklist"] = agent_infra_scan.build_secondary_rd_checklist(res)
        return out, 200

    if path == "/api/v1/agent-infra/scan-portfolio":
        specs = body.get("specs") or []
        if not isinstance(specs, list) or not specs:
            return {"ok": False, "error": "specs (non-empty list) required"}, 400
        pf = agent_infra_scan.scan_portfolio(specs)
        pf["ok"] = True
        return pf, 200

    if path.startswith("/api/v1/agent-infra"):
        return {"ok": False, "error": f"unknown POST route: {path}"}, 404

    plat = _plat(path)
    if not plat:
        return {"ok": False, "error": "platform required"}, 400

    # 授权 URL 生成
    if path.endswith("/oauth/authorize"):
        if plat == MUSE_PLATFORM_ID:
            from connectors.muse import build_authorize_url_muse
            r = build_authorize_url_muse(
                client_id=body.get("client_id", ""),
                redirect_uri=body.get("redirect_uri"),
                scopes=body.get("scopes"),
            )
            return {"ok": r.get("ok"), **r}, 200 if r.get("ok") else 400
        if plat == GROK_PLATFORM_ID:
            from connectors.grok_bot import build_authorize_url_xai
            r = build_authorize_url_xai(
                client_id=body.get("client_id", ""),
                redirect_uri=body.get("redirect_uri"),
                scopes=body.get("scopes"),
            )
            return {"ok": r.get("ok"), **r}, 200 if r.get("ok") else 400
        return {"ok": False, "error": f"unsupported platform: {plat}"}, 400

    # OAuth code 换 token
    if path.endswith("/oauth/token"):
        if plat == MUSE_PLATFORM_ID:
            from connectors.muse import exchange_muse_code
            r = exchange_muse_code(
                code=body.get("code", ""),
                client_id=body.get("client_id", ""),
                redirect_uri=body.get("redirect_uri"),
            )
            return {"ok": r.get("ok"), **r}, 200 if r.get("ok") else 400
        if plat == GROK_PLATFORM_ID:
            from connectors.grok_bot import exchange_xai_code
            r = exchange_xai_code(
                code=body.get("code", ""),
                client_id=body.get("client_id", ""),
                redirect_uri=body.get("redirect_uri"),
            )
            return {"ok": r.get("ok"), **r}, 200 if r.get("ok") else 400
        return {"ok": False, "error": f"unsupported platform: {plat}"}, 400

    # Agent 注册
    if path.endswith("/agents/register"):
        r = register_agent(plat, **body)
        return {"ok": r.get("ok"), **r}, 200 if r.get("ok") else 400

    # Preflight 检查
    if path.endswith("/actions/preflight"):
        from connectors.dispatcher import preflight
        r = preflight(plat, **body)
        return {"ok": r.get("ok"), **r}, 200 if r.get("ok") else 400

    # 执行动作
    if path.endswith("/actions/run"):
        r = run_action(plat, **body)
        status = 200 if r.get("ok") else (409 if r.get("verdict", {}).get("verdict") == "denied" else 400)
        return {"ok": r.get("ok"), **r}, status

    return {"ok": False, "error": f"unknown POST route: {path}"}, 404


__all__ = ["handle_get", "handle_post", "supported_platforms"]
