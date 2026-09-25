#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI 自扫描门禁 —— 把 self_scan.py 的结论收敛成一个"带分数的报告"。

为什么有这一层
--------------
`scripts/self_scan.py` 输出的是**发现清单**（totals / sources / stale_allowlist_entries），
没有总分。而 `.github/workflows/security-scan.yml` 的门禁要读一个 0-100 的分数并跟阈值比——
没有分数，门禁只能"数发现条数"，而"数条数"和"分数低于阈值"是两种不同的失败语义：
前者不知道严重程度，后者不知道发生了什么。

2026-08-05 的真实事故是：门禁读 `d.get('score', 0)`，而响应里根本没有 `score` 键，
于是门禁恒得 0 分、连红 17 次 / 48h，而被守护对象其实是健康的。
`tests/test_ci_contract.py::TestSecurityGateReadsRealKeys` 把这件事钉死了：
**门禁读的每一个键，都必须真实存在于它读的 JSON 里。**

所以这里产出的 summary 严格只用 API_SCORE_KEYS 里的键：
    score / overall_score / risk_level / badge_level / report
其余明细（发现清单、免杀统计、allowlist 版本）全部塞进 `report`，
不占用顶层——这样门禁永远不会静默取到默认值。

分数语义
--------
    overall_score  = 各源扫描器打分的文件数加权平均（0-100，扫描器自己的质量分）
    扣分            = 40 * 未登记阻断级发现数 + 15 * 腐烂 allowlist 条目数
    score          = clamp(overall_score - 扣分, 0, 100)

阈值 60 因此不是形式：当前干净态 score≈93；出现 1 条未登记阻断 → 93-40=53 < 60 立刻红。
（实测过，不是纸上推导。）

退出码契约（三档，全部让 CI 红，但语义不同）
--------
    0 = 干净：无未登记的阻断级发现，且 allowlist 没有腐烂
    1 = 真实信号：存在未登记的阻断级发现，必须处理
    2 = 门禁失效：allowlist 条目已腐烂（不再匹配任何实际发现），
      说明自指误报的豁免清单过期了，等于自扫描在静默放行——必须清理清单

    注：self_scan.py 的 docstring 声称有第 3 档但 main() 只实现到 exit 1；
    这一档是在本脚本里真正落地的。

不变量：只读文件，不执行任何扫描目标里的命令，不发起网络请求。
零第三方依赖：stdlib + scanner.* + scripts/verify_distribution.py。
用法：
    python scripts/ci_self_scan_gate.py                 # 人读报告 + 落盘两个文件
    python scripts/ci_self_scan_gate.py --out s.json    # 自定义 summary 路径
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
for p in (ROOT, SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)

import self_scan  # noqa: E402  (scripts/self_scan.py)

DEFAULT_OUT = os.path.join(ROOT, "self-scan-summary.json")
DEFAULT_COMMENT = os.path.join(ROOT, "self-scan-comment.md")

# 与 security-scan.yml 里的阈值保持同一量级：见 WORKFLOW_THRESHOLD。
# 若改动这里，务必同步改 workflow 里的 `if score < 60`，两者必须同向。
WORKFLOW_THRESHOLD = 60
BLOCKING_PENALTY = 40
STALE_PENALTY = 15


def _badge(score):
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _risk(score):
    if score >= 90:
        return "safe"
    if score >= 75:
        return "low"
    if score >= 60:
        return "medium"
    if score >= 40:
        return "high"
    return "critical"


def build_summary(summary):
    """把 self_scan.scan() 的结论折成一个带分数的报告。"""
    sources = summary["sources"]
    files_w = [r["files"] for r in sources]
    scores = [r["overall_score"] for r in sources if r["overall_score"] is not None]
    weights = [r["files"] for r in sources if r["overall_score"] is not None]

    if weights:
        overall = sum(s * w for s, w in zip(scores, weights)) / max(1, sum(weights))
    else:
        overall = 0.0
    overall = int(round(overall))

    blocking = int(summary["totals"]["blocking_unsuppressed"])
    stale = len(summary["stale_allowlist_entries"])
    deductions = blocking * BLOCKING_PENALTY + stale * STALE_PENALTY
    score = max(0, min(100, overall - deductions))

    return {
        "score": score,
        "overall_score": overall,
        "risk_level": _risk(score),
        "badge_level": _badge(score),
        "report": {
            "totals": summary["totals"],
            "sources": sources,
            "stale_allowlist_entries": summary["stale_allowlist_entries"],
            "allowlist_version": summary["allowlist_version"],
            "invariants": summary.get("invariants", {}),
            "deductions": {
                "blocking_findings": blocking,
                "blocking_penalty_each": BLOCKING_PENALTY,
                "stale_allowlist_entries": stale,
                "stale_penalty_each": STALE_PENALTY,
                "total": deductions,
            },
            "gate_threshold": WORKFLOW_THRESHOLD,
            "clean": blocking == 0 and stale == 0,
        },
    }


def exit_code(summary):
    """三档退出码：干净 / 真实信号 / 门禁失效。"""
    if summary["totals"]["blocking_unsuppressed"] > 0:
        return 1
    if summary["stale_allowlist_entries"]:
        return 2
    return 0


