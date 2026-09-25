"""
api/personal_agent_api.py — 个人 Agent 治理 API

覆盖 6 组能力（对齐 eco/personal_agent.py）：
  - PAI 身份          : /api/v1/personal-agents/users
  - Agent 实例        : /api/v1/personal-agents/users/{uid}/agent-instances
  - Capability Ticket : /api/v1/personal-agents/users/{uid}/tickets
  - 预算守护          : /api/v1/personal-agents/budget/*
  - 行动溯源          : /api/v1/personal-agents/users/{uid}/actions
  - Dispute & Vet     : /api/v1/personal-agents/users/{uid}/disputes,
                        /api/v1/personal-agents/users/{uid}/connectors/vet

路由前缀：/api/v1/personal-agents/
"""
from __future__ import annotations

import json
import os
import re
import sys
from urllib.parse import parse_qs

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_BASE, _BASE + "/eco", _BASE + "/api"):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── 惰性导入 ──
def _pa():
    from eco import personal_agent
    return personal_agent


# ── 路径匹配 helper ──
_USER_ID_RE = re.compile(r"[\w@.\-:/]+")


def _extract_user_id(path, prefix):
    """从 path 里提取 {user_id} 段。返回 (user_id, remainder) 或 None。"""
    if not path.startswith(prefix):
        return None
    rest = path[len(prefix):]
    parts = [p for p in rest.split("/") if p]
    if not parts:
        return None
    uid = parts[0]
    if not _USER_ID_RE.fullmatch(uid):
        return None
    return uid, "/".join(parts[1:])


def _ok(payload, status=200):
    return payload, status


def _err(msg, status=400):
    return {"error": str(msg)}, status


# ══════════════════════════════════════════════════════════════
# GET
# ══════════════════════════════════════════════════════════════
def handle_get(path, query=""):
    q = parse_qs(query) if query else {}
    q = {k: (v[0] if len(v) == 1 else v) for k, v in q.items()}
    try:
        pa = _pa()
    except Exception as e:
        return _err(f"personal_agent 模块不可用: {e}", 500)

    # ── Stats ──
    if path == "/api/v1/personal-agents/stats":
        return _ok(pa._export_public_state())

    # ── List users ──
    if path == "/api/v1/personal-agents/users":
        return _ok({"users": pa.list_users()})

    # ── User state / instances / tickets / actions / disputes / budget ──
    m = _extract_user_id(path, "/api/v1/personal-agents/users/")
    if m:
        uid, rest = m
        try:
            if rest == "":
                return _ok(pa.get_user_state(uid))
            if rest == "agent-instances":
                st = pa.get_user_state(uid)
                return _ok({"instances": st.get("agent_instances", [])})
            if rest == "tickets":
                # 返回所有 ticket（简化：通过 user_state）
                st = pa.get_user_state(uid)
                return _ok({"active_tickets": st.get("active_tickets", 0),
                            "tickets_total": st.get("tickets_total", 0)})
            if rest == "actions/verify":
                return _ok(pa.verify_action_chain(uid))
            if rest.startswith("actions/"):
                parts = rest.split("/")
                if len(parts) == 2 and parts[1].isdigit():
                    seq = int(parts[1])
                    r = pa.get_action_receipt(uid, seq)
                    if "found" in r and not r.get("found"):
                        return _err("action record 不存在", 404)
                    return _ok(r)
                return _err("路径不匹配: /actions/{seq}", 400)
            if rest == "disputes":
                status = q.get("status")
                return _ok({"disputes": pa.get_disputes(uid, status=status)})
            if rest == "budget":
                cur = q.get("currency", "CNY")
                return _ok(pa.get_budget_policy(uid, cur))
            if rest == "budget/usage":
                cur = q.get("currency", "CNY")
                return _ok(pa.budget_usage(uid, cur))
            return _err("路径不匹配", 404)
        except ValueError as e:
            return _err(str(e), 400)
        except Exception as e:
            return _err(f"server error: {e}", 500)

    # ── 平台注册表（v4.8.1+）──
    if path.startswith("/api/v1/platforms"):
        try:
            from eco import platform_registry as pr
        except Exception as e:
            return _err(f"platform_registry 不可用: {e}", 500)

        if path == "/api/v1/platforms":
            plist = pr.list_platforms(
                family=q.get("family"),
                cny_accessible=q.get("cny_accessible"),
                access_path=q.get("access_path"),
                includes_gaps=q.get("include_gaps") == "1",
            )
            return _ok({"platforms": plist, "stats": pr.stats()})

        if path == "/api/v1/platforms/stats":
            return _ok(pr.stats())

        if path == "/api/v1/platforms/gap-matrix":
            return _ok({"matrix": pr.governance_gap_matrix()})

        # /api/v1/platforms/{id}
        parts = path.split("/")
        if len(parts) == 5 and parts[1] == "api" and parts[2] == "v1" and parts[3] == "platforms":
            pid = parts[4]
            p = pr.get_platform(pid)
            if not p:
                return _err("platform 不存在", 404)
            return _ok(p)

        return _err("路径不匹配", 404)

    return _err("not found", 404)


