"""B1 契约测试：扫描器产出的 finding 必须携带精确锚点字段（file + lines/evidence）。

这是 MCP 层 `formatFinding`（mcp-server/src/index.ts）能渲染
`file:line + 命中片段 + rule id` 的**数据侧保证**。

借鉴 heyclicky 的 `[POINT:x,y]` 精确指向：告警必须"指到现场"，而不只是
"你有漏洞"。如果某条扫描器把锚点字段丢了，B1 的渲染就会退化成
`[severity] desc`，本测试会立刻变红。
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scanner.engine import secrets_detection, taint_analysis


class TestFindingAnchor(unittest.TestCase):
    def test_secrets_finding_carries_anchor(self):
        findings = secrets_detection({
            "db.py": "conn = 'postgresql://user:pass@db.host:5432/app'",
        })["findings"]
        self.assertTrue(findings, "应至少产出 1 条密钥检测 finding")
        for f in findings:
            with self.subTest(ftype=f.get("type")):
                self.assertIn("file", f, "finding 缺少 file 锚点")
                self.assertTrue(
                    f.get("lines") or f.get("evidence"),
                    f"finding 既无 lines 也无 evidence，B1 渲染将无锚点: {f}",
                )

    def test_taint_finding_carries_line_anchor(self):
        # taint_analysis 直接返回 findings 列表（非 dict 包装）
        findings = taint_analysis({
            "app.py": "user = request.args.get('x')\nos.system(user)\n",
        })
        self.assertTrue(findings, "应至少产出 1 条污点流 finding")
        for f in findings:
            with self.subTest(ftype=f.get("type")):
                self.assertIn("file", f)
                self.assertTrue(
                    f.get("lines") or f.get("evidence"),
                    f"finding 既无 lines 也无 evidence，B1 渲染将无锚点: {f}",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
