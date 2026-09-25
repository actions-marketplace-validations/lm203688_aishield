"""
版本声明位覆盖测试 — 防止"门禁假绿"。

背景
----
2026-09-25 发现 `api/server.py` 里有 6 处硬编码 `"version": "4.3.0"`，
同进程 `/api/v1/health` 对外自报 4.3.0，而 `mcp-server/mcp.json` 已是 4.8.3。
`scripts/sync_version.py --check` 当时报"所有声明位一致"——因为它只管
TARGETS 里登记的 25 处，那 8 处根本不在登记册里。这就是典型的假绿：
门禁是绿的，但用户看到的是错版本号。

同一类逃逸位还包括 `scanner/sbom.py` 的 TOOL_VERSION、
`api/static/.well-known/agent-card.json`、`mcp/server-card.json`
（MCP 客户端握手时直接读的那份）、以及根目录 `aishield.sarif` 样例的
driver.version。

本测试做三件事，把"门禁看不见"从可能变成不可能：

1. 门禁自身无失明——TARGETS 里每个声明位的正则都还能匹配到（文件重构后
   正则失配会静默失效；read_all 只标 error，默认模式只打印不退出非零）。
2. 全仓只存在一个版本值（不存在 4.3.0 与 4.8.3 并存）。
3. 主动发现生产代码里的产品版本字面量，断言每个命中文件都在门禁登记册内。
   第 3 条不用等人发现漂移——以后再有人新写一个字面量，测试直接点名
   "这个文件没在 sync_version 里登记"。
"""

import os
import re
import sys
import unittest

sys_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, sys_path)
sys.path.insert(0, os.path.join(sys_path, "scripts"))

import sync_version


REPO_ROOT = os.path.abspath(sys_path)

# 带引号的 JSON/YAML 版本字面量：`"version": "X.Y.Z"`。
# 前导负向断言保证不会命中 `"protocol_version"` / `"mcp_protocol_version"`
# / `"owasp_version"` / `"aip_protocol_version"` —— 那些是协议或规范版本，
# 不该跟着产品版本走。
VERSION_LITERAL = re.compile(r'(?<![A-Za-z0-9_])("version"\s*:\s*")(\d+\.\d+\.\d+)')
# YAML 形式：frontmatter 或无引号键值。
VERSION_LITERAL_YAML = re.compile(r'(?m)^\s*version:\s*"?(\d+\.\d+\.\d+)')
# 纯文本大写形式。锚在 llms-full.txt 的 *Canonical* 头部行——那是唯一的
# 版本声明位。不锚的话会同时命中正文里的 **Shipped in v4.2.0** 这类
# 变更日志标题：那是刻意保留的历史记录，改之等于篡改史实。
VERSION_LITERAL_TEXT = re.compile(
    r'(?m)^\*Canonical:.*?Version:\s*(\d+\.\d+\.\d+)')
# Python/TS 常量：TOOL_VERSION / SERVER_VERSION / API_VERSION 等。
VERSION_CONSTANT = re.compile(
    r'(?<![A-Za-z0-9_])([A-Z]+_VERSION)\s*=\s*"(\d+\.\d+\.\d+)')
# 用户直接复制的安装命令：README 里 `npm install pkg@X.Y.Z` 写死旧版本会
# 误导升级路径，2026-09-25 实测 mcp-server/README.md 就停在 4.3.0。
VERSION_LITERAL_NPM = re.compile(r'(aishield-mcp-server@)(\d+\.\d+\.\d+)')

# 扫描范围：用户能读到版本的生产路径。docs/ 和 distribution/ 是关键——
# docs/.well-known/agent-card.json 才是线上 A2A 发现端点真正返回的那份。
PRODUCTION_DIRS = ["api", "scanner", "eco", "registry", "mcp-server",
                   "docs", "distribution"]
ROOT_FILES = ["action_entrypoint.py", "aishield.sarif", "AGENTS.md",
              "COMMUNITY.md", "smithery.yaml"]

SKIP_DIR_PARTS = {"node_modules", ".git", "__pycache__", ".workbuddy",
                  "dist", "build", ".venv", "venv", "intel", "reports"}

# 整个文件跳过：依赖锁文件 / 第三方工具的数据夹具 / 扫描输出，
# 里面全是别人的版本号或历史快照，不是产品版本声明。
SKIP_FILES = {"package-lock.json", "npm-shrinkwrap.json", "yarn.lock",
              "pnpm-lock.yaml", "poetry.lock", "published.json",
              # 机器生成的 SBOM：每个组件版本都由 gen_project_sbom.py 从
              # setup.py 派生后统一盖章，锚定 application 组件那一个声明位即可，
              # 逐行扫描会把 90 个内部源文件全报成"未登记"。
              "project-sbom.cyclonedx.json"}
