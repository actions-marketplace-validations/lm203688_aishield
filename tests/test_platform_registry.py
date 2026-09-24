"""tests/test_platform_registry.py — 平台注册表 + 治理缺口矩阵测试。

覆盖 v4.8.1 新增能力：
- 33 平台注册表（含大陆可达 / 验证不通分类）
- 5 类接入路径定义
- 治理项 → AIShield provision 映射完整性
- 推荐引擎（大陆过滤、MCP 优先、能力匹配）
- 运行时注册
- 与 personal_agent.register_agent_instance 的结构化平台字段集成
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJECT = _HERE.parent
sys.path.insert(0, str(_PROJECT))
sys.path.insert(0, str(_PROJECT / "eco"))
sys.path.insert(0, str(_PROJECT / "api"))


class PlatformRegistryTest(unittest.TestCase):
    """基础注册表功能。"""

    def setUp(self):
        # 隔离持久化数据：直接删除测试数据文件
        import eco.personal_agent as _pa
        if os.path.exists(_pa.STORE_FILE):
            os.remove(_pa.STORE_FILE)
        if os.path.exists(_pa.STORE_FILE + ".tmp"):
            os.remove(_pa.STORE_FILE + ".tmp")
        from eco import platform_registry
        self.pr = platform_registry

    # ── 基础 ──

    def test_total_platforms_minimum(self):
        """至少 25 平台（保证覆盖主流海外 + 大陆）。"""
        stats = self.pr.stats()
        self.assertGreaterEqual(stats["total_platforms"], 25)

    def test_all_platforms_have_required_fields(self):
        """每个平台都有关键字段。"""
        for pid, p in self.pr.PLATFORMS.items():
            for key in ("id", "name", "vendor", "family", "cny_accessible",
                        "access_paths", "governance", "gaps"):
                self.assertIn(key, p, f"{pid} 缺 {key}")
            self.assertEqual(p["id"], pid, f"平台 id 与 key 不一致：{pid}")
            self.assertIn(p["family"], ("consumer", "developer",
                                        "enterprise", "infrastructure"),
                          f"{pid} family 非法")
            self.assertIn(p["cny_accessible"], ("reachable", "verified_blocked",
                                                 "regional_only", "unknown"))
            self.assertIsInstance(p["access_paths"], list)
            self.assertIsInstance(p["governance"], list)
            self.assertIsInstance(p["gaps"], list)

    # ── 大陆可达性分类 ──

    def test_muse_verified_blocked(self):
        p = self.pr.get_platform("meta-muse")
        self.assertIsNotNone(p)
        self.assertEqual(p["cny_accessible"], "verified_blocked")
        self.assertIn("connector_official", p["access_paths"])
        self.assertIn("mcp", p["access_paths"])

    def test_grok_bot_verified_blocked(self):
        p = self.pr.get_platform("xai-grok-bot")
        self.assertIsNotNone(p)
        self.assertEqual(p["cny_accessible"], "verified_blocked")
        self.assertIn("openai_compat", p["access_paths"])
        self.assertIn("browser_agent", p["access_paths"])

    def test_coze_reachable(self):
        p = self.pr.get_platform("bytedance-coze")
        self.assertIsNotNone(p)
        self.assertEqual(p["cny_accessible"], "reachable")
        self.assertIn("mcp", p["access_paths"], "Coze 必须支持 MCP")

    def test_deepseek_reachable_openai_compat(self):
        p = self.pr.get_platform("deepseek")
        self.assertIsNotNone(p)
        self.assertEqual(p["cny_accessible"], "reachable")
        self.assertIn("openai_compat", p["access_paths"])

    # ── 接入路径定义 ──

    def test_all_access_paths_defined(self):
        expected = {"mcp", "openai_compat", "connector_official",
                    "native_sdk", "browser_agent"}
        self.assertEqual(set(self.pr.ACCESS_PATHS.keys()), expected)

    def test_platforms_use_only_defined_access_paths(self):
        valid = set(self.pr.ACCESS_PATHS.keys())
        for pid, p in self.pr.PLATFORMS.items():
            for ap in (p.get("access_paths") or []):
                self.assertIn(ap, valid,
                              f"{pid} 使用了未定义的 access_path: {ap}")

    # ── 治理项映射 ──

    def test_all_gaps_have_provision_mapping(self):
        """每个平台的 gap 都映射到 GOVERNANCE_PROVISIONS。"""
        all_gaps = set()
        for p in self.pr.PLATFORMS.values():
            all_gaps.update(p.get("gaps") or [])
        for g in all_gaps:
            self.assertIn(g, self.pr.GOVERNANCE_PROVISIONS,
                          f"gap {g} 没有 provision 映射")

    def test_core_governance_provisions(self):
        core = {"portable_personal_identity", "cumulative_budget_governance",
                "connector_independent_review", "user_level_dispute_receipt"}
        for c in core:
            self.assertIn(c, self.pr.GOVERNANCE_PROVISIONS)

    # ── 查询 ──

    def test_list_platforms_no_filter(self):
        pl = self.pr.list_platforms()
        self.assertEqual(len(pl), self.pr.stats()["total_platforms"])

    def test_list_platforms_filter_reachable(self):
        pl = self.pr.list_platforms(cny_accessible="reachable")
        for p in pl:
            self.assertEqual(p["cny_accessible"], "reachable")

    def test_list_platforms_filter_mcp(self):
        pl = self.pr.list_platforms(access_path="mcp")
        for p in pl:
            self.assertIn("mcp", p["access_paths"])

    def test_get_platform_by_id(self):
        p = self.pr.get_platform("bytedance-coze")
        self.assertIsNotNone(p)
        self.assertEqual(p["id"], "bytedance-coze")

    def test_get_platform_unknown(self):
        p = self.pr.get_platform("nonexistent-xyz")
        self.assertIsNone(p)

    # ── 推荐引擎 ──

    def test_recommend_cn_filters_blocked(self):
        """大陆用户推荐时排除 verified_blocked 平台。"""
        recs = self.pr.recommend_platforms(
            user_country="CN",
            capabilities_needed=["portable_personal_identity"],
        )
        for r in recs:
            self.assertNotEqual(r.get("cny_accessible"), "verified_blocked",
                                f"大陆用户不应推荐不可达平台：{r['id']}")

    def test_recommend_us_includes_blocked(self):
        """美国用户能看到海外平台。"""
        recs = self.pr.recommend_platforms(
            user_country="US",
            capabilities_needed=["portable_personal_identity"],
        )
        ids = {r["id"] for r in recs}
        # 海外至少一家能上榜
        self.assertTrue(
            ids & {"meta-muse", "xai-grok-bot", "openai-chatgpt-agent",
                   "anthropic-claude-agent"},
            f"海外用户推荐里应有海外平台，实际: {ids}"
        )

    def test_recommend_prefers_mcp(self):
        """MCP 优先时，支持 MCP 的平台应该排前面。"""
        recs = self.pr.recommend_platforms(
            user_country="CN",
            capabilities_needed=["portable_personal_identity"],
            prefer_mcp=True,
        )
        if not recs:
            self.skipTest("无推荐结果")
        top = recs[0]
        self.assertIn("mcp", top["access_paths"],
                      f"top 推荐应该支持 MCP：{top['id']}")

    def test_recommend_scoring_decreasing(self):
        """推荐分数应该递减。"""
        recs = self.pr.recommend_platforms(
            user_country="CN",
            capabilities_needed=["portable_personal_identity"],
        )
        scores = [r["_score"] for r in recs]
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1],
                                    f"第 {i} 项分数应 ≥ 第 {i+1} 项")

    def test_recommend_no_match_returns_empty(self):
        """要求不存在的治理能力，返回空。"""
        recs = self.pr.recommend_platforms(
            user_country="CN",
            capabilities_needed=["nonexistent_capability_xyz"],
        )
        self.assertEqual(len(recs), 0)

    # ── 治理缺口矩阵 ──

    def test_gap_matrix_covers_all_platforms(self):
        matrix = self.pr.governance_gap_matrix()
        self.assertEqual(set(matrix.keys()), set(self.pr.PLATFORMS.keys()))

    def test_gap_matrix_entry_structure(self):
        matrix = self.pr.governance_gap_matrix()
        entry = matrix["meta-muse"]
        for k in ("platform_id", "name", "covered", "gaps",
                  "gaps_with_provisions"):
            self.assertIn(k, entry)
        self.assertEqual(entry["platform_id"], "meta-muse")
        self.assertIsInstance(entry["gaps_with_provisions"], dict)

    # ── 运行时注册 ──

    def test_register_new_platform(self):
        new = self.pr.register_platform(
            "test-runtime", name="TestRuntime", vendor="Test",
            family="developer", cny_accessible="reachable",
            access_paths=["mcp"],
        )
        self.assertEqual(new["id"], "test-runtime")
        p = self.pr.get_platform("test-runtime")
        self.assertIsNotNone(p)
        self.assertEqual(p["name"], "TestRuntime")

    def test_register_update_existing(self):
        """已存在的平台允许更新字段。"""
        self.pr.register_platform("meta-muse", name="Meta Muse (updated)")
        p = self.pr.get_platform("meta-muse")
        self.assertEqual(p["name"], "Meta Muse (updated)")

    def test_register_invalid_id(self):
        with self.assertRaises(ValueError):
            self.pr.register_platform("")
        with self.assertRaises(ValueError):
            self.pr.register_platform("123")

    # ── 与 personal_agent 集成 ──

    def test_register_instance_with_known_platform(self):
        from eco import personal_agent as pa
        pa.create_personal_did("alice@example.com")
        inst = pa.register_agent_instance(
            "alice@example.com", "GrokBot", "xAI",
            platform="xai-grok-bot", platform_tier="super_grok_heavy",
        )
        self.assertEqual(inst["platform"]["id"], "xai-grok-bot")
        self.assertTrue(inst["platform"]["known"])
        self.assertEqual(inst["platform"]["vendor"], "xAI")
        self.assertIn("portable_personal_identity",
                       inst["platform"].get("governance_gaps", []))
        self.assertEqual(inst["platform_tier"], "super_grok_heavy")

    def test_register_instance_with_unknown_platform(self):
        from eco import personal_agent as pa
        pa.create_personal_did("alice@example.com")
        inst = pa.register_agent_instance(
            "alice@example.com", "Unknown", "X",
            platform="nonexistent-xyz",
        )
        self.assertEqual(inst["platform"]["id"], "nonexistent-xyz")
        self.assertFalse(inst["platform"]["known"])
        self.assertEqual(inst["platform"].get("reason_unknown"),
                         "platform_id not in registry")

    def test_register_instance_legacy_hint_only(self):
        """旧 API 只用 platform_hint 仍然工作。"""
        from eco import personal_agent as pa
        pa.create_personal_did("alice@example.com")
        inst = pa.register_agent_instance(
            "alice@example.com", "Muse", "Meta",
            platform_hint="muse-ios",
        )
        self.assertIsNone(inst["platform"]["id"])
        self.assertEqual(inst["platform"]["hint"], "muse-ios")
        self.assertEqual(inst["platform_hint"], "muse-ios")

    def test_register_instance_platform_dict(self):
        """平台 dict 输入允许携带 capabilities_needed。"""
        from eco import personal_agent as pa
        pa.create_personal_did("alice@example.com")
        inst = pa.register_agent_instance(
            "alice@example.com", "CozeBot", "ByteDance",
            platform={"id": "bytedance-coze",
                      "capabilities_needed": ["personal_identity"]},
        )
        self.assertEqual(inst["platform"]["id"], "bytedance-coze")
        self.assertTrue(inst["platform"]["known"])
        self.assertEqual(
            inst["platform"]["capabilities_needed"],
            ["personal_identity"]
        )

    def test_get_platform_for_instance_reverse(self):
        from eco import personal_agent as pa
        pa.create_personal_did("alice@example.com")
        inst = pa.register_agent_instance(
            "alice@example.com", "Muse", "Meta", platform="meta-muse",
        )
        r = pa.get_platform_for_instance("alice@example.com",
                                          inst["instance_id"])
        self.assertTrue(r["found"])
        self.assertEqual(r["platform"]["id"], "meta-muse")

    def test_list_instances_by_platform(self):
        from eco import personal_agent as pa
        pa.create_personal_did("alice@example.com")
        for i in range(2):
            pa.register_agent_instance(
                "alice@example.com", f"GB-{i}", "xAI",
                platform="xai-grok-bot",
            )
        pa.register_agent_instance(
            "alice@example.com", "Muse-0", "Meta",
            platform="meta-muse",
        )
        list_x = pa.list_instances_by_platform(
            "alice@example.com", platform_id="xai-grok-bot")
        self.assertEqual(len(list_x), 2)
        for inst in list_x:
            self.assertEqual(inst["platform"]["id"], "xai-grok-bot")


if __name__ == "__main__":
    unittest.main(verbosity=2)