# ══════════════════════════════════════════════════════════════
# POST
# ══════════════════════════════════════════════════════════════
def handle_post(path, data):
    data = data or {}
    try:
        pa = _pa()
    except Exception as e:
        return _err(f"personal_agent 模块不可用: {e}", 500)

    # ── Create / get PAI DID ──
    if path == "/api/v1/personal-agents/users":
        uid = data.get("user_id")
        if not uid:
            return _err("user_id 必填", 400)
        try:
            r = pa.create_personal_did(uid,
                                        display_name=data.get("display_name"),
                                        email=data.get("email"))
            return _ok(r, 201 if "idempotent" not in r else 200)
        except ValueError as e:
            return _err(str(e), 400)

    # ── Register agent instance ──
    m = _extract_user_id(path, "/api/v1/personal-agents/users/")
    if m:
        uid, rest = m
        try:
            if rest == "agent-instances":
                inst = pa.register_agent_instance(
                    uid,
                    agent_name=data.get("agent_name"),
                    provider=data.get("provider"),
                    capabilities=data.get("capabilities"),
                    platform_hint=data.get("platform_hint"),
                    platform=data.get("platform"),
                    platform_tier=data.get("platform_tier"),
                )
                return _ok(inst, 201)

            if rest == "tickets":
                tk = pa.create_capability_ticket(
                    uid,
                    instance_id=data.get("instance_id"),
                    actions=data.get("actions"),
                    scope=data.get("scope"),
                    expires_in=data.get("expires_in", 3600),
                    reason=data.get("reason", ""),
                )
                return _ok(tk, 201)

            if rest.startswith("agent-instances/") and rest.endswith("/revoke"):
                parts = rest.split("/")
                if len(parts) == 3:
                    inst_id = parts[1]
                    r = pa.revoke_agent_instance(
                        uid, inst_id, reason=data.get("reason", ""))
                    if not r.get("success"):
                        return _err(r.get("reason", "revoke failed"), 404)
                    return _ok(r)
                return _err("路径不匹配", 400)

            if rest == "actions":
                r = pa.record_action(
                    uid,
                    action=data.get("action"),
                    payload=data.get("payload"),
                    instance_id=data.get("instance_id"),
                    ticket_id=data.get("ticket_id"),
                    verdict=data.get("verdict", "allow"),
                    actor_did=data.get("actor_did"),
                    note=data.get("note", ""),
                )
                return _ok(r, 201)

            if rest == "disputes":
                r = pa.file_dispute(
                    uid,
                    seq=data.get("seq"),
                    reason=data.get("reason", ""),
                    description=data.get("description", ""),
                )
                if not r.get("success"):
                    return _err(r.get("reason", "dispute failed"), 404)
                return _ok(r, 201)

            if rest == "connectors/vet":
                r = pa.vet_connector(uid, data.get("connector") or data)
                return _ok(r)

            if rest == "budget/policy":
                r = pa.set_budget_policy(
                    uid,
                    currency=data.get("currency", "CNY"),
                    per_tx=data.get("per_tx"),
                    daily=data.get("daily"),
                    weekly=data.get("weekly"),
                    monthly=data.get("monthly"),
                    note=data.get("note", ""),
                )
                if not r.get("success"):
                    return _err(r.get("error"), 400)
                return _ok(r)

            return _err("路径不匹配", 404)
        except ValueError as e:
            return _err(str(e), 400)
        except Exception as e:
            return _err(f"server error: {e}", 500)

    # ── Budget 全局端点 ──
    if path == "/api/v1/personal-agents/budget/check":
        r = pa.check_budget_and_risk(
            user_id=data.get("user_id"),
            action=data.get("action"),
            amount=data.get("amount"),
            currency=data.get("currency", "CNY"),
            target_url=data.get("target_url"),
            category=data.get("category"),
            payload=data.get("payload"),
        )
        return _ok(r)

    if path == "/api/v1/personal-agents/budget/reserve":
        r = pa.reserve_budget(
            user_id=data.get("user_id"),
            order_id=data.get("order_id"),
            amount=data.get("amount"),
            currency=data.get("currency", "CNY"),
            target=data.get("target"),
            note=data.get("note", ""),
        )
        if not r.get("success"):
            return _err(r.get("error", "reserve failed"), 400)
        return _ok(r, 201)

    if path == "/api/v1/personal-agents/budget/commit":
        r = pa.commit_budget(
            reservation_id=data.get("reservation_id"),
            order_id=data.get("order_id"),
            user_id=data.get("user_id"),
            amount=data.get("amount"),
            currency=data.get("currency"),
        )
        if not r.get("success"):
            return _err(r.get("error", "commit failed"), 400)
        return _ok(r)

    if path == "/api/v1/personal-agents/budget/release":
        r = pa.release_budget(
            reservation_id=data.get("reservation_id"),
            order_id=data.get("order_id"),
        )
        if not r.get("success"):
            return _err(r.get("error", "release failed"), 404)
        return _ok(r)

    # ── Ticket 全局端点 ──
    if path == "/api/v1/personal-agents/tickets/verify":
        r = pa.verify_capability_ticket(data.get("ticket") or data)
        return _ok(r)

    if path == "/api/v1/personal-agents/tickets/consume":
        r = pa.check_and_consume_ticket(
            data.get("ticket") or {},
            action=data.get("action"),
            payload=data.get("payload") or {},
        )
        return _ok(r)

    # ── 平台推荐 (v4.8.1+) ──
    if path == "/api/v1/platforms/recommend":
        try:
            from eco import platform_registry as pr
        except Exception as e:
            return _err(f"platform_registry 不可用: {e}", 500)
        recs = pr.recommend_platforms(
            user_country=data.get("user_country", "CN"),
            capabilities_needed=data.get("capabilities_needed"),
            budget=data.get("budget", "free"),
            developer_level=data.get("developer_level", "beginner"),
            prefer_mcp=data.get("prefer_mcp", True),
        )
        return _ok({"recommendations": recs})

    # ── 运行时注册平台 (v4.8.1+) ──
    if path == "/api/v1/platforms/register":
        try:
            from eco import platform_registry as pr
        except Exception as e:
            return _err(f"platform_registry 不可用: {e}", 500)
        pid = data.get("id") or data.get("platform_id")
        if not pid:
            return _err("id 必填", 400)
        try:
            r = pr.register_platform(pid, **{
                k: v for k, v in data.items()
                if k not in ("id", "platform_id")
            })
            return _ok(r, 201)
        except ValueError as e:
            return _err(str(e), 400)

    return _err("not found", 404)
