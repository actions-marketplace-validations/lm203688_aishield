"""
eco/leaderboard.py — Public Trust Leaderboard（L1 差异化 · R2 首批）

思路：让"信任"从抽象分数变成**可排名、可对比、可分享**的公共产物。
这是 agent 生态活跃度最直观的锚点：
  - 消费方（编排器 / LLM 路由）查榜单选 agent
  - 生产者（agent 作者）看到自己排名、被激励提升
  - 中立信任服务的公开承诺（分数不是黑箱，任何人可查、可排序、可下载）

数据源（只读）：
  - api/data/certifications.json   — 认证记录（score / badge_level / risk_level）
  - api/data/agent_registry.json   — Agent 注册表（name / provider / capabilities）
  - api/data/specialist_registry.json — 专业域注册（domain）

聚合维度：
  1. top_by_score      : 全库分数降序 Top-N
  2. top_by_domain     : 8 专业域内各自 Top-N（legal / medical / ...）
  3. top_by_provider   : 每个 provider 的均值与最高分（组织级看板）
  4. snapshot          : 快照 JSON（供外部抓去渲染）

零依赖；只读聚合，不改底层数据。
线程安全（RLock）。
"""
from __future__ import annotations

import json
import os
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA = os.path.join(_BASE, "api", "data")
CERT_FILE = os.path.join(_DATA, "certifications.json")
REGISTRY_FILE = os.path.join(_DATA, "agent_registry.json")
SPECIALIST_FILE = os.path.join(_DATA, "specialist_registry.json")

_lock = threading.RLock()

BADGE_ORDER = {"none": 0, "bronze": 1, "silver": 2, "gold": 3, "platinum": 4}
RISK_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4, "safe": 4}

# 8 专业域（与 specialist_registry.DOMAINS 保持一致）
DOMAINS = ("legal", "medical", "finance", "education",
           "engineering", "design", "research", "civic")


def _load_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _certifications() -> dict:
    d = _load_json(CERT_FILE, {"certifications": {}})
    return d.get("certifications", {})


def _specialists() -> dict:
    d = _load_json(SPECIALIST_FILE, {"agents": {}})
    return d.get("agents", {})


def _providers_map() -> dict:
    """source_url -> provider 名称（从 agent_registry 反查）。"""
    d = _load_json(REGISTRY_FILE, {"agents": {}})
    agents = d.get("agents", {})
    providers = {}
    # agent_registry 里 url 字段可能对应 certifications 里的 source_url
    for _, a in agents.items():
        if isinstance(a, dict):
            url = a.get("url", "")
            name = a.get("provider") or a.get("name", "")
            if url:
                providers[url] = name
    return providers


def _domain_map() -> dict:
    """agent_id -> domain（从 specialist_registry 反查）。"""
    specialists = _specialists()
    result = {}
    for aid, rec in specialists.items():
        if isinstance(rec, dict) and rec.get("domain"):
            result[aid] = rec["domain"]
            # 也允许通过 url 匹配
            if rec.get("url"):
                result.setdefault(rec["url"], rec["domain"])
    return result


def _iter_certifications():
    for cert_id, rec in _certifications().items():
        if not isinstance(rec, dict):
            continue
        yield cert_id, rec


# ══════════════════════════════════════════════
# 聚合
# ══════════════════════════════════════════════
def top_by_score(limit: int = 20, min_score: int = 0) -> list:
    """全库分数降序 Top-N。"""
    with _lock:
        rows = []
        for cert_id, rec in _iter_certifications():
            score = rec.get("score")
            if score is None or score < min_score:
                continue
            rows.append({
                "cert_id": cert_id,
                "source_url": rec.get("source_url", ""),
                "name": rec.get("name", "") or os.path.basename(rec.get("source_url", "")),
                "score": score,
                "badge_level": rec.get("badge_level", "none"),
                "risk_level": rec.get("risk_level", ""),
                "findings_count": rec.get("findings_count", 0),
                "issued_at": rec.get("issued_at", ""),
            })
        rows.sort(key=lambda r: (-r["score"], r.get("risk_level", "")))
        return rows[:limit]