def render_text(gate):
    t = gate["report"]["totals"]
    d = gate["report"]["deductions"]
    lines = []
    lines.append("=== AIShield self-scan gate ===")
    lines.append("  overall_score (文件数加权): %d/100" % gate["overall_score"])
    lines.append("  - blocking x%d x %d      = -%d"
                 % (d["blocking_findings"], BLOCKING_PENALTY,
                    d["blocking_findings"] * BLOCKING_PENALTY))
    lines.append("  - stale    x%d x %d      = -%d"
                 % (d["stale_allowlist_entries"], STALE_PENALTY,
                    d["stale_allowlist_entries"] * STALE_PENALTY))
    lines.append("  score                 : %d/100 (risk=%s badge=%s)"
                 % (gate["score"], gate["risk_level"], gate["badge_level"]))
    lines.append("  findings=%d  suppressed=%d  blocking_unsuppressed=%d"
                 % (t["findings"], t["suppressed"], t["blocking_unsuppressed"]))
    lines.append("  sources scanned       : %d" % len(gate["report"]["sources"]))
    lines.append("  allowlist version     : %s" % gate["report"]["allowlist_version"])
    lines.append("  gate threshold        : score < %d => FAIL" % WORKFLOW_THRESHOLD)

    bad = [s for s in gate["report"]["sources"] if s["blocking_unsuppressed"]]
    if bad:
        lines.append("")
        lines.append("--- 未登记的阻断级发现（真实信号）---")
        for s in bad:
            for f in s["blocking_unsuppressed"]:
                lines.append("  [%s] %s -> %s"
                             % (f.get("severity"), s["source"],
                                f.get("rule_id") or f.get("rule")))
    if gate["report"]["stale_allowlist_entries"]:
        lines.append("")
        lines.append("--- 腐烂的 allowlist 条目（门禁失效，需清理）---")
        for k in gate["report"]["stale_allowlist_entries"][:20]:
            lines.append("  - %s" % k)
    return "\n".join(lines)


def render_comment(gate):
    """PR 评论。刻意写成静态 markdown，不依赖 workflow 里的 .get() 取值。"""
    rep = gate["report"]
    t = rep["totals"]
    d = rep["deductions"]
    bad = [(s["source"], f) for s in rep["sources"] for f in s["blocking_unsuppressed"]]
    ok = gate["report"]["clean"] and gate["score"] >= WORKFLOW_THRESHOLD

    lines = ["## AIShield Self-Scan", ""]
    lines.append("**Result**: %s | **Score**: %d/100 | **Risk**: %s"
                 % ("PASS" if ok else "FAIL", gate["score"], gate["risk_level"]))
    lines.append("")
    lines.append("| 项 | 值 |")
    lines.append("|----|----|")
    lines.append("| 扫描源 | %d |" % len(rep["sources"]))
    lines.append("| 全部发现 | %d |" % t["findings"])
    lines.append("| 自指误报（已消噪） | %d |" % t["suppressed"])
    lines.append("| 未登记阻断级 | %d |" % t["blocking_unsuppressed"])
    lines.append("| 腐烂 allowlist 条目 | %d |" % len(rep["stale_allowlist_entries"]))
    lines.append("| 免杀清单版本 | %s |" % rep["allowlist_version"])
    lines.append("")
    if bad:
        lines.append("### 未登记的阻断级发现（必须处理）")
        lines.append("")
        for src, f in bad:
            lines.append("- **%s** [%s] %s — %s"
                         % (src, f.get("severity"), f.get("rule_id") or f.get("rule"),
                            f.get("description") or f.get("type")))
        lines.append("")
    if rep["stale_allowlist_entries"]:
        lines.append("### 腐烂的 allowlist 条目（自扫描正在静默放行）")
        lines.append("")
        for k in rep["stale_allowlist_entries"]:
            lines.append("- `%s`" % k)
        lines.append("")
    lines.append("> 评分口径：各源扫描分文件数加权 = %d，扣 未登记阻断 x%d、"
                 "腐烂条目 x%d → %d/100。阈值 < %d 即失败。"
                 % (gate["overall_score"], BLOCKING_PENALTY, STALE_PENALTY,
                    gate["score"], WORKFLOW_THRESHOLD))
    lines.append("> 免杀清单：`distribution/self_reference_allowlist.json` v%s。"
                 % rep["allowlist_version"])
    lines.append("> 只读扫描：不执行被扫文件里的任何命令，不发起网络请求。")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="CI 自扫描门禁（把结论折成带分数的报告）")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="summary JSON 输出路径（门禁读它取 score）")
    parser.add_argument("--comment-out", default=DEFAULT_COMMENT,
                        help="PR 评论 markdown 输出路径")
    parser.add_argument("--quiet", action="store_true", help="不打印人读报告")
    args = parser.parse_args(argv)

    summary = self_scan.scan()
    gate = build_summary(summary)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, ensure_ascii=False, indent=2)
    with open(args.comment_out, "w", encoding="utf-8") as fh:
        fh.write(render_comment(gate))

    if not args.quiet:
        print(render_text(gate))

    rc = exit_code(summary)
    if rc != 0:
        print("[gate] exit %d" % rc, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
