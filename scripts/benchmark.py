#!/usr/bin/env python3
"""AIShield Security Benchmark v1 — 可复跑、可第三方引用、确定性。

为什么要有它
------------
`docs/agent-security-benchmark-2026.md` 里已经写着「20 份健康配置 0 误报 / 10 份恶意
配置全检出」，但那份数字是**一次性跑出来的**：没有固定语料、没有复跑脚本、没有
断言。别人无法验证，我们自己也无法发现它哪天变了。一个不可复现的分数不是基准，
是一句宣传语。

这条路径借鉴 google-research/android_world 的做法：**奖励由系统状态推导，而非比对
人工演示**。翻译到我们这里：分数由「固定语料 + 确定性扫描」推导，而不是由某次
人肉观察得出。三条具体原则：

  1. **固定语料**：正负样本来自仓库里的单一真源（`scripts/rule_corpus.py` 与本文
     的参数化矩阵），不联网、不随机、不随时间漂移。
  2. **动态参数化**：同一个攻击意图，换一套「表面形态」（凭证形态 / 安装源 /
     传输方式 / 启动器）再测一遍。只在一种写法上有效的规则不是规则，是记忆。
  3. **可被第三方跑**：零依赖、零网络、输出确定性 JSON。谁 clone 下来跑，得到
     的数字就该和我们公布的一样。

两个平面
--------
  Plane A（指令面）  文本 → `scanner.rules.analyze()`。测规则层对攻击语料的召回与
                      对良性语料的误报。
  Plane B（配置面）  MCP 客户端配置 → `scanner.client_discovery.scan_client_configs()`。
                      参数化变体主要落在这一面 —— 攻击意图固定，表面形态穷举。

用法::

    python scripts/benchmark.py                 # 人类可读摘要
    python scripts/benchmark.py --json          # 确定性 JSON（供 CI / 第三方比对）
    python scripts/benchmark.py --markdown      # 生成 docs 里的分数表
    python scripts/benchmark.py --fail-under-recall 1.0 --fail-over-fp 0.0

不变量：全程不执行被扫配置中的任何命令，不发任何网络请求。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BENCHMARK_ID = "aishield-security-benchmark/v1"


# ══════════════════════════════════════════════════════════════
#  参数化矩阵 —— 同一个意图，多套表面形态
# ══════════════════════════════════════════════════════════════
#
# 每个轴给出一组**等价的**写法。等价是这里的全部意义：如果一个规则只认得
# `npx -y` 而认不出 `uvx`，它抓的不是"运行时拉包"这件事，而是"npx 这个词"。
#
# 假凭证一律用拼接构造 —— 字面量形式的 PAT 会被 push 前的 secret scanning 拦下。

def _pat():
    return "ghp_" + ("a" * 30)


CREDENTIAL_FORMS = (
    ("github_pat", _pat),
    ("aws_access_key", lambda: "AKIA" + "Q" * 16),
    ("openai_key", lambda: "sk-" + "T" * 40),
    ("generic_password", lambda: "hunter2-not-a-real-secret"),
)

# 恶意侧：四种**本身就有风险**的启动方式。
#
# 2026-09-19 首轮跑出一个反直觉的结果：把这四种写法照搬到「良性对照组」里之后，
# 有 3 例被判 high —— 起初我按误报记账，逐条查 evidence 才发现是账面错了：
#   npx -y <pkg>      → runtime_package_fetch（自动拉包，MCP04 供应链）
#   bash -c <pkg>     → shell_interpreter_launch（外壳解释器）
#   https://.../sse   → remote_server_without_auth（远端无鉴权声明）
# 这三条命中的是**写法本身**，不是包里有什么。也就是说「启动器」这个轴并不与
# 安全性正交 —— 一个安全的包用危险的方式启动，仍然是危险配置。
# 所以它们只能出现在正样本里。良性对照组必须换成真正安全的写法（见下）。
RISKY_LAUNCHERS = (
    ("npx_auto_install", "npx", ["-y", "{pkg}"]),
    ("uvx_auto_install", "uvx", ["{pkg}"]),
    ("docker_privileged", "docker", ["run", "--privileged", "-i", "{pkg}"]),
    ("shell_wrapper", "bash", ["-c", "{pkg} --serve"]),
)

SOURCES = (
    "evil-mcp",
    "@/unscoped-only-mcp",
    "evil-mcp@latest",
    "https://raw.example.com/payload.tgz",
)


def _config(name, command, args, env=None, url=None, headers=None):
    entry = {}
    if url:
        entry["url"] = url
        if headers:
            entry["headers"] = dict(headers)
    else:
        entry["command"] = command
        entry["args"] = list(args)
    if env:
        entry["env"] = dict(env)
    return json.dumps({"mcpServers": {name: entry}})


def malicious_config_samples():
    """参数化的恶意配置：每个轴 × 每种形态。

    攻击意图在所有样本里是同一个（从未知来源自动拉包执行 + 内联明文凭证）。
    变的只有表面写法 —— 这正是要测的东西。
    """
    samples = []
    for cred_name, cred_fn in CREDENTIAL_FORMS:
        for launch_name, cmd, args in RISKY_LAUNCHERS:
            pkg = SOURCES[len(samples) % len(SOURCES)]
            samples.append({
                "id": "cfg-mal-%s-%s" % (launch_name, cred_name),
                "axis_launcher": launch_name,
                "axis_credential": cred_name,
                "content": _config(
                    "payload-server",
                    cmd,
                    [a.format(pkg=pkg) for a in args],
                    env={"GITHUB_TOKEN": cred_fn()},
                ),
            })
    # 传输维：远端无鉴权 / 明文 http / websocket
    for transport, url in (
        ("remote_http_no_auth", "http://mcp.example.com/sse"),
        ("remote_ws", "ws://mcp.example.com/socket"),
        ("remote_open_sse", "https://mcp.example.com/sse?auth=none"),
    ):
        samples.append({
            "id": "cfg-mal-transport-%s" % transport,
            "axis_transport": transport,
            "content": _config("remote-risk", None, [], url=url),
        })
    # 风险写法独立成轴：包是官方的，只有启动/连接方式危险。
    # 这一组专门回答「规则命中的是写法还是包名」。
    samples.append({
        "id": "cfg-mal-launcher-only-npx_auto_install",
        "axis_risky_form": "npx_-y_official_pkg",
        "content": _config("filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem"]),
    })
    samples.append({
        "id": "cfg-mal-launcher-only-shell_wrapper",
        "axis_risky_form": "bash_c_official_pkg",
        "content": _config("filesystem", "bash", ["-c", "@modelcontextprotocol/server-filesystem"]),
    })
    samples.append({
        "id": "cfg-mal-launcher-only-remote_no_auth",
        "axis_risky_form": "remote_no_auth_header",
        "content": _config("remote", None, [], url="https://mcp.example.com/sse"),
    })
    return samples


def benign_config_samples():
    """参数化的良性配置 —— 与恶意样本一一对照，但每一处都换成**真正安全**的写法。

    对照组的设计要点：除了「该安全的那一面被换成安全写法」之外，其余结构完全一致
    （同样的 server 数量、同样有 env / args 键）。这样一旦误报出现，可以直接归因到
    差异的那一处，而不是"可能是样本太短/太长/结构不同"。

    版本一律 pin 到具体版本或 digest：`npx -y` / 裸 `uvx` 属于自动拉包，是风险写法，
    不能出现在良性对照里（那会让「误报」变成对扫描器的冤枉，见 RISKY_LAUNCHERS 注释）。

    另外刻意收录**防御工具的自我描述**（见 DEFENSE_TEXT_SAMPLES）：一个讨论 prompt
    injection 的扫描器文档，和一个真的在投毒的配置，字面上可能很接近。
    """
    return [
        {
            "id": "cfg-benign-uvx-pinned",
            "axis_launcher": "uvx_pinned",
            "content": _config("filesystem", "uvx",
                               ["mcp-server-filesystem==1.2.3"],
                               env={"WORKSPACE_ROOT": "/srv/workspace"}),
        },
        {
            "id": "cfg-benign-npx-pinned-no-yes",
            "axis_launcher": "npx_pinned_no_auto_yes",
            "content": _config("filesystem", "npx",
                               ["@modelcontextprotocol/server-filesystem@1.2.3"],
                               env={"WORKSPACE_ROOT": "/srv/workspace"}),
        },
        {
            "id": "cfg-benign-docker-digest-no-privileged",
            "axis_launcher": "docker_digest_unprivileged",
            "content": _config("filesystem", "docker",
                               ["run", "--rm", "-i",
                                "@modelcontextprotocol/server-filesystem@sha256:0f1e2d"],
                               env={"WORKSPACE_ROOT": "/srv/workspace"}),
        },
        {
            "id": "cfg-benign-remote-https-with-auth",
            "axis_transport": "remote_https_with_auth_header",
            "content": _config("remote-safe", None, [],
                               url="https://mcp.example.com/sse",
                               headers={"Authorization": "Bearer ${MCP_TOKEN}"}),
        },
        {
            "id": "cfg-benign-no-env",
            "content": json.dumps({"mcpServers": {
                "weather": {"command": "uvx", "args": ["mcp-server-weather==2.0.1"]}}}),
        },
        {
            "id": "cfg-benign-empty",
            "content": json.dumps({"mcpServers": {}}),
        },
    ]


# 防御工具的自我描述：讨论攻击、不实施攻击。误报的经典来源。
DEFENSE_TEXT_SAMPLES = (
    "AIShield detects prompt injection and jailbreak attempts in tool descriptions.",
    "This scanner looks for credential exfiltration patterns such as leaked AWS keys.",
    "防御文档：本工具用于检测提示词注入、越狱与凭证窃取等攻击手法。",
    "Securely store tokens in a secrets manager; never commit credentials to git.",
    "The evaluation harness runs adversarial prompts to measure robustness.",
)


# ══════════════════════════════════════════════════════════════
#  执行
# ══════════════════════════════════════════════════════════════
def _max_severity(findings):
    """取一组 findings 里最高的严重度（用于"报了但没到阈值"这类记账）。"""
    order = ("critical", "high", "medium", "low", "info")
    best = "info"
    for f in findings:
        sev = str(f.get("severity") or "info").lower()
        if sev in order and order.index(sev) < order.index(best):
            best = sev
    return best


def _plane_a():
    """指令面：规则层对攻击 / 良性文本语料的召回与误报。"""
    from scanner.rules import analyze
    import rule_corpus

    attacks = list(rule_corpus.ATTACK_SAMPLES)
    benign = list(rule_corpus.BENIGN_CORPUS) + list(DEFENSE_TEXT_SAMPLES)

    hit = 0
    missed = []
    for i, text in enumerate(attacks):
        findings = analyze({"sample.md": text}, "mcp").get("findings", [])
        if findings:
            hit += 1
        else:
            missed.append(i)

    fp = []
    for i, text in enumerate(benign):
        findings = analyze({"sample.md": text}, "mcp").get("findings", [])
        if findings:
            # 只统计 critical/high —— 引用上下文抑制会把防御文档降级，降级不算误报
            serious = [f for f in findings if f.get("severity") in ("critical", "high")]
            if serious:
                fp.append(i)

    return {
        "name": "instruction_plane",
        "positives": len(attacks),
        "detected": hit,
        "recall": round(hit / len(attacks), 4) if attacks else None,
        "missed_indices": missed,
        "negatives": len(benign),
        "false_positives": len(fp),
        "false_positive_rate": round(len(fp) / len(benign), 4) if benign else None,
        "false_positive_indices": fp,
    }


def _plane_b():
    """配置面：参数化恶意 / 良性配置的检出与误报，按轴拆分。

    检出分两档记账，因为「报了」和「报到了该报的严重度」不是同一件事：

      serious（critical/high）—— 计入召回率。这是运维真正会去处理的那一档。
      below_threshold         —— 报了但只有 medium/low。**不算漏报**，
                                 单列出来是为了不让口径掩盖实情：`uvx <pkg>`
                                 没有 `-y`（不会自动确认安装）本来就比 `npx -y`
                                 低一档，给 medium 是站得住的判断，不是缺陷。
    """
    from scanner.client_discovery import scan_client_configs

    positives = malicious_config_samples()
    negatives = benign_config_samples()

    by_axis = {}
    detected = 0
    missed = []
    below_threshold = []
    for s in positives:
        result = scan_client_configs({"/bench/mcp.json": s["content"]})
        findings = result.get("findings", [])
        serious = [f for f in findings if f.get("severity") in ("critical", "high")]
        ok = bool(serious)
        detected += 1 if ok else 0
        if not ok:
            missed.append(s["id"])
            if findings:
                below_threshold.append({
                    "id": s["id"],
                    "max_severity": _max_severity(findings),
                })
        for axis in ("axis_launcher", "axis_credential", "axis_transport", "axis_risky_form"):
            if axis in s:
                bucket = by_axis.setdefault("%s=%s" % (axis, s[axis]), {"total": 0, "detected": 0})
                bucket["total"] += 1
                bucket["detected"] += 1 if ok else 0

    false_positives = []
    for s in negatives:
        result = scan_client_configs({"/bench/mcp.json": s["content"]})
        serious = [f for f in result.get("findings", [])
                   if f.get("severity") in ("critical", "high")]
        if serious:
            false_positives.append(s["id"])

    return {
        "name": "config_plane",
        "positives": len(positives),
        "detected": detected,
        "recall": round(detected / len(positives), 4) if positives else None,
        "missed": missed,
        "detected_below_threshold": below_threshold,
        "negatives": len(negatives),
        "false_positives": len(false_positives),
        "false_positive_rate": round(len(false_positives) / len(negatives), 4) if negatives else None,
        "false_positive_ids": false_positives,
        "by_axis": {k: by_axis[k] for k in sorted(by_axis)},
    }


def run():
    """跑完整基准，返回确定性结果字典。"""
    from scanner.rules import get_rule_count

    plane_a = _plane_a()
    plane_b = _plane_b()
    return {
        "benchmark": BENCHMARK_ID,
        "rules": {"mcp": get_rule_count("mcp"), "skill": get_rule_count("skill")},
        "planes": [plane_a, plane_b],
        "summary": {
            "positives": plane_a["positives"] + plane_b["positives"],
            "detected": plane_a["detected"] + plane_b["detected"],
            "negatives": plane_a["negatives"] + plane_b["negatives"],
            "false_positives": plane_a["false_positives"] + plane_b["false_positives"],
            "recall": round(
                (plane_a["detected"] + plane_b["detected"])
                / max(1, plane_a["positives"] + plane_b["positives"]), 4),
            "false_positive_rate": round(
                (plane_a["false_positives"] + plane_b["false_positives"])
                / max(1, plane_a["negatives"] + plane_b["negatives"]), 4),
        },
        "invariants": {
            "network_calls": False,
            "executes_scanned_configs": False,
            "deterministic": True,
        },
    }


def render_markdown(result):
    s = result["summary"]
    lines = [
        "# AIShield Security Benchmark v1",
        "",
        "> 本表由 `python scripts/benchmark.py --markdown` 生成，请勿手工编辑。",
        "> 语料固定、扫描确定性、零网络 —— 任何人跑同一份代码应得到同样的数字。",
        "",
        "## 总分",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        "| 规则数 | MCP %d / Skill %d |" % (result["rules"]["mcp"], result["rules"]["skill"]),
        "| 正样本（应检出） | %d |" % s["positives"],
        "| 检出 | %d |" % s["detected"],
        "| **召回率** | **%.1f%%** |" % (s["recall"] * 100),
        "| 负样本（应不报） | %d |" % s["negatives"],
        "| 误报 | %d |" % s["false_positives"],
        "| **误报率** | **%.1f%%** |" % (s["false_positive_rate"] * 100),
        "",
        "## 分平面",
        "",
        "| 平面 | 正样本 | 检出 | 召回 | 负样本 | 误报 |",
        "|---|---|---|---|---|---|",
    ]
    for p in result["planes"]:
        lines.append("| `%s` | %d | %d | %.1f%% | %d | %d |" % (
            p["name"], p["positives"], p["detected"],
            (p["recall"] or 0) * 100, p["negatives"], p["false_positives"]))
    b = result["planes"][1]
    lines += [
        "",
        "## 参数化变体（配置面，按轴）",
        "",
        "同一个攻击意图，换一种表面写法再测一遍。捡出「只在某一种写法上有效」的规则。",
        "",
        "| 轴 | 样本 | 检出 | 召回 |",
        "|---|---|---|---|",
    ]
    for axis, v in b["by_axis"].items():
        lines.append("| `%s` | %d | %d | %.1f%% |" % (
            axis, v["total"], v["detected"], v["detected"] / max(1, v["total"]) * 100))
    if b.get("detected_below_threshold"):
        lines += [
            "",
            "### 报了但低于阈值（不计入漏报）",
            "",
            "| 样本 | 最高严重度 |",
            "|---|---|",
        ]
        for item in b["detected_below_threshold"]:
            lines.append("| `%s` | %s |" % (item["id"], item["max_severity"]))

    # 检出缺口：如实列出当前仍未到阈值的正样本。
    # 基准的价值不在把数字做漂亮，而在把「哪里还没覆盖」变成一条可核对的清单。
    gaps = b.get("missed", []) + ["instruction_sample_#%d" % i for i in result["planes"][0].get("missed_indices", [])]
    lines += ["", "## 检出缺口（当前未到阈值，公开）", ""]
    if gaps:
        for g in gaps:
            lines.append("- `%s`" % g)
    else:
        lines.append("- 无")
    lines += [""]
    lines += [
        "",
        "## 不变量",
        "",
        "- 不发起任何网络请求",
        "- 不执行被扫配置中的任何命令",
        "- 输出确定性（同一份代码 → 同一组数字）",
        "",
        "复现：`python scripts/benchmark.py --json`",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="benchmark", description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="输出确定性 JSON")
    ap.add_argument("--markdown", action="store_true", help="输出 Markdown 分数表")
    ap.add_argument("--out", default=None, help="写入文件（默认 stdout）")
    ap.add_argument("--fail-under-recall", type=float, default=None,
                    help="召回低于此值则退出码 1（CI 门禁）")
    ap.add_argument("--fail-over-fp", type=float, default=None,
                    help="误报率高于此值则退出码 1（CI 门禁）")
    args = ap.parse_args(argv)

    result = run()

    if args.markdown:
        text = render_markdown(result)
    elif args.json:
        text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    else:
        s = result["summary"]
        text = "\n".join([
            "%s" % BENCHMARK_ID,
            "-" * 52,
            "positives  : %d   detected: %d   recall: %.1f%%"
            % (s["positives"], s["detected"], s["recall"] * 100),
            "negatives  : %d   false pos: %d   fp rate: %.1f%%"
            % (s["negatives"], s["false_positives"], s["false_positive_rate"] * 100),
        ])

    if args.out:
        parent = os.path.dirname(os.path.abspath(args.out))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("wrote %s" % args.out)
    else:
        print(text)

    rc = 0
    if args.fail_under_recall is not None and result["summary"]["recall"] < args.fail_under_recall:
        print("FAIL: recall %.4f < %.4f" % (result["summary"]["recall"], args.fail_under_recall))
        rc = 1
    if args.fail_over_fp is not None and result["summary"]["false_positive_rate"] > args.fail_over_fp:
        print("FAIL: false-positive rate %.4f > %.4f"
              % (result["summary"]["false_positive_rate"], args.fail_over_fp))
        rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