def top_by_domain(domain: str, limit: int = 10) -> list:
    """指定专业域内的分数降序 Top-N。"""
    if domain not in DOMAINS:
        raise ValueError(f"unknown domain: {domain}; must be one of {DOMAINS}")
    with _lock:
        dm = _domain_map()
        rows = []
        for cert_id, rec in _iter_certifications():
            url = rec.get("source_url", "")
            aid = rec.get("agent_id", "")
            # 用 url 或 agent_id 反查 domain
            dom = dm.get(url) or dm.get(aid)
            if dom != domain:
                continue
            score = rec.get("score") or 0
            rows.append({
                "cert_id": cert_id,
                "source_url": url,
                "agent_id": aid,
                "name": rec.get("name", "") or os.path.basename(url),
                "score": score,
                "badge_level": rec.get("badge_level", "none"),
                "risk_level": rec.get("risk_level", ""),
                "domain": domain,
                "issued_at": rec.get("issued_at", ""),
            })
        rows.sort(key=lambda r: -r["score"])
        return rows[:limit]


def top_by_provider(limit: int = 20) -> list:
    """按 provider 聚合：mean_score / max_score / count。"""
    with _lock:
        pm = _providers_map()
        by_prov = defaultdict(lambda: {"scores": [], "max": 0, "certs": []})
        for cert_id, rec in _iter_certifications():
            url = rec.get("source_url", "")
            prov = pm.get(url) or "unknown"
            score = rec.get("score") or 0
            entry = by_prov[prov]
            entry["scores"].append(score)
            entry["max"] = max(entry["max"], score)
            entry["certs"].append(cert_id)
        rows = []
        for prov, agg in by_prov.items():
            scores = agg["scores"]
            rows.append({
                "provider": prov,
                "count": len(scores),
                "mean_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "max_score": agg["max"],
                "cert_ids": agg["certs"][:5],  # 只回传前 5 个避免过大
            })
        rows.sort(key=lambda r: (-r["mean_score"], -r["count"]))
        return rows[:limit]


def top_by_badge(badge: str = "gold", limit: int = 20) -> list:
    """按徽章等级过滤 Top-N。"""
    with _lock:
        rows = []
        for cert_id, rec in _iter_certifications():
            if rec.get("badge_level") != badge:
                continue
            rows.append({
                "cert_id": cert_id,
                "source_url": rec.get("source_url", ""),
                "name": rec.get("name", "") or os.path.basename(rec.get("source_url", "")),
                "score": rec.get("score", 0),
                "risk_level": rec.get("risk_level", ""),
                "issued_at": rec.get("issued_at", ""),
            })
        rows.sort(key=lambda r: -r["score"])
        return rows[:limit]


def snapshot() -> dict:
    """生成完整榜单快照（供外部抓去渲染 / 缓存）。"""
    with _lock:
        return {
            "schema": "https://aishield.tools/schema/trust-leaderboard/v1",
            "generated_at": datetime.now(TZ).isoformat(),
            "totals": {
                "certifications": len(_certifications()),
                "agents_registered": len(_specialists()),
            },
            "top_by_score": top_by_score(limit=20),
            "top_by_badge": {
                lvl: top_by_badge(lvl, limit=10)
                for lvl in ("platinum", "gold", "silver", "bronze")
            },
            "top_by_domain": {
                d: top_by_domain(d, limit=10) for d in DOMAINS
            },
            "top_by_provider": top_by_provider(limit=20),
        }


def export_snapshot(path: str | None = None) -> str:
    """写盘到指定路径（默认 api/data/leaderboard_snapshot.json）。"""
    p = path or os.path.join(_DATA, "leaderboard_snapshot.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    snap = snapshot()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    return p


if __name__ == "__main__":
    print("── Trust Leaderboard 快照 ──")
    top = top_by_score(limit=5)
    print(f"全库 Top 5: {len(top)}")
    for r in top:
        print(f"  #{r['score']:>3}  [{r['badge_level']:<7}] {r['name'][:40]}")
    print()
    for dom in ("engineering", "legal", "medical", "finance"):
        try:
            d = top_by_domain(dom, limit=3)
            print(f"{dom:>10}  Top {len(d)}: {[(r['name'][:20], r['score']) for r in d]}")
        except ValueError as e:
            print(f"  {e}")
    print()
    provs = top_by_provider(limit=5)
    print("Providers:", [(r['provider'], r['count'], r['mean_score']) for r in provs])