SKIP_FILE_SUBSTR = ("/data/", os.sep + "data" + os.sep,
                    "/_scan_", os.sep + "_scan_")

# 带日期的历史报告与台账，按项目既有约定"刻意保留原值，改之等于篡改史实"
# （见 COMMUNITY.md 的 2026-09-15 sweep 说明）。每条都写明理由。
HISTORICAL_ALLOWLIST = {
    "distribution/listings/SUBMIT.md": "带日期的渠道巡检记录（2026-09-19 curl 实测结论）",
    "distribution/aishield-plugins/SUBMISSION.md": "向 Anthropic 插件市场的提交记录与自检清单",
    "distribution/published.json": "发布台账，记录的是各次发布当时的版本",
    "action_entrypoint.py": "注释里引用的历史状态，用于说明为何不再硬编码版本号",
    "COMMUNITY.md": "含 2026-09-15 sweep 的历史陈述（第 10 行现状已随版本更新）",
    "docs/agent-ecosystem-distribution.md":
        "带日期的生态分布报告，COMMUNITY.md 已明确点名保留原值",
    "docs/investor-strategy-2026-08.md": "2026-08 月度的投资人策略快照",
}


def _is_dated_report(rel):
    """文件名或路径含 YYYY-MM-DD 或 YYYY-MM 的，视为带日期的历史文档。"""
    return bool(re.search(r"\d{4}-\d{2}(-\d{2})?", rel))


def _scan_exts(fn):
    return fn.endswith((".py", ".json", ".yaml", ".yml", ".ts", ".html",
                        ".txt", ".md", ".sarif", ".toml"))


def _walk_production():
    for top in PRODUCTION_DIRS:
        root = os.path.join(REPO_ROOT, top)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, REPO_ROOT)
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS]
            for fn in filenames:
                if not _scan_exts(fn):
                    continue
                if fn in SKIP_FILES:
                    continue
                rel = rel_dir.replace(os.sep, "/") + "/" + fn
                if any(s in rel.replace("/", os.sep) for s in SKIP_FILE_SUBSTR):
                    continue
                yield rel
    for fn in ROOT_FILES:
        if os.path.exists(os.path.join(REPO_ROOT, fn)):
            yield fn


def _major(v):
    return int(v.split(".")[0])


_HIT_RE = re.compile(r'^line (\d+): (.+?) (\d+\.\d+\.\d+)$')


def _parse_hit(hit):
    """把 "line 12: \"version\": 4.3.0" 解析成 (12, '"version":', '4.3.0')。"""
    m = _HIT_RE.match(hit)
    if not m:
        return 0, "", ""
    return m.group(1), m.group(2), m.group(3)


class TestGateIntegrity(unittest.TestCase):
    """门禁自身必须可信：声明位失配等于对那一处失明。"""

    def test_every_declared_site_still_matches(self):
        broken = [i for i in sync_version.read_all() if i.get("error")]
        self.assertEqual(
            broken, [],
            msg="以下声明位的正则已失配（文件结构变了），门禁对它们失明：\n" +
            "\n".join("  {path}: {error}".format(**i) for i in broken))

    def test_every_declared_file_exists(self):
        missing = [i["path"] for i in sync_version.read_all() if not i["exists"]]
        self.assertEqual(
            missing, [],
            msg="TARGETS 登记了不存在的文件：{0}\n"
                "（本地有而 CI 无的文件会让门禁本地绿、CI 红）".format(missing))

    def test_only_one_version_value_exists(self):
        items = sync_version.read_all()
        versions = sorted({i["version"] for i in items if i.get("version")},
                          key=sync_version._semver_key)
        self.assertEqual(
            len(versions), 1,
            msg="版本声明位不一致：{0}（基准 {1}）".format(
                versions, sync_version.baseline(items)))

    def test_baseline_not_zero(self):
        self.assertNotEqual(sync_version.baseline(sync_version.read_all()),
                            "0.0.0", msg="基准版本解析为 0.0.0，所有声明位都失配了")


