#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIShield · Radar Rule Effect Measurement
========================================

Closes the *last* link of the Tech Radar loop:

    signal -> draft candidate -> promote -> [THIS] EFFECT

`scripts/promote_rule.py` takes a candidate from draft to live and writes it
to `data/radar_rules.json`. But a promoted rule is a hypothesis: nobody was
checking whether it actually *catches* anything, or whether it quietly fires on
benign input. A rule that never fires is dead weight; a rule that fires on
benign input is worse than none. This module measures both, deterministically,
and records the result for the meta-monitor (M9) to police.

Two axes are measured per promoted pattern:

  * catch (positive control)  -- does the regex match a labelled corpus of
    attack-shaped samples? A pattern derived from its own signal but unable to
    match any attack text is ineffective.
  * false_positive (negative control) -- does the regex match the same benign
    corpus the promotion gate uses? Re-checked after the fact, so a later
    corpus widening or rule edit cannot slip a misfiring rule past unnoticed.

Plus a real-world hit counter (`record_hits`) that any scan path may call to
increment per-pattern telemetry; it is preserved across re-evaluations.

Determinism note: catch/hit figures here are measured against a *fixed labelled
corpus*, not live traffic -- so they are reproducible in CI and cannot be
inflated by the scanner matching its own reports. Live hit counters are a bonus
layer carried in the same store.

Usage:
  python scripts/radar_effect.py            # evaluate + print report
  python scripts/radar_effect.py --report    # print last evaluation only
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

RADAR_RULES = os.path.join(ROOT, "data", "radar_rules.json")
EFFECT_FILE = os.path.join(ROOT, "data", "state", "radar_effect.json")

# 语料单一真源。此前 BENIGN_CORPUS 在本文件与 scripts/promote_rule.py 各存一份
# （互为"镜像"），两边扩宽时 CI 看不见另一边的漂移；ATTACK_SAMPLES 的覆盖率
# 断言也只查这一侧。现统一收口到 scripts/rule_corpus.py。
from rule_corpus import ATTACK_SAMPLES, BENIGN_CORPUS  # noqa: E402


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_effect():
    data = _load_json(EFFECT_FILE, {"version": 1, "rules": {}})
    if not isinstance(data, dict):
        data = {"version": 1, "rules": {}}
    data.setdefault("rules", {})
    return data


def save_effect(store):
    os.makedirs(os.path.dirname(EFFECT_FILE), exist_ok=True)
    with open(EFFECT_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def radar_rules():
    return _load_json(RADAR_RULES, {"rules": {}, "provenance": {}})


def record_hits(patterns):
    """Increment real-world hit counters. Safe to call with any iterable.

    Preserves the deterministic catch/fp fields; only bumps `hits`.
    """
    store = load_effect()
    rules = store.setdefault("rules", {})
    n = 0
    for pat in patterns or []:
        if not pat:
            continue
        rec = rules.setdefault(str(pat), {})
        rec["hits"] = int(rec.get("hits", 0) or 0) + 1
        rec["last_hit"] = _now()
        n += 1
    save_effect(store)
    return n


def evaluate(store=None, save=True):
    """Re-measure catch / false-positive for every promoted radar rule.

    Pass ``store`` (a full ``radar_rules.json``-shaped dict) to measure a
    *hypothetical* rule set without writing ``data/radar_rules.json`` — this is
    what ``promote_rule.py --shadow`` uses to preview a promotion transaction
    without mutating live state. Default (``store=None``) keeps the historical
    behaviour of reading the live file.
    """
    store = store if store is not None else radar_rules()
    rules = store.get("rules", {}) or {}
    prov = store.get("provenance", {}) or {}
    eff = load_effect()
    eff_rules = eff.setdefault("rules", {})
    now = _now()

    for pattern, val in rules.items():
        desc = val[0] if isinstance(val, (list, tuple)) and val else ""
        sev = val[1] if isinstance(val, (list, tuple)) and len(val) > 1 else ""
        rec = eff_rules.setdefault(pattern, {})
        rec.update({"description": desc, "severity": sev,
                    "hits": int(rec.get("hits", 0) or 0)})
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            rec.update({"catch": False, "false_positive": False,
                        "error": f"regex does not compile: {e}",
                        "evaluated_at": now})
            continue
        samples = [s for s in ATTACK_SAMPLES if compiled.search(s)]
        fp_sample = next((s for s in BENIGN_CORPUS if compiled.search(s)), None)
        rec.update({
            "catch": bool(samples),
            "catch_samples": len(samples),
            "false_positive": bool(fp_sample),
            "fp_sample": (fp_sample or "")[:80] or None,
            "signal_url": (prov.get(pattern, {}) or {}).get("signal_url", ""),
            "evaluated_at": now,
        })
        rec.pop("error", None)

    # drop effect entries for rules no longer live (kept honest)
    for pat in list(eff_rules):
        if pat not in rules:
            del eff_rules[pat]

    live = list(rules)
    eff["summary"] = {
        "promoted": len(live),
        "with_catch": sum(1 for p in live if eff_rules[p].get("catch")),
        "false_positives": sum(1 for p in live if eff_rules[p].get("false_positive")),
        "total_hits": sum(int(eff_rules[p].get("hits", 0) or 0) for p in live),
        "evaluated_at": now,
    }
    if save:
        save_effect(eff)
    return eff


def render(store):
    s = store.get("summary", {})
    lines = [f"雷达规则效果 @ {s.get('evaluated_at', '?')}"]
    lines.append(f"  已晋升 {s.get('promoted', 0)} 条 | 有命中 {s.get('with_catch', 0)} 条 | "
                 f"误报 {s.get('false_positives', 0)} 条 | 累计真实命中 {s.get('total_hits', 0)}")
    rules = store.get("rules", {})
    if not rules:
        lines.append("  （暂无已晋升雷达规则）")
        return "\n".join(lines)
    for pat, r in sorted(rules.items(),
                         key=lambda kv: (-int(kv[1].get("hits", 0) or 0),
                                         not kv[1].get("catch"))):
        flags = []
        flags.append("命中" if r.get("catch") else "零命中")
        if r.get("false_positive"):
            flags.append(f"⚠️误报:{r.get('fp_sample')}")
        lines.append(f"  [{r.get('severity', '?')}] {'/'.join(flags)} hits={r.get('hits', 0)} "
                     f"{r.get('description', '')}")
        lines.append(f"        pattern: {pat}")
    return "\n".join(lines)


def cmd_evaluate():
    store = evaluate()
    print(render(store))
    return 1 if store.get("summary", {}).get("false_positives") else 0


def cmd_report():
    store = load_effect()
    if not store.get("summary"):
        return cmd_evaluate()
    print(render(store))
    return 0


def main():
    ap = argparse.ArgumentParser(description="AIShield radar rule effect measurement")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--report", action="store_true", help="Print last evaluation only")
    args = ap.parse_args()
    if args.report:
        return cmd_report()
    return cmd_evaluate()


if __name__ == "__main__":
    sys.exit(main())
