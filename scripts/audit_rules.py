#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIShield · 规则基线审计 (Rule Baseline Audit)
=============================================

2026-09-18 的审计发现一个架构缺陷：**晋升闸门只审候选，不审基线。**

`scripts/promote_rule.py` 对每条雷达晋升候选做 schema / 良性误报 / 攻击命中
三轴校验，所以新规则质量是有保证的。但静态基线（208 条）与情报生成规则（8 条）
从未被同一标准审过——它们是逐条手写的历史产物。结果就是这次查出来的：

  * wget 管道规则 0 正样本（读作"死规则"，实为语料缺样本）
  * 3 条规则命中同一条正样本（finding 双倍/三倍计数，严重度重复计分）
  * 2 条 critical 级裸关键字规则，唯一正样本是叙述句而非祈使载荷
  * 10 处 critical 级误报落在防御文档的引用场景上

这些都能通过，因为没有任何 CI 检查问过"基线在良性语料上表现如何"。

本脚本把晋升闸门的标准下放到基线：**同一条 BENIGN_CORPUS，同一套判定语义。**

用法：
    python scripts/audit_rules.py            # 完整审计，critical/high 误报非零退出
    python scripts/audit_rules.py --json     # 机器可读输出
    python scripts/audit_rules.py --strict   # low/medium/info 误报也判失败
    python scripts/audit_rules.py --no-dead  # 跳过未覆盖雷达规则检查
    python scripts/audit_rules.py --no-dupes # 跳过正样本重叠检查

判定语义与 promote_rule.py 对齐：
    fail   -- 存在 critical/high 级良性误报（不可发布）
    warn   -- 存在未覆盖雷达规则或正样本重叠（可发布，但要清理）
    pass   -- 干净

退出码：0 = pass/warn（--strict 下含 fail），1 = fail，2 = 环境错误。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from rule_corpus import ATTACK_SAMPLES, BENIGN_CORPUS  # noqa: E402

# 样本放在 /skills/ 下喂样，使 is_agent_instruction_doc=True、analyze() 的
# is_doc 置为 False —— 这是最坏情况，也是引用场景误报真正危害所在的位置
# （防御类 SKILL.md）。文件名必须各不相同，否则 20 条样本会落进同一文件互相覆盖。
WORST_CASE_FILENAMES = ("skills/skill_%02d.md",)

# 引用场景子类：BENIGN_CORPUS 中专门测"话题提及 vs 祈使执行"的那几条。
# 与 promote_rule 的良性判定同源，这里单独标记出来便于报告层区分
# "规则特异性不足"与"引用语境未抑制"两类问题。
CITATION_MARKERS = re.compile(
    r"(?i)(detects?|catches?|blocks?|prevents?|classif|such as|patterns like|"
    r"fixture|sample|e\.g\.|canonical|threat model|docs\s*[:=])"
)


def _benign_kind(text: str) -> str:
    return "citation" if CITATION_MARKERS.search(text) else "general"


def _load_rule_stores() -> Dict[str, Dict[str, Tuple[str, str]]]:
    """返回 {存储名: {pattern: (desc, severity)}}。

    不用 ALL_RULES：它已经合并了情报生成与雷达晋升规则，用它会导致报告里
    "static" 标签下混进 [雷达]/[情报驱动] 条目 —— 标签说谎。这里逐个取原始
    规则集，标签与来源一一对应。
    """
    import importlib
    r = importlib.import_module("scanner.rules")
    names = ["SANDBOX_RULES", "ZH_PROMPT_INJECTION_RULES", "SKILL_EXTRA_RULES"]
    names += ["MCP%02d_RULES" % i for i in range(1, 11)]
    names += ["ASI%02d_RULES" % i for i in range(1, 11)]
    static = {}
    skill_extra = {}
    for name in names:
        store = getattr(r, name, None)
        if not isinstance(store, dict):
            continue
        bucket = skill_extra if name == "SKILL_EXTRA_RULES" else static
        for p, v in store.items():
            if isinstance(v, tuple) and len(v) == 2:
                bucket[p] = tuple(v)
    stores = {"static": static, "skill_extra": skill_extra}
    generated = getattr(r, "GENERATED_RULES", None)
    if isinstance(generated, dict) and generated:
        stores["generated"] = {
            p: tuple(v) for p, v in generated.items()
            if isinstance(v, tuple) and len(v) == 2}
    radar = getattr(r, "RADAR_RULES", None)
    if isinstance(radar, dict) and radar:
        stores["radar"] = {
            p: tuple(v) for p, v in radar.items()
            if isinstance(v, tuple) and len(v) == 2}
    return stores


