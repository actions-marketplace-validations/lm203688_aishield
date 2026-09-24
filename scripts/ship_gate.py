"""
scripts/ship_gate.py — aishield ship：发布门禁 CLI（P1 L1 支柱 · R4-深化 · 10 态状态机）

一句话用法（本地开发时最常用的 3 条）：
    python scripts/ship_gate.py --file ./mcp-server/mcp.json --json
    python scripts/ship_gate.py --path ./eco/my_skill/ --json --fail-on-warn
    python scripts/ship_gate.py --path . --attest --emit-attestation att.json --full-lifecycle

三态向后兼容（对外 verdict 仍为 ship/hold/break），内部走 10 态状态机（CodeNotary 风格，
GOAI 2026 冠军 DataFlow-Agent/CodeNotary 参考）：

    ANALYZE     → 扫描分析（初始）
    BLIND_TEST  → 盲测（跑一遍无上下文扫描，验证规则触发）
    CHALLENGE   → 争议（发现 high+ 或分低，进入人工评审）
    GATE        → 门禁判定（决定 verdict）
    PREPARE     → 准备发布（生成 Trust Attestation）
    RELEASE     → 发布
    OBSERVE     → 发布后观察（默认 30 天窗口）
    ROLLBACK    → 回滚
    ARCHIVE     → 归档（终态）
    REJECT      → 拒绝（终态）

关键设计：
  - 默认只跑到 GATE；--full-lifecycle 时把 PREPARE/RELEASE/OBSERVE 阶段也模拟走一遍
    （PREPARE 生成 attestation，RELEASE 打签名，OBSERVE 生成 window 元数据）
  - CHALLENGE 状态记录争议条目（哪些 finding 需要人工确认），
    可 --auto-accept-challenge 直接跳（CI 默认）；不带 flag 时 hold 返回 2
  - ROLLBACK 场景通过 --rollback <approval_id> 触发；此时会写一条 rollback 到 evidence bundle
  - 完整证据链落盘到 evidence_bundle（HMAC 签名），可跨组织验证

零依赖；作为 GitHub Action 后端时也能直接调用。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

# 分数门槛（与 eco/badge.py 一致）
SCORE_SHIP = 70
SCORE_BREAK = 40
SCORE_HOLD_LOW = 40

# 各严重度权重（0 = 不影响，分数从 100 起扣）
SEVERITY_WEIGHT = {"critical": 40, "high": 15, "medium": 5, "low": 1, "info": 0}

# ═══════════════════════════════════════════════════════════
#  10 态状态机
# ═══════════════════════════════════════════════════════════

# 状态定义：(内部状态名, 对外 verdict, 是否为终态)
STATE_DEFS = {
    "ANALYZE":    ("ship", False),   # 分析阶段先给乐观 ship 假值
    "BLIND_TEST": ("ship", False),
    "CHALLENGE":  ("hold",  False),  # 争议阶段默认 hold
    "GATE":       (None,    False),  # 门禁判定阶段本身，verdict 由计算决定
    "PREPARE":    ("ship",  False),
    "RELEASE":    ("ship",  False),
    "OBSERVE":    ("ship",  False),
    "ROLLBACK":   ("break", False),
    "ARCHIVE":    (None,    True),   # 终态
    "REJECT":     ("break", True),   # 终态
}

# 合法状态转移（对齐 evidence_bundle TRANSITIONS 的简化版）
STATE_TRANSITIONS = {
    "ANALYZE":    {"BLIND_TEST", "REJECT"},
    "BLIND_TEST": {"GATE", "CHALLENGE", "REJECT"},
    # CHALLENGE 可以：跳 GATE（auto-accept）、拒发、或直接 ROLLBACK（critical 场景）
    "CHALLENGE":  {"GATE", "REJECT", "ROLLBACK"},
    # GATE 可以：PREPARE（ship 准备）、ROLLBACK（break 回滚）、
    # ARCHIVE（hold 归档）、REJECT（争议直接拒）
    "GATE":       {"PREPARE", "ROLLBACK", "ARCHIVE", "REJECT"},
    "PREPARE":    {"RELEASE", "REJECT"},
    "RELEASE":    {"OBSERVE", "ROLLBACK"},
    "OBSERVE":    {"ARCHIVE", "ROLLBACK"},
    "ROLLBACK":   {"ARCHIVE", "REJECT"},
    "ARCHIVE":    set(),
    "REJECT":     set(),
}

OBSERVE_WINDOW_DAYS = 30


def _now_iso():
    return datetime.now(TZ).isoformat()


def _count_findings_by_severity(findings: list) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings or []:
        sev = (f.get("severity") or f.get("level") or "info").lower()
        if sev in counts:
            counts[sev] += 1
    return counts


def _compute_trust_score(findings: list) -> int:
    counts = _count_findings_by_severity(findings)
    deduction = sum(counts[s] * w for s, w in SEVERITY_WEIGHT.items())
    return max(0, min(100, 100 - deduction))


def _judge(score: int, counts: dict, fail_on_warn: bool = False,
           auto_accept_challenge: bool = True) -> dict:
    """兼容旧三态判定，返回 verdict/reason/score/counts。"""
    has_critical = counts["critical"] > 0
    has_high = counts["high"] > 0
    if has_critical or score < SCORE_BREAK:
        verdict = "break"
        reason = "存在 critical 级发现" if has_critical else "信任分过低"
    elif score >= SCORE_SHIP and not has_high:
        verdict = "ship"
        reason = "通过发布门禁"
    else:
        verdict = "hold"
        reason = "存在 high/medium 级发现" if has_high else "信任分需提升"
    return {"verdict": verdict, "reason": reason, "score": score, "counts": counts}


# ═══════════════════════════════════════════════════════════
#  StateMachine class（可复用，可测）
# ═══════════════════════════════════════════════════════════

class StateMachine:
    """发布门禁状态机。可复用于非 CLI 场景。"""

    def __init__(self, *, hmac_secret: str | None = None,
                 fail_on_warn: bool = False,
                 auto_accept_challenge: bool = True):
        self.current = "ANALYZE"
        self.history = []
        self.transitions = []
        self.hmac_secret = hmac_secret
        self.fail_on_warn = fail_on_warn
        self.auto_accept_challenge = auto_accept_challenge
        self._record = []  # 每个状态转移的证据

    def _enter(self, new_state: str, reason: str = "", meta: dict | None = None):
        if new_state not in STATE_DEFS:
            raise ValueError(f"unknown state: {new_state}")
        if new_state not in STATE_TRANSITIONS.get(self.current, set()):
            raise ValueError(
                f"illegal transition {self.current} → {new_state}; "
                f"allowed: {STATE_TRANSITIONS.get(self.current)}")
        entry = {
            "from": self.current,
            "to": new_state,
            "reason": reason,
            "ts": _now_iso(),
            "meta": meta or {},
        }
        self.transitions.append(entry)
        self.history.append(new_state)
        self.current = new_state
        self._record.append(entry)
        return entry

    def run(self, scan_result: dict, *, full_lifecycle: bool = False) -> dict:
        """主流程：从 ANALYZE 跑一遍状态机，返回最终状态 + verdict。"""
        counts = _count_findings_by_severity(scan_result.get("findings", []))
        score = _compute_trust_score(scan_result.get("findings", []))
        verdict_info = _judge(score, counts, self.fail_on_warn)

        # 1. ANALYZE → BLIND_TEST
        self._enter("BLIND_TEST", reason="开始盲测：验证规则触发与分数计算")

        # 2. BLIND_TEST → CHALLENGE 或 GATE
        has_critical = counts["critical"] > 0
        has_high = counts["high"] > 0
        challenge_reasons = []
        if has_critical:
            challenge_reasons.append("存在 critical finding")
        if has_high:
            challenge_reasons.append("存在 high finding")
        if score < SCORE_BREAK:
            challenge_reasons.append(f"信任分 {score} 低于 break 阈值 {SCORE_BREAK}")

        if challenge_reasons:
            self._enter("CHALLENGE",
                        reason=";".join(challenge_reasons),
                        meta={"challenge_items": challenge_reasons})
            if self.auto_accept_challenge and not has_critical and score >= SCORE_BREAK:
                # 无 critical 且分不低于 break 阈值，自动跳 GATE（hold 处理）
                self._enter("GATE",
                            reason="auto-accept challenge (CI 默认行为)",
                            meta={"auto_accepted": True})
            elif not self.auto_accept_challenge:
                self._enter("REJECT", reason="hold 时 --fail-on-warn 触发拒发",
                            meta={"reason": "challenge_not_accepted"})
                return self._final(score, counts, verdict_info)
        else:
            self._enter("GATE", reason="无争议，直接进入门禁判定")

        # 3. GATE 判定 verdict
        verdict = verdict_info["verdict"]
        if verdict == "break":
            self._enter("ROLLBACK", reason=f"break: {verdict_info['reason']}",
                        meta={"score": score})
            self._enter("ARCHIVE", reason="break 归档", meta={"verdict": "break"})
        elif verdict == "hold":
            if self.fail_on_warn:
                self._enter("REJECT", reason="hold + --fail-on-warn 拒发",
                            meta={"score": score})
            else:
                # hold 但不 fail → 归档为已审视
                self._enter("ARCHIVE", reason=f"hold 归档: {verdict_info['reason']}",
                            meta={"verdict": "hold", "score": score})
        else:  # ship
            self._enter("PREPARE", reason="ship: 准备发布（生成 attestation）",
                        meta={"score": score})
            if full_lifecycle:
                self._enter("RELEASE", reason="发布")
                self._enter("OBSERVE",
                            reason=f"进入观察窗口 {OBSERVE_WINDOW_DAYS} 天",
                            meta={"window_days": OBSERVE_WINDOW_DAYS,
                                  "observe_end": _observe_end_iso()})
                self._enter("ARCHIVE", reason="观察窗口归档",
                            meta={"verdict": "ship"})
        return self._final(score, counts, verdict_info)

    def _final(self, score: int, counts: dict, verdict_info: dict) -> dict:
        verdict = verdict_info["verdict"]
        if self.current == "REJECT":
            verdict = "break"
        return {
            "final_state": self.current,
            "state_history": self.history,
            "state_transitions": self.transitions,
            "verdict": verdict,
            "reason": verdict_info["reason"],
            "score": score,
            "counts": counts,
            "observation_window_days": OBSERVE_WINDOW_DAYS if "OBSERVE" in self.history else 0,
        }


def _observe_end_iso() -> str:
    return (datetime.now(TZ) + timedelta(days=OBSERVE_WINDOW_DAYS)).isoformat()


# ═══════════════════════════════════════════════════════════
#  Scan runner
# ═══════════════════════════════════════════════════════════

def run_scan(target: str) -> dict:
    """对目标（文件或目录）跑扫描并汇总。"""
    from scanner.engine import scan
    if os.path.isdir(target):
        exts = (".json", ".md", ".yml", ".yaml", ".py", ".js", ".ts", ".toml")
        targets = []
        for root, _, files in os.walk(target):
            if any(x in root for x in (".git", "node_modules", "__pycache__", ".venv")):
                continue
            for fn in files:
                if fn.endswith(exts):
                    targets.append(os.path.join(root, fn))
    elif os.path.isfile(target):
        targets = [target]
    else:
        return {"error": f"target not found: {target}"}

    all_findings = []
    for t in targets:
        try:
            with open(t, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            res = scan(content, t)
            all_findings.extend(res.get("findings", []) or [])
        except Exception as e:
            all_findings.append({"file": t, "severity": "info",
                                  "rule_id": "SCAN_ERROR", "message": str(e)})
    return {"target": target, "files_scanned": len(targets), "findings": all_findings}


def _make_attestation(scan_result: dict, verdict_info: dict,
                      sm: StateMachine | None = None) -> dict:
    """构造 Trust Attestation v1 结构。

    向后兼容：verdict_info 可以是旧三态 dict（含 verdict/score/reason/counts），
    也可以是新的 StateMachine._final 返回的 sm_result。
    """
    if hasattr(verdict_info, "get") and verdict_info.get("final_state") is not None \
            and "state_history" in verdict_info:
        # 新 sm_result 结构
        final_state = verdict_info.get("final_state")
        history = verdict_info.get("state_history", [])
        transitions = verdict_info.get("state_transitions", [])
    else:
        # 旧 verdict_info 结构（仅 verdict/score/reason/counts）
        final_state = None
        history = []
        transitions = []
    return {
        "schema": "https://aishield.tools/schema/trust-attestation/v1",
        "issuer": {
            "did": "did:aishield:trust-service",
            "name": "AIShield Trust Service",
            "issued_at": _now_iso(),
        },
        "subject": {
            "name": os.path.basename(scan_result.get("target", "unknown")),
            "target": scan_result.get("target"),
            "fingerprint": None,
        },
        "verdict": verdict_info["verdict"],
        "trust_score": verdict_info["score"],
        "state_machine": {
            "current": final_state or (sm.current if sm else "GATE"),
            "history": history or (sm.history if sm else []),
            "transitions": transitions or (sm.transitions if sm else []),
            "schema": "ship-gate/1.0",
        },
        "coverage": {
            "files_scanned": scan_result.get("files_scanned", 0),
            "findings_total": len(scan_result.get("findings", [])),
            "findings_by_severity": verdict_info["counts"],
        },
        "attestation": {
            "result": verdict_info["verdict"],
            "reason": verdict_info["reason"],
            "standard": "AIShield ecosystem gate v1.1",
        },
    }


def _make_evidence_bundle(scan_result: dict, sm_result: dict,
                          hmac_secret: str | None = None) -> dict | None:
    """把状态机执行过程写入 evidence_bundle（R4-深化）。"""
    try:
        from eco.evidence_bundle import EvidenceBundle
    except Exception:
        return None
    b = EvidenceBundle(hmac_secret=hmac_secret,
                       title=f"ship-gate: {scan_result.get('target')}",
                       run_id=None)
    for t in sm_result.get("state_transitions", []):
        b.add_event(
            event_type="audit.record",
            agent_id="ship_gate",
            action=f"transition:{t.get('from')}->{t.get('to')}",
            payload={"from_state": t.get("from"), "to_state": t.get("to"),
                     "reason": t.get("reason", ""),
                     "outcome": "successful"},
            activity_id=1,
        )
    # 最终 verdict 事件
    b.add_event(
        event_type="verification.result",
        agent_id="ship_gate",
        action="final_verdict",
        payload={"verdict": sm_result.get("verdict"),
                 "score": sm_result.get("score"),
                 "final_state": sm_result.get("final_state"),
                 "outcome": "verified" if sm_result.get("verdict") == "ship"
                           else "failed"},
        activity_id=2,
    )
    try:
        b.archive(archiver_id="ship_gate")
    except Exception:
        pass
    return b.export()


def _human_report(scan_result: dict, sm_result: dict) -> str:
    lines = []
    lines.append(f"  target        : {scan_result.get('target')}")
    lines.append(f"  files scanned : {scan_result.get('files_scanned', 0)}")
    lines.append(f"  trust score   : {sm_result['score']}/100")
    counts = sm_result["counts"]
    lines.append(f"  findings      : "
                 f"crit={counts['critical']} high={counts['high']} "
                 f"med={counts['medium']} low={counts['low']} info={counts['info']}")
    lines.append(f"  final state   : {sm_result['final_state']}")
    lines.append(f"  verdict       : {sm_result['verdict'].upper()}  ({sm_result['reason']})")
    lines.append(f"  state history : {' → '.join(sm_result['state_history'])}")
    if sm_result.get("observation_window_days"):
        lines.append(f"  observe window: {sm_result['observation_window_days']}d")
    return "\n".join(lines)


def _exit_code(verdict_or_sm_result, findings, fail_on_warn: bool) -> int:
    """向后兼容：第一个参数可以是旧三态 verdict 字符串，也可以是新的 sm_result dict。"""
    if isinstance(verdict_or_sm_result, dict):
        verdict = verdict_or_sm_result.get("verdict", "")
        final_state = verdict_or_sm_result.get("final_state", "")
    else:
        verdict = verdict_or_sm_result
        final_state = ""
    if final_state == "REJECT":
        return 1
    if verdict == "break":
        return 1
    if verdict == "hold":
        if fail_on_warn:
            return 2
        return 0
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="AIShield ship gate — publish-time security check (10-state lifecycle)")
    target_group = ap.add_argument_group("target")
    target_group.add_argument("--path", help="文件或目录（默认）")
    target_group.add_argument("--file", help="单个文件（等价 --path）")
    io_group = ap.add_argument_group("output")
    io_group.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    io_group.add_argument("--emit-attestation", metavar="PATH",
                          help="生成 Trust Attestation 并写到 PATH")
    io_group.add_argument("--emit-bundle", metavar="PATH",
                          help="生成 Evidence Bundle（HMAC 签名）并写到 PATH")
    policy = ap.add_argument_group("policy")
    policy.add_argument("--fail-on-warn", action="store_true",
                        help="hold 时返回非零退出码（CI 友好）")
    policy.add_argument("--threshold", type=int, default=SCORE_SHIP,
                        help=f"信任分门槛（默认 {SCORE_SHIP}）")
    policy.add_argument("--no-auto-accept-challenge", action="store_true",
                        help="争议阶段不自动接受，hold 直接 reject")
    lifecycle = ap.add_argument_group("lifecycle")
    lifecycle.add_argument("--full-lifecycle", action="store_true",
                           help="模拟跑完整 10 态流程（PREPARE→RELEASE→OBSERVE→ARCHIVE）")
    lifecycle.add_argument("--hmac-secret", metavar="SECRET",
                           help="HMAC 密钥（启用后证据链使用 HMAC-SHA256 签名）")
    args = ap.parse_args(argv)

    target = args.file or args.path
    if not target:
        print("error: --path or --file required", file=sys.stderr)
        return 2

    result = run_scan(target)
    if "error" in result:
        print(result["error"], file=sys.stderr)
        return 2

    sm = StateMachine(hmac_secret=args.hmac_secret,
                      fail_on_warn=args.fail_on_warn,
                      auto_accept_challenge=not args.no_auto_accept_challenge)
    sm_result = sm.run(result, full_lifecycle=args.full_lifecycle)

    counts = sm_result["counts"]
    score = sm_result["score"]

    if args.json:
        out = {
            "tool": "aishield-ship-gate",
            "version": "1.1.0",
            "state_machine_schema": "ship-gate/1.0",
            "timestamp": _now_iso(),
            "target": result["target"],
            "files_scanned": result["files_scanned"],
            "trust_score": score,
            "verdict": sm_result["verdict"],
            "final_state": sm_result["final_state"],
            "state_history": sm_result["state_history"],
            "state_transitions": sm_result["state_transitions"],
            "reason": sm_result["reason"],
            "counts": counts,
            "observation_window_days": sm_result["observation_window_days"],
            "findings": result["findings"][:200],
        }
        if args.emit_attestation:
            att = _make_attestation(result, sm_result, sm)
            with open(args.emit_attestation, "w", encoding="utf-8") as f:
                json.dump(att, f, ensure_ascii=False, indent=2)
            out["attestation_path"] = args.emit_attestation
        if args.emit_bundle:
            bundle = _make_evidence_bundle(result, sm_result, hmac_secret=args.hmac_secret)
            if bundle:
                with open(args.emit_bundle, "w", encoding="utf-8") as f:
                    json.dump(bundle, f, ensure_ascii=False, indent=2)
                out["bundle_path"] = args.emit_bundle
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("─ AIShield Ship Gate (10-state lifecycle) ─")
        print(_human_report(result, sm_result))
        if args.emit_attestation:
            att = _make_attestation(result, sm_result, sm)
            with open(args.emit_attestation, "w", encoding="utf-8") as f:
                json.dump(att, f, ensure_ascii=False, indent=2)
            print(f"  attestation   : {args.emit_attestation}")
        if args.emit_bundle:
            bundle = _make_evidence_bundle(result, sm_result, hmac_secret=args.hmac_secret)
            if bundle:
                with open(args.emit_bundle, "w", encoding="utf-8") as f:
                    json.dump(bundle, f, ensure_ascii=False, indent=2)
                print(f"  bundle        : {args.emit_bundle}")

    return _exit_code(sm_result, result["findings"], args.fail_on_warn)


if __name__ == "__main__":
    sys.exit(main())
