"""
eco/trust_score.py — 统一信任分（0-100）

把分散的信号（安全扫描、持续鉴证、信誉、责任链完整性）合成为单一可机读、可排序的
信任分，供 discovery 排序、LLM 路由、平台徽章统一使用。

加权模型（R1 基线，后续可校准）：
  - 安全扫描分 (40%): scanner.engine 的 overall_score（0-100）
  - 持续鉴证   (25%): eco.attestation 的 continuously_verified + 证据链长度
  - 信誉分     (20%): 平台累计 reputation_score（0-100）
  - 责任链     (15%): 多 agent 协作时的链完整性与深度

设计为纯函数：输入缺失时给出保守默认，绝不抛异常。
"""
from __future__ import annotations


def _clamp(v, lo=0, hi=100):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, v))


def compute_trust_score(
    scan: dict | None = None,
    attestation: dict | None = None,
    reputation: int | float | None = None,
    chain: dict | None = None,
) -> dict:
    """合成信任分。

    Args:
        scan:        {"overall_score": 0-100, "risk_level": "low|medium|high|critical"}
        attestation: {"subscribed": bool, "continuously_verified": bool, "evidence_entries": int}
        reputation:  平台信誉分 0-100（None 时按 50 默认值，但权重计入「未知」惩罚）
        chain:       {"integrity": bool, "depth": int}  多 agent 责任链
    """
    # 安全扫描分
    scan_score = _clamp((scan or {}).get("overall_score", 0))
    risk = (scan or {}).get("risk_level", "")
    if risk in ("critical", "high"):
        scan_score *= 0.6  # 高危直接打折

    # 持续鉴证
    att = attestation or {}
    if att.get("continuously_verified"):
        att_score = 100
    elif att.get("subscribed"):
        att_score = 55  # 已订阅但未通过连续验证
    else:
        att_score = 30  # 一次性快照
    entries = int(att.get("evidence_entries", 0) or 0)
    att_score = min(100, att_score + min(entries, 10) * 1.5)  # 证据越多越稳

    # 信誉分
    rep_unknown = reputation is None
    rep_score = _clamp(50 if rep_unknown else reputation)

    # 责任链
    ch = chain or {}
    if ch:
        chain_ok = bool(ch.get("integrity", True))
        depth = int(ch.get("depth", 1) or 1)
        chain_score = 100 if chain_ok else 20
        chain_score = min(100, chain_score + min(depth, 5) * 2)
    else:
        chain_score = 100  # 单 agent 无链，不扣分

    weights = {"scan": 0.40, "att": 0.25, "rep": 0.20, "chain": 0.15}
    score = (
        scan_score * weights["scan"]
        + att_score * weights["att"]
        + rep_score * weights["rep"]
        + chain_score * weights["chain"]
    )
    # 信誉未知时整体轻微惩罚（避免无历史 agent 虚高）
    if rep_unknown:
        score *= 0.92

    score = round(_clamp(score), 1)

    if score >= 90:
        level = "gold"
    elif score >= 80:
        level = "silver"
    elif score >= 70:
        level = "bronze"
    else:
        level = "none"

    return {
        "score": score,
        "level": level,
        "components": {
            "scan": round(scan_score, 1),
            "attestation": round(att_score, 1),
            "reputation": round(rep_score, 1),
            "responsibility_chain": round(chain_score, 1),
        },
        "weights": weights,
        "reputation_unknown": rep_unknown,
    }


if __name__ == "__main__":
    r = compute_trust_score(
        scan={"overall_score": 92, "risk_level": "low"},
        attestation={"subscribed": True, "continuously_verified": True, "evidence_entries": 7},
        reputation=85,
    )
    print("高可信 agent:", r["score"], r["level"])
    r2 = compute_trust_score(scan={"overall_score": 95})
    print("仅扫描、无鉴证:", r2["score"], r2["level"])
    r3 = compute_trust_score(
        scan={"overall_score": 40, "risk_level": "high"},
        attestation={"subscribed": False},
        reputation=10,
    )
    print("高危低信誉:", r3["score"], r3["level"])