def audit_false_positives(stores: Dict[str, Dict[str, Tuple[str, str]]]) -> Dict[str, Any]:
    """在 analyze() 层测良性误报，反映引用抑制生效后的真实行为。

    逐条样本单独成文件（每个样本一个文件名），避免规则在同一文件里重复计数
    干扰"这条规则是否误报"的判断。
    """
    import importlib
    rules_mod = importlib.import_module("scanner.rules")

    # 路径落在 /skills/ 下 → is_agent_instruction_doc=True → is_doc 不生效。
    # 这是最坏情况，也是引用场景误报真正危害所在的位置（防御类 skill 文档）。
    # 不能只用 SKILL.md 这个名字：20 条样本会全部落进同一个文件，互相覆盖。
    files = {"skills/skill_%02d.md" % i: t for i, t in enumerate(BENIGN_CORPUS)}
    by_file = {name: _benign_kind(text) for name, text in files.items()}
    result = rules_mod.analyze(files, "mcp")
    hits: List[Dict[str, Any]] = []
    for f in result["findings"]:
        hits.append({
            "rule_id": f.get("rule_id"),
            "severity": f.get("severity"),
            "description": f.get("description"),
            "evidence": f.get("evidence"),
            "file": f.get("file"),
            "citation_context": bool(f.get("citation_context")),
            "benign_kind": by_file.get(f.get("file", ""), "unknown"),
        })

    crit_high = [h for h in hits if h["severity"] in ("critical", "high")]
    noisy = [h for h in hits if h["severity"] in ("medium", "low", "info")]
    return {
        "benign_samples": len(BENIGN_CORPUS),
        "total_findings": len(hits),
        "critical_high": len(crit_high),
        "critical_high_details": crit_high,
        "noisy": len(noisy),
        "noisy_details": noisy,
    }


def _attack_hits(pattern: str) -> frozenset:
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return frozenset()
    return frozenset(i for i, s in enumerate(ATTACK_SAMPLES) if rx.search(s))


def audit_uncovered_radar_rules() -> List[Dict[str, Any]]:
    """零正样本的**雷达**规则。

    只审雷达规则，不审静态基线：ATTACK_SAMPLES 是按 prompt-injection / agent
    家族策展的，而静态基线覆盖密钥泄露、容器逃逸、SSRF、命令注入等 200 余条
    规则族，那个语料里天然没有它们的正样本。把"零命中"套在整个基线上会报出
    200+ 条"死规则"——那是语料的适用范围问题，不是规则的缺陷。

    语料权威的只有雷达晋升闸门：test_radar_effect.py 明确 pin 了"每条线上雷达
    规则至少命中一个 ATTACK_SAMPLES 样本"。这里对同一批规则复查同一标准。
    """
    import importlib
    r = importlib.import_module("scanner.rules")
    out = []
    for name in ("RADAR_RULES",):
        store = getattr(r, name, None)
        if not isinstance(store, dict):
            continue
        for pat, (desc, sev) in store.items():
            if not _attack_hits(pat):
                out.append({"store": name, "pattern": pat,
                            "description": desc, "severity": sev,
                            "attack_samples_hit": 0})
    return out


def audit_overlapping_rules(stores: Dict[str, Dict[str, Tuple[str, str]]]) -> List[Dict[str, Any]]:
    """同一正样本被 2+ 条规则命中的规则对。

    **这只是诊断信息，不是删除指令。** ATTACK_SAMPLES 只有 28 条，命中集相等
    远不能证明语义冗余：curl 管道执行规则要求 `| bash`，外部下载规则要求 `.sh`
    后缀，两者正则语义完全不同，却恰好都命中样本 11。把它们当"可删的重复"会
    诱导人删掉一条有效规则 —— 这是审计脚本自己制造假绿的反面（假删）。

    真正的处置取决于语义：语义子集才该合并（用合成变体穷举验证，见
    2026-09-18 的 3600 变体检查）；语义独立的重叠是纵深防御，同一行被多个控制
    命中是预期行为，代价是 finding 数量与风险分被重复累加。
    """
    hits = []
    for store_name, store in stores.items():
        for pat, (desc, sev) in store.items():
            h = _attack_hits(pat)
            if h:
                hits.append((store_name, pat, desc, sev, h))

    dupes: List[Dict[str, Any]] = []
    for i in range(len(hits)):
        for j in range(i + 1, len(hits)):
            overlap = hits[i][4] & hits[j][4]
            if not overlap:
                continue
            si, sj = hits[i][4], hits[j][4]
            if si == sj:
                rel = "equal"        # 命中集相同：语义大概率独立，见函数 docstring
            elif si >= sj:
                rel, a, b = "subset", hits[j], hits[i]
            elif sj >= si:
                rel, a, b = "subset", hits[i], hits[j]
            else:
                continue  # 部分重叠：两者各有独立贡献，不报
            if rel == "subset":
                entry = {
                    "relation": rel,
                    "narrower": {"store": a[0], "pattern": a[1],
                                 "description": a[2], "severity": a[3],
                                 "attack_samples": sorted(a[4])},
                    "wider": {"store": b[0], "pattern": b[1],
                              "description": b[2], "severity": b[3],
                              "attack_samples": sorted(b[4])},
                }
            else:
                entry = {
                    "relation": rel,
                    "rules": [{"store": h[0], "pattern": h[1], "description": h[2],
                               "severity": h[3], "attack_samples": sorted(h[4])}
                              for h in (hits[i], hits[j])],
                }
            dupes.append(entry)
    return dupes