class TestGateCoverage(unittest.TestCase):
    """主动防线：生产代码里的产品版本字面量必须全部在门禁登记册内。"""

    def _declaration_files(self):
        """发现产品版本字面量。只认与基准同一主版本的值——
        漂移的产品版本仍在同一主版本家族内，而 1.0.0 / 2.1.0 / 22.20.1
        这类协议版本与依赖版本自然被排除。

        返回 {rel: (hits, reason)}；reason 非空表示已按约定豁免。"""
        base_major = _major(sync_version.baseline(sync_version.read_all()))
        found = {}
        for rel in _walk_production():
            try:
                with open(os.path.join(REPO_ROOT, rel), "r",
                          encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            hits = []
            for rx, label in ((VERSION_LITERAL, '"version":'),
                              (VERSION_LITERAL_YAML, 'version:'),
                              (VERSION_LITERAL_TEXT, 'Version:'),
                              (VERSION_LITERAL_NPM, '@')):
                for m in rx.finditer(text):
                    v = m.group(m.lastindex)
                    if _major(v) == base_major:
                        hits.append('line %d: %s %s' % (
                            text.count("\n", 0, m.start()) + 1, label, v))
            for m in VERSION_CONSTANT.finditer(text):
                if _major(m.group(2)) == base_major:
                    hits.append('line %d: %s = %s' % (
                        text.count("\n", 0, m.start()) + 1,
                        m.group(1), m.group(2)))
            if not hits:
                continue
            reason = None
            if rel in HISTORICAL_ALLOWLIST:
                reason = HISTORICAL_ALLOWLIST[rel]
            elif _is_dated_report(rel):
                reason = "带日期的历史文档（文件名含日期）"
            found[rel] = (hits, reason)
        return found

    def test_all_declaration_files_are_gated(self):
        gated = {rel for rel, _, _ in sync_version.TARGETS}
        found = self._declaration_files()
        ungated = {rel: hits for rel, (hits, reason) in found.items()
                   if rel not in gated and reason is None}
        self.assertEqual(
            ungated, {},
            msg="以下文件写有产品版本字面量，但不在 sync_version.TARGETS 登记册内——"
                "它会静默漂移（这就是 2026-09-25 那 8 处 4.3.0 的成因）：\n" +
            "\n".join("  {0}: {1}".format(rel, "; ".join(h))
                      for rel, h in sorted(ungated.items())))

    def test_exemptions_are_named(self):
        """每一个豁免都必须有条目级别的理由，不能只靠"文件名含日期"糊过去。"""
        found = self._declaration_files()
        unnamed = [rel for rel, (h, r) in found.items()
                   if r is not None and rel in HISTORICAL_ALLOWLIST
                   and not HISTORICAL_ALLOWLIST[rel].strip()]
        self.assertEqual(unnamed, [],
                         msg="HISTORICAL_ALLOWLIST 里存在无理由的豁免条目：{0}".format(unnamed))

    def test_no_stale_major_family_values(self):
        """同一主版本家族里不允许并存多个不同版本值。
        这是最能一眼看出漂移的检查：如果哪天出现 4.8.3 与 4.9.0 并存，
        或残留 4.3.0，这里直接点名文件与行号。"""
        items = sync_version.read_all()
        base = sync_version.baseline(items)
        base_major = _major(base)
        found = self._declaration_files()
        offenders = {}
        for rel, (hits, reason) in found.items():
            if reason is not None:
                continue
            for line, label, val in (_parse_hit(h) for h in hits):
                if val != base and _major(val) == base_major:
                    offenders.setdefault(rel, []).append(
                        "line %s: %s %s（应为 %s）" % (line, label, val, base))
        self.assertEqual(
            offenders, {},
            msg="存在与基准 {0} 不一致的同主版本声明位：\n".format(base) +
            "\n".join("  {0}: {1}".format(rel, "; ".join(v))
                      for rel, v in sorted(offenders.items())))

    def test_gated_literals_match_baseline(self):
        items = sync_version.read_all()
        base = sync_version.baseline(items)
        stale = [{"path": i["path"], "version": i["version"]}
                 for i in items if i.get("version") and i["version"] != base]
        self.assertEqual(stale, [],
                         msg="落后于基准 {0} 的声明位：{1}".format(base, stale))

    def test_gated_target_count(self):
        """登记位只增不减的底线。2026-09-25 补齐 4 处（api/server.py 收敛为
        常量、sbom.py、agent-card.json、server-card.json、aishield.sarif）后为 29。"""
        self.assertGreaterEqual(len(sync_version.TARGETS), 29,
                                msg="sync_version 登记位只有 {0} 个，可能有人删了登记项"
                                    .format(len(sync_version.TARGETS)))


if __name__ == "__main__":
    unittest.main()
