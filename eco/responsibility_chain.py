"""
eco/responsibility_chain.py — 多 Agent 责任链（硬骨头 #1：多 agent 责任归属）

问题：agent 编排里一个任务常由多个子 agent 级联完成。出事时（错误输出 / 越权 / 数据泄露）
很难定位「是谁、在哪个环节、因为什么输入」引入问题。CA AB 316 已取消"AI did it"辩护，
责任必须可追溯。

对策：把每次 agent 调用抽象为链上一条「证据」，前后用哈希链接（类似区块链的链式存证）：
    entry[i].prev_hash = hash(entry[i-1])
    entry[i].hash      = hash(canonical(entry[i]))
从而：
  - 任何一条被篡改都能被 verify() 检出；
  - 给定某个「问题输出」的 hash，trace() 能反查完整调用链，root_cause() 定位首因。

R4-深化（2026-09-24）新增能力：
  - hmac_key: 可选 HMAC 密钥；提供时用 HMAC-SHA256 链式签名（防内部记录者篡改），
    None 时退化为纯 SHA-256（保持向后兼容）
  - state_machine: 状态机字段 state/round，支持 inconclusive→proposed→verified 双轮复测
  - proposal_binding: proposal_id/approval_id 字段，实现 proposal-bound approval
  - to_evidence_bundle: 迁移为 eco.evidence_bundle.EvidenceBundle

线程安全；零依赖；可序列化导出供审计。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import threading
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
GENESIS_HASH = "0" * 64
SCHEMA_VERSION = "responsibility-chain/1.1"  # 1.0 → 1.1 加了 hmac/state/proposal 支持
_lock = threading.RLock()

# 状态机（对齐 evidence_bundle 的双轮独立复测）
VALID_STATES = (
    "pending", "proposed", "approved", "executing", "executed",
    "observing", "inconclusive", "verified", "failed", "rolled_back",
    "archived", "rejected",
)


def _now_iso():
    return datetime.now(TZ).isoformat()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _hash(obj, hmac_key: bytes | None = None) -> str:
    payload = _canonical(obj).encode("utf-8")
    if hmac_key:
        return hmac.new(hmac_key, payload, hashlib.sha256).hexdigest()
    return hashlib.sha256(payload).hexdigest()


def _ref(value) -> str | None:
    """把输入/输出归一为引用哈希（接受原始值或已是 hash 的字符串）。"""
    if value is None:
        return None
    if isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value):
        return value
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _normalize_key(secret: str | bytes | None) -> bytes | None:
    """把字符串 secret 归一为 HMAC key（SHA-256(secret) 保证等长）。"""
    if not secret:
        return None
    if isinstance(secret, bytes):
        return hashlib.sha256(secret).hexdigest().encode("utf-8")
    return hashlib.sha256(secret.encode("utf-8")).hexdigest().encode("utf-8")


class ResponsibilityChain:
    """链式责任存证。"""

    def __init__(self, chain_id=None, hmac_key: str | bytes | None = None):
        self.chain_id = chain_id or f"chain-{hashlib.sha256(_now_iso().encode()).hexdigest()[:12]}"
        self.entries: list[dict] = []
        self._head = GENESIS_HASH
        self._hmac_key = _normalize_key(hmac_key)
        self.schema_version = SCHEMA_VERSION

    @property
    def hmac_enabled(self) -> bool:
        return self._hmac_key is not None

    # ── 记录 ──
    def record(self, *, agent_id: str, action: str, parent_seq: int | None = None,
               input_ref=None, output_ref=None, meta: dict | None = None,
               state: str = "pending", round_no: int = 1,
               proposal_id: str | None = None,
               approval_id: str | None = None,
               ttp: str | None = None) -> dict:
        """追加一条调用证据。

        新增参数（R4-深化）：
            state:       当前状态（pending/proposed/approved/...）
            round_no:    复测轮次（1=首轮，2=双轮）
            proposal_id: 关联的 proposal id
            approval_id: 关联的 approval id
            ttp:         TTP 标签（映射到 ATT&CK，见 evidence_bundle.ATTACK_TTP_MAP）
        """
        if state not in VALID_STATES:
            raise ValueError(f"invalid state {state!r}; must be one of {VALID_STATES}")
        if round_no not in (1, 2):
            raise ValueError(f"round_no must be 1 or 2, got {round_no}")
        with _lock:
            seq = len(self.entries) + 1
            entry = {
                "seq": seq,
                "agent_id": agent_id,
                "action": action,
                "parent_seq": parent_seq,
                "input_ref": _ref(input_ref),
                "output_ref": _ref(output_ref),
                "meta": meta or {},
                "ts": _now_iso(),
                "prev_hash": self._head,
                "state": state,
                "round": round_no,
                "proposal_id": proposal_id,
                "approval_id": approval_id,
                "ttp": ttp,
                "schema": SCHEMA_VERSION,
            }
            signing_input = {k: v for k, v in entry.items() if k != "hash"}
            entry["hash"] = _hash(signing_input, self._hmac_key)
            self.entries.append(entry)
            self._head = entry["hash"]
            return dict(entry)

    # ── 校验 ──
    def verify(self) -> dict:
        """校验整条链完整性。"""
        with _lock:
            prev = GENESIS_HASH
            for i, e in enumerate(self.entries):
                if e.get("prev_hash") != prev:
                    return {"valid": False, "broken_at": i + 1,
                            "reason": "prev_hash 不匹配",
                            "expected": prev, "got": e.get("prev_hash")}
                signing_input = {k: v for k, v in e.items() if k != "hash"}
                expected = _hash(signing_input, self._hmac_key)
                if not hmac.compare_digest(expected, e.get("hash", "")):
                    return {"valid": False, "broken_at": i + 1,
                            "reason": "记录被篡改"}
                prev = e["hash"]
            return {"valid": True, "entries": len(self.entries),
                    "head_hash": prev, "hmac": self.hmac_enabled,
                    "schema": SCHEMA_VERSION}

    # ── 溯源 ──
    def trace(self, output_ref) -> list:
        """反查：某个输出 hash 出现在哪一步，并回溯其全部祖先（调用链）。"""
        target = _ref(output_ref)
        if target is None:
            return []
        with _lock:
            idx_by_seq = {e["seq"]: e for e in self.entries}
            leaves = [e for e in self.entries if e.get("output_ref") == target]
            if not leaves:
                return []
            path = []
            seen = set()
            for leaf in leaves:
                cur = leaf
                while cur and cur["seq"] not in seen:
                    seen.add(cur["seq"])
                    path.append(cur)
                    p = cur.get("parent_seq")
                    cur = idx_by_seq.get(p) if p else None
            path.sort(key=lambda e: e["seq"])
            return path

    def root_cause(self, output_ref):
        """定位首因：返回问题输出所在调用链的根步骤。"""
        chain = self.trace(output_ref)
        return chain[0] if chain else None

    def find_by_state(self, state: str) -> list:
        """按状态查询（例如找所有 inconclusive 的条目，等待 re-proposal）。"""
        return [e for e in self.entries if e.get("state") == state]

    def find_by_proposal(self, proposal_id: str) -> list:
        """按 proposal 查询（proposal-bound 追踪）。"""
        return [e for e in self.entries if e.get("proposal_id") == proposal_id]

    # ── 导出 ──
    def export(self) -> dict:
        with _lock:
            return {
                "schema": SCHEMA_VERSION,
                "chain_id": self.chain_id,
                "entries": list(self.entries),
                "head_hash": self._head,
                "hmac": self.hmac_enabled,
                "verified": self.verify()["valid"],
                "stats": self.stats(),
            }

    def stats(self) -> dict:
        """统计链上各状态的条目数。"""
        counts = {}
        for e in self.entries:
            s = e.get("state", "pending")
            counts[s] = counts.get(s, 0) + 1
        return {"total": len(self.entries), "by_state": counts,
                "hmac": self.hmac_enabled, "depth": len(self.entries)}

    # ── 迁移：转 evidence_bundle ──
    def to_evidence_bundle(self, *, hmac_secret: str | None = None,
                           title: str = "", run_id: str | None = None):
        """把责任链迁移为 EvidenceBundle（R4-深化产物，见 eco.evidence_bundle）。

        用于：旧责任链数据可无损升级到新证据体系。
        """
        from eco import evidence_bundle as eb
        bundle = eb.EvidenceBundle(run_id=run_id, hmac_secret=hmac_secret,
                                   title=title or f"migrated from {self.chain_id}")
        for e in self.entries:
            payload = {
                "agent_id": e.get("agent_id"),
                "action": e.get("action"),
                "input_ref": e.get("input_ref"),
                "output_ref": e.get("output_ref"),
                "parent_seq": e.get("parent_seq"),
                "meta": e.get("meta", {}),
                "outcome": "verified" if e.get("state") == "verified"
                          else ("failed" if e.get("state") == "failed"
                                else "successful"),
            }
            evt_type = {
                "verified": "verification.result",
                "failed": "verification.result",
                "approved": "proposal.approve",
                "rejected": "proposal.reject",
                "proposed": "proposal.create",
                "rolled_back": "audit.rollback",
                "archived": "audit.record",
            }.get(e.get("state"), "audit.record")
            bundle.add_event(event_type=evt_type,
                             agent_id=e.get("agent_id", "unknown"),
                             action=e.get("action", "record"),
                             payload=payload,
                             outcome=payload["outcome"],
                             ttp=e.get("ttp"))
        return bundle

    def depth(self) -> int:
        return len(self.entries)


if __name__ == "__main__":
    import os, sys
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _base not in sys.path:
        sys.path.insert(0, _base)

    # 基础链（无 hmac，向后兼容）
    c = ResponsibilityChain()
    r1 = c.record(agent_id="planner", action="plan", input_ref="user:扫描X",
                  output_ref={"subtasks": ["scan", "report"]})
    r2 = c.record(agent_id="scanner", action="call_tool:scan", parent_seq=r1["seq"],
                  input_ref=r1["output_ref"], output_ref={"score": 30, "findings": ["RCE"]},
                  state="executed", ttp="supply_chain")
    r3 = c.record(agent_id="reporter", action="format", parent_seq=r2["seq"],
                  input_ref=r2["output_ref"], output_ref="report-md",
                  state="verified")
    print(f"[chain-v1.1] depth={c.depth()} verify={c.verify()['valid']} "
          f"hmac={c.hmac_enabled}")
    bad = r2["output_ref"]
    chain = c.trace(bad)
    print(f"  trace chain: {[e['agent_id'] for e in chain]}")
    print(f"  root cause: {c.root_cause(bad)['agent_id']}")
    # 篡改检测
    c.entries[1]["output_ref"] = {"score": 99}
    print(f"  tampered verify: {c.verify()['valid']}")
    # stats
    c2 = ResponsibilityChain()
    c2.record(agent_id="a", action="x", state="pending")
    c2.record(agent_id="b", action="y", state="verified")
    c2.record(agent_id="c", action="z", state="inconclusive")
    print(f"  stats: {c2.stats()['by_state']}")

    # HMAC 链
    c_hmac = ResponsibilityChain(hmac_key="aishield-dev-key")
    e1 = c_hmac.record(agent_id="a", action="x", state="approved",
                       proposal_id="prop-123", approval_id="appr-456")
    print(f"  hmac chain: depth={c_hmac.depth()} verify={c_hmac.verify()['valid']} "
          f"hmac={c_hmac.hmac_enabled}")
    # 转 evidence bundle
    from eco import evidence_bundle as eb
    b = c_hmac.to_evidence_bundle(hmac_secret="k", title="migrated")
    print(f"  migrated bundle: events={b.verify()['events']} "
          f"verify={b.verify()['valid']}")
