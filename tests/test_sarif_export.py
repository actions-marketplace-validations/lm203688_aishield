"""
SARIF 导出契约测试 — 验证 sbom.sarif_from_scan 产出符合 4.3.0 的合法 SARIF 2.1.0。
"""

import json
import os
import unittest

sys_path = os.path.join(os.path.dirname(__file__), "..")
import sys
sys.path.insert(0, sys_path)

from scanner import sbom


class TestSarifExport(unittest.TestCase):
    def test_tool_version_is_4_3_0(self):
        self.assertEqual(sbom.TOOL_VERSION, "4.3.0")

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
        self.assertEqual(sar["version"], "2.1.0")
        self.assertIn("$schema", sar)
        run = sar["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "AIShield")
        self.assertEqual(run["tool"]["driver"]["version"], "4.3.0")
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
        self.assertEqual(data["runs"][0]["tool"]["driver"]["version"], "4.3.0")
        self.assertGreater(len(data["runs"][0]["results"]), 0)


if __name__ == "__main__":
    unittest.main()
