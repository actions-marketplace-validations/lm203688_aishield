"""
在线扫描页 + 框架适配器契约测试。

验证两件事：
1) framework-adapters 的零依赖门禁 gate_mcp_config 能正确拦截危险配置、放行安全配置；
2) /scan 前端页确实接入了真实后端端点（绝不漂移到假端点 / 假绿）。
"""

import os
import sys
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from distribution.framework_adapters import gate_mcp_config


GOOD_CONFIG = json.dumps({
    "mcpServers": {
        "safe": {"command": "npx", "args": ["-y", "@scope/pkg@1.2.3"]}
    }
})

BAD_CONFIG = json.dumps({
    "mcpServers": {
        "leaky": {
            "command": "npx", "args": ["-y", "@scope/pkg@latest"],
            "env": {"OPENAI_API_KEY": "sk-abcdefghijklmnopqrstuvwxyz1234567890ABCD"}
        }
    }
})


class TestFrameworkAdapterGate(unittest.TestCase):
    def test_blocks_credential_exposure(self):
        r = gate_mcp_config(BAD_CONFIG, fail_on="high")
        self.assertFalse(r.ok, "含明文凭证的配置不应通过门禁")
        self.assertGreater(r.findings_total, 0)
        self.assertTrue(any(f.get("severity") == "critical" for f in r.findings))

    def test_passes_clean_config(self):
        r = gate_mcp_config(GOOD_CONFIG, fail_on="high")
        # 干净配置只有 info 级 STDIO 提示，不应触发 high 拦截
        self.assertTrue(r.ok, f"干净配置应通过门禁: {r.errors}")
        self.assertGreaterEqual(r.config_score, 0)

    def test_never_spawns_commands(self):
        # 即便配置里嵌了 `sh -c`，门禁也只是报告风险，不执行
        evil = json.dumps({"mcpServers": {"x": {"command": "sh", "args": ["-c", "rm -rf /"]}}})
        r = gate_mcp_config(evil, fail_on="high")
        self.assertFalse(r.ok)
        # 关键点：函数正常返回，没有抛异常也没有真正执行命令（无法断言副作用，
        # 但至少确认我们是静态分析路径：findings 由 analyze_server_entry 产生）
        self.assertIn("shell_interpreter_launch", {f.get("type") for f in r.findings})


class TestScanPageWiring(unittest.TestCase):
    def test_scan_html_wired_to_real_endpoints(self):
        path = os.path.join(os.path.dirname(__file__), "..", "api", "static", "scan.html")
        self.assertTrue(os.path.exists(path), "api/static/scan.html 缺失")
        with open(path, encoding="utf-8") as f:
            html = f.read()
        self.assertIn("/api/v1/scan/client-config", html, "页面未接入真实扫描端点")
        self.assertIn("/api/v1/export/sarif", html, "页面未接入 SARIF 导出端点")
        # 静态分析承诺：页面文案须声明不执行命令
        self.assertIn("静态分析", html)

    def test_scan_page_does_not_misrepresent_data_flow(self):
        """The pasted config IS posted to the server.

        Claiming "代码不出机" would be a materially false statement on a
        security tool's landing page. Pin both halves: the false claim must be
        gone, and an accurate disclosure must be present.
        """
        path = os.path.join(os.path.dirname(__file__), "..", "api", "static", "scan.html")
        with open(path, encoding="utf-8") as f:
            html = f.read()
        self.assertNotIn(
            "代码不出机", html,
            "在线扫描页会把粘贴内容发到服务端，不得宣称「代码不出机」",
        )
        self.assertIn("发送到 aishield.tools", html, "需明示粘贴内容会传输到服务端")
        self.assertIn("npx aishield-mcp-server", html, "需给出完全本机处理的替代路径")

    def test_server_route_registers_scan(self):
        # 确认 server.py 的 _STATIC_PAGES 含 /scan -> scan.html
        server_path = os.path.join(os.path.dirname(__file__), "..", "api", "server.py")
        with open(server_path, encoding="utf-8") as f:
            src = f.read()
        self.assertIn('"/scan": "scan.html"', src, "server.py 未注册 /scan 路由")


if __name__ == "__main__":
    unittest.main()
