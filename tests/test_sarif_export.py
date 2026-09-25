"""
SARIF 导出契约测试 — 验证 sbom.sarif_from_scan 产出合法的 SARIF 2.1.0。

注意：工具版本不再硬编码断言。此前三个用例都写死 "4.3.0"，于是版本号只能靠
改测试才能推进——升版时忘改测试就红，改了测试却忘改产物也测不出来。现在改为
断言「产物里的 driver.version 等于 TOOL_VERSION 常量」，并把 TOOL_VERSION 的
合法性与 scripts/sync_version.py 的基准值一致性交给 test_version_declare.py。
"""

import json
import os
import re
import unittest

sys_path = os.path.join(os.path.dirname(__file__), "..")
import sys
sys.path.insert(0, sys_path)

from scanner import sbom

# SARIF 规范自身的版本，与产品版本无关，必须写死——它由 schema 决定。
SARIF_SPEC_VERSION = "2.1.0"


class TestSarifExport(unittest.TestCase):
    def test_tool_version_is_valid_semver(self):
        # 断言结构而非具体值：升版不应要求改测试。
        self.assertRegex(sbom.TOOL_VERSION, r"^\d+\.\d+\.\d+$",
                         "TOOL_VERSION 必须是语义化版本")

    def _sample(self):
        return {
            "findings": [
                {"file": "server.py", "lines": "12", "severity": "critical",
                 "description": "硬编码API密钥", "owasp_category": "MCP01"},
                {"file": "agent.py", "lines": "30", "severity": "high",
                 "description": "关闭人类确认环", "owasp_category": "ASI03",
                 "type": "no_human_confirm", "evidence": "auto_approve=True"},
            ]
        }

    def test_sarif_structure(self):
        sar = sbom.sarif_from_scan(self._sample(), "demo")
        self.assertEqual(sar["version"], SARIF_SPEC_VERSION)
        self.assertIn("$schema", sar)
        run = sar["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "AIShield")
        self.assertEqual(run["tool"]["driver"]["version"], sbom.TOOL_VERSION)
        self.assertEqual(len(run["results"]), 2)
        self.assertEqual(len(run["tool"]["driver"]["rules"]), 2)

    def test_sarif_severity_levels(self):
        sar = sbom.sarif_from_scan(self._sample(), "demo")
        levels = {r["level"] for r in sar["runs"][0]["results"]}
        # critical/high 都映射到 error
        self.assertIn("error", levels)

    def test_sarif_serializable(self):
        sar = sbom.sarif_from_scan(self._sample(), "demo")
        text = json.dumps(sar, ensure_ascii=False)
        self.assertIsInstance(text, str)
        json.loads(text)  # 不抛异常即合法 JSON

    def test_aishield_sarif_sample_file_present_and_valid(self):
        path = os.path.join(sys_path, "aishield.sarif")
        self.assertTrue(os.path.exists(path), "aishield.sarif 样例缺失")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["version"], SARIF_SPEC_VERSION)
        self.assertEqual(data["runs"][0]["tool"]["driver"]["version"],
                         sbom.TOOL_VERSION)
        self.assertGreater(len(data["runs"][0]["results"]), 0)


if __name__ == "__main__":
    unittest.main()
