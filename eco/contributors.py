"""
eco/contributors.py — 规则贡献者激励系统（L4 社区飞轮 · R2 首批）

思路：aishield 的 235 条规则不是天上掉下来的，来自社区提案。
要让贡献持续，必须有可见的**贡献计量 + 等级 + 徽章**：
  - 提交规则 → 走 promote_rule shadow 门控 → 沉淀 → 加贡献分
  - 每条被"采纳并长期在库"的规则给提交者加分
  - 累计分升等（Contributor → Reviewer → Maintainer → Trustee）
  - 提供公开 API：贡献者主页、排行、贡献历史

等级门槛（示意，可配置）：
  Contributor  : 0+ 分（首次贡献）
  Reviewer     : 30+ 分（≥3 条规则沉淀）
  Maintainer   : 80+ 分（≥10 条规则沉淀）
  Trustee      : 200+ 分（≥25 条规则沉淀）

零依赖；数据文件在 api/data/contributors.json。
线程安全（RLock）。
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone, timedelta
from typing import Any

TZ = timezone(timedelta(hours=8))
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA = os.path.join(_BASE, "api", "data")
FILE = os.path.join(_DATA, "contributors.json")

_lock = threading.RLock()

# 等级门槛：分数阈值 + 至少沉淀的规则数
TIERS = [
    ("Contributor", 0,   1),
    ("Reviewer",    30,  3),
    ("Maintainer",  80,  10),
    ("Trustee",    200,  25),
]


def _now_iso() -> str:
    return datetime.now(TZ).isoformat()


def _tier_for(score: int, rules_matured: int) -> dict:
    current = TIERS[0]
    for name, thr_score, thr_rules in TIERS:
        if score >= thr_score and rules_matured >= thr_rules:
            current = (name, thr_score, thr_rules)
    next_tier = None
    for i, (name, _, _) in enumerate(TIERS):
        if (name, _, _) == current and i + 1 < len(TIERS):
            next_tier = TIERS[i + 1]
            break
    progress = {
        "score": score,
        "rules_matured": rules_matured,
        "tier_score_threshold": current[1],
        "tier_rules_threshold": current[2],
    }
    return {
        "tier": current[0],
        "next_tier": next_tier[0] if next_tier else None,
        "progress": progress,
    }


def _load() -> dict:
    if not os.path.exists(FILE):
        return {"version": 1, "contributors": {}}
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": 1, "contributors": {}}


def _save(doc: dict):
    os.makedirs(_DATA, exist_ok=True)
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE)


def _fingerprint(contributor_id: str, event_type: str, ts: str) -> str:
    payload = json.dumps(
        {"id": contributor_id, "t": event_type, "ts": ts},
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


# ══════════════════════════════════════════════
#  事件类型 → 加分规则
# ══════════════════════════════════════════════
EVENT_SCORES = {
    "rule_proposed":    2,    # 提交了新规则候选
    "rule_shadowed":    5,    # 规则通过 shadow 门控进入观察
    "rule_matured":   15,    # 规则从 shadow 晋升为 enforce（长期在库）
    "review_performed": 3,    # 对其他贡献者规则做了评审
    "bug_reported":     5,    # 报告了一条真实漏洞
    "docs_contributed": 4,    # 文档改进
}


def register_contributor(contributor_id: str, name: str = "", email: str = "",
                          github: str = "", bio: str = "") -> dict:
    """注册（或覆盖更新）一个贡献者。"""
    if not contributor_id:
        raise ValueError("contributor_id required")
    now = _now_iso()
    with _lock:
        doc = _load()
        rec = doc["contributors"].get(contributor_id, {})
        rec.setdefault("contributor_id", contributor_id)
        rec.setdefault("registered_at", now)
        rec["updated_at"] = now
        rec["name"] = name or rec.get("name", contributor_id)
        rec["email"] = email or rec.get("email", "")
        rec["github"] = github or rec.get("github", "")
        rec["bio"] = bio or rec.get("bio", "")
        rec.setdefault("score", 0)
        rec.setdefault("rules_matured", 0)
        rec.setdefault("events", [])
        doc["contributors"][contributor_id] = rec
        rec = dict(rec)
        rec["tier_info"] = _tier_for(rec["score"], rec["rules_matured"])
        _save(doc)
        return rec


def add_event(contributor_id: str, event_type: str, *,
              rule_id: str = "", rule_name: str = "",
              description: str = "", extra: dict = None) -> dict:
    """记录一次贡献事件并自动加分。

    Args:
        contributor_id: 贡献者 ID
        event_type:     EVENT_SCORES 中的键
        rule_id:        如规则相关，填规则 ID
        rule_name:      规则名称
        description:    简述
        extra:          任意附带元数据
    """
    if event_type not in EVENT_SCORES:
        raise ValueError(f"unknown event_type: {event_type}; must be one of {list(EVENT_SCORES)}")
    delta = EVENT_SCORES[event_type]
    now = _now_iso()
    with _lock:
        doc = _load()
        if contributor_id not in doc["contributors"]:
            # 首次事件自动建档
            doc["contributors"][contributor_id] = {
                "contributor_id": contributor_id,
                "name": contributor_id,
                "registered_at": now,
                "updated_at": now,
                "score": 0,
                "rules_matured": 0,
                "events": [],
            }
        rec = doc["contributors"][contributor_id]
        rec["score"] = int(rec.get("score", 0)) + delta
        if event_type == "rule_matured":
            rec["rules_matured"] = int(rec.get("rules_matured", 0)) + 1
        event = {
            "type": event_type,
            "delta": delta,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "description": description,
            "ts": now,
            "fingerprint": _fingerprint(contributor_id, event_type, now),
            "extra": extra or {},
        }
        rec.setdefault("events", []).append(event)
        rec["updated_at"] = now
        _save(doc)
        result = dict(rec)
        result["tier_info"] = _tier_for(result["score"], result["rules_matured"])
        return result


def get(contributor_id: str) -> dict | None:
    with _lock:
        rec = _load()["contributors"].get(contributor_id)
        if not rec:
            return None
        rec = dict(rec)
        rec["tier_info"] = _tier_for(rec.get("score", 0), rec.get("rules_matured", 0))
        return rec


def list_all(include_tier: bool = True, limit: int = 100) -> list:
    """全部贡献者，按分数降序。"""
    with _lock:
        doc = _load()
        rows = []
        for rec in doc["contributors"].values():
            row = dict(rec)
            if include_tier:
                row["tier_info"] = _tier_for(rec.get("score", 0), rec.get("rules_matured", 0))
            rows.append(row)
        rows.sort(key=lambda r: -r.get("score", 0))
        return rows[:limit]


def leaderboard(limit: int = 20) -> list:
    """贡献者排行榜（分数 + 等级 + 规则数）。"""
    with _lock:
        rows = []
        for rec in _load()["contributors"].values():
            score = rec.get("score", 0)
            matured = rec.get("rules_matured", 0)
            tier_info = _tier_for(score, matured)
            rows.append({
                "contributor_id": rec["contributor_id"],
                "name": rec.get("name", ""),
                "github": rec.get("github", ""),
                "score": score,
                "rules_matured": matured,
                "tier": tier_info["tier"],
                "next_tier": tier_info["next_tier"],
                "events_count": len(rec.get("events", [])),
                "last_contribution": rec.get("updated_at", ""),
            })
        rows.sort(key=lambda r: (-r["score"], -r["rules_matured"]))
        return rows[:limit]


def tier_summary() -> dict:
    """各等级贡献者数量分布。"""
    with _lock:
        counts = {t[0]: 0 for t in TIERS}
        for rec in _load()["contributors"].values():
            score = rec.get("score", 0)
            matured = rec.get("rules_matured", 0)
            tier = _tier_for(score, matured)["tier"]
            counts[tier] = counts.get(tier, 0) + 1
        return counts


# 内置种子：把 aishield 自家规则作者标进来，方便外部看到"贡献生态有活"
_SEED = [
    ("aishield-core", "AIShield Core Team", "AIShield",
     "https://github.com/lm203688/aishield", "AIShield 官方维护者"),
]


def seed_if_empty(force: bool = False) -> int:
    """注册示例贡献者（幂等）。"""
    if force:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "contributors": {}}, f)
    doc = _load()
    added = 0
    for cid, name, github, bio_url, bio in _SEED:
        if cid in doc["contributors"]:
            continue
        register_contributor(cid, name=name, github=github, bio=bio)
        # 模拟初始贡献
        add_event(cid, "rule_matured", rule_id="MCP01", rule_name="OWASP MCP Top 10 (MCP01)",
                   description="初始基线：235 条规则库的种子维护")
        add_event(cid, "rule_matured", rule_id="MCP05", rule_name="Prompt Injection (MCP05)",
                   description="初始基线：Prompt 注入规则族")
        add_event(cid, "rule_matured", rule_id="ASI01", rule_name="OWASP Agentic ASI01",
                   description="初始基线：ASI 规则族")
        added += 1
    return added


if __name__ == "__main__":
    seed_if_empty(force=True)
    print("── 贡献者等级分布 ──")
    for tier, count in tier_summary().items():
        print(f"  {tier:<12}  {count}")
    print("\n── 排行榜 ──")
    for r in leaderboard(limit=5):
        print(f"  {r['contributor_id']:<20}  score={r['score']:>3}  "
              f"rules={r['rules_matured']}  tier={r['tier']}")
    print("\n── 事件类型 → 加分 ──")
    for t, s in EVENT_SCORES.items():
        print(f"  {t:<20}  +{s}")
