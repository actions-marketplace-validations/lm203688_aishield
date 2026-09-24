"""
scripts/ship_gate.py — aishield ship：发布门禁 CLI（P1 L1 支柱）

一句话用法（本地开发时最常用的 3 条）：
    python scripts/ship_gate.py --file ./mcp-server/mcp.json --json
    python scripts/ship_gate.py --path ./eco/my_skill/ --json --fail-on-warn
    python scripts/ship_gate.py --path . --attest --emit-attestation att.json

行为：
    1. 用 scanner.engine.scan 扫描指定目标（文件或目录）
    2. 计算信任分（critical/high 各扣一档），映射 0-100
    3. 判定 ship/hold/break 三态：
         - ship :   trust_score >= 70  且 无 critical
         - hold :   有 high/medium 或分数在 40-69
         - break:  有 critical 或分数 < 40
    4. --attest 时同时生成 Trust Attestation v1（走 api/trust_api.py）
    5. --json 时输出机器可读 JSON；--emit-attestation <path> 时把 attestation 写盘
    6. --fail-on-warn 时若有 high+ finding 则退出码 2（CI 友好）

零依赖；作为 GitHub Action 后端时也能直接调用。
"""
from __future__ import annotations

import argparse
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


def _judge(score: int, counts: dict) -> dict:
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


def run_scan(target: str) -> dict:
    """对目标（文件或目录）跑扫描并汇总。"""
    from scanner.engine import scan
    if os.path.isdir(target):
        # 目录扫描：找所有 .json/.md/.yml/.yaml/.py/.js/.ts 文件
        exts = (".json", ".md", ".yml", ".yaml", ".py", ".js", ".ts", ".toml")
        targets = []
        for root, _, files in os.walk(target):
            # 跳过虚拟环境、node_modules、.git
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


def _make_attestation(scan_result: dict, verdict_info: dict) -> dict:
    """构造一份 Trust Attestation v1 结构的 dict（不落盘，由调用方决定）。"""
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
        "coverage": {
            "files_scanned": scan_result.get("files_scanned", 0),
            "findings_total": len(scan_result.get("findings", [])),
            "findings_by_severity": verdict_info["counts"],
        },
        "attestation": {
            "result": verdict_info["verdict"],
            "reason": verdict_info["reason"],
            "standard": "AIShield ecosystem gate v1",
        },
    }


def _human_report(scan_result: dict, verdict_info: dict) -> str:
    lines = []
    lines.append(f"  target        : {scan_result.get('target')}")
    lines.append(f"  files scanned : {scan_result.get('files_scanned', 0)}")
    lines.append(f"  trust score   : {verdict_info['score']}/100")
    counts = verdict_info["counts"]
    lines.append(f"  findings      : "
                 f"crit={counts['critical']} high={counts['high']} "
                 f"med={counts['medium']} low={counts['low']} info={counts['info']}")
    lines.append(f"  verdict       : {verdict_info['verdict'].upper()}  ({verdict_info['reason']})")
    return "\n".join(lines)


def _exit_code(verdict: str, findings: list, fail_on_warn: bool) -> int:
    if verdict == "break":
        return 1
    if verdict == "hold":
        if fail_on_warn:
            return 2
        return 0
    return 0  # ship


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AIShield ship gate — publish-time security check")
    target_group = ap.add_argument_group("target")
    target_group.add_argument("--path", help="文件或目录（默认）")
    target_group.add_argument("--file", help="单个文件（等价 --path）")
    io_group = ap.add_argument_group("output")
    io_group.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    io_group.add_argument("--emit-attestation", metavar="PATH",
                          help="生成 Trust Attestation 并写到 PATH")
    policy = ap.add_argument_group("policy")
    policy.add_argument("--fail-on-warn", action="store_true",
                        help="hold 时返回非零退出码（CI 友好）")
    policy.add_argument("--threshold", type=int, default=SCORE_SHIP,
                        help=f"信任分门槛（默认 {SCORE_SHIP}）")
    args = ap.parse_args(argv)

    target = args.file or args.path
    if not target:
        print("error: --path or --file required", file=sys.stderr)
        return 2

    result = run_scan(target)
    if "error" in result:
        print(result["error"], file=sys.stderr)
        return 2

    counts = _count_findings_by_severity(result["findings"])
    score = _compute_trust_score(result["findings"])
    verdict_info = _judge(score, counts)

    if args.json:
        out = {
            "tool": "aishield-ship-gate",
            "version": "1.0.0",
            "timestamp": _now_iso(),
            "target": result["target"],
            "files_scanned": result["files_scanned"],
            "trust_score": score,
            "verdict": verdict_info["verdict"],
            "reason": verdict_info["reason"],
            "counts": counts,
            "findings": result["findings"][:200],
        }
        if args.emit_attestation:
            att = _make_attestation(result, verdict_info)
            with open(args.emit_attestation, "w", encoding="utf-8") as f:
                json.dump(att, f, ensure_ascii=False, indent=2)
            out["attestation_path"] = args.emit_attestation
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("─ AIShield Ship Gate ─")
        print(_human_report(result, verdict_info))
        if args.emit_attestation:
            att = _make_attestation(result, verdict_info)
            with open(args.emit_attestation, "w", encoding="utf-8") as f:
                json.dump(att, f, ensure_ascii=False, indent=2)
            print(f"  attestation   : {args.emit_attestation}")

    return _exit_code(verdict_info["verdict"], result["findings"], args.fail_on_warn)


if __name__ == "__main__":
    sys.exit(main())