def run_audit(strict: bool = False, check_dead: bool = True,
              check_dupes: bool = True) -> Dict[str, Any]:
    stores = _load_rule_stores()
    fp = audit_false_positives(stores)
    uncovered_radar = audit_uncovered_radar_rules() if check_dead else []
    dupes = audit_overlapping_rules(stores) if check_dupes else []

    verdict = "pass"
    if fp["critical_high"]:
        verdict = "fail"
    elif strict and fp["noisy"]:
        verdict = "fail"
    elif uncovered_radar or dupes:
        verdict = "warn"

    return {
        "verdict": verdict,
        "rules_audited": sum(len(s) for s in stores.values()),
        "benign_samples": fp["benign_samples"],
        "attack_samples": len(ATTACK_SAMPLES),
        "false_positives": fp,
        "uncovered_radar_rules": uncovered_radar,
        "duplicate_rules": dupes,
    }


def _print_report(a: Dict[str, Any]) -> None:
    v = a["verdict"]
    bar = "=" * 62
    print(bar)
    print("AIShield 规则基线审计  verdict = %s" % v.upper())
    print(bar)
    print("规则数: %-6d  良性样本: %-3d  攻击样本: %d"
          % (a["rules_audited"], a["benign_samples"], a["attack_samples"]))
    fp = a["false_positives"]
    print("\n[1] 良性语料误报（analyze() 层，含引用上下文抑制）")
    print("    findings: %d  |  critical/high: %d  |  medium/low/info: %d"
          % (fp["total_findings"], fp["critical_high"], fp["noisy"]))
    for h in fp["critical_high_details"]:
        print("    [!! %s] %-12s %s" % (h["severity"], h["rule_id"] or "-",
                                        (h["description"] or "")[:44]))
        print("         evidence: %s" % (h["evidence"] or "")[:60])
    if fp["critical_high"]:
        print("    -> 不可发布：良性语料上的 critical/high 级误报比没有规则更糟")
    for h in fp["noisy_details"]:
        # description 已自带 analyze() 加的 "(引用上下文)" 标记，
        # 这里不再重复拼接。
        print("    [%-8s] %-12s %s" % (h["severity"], h["rule_id"] or "-",
                                       (h["description"] or "")[:52]))

    print("\n[2] 未被覆盖的雷达规则（ATTACK_SAMPLES 零命中：%d 条）"
          % len(a["uncovered_radar_rules"]))
    for d in a["uncovered_radar_rules"]:
        print("    [%-8s] %-14s %s" % (d["severity"], d["store"],
                                       d["description"][:44]))
        print("         %s" % d["pattern"][:64])
    if a["uncovered_radar_rules"]:
        print("    -> 雷达晋升闸门要求每条线上规则至少命中一个正样本；"
              "规则无效就删，语料缺口就补样本")

    print("\n[3] 正样本重叠（同一 ATTACK_SAMPLE 被 2+ 条规则命中：%d 组）"
          % len(a["duplicate_rules"]))
    for d in a["duplicate_rules"]:
        if d["relation"] == "subset":
            n, w = d["narrower"], d["wider"]
            print("    子集 %-14s %-8s %s" % (n["store"], n["severity"], n["description"][:36]))
            print("    超集 %-14s %-8s %s" % (w["store"], w["severity"], w["description"][:36]))
            print("         共享正样本: %s  <- 疑似可合并，须先做语义验证" % n["attack_samples"])
        else:
            print("    等集 命中集相同（语义大概率独立，不是可删的重复）")
            for rule in d["rules"]:
                print("         %-14s %-8s %s" % (rule["store"], rule["severity"],
                                                  rule["description"][:34]))
            print("         共享正样本: %s" % d["rules"][0]["attack_samples"])
    if a["duplicate_rules"]:
        print("    -> 代价是 finding 与风险分被重复累加；只有'子集'且语义验证通过才该合并")
    print(bar)


def main() -> int:
    ap = argparse.ArgumentParser(description="AIShield 规则基线审计")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非可读报告")
    ap.add_argument("--strict", action="store_true",
                    help="medium/low/info 级误报也判失败")
    ap.add_argument("--no-dead", action="store_true", help="跳过死规则检查")
    ap.add_argument("--no-dupes", action="store_true", help="跳过重复规则检查")
    args = ap.parse_args()

    try:
        a = run_audit(strict=args.strict, check_dead=not args.no_dead,
                      check_dupes=not args.no_dupes)
    except Exception as exc:  # 环境错误与判定失败必须分开，否则 CI 会把导入失败当绿灯
        print("审计环境错误：%s" % exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(a, ensure_ascii=False, indent=2))
    else:
        _print_report(a)

    return 1 if a["verdict"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
