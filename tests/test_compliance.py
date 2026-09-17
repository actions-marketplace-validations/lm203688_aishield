# -*- coding: utf-8 -*-
"""
合规映射模块测试 — tests/test_compliance.py

红线：
    - 映射是静态知识，必须确定性（同输入同输出，无随机/无网络）
    - 全 20 个 OWASP 类别（MCP01-10 + ASI01-10）都要有映射，漏类 = 报告盲区
    - 未知类别/空输入不崩溃，unmapped 计数如实
    - 不输出"合规分数/合规结论"（中性信任机构红线）
"""
import unittest

from scanner.compliance import (
    CATEGORY_CONTROLS,
    MAESTRO_LAYER_NAMES,
    MAESTRO_THREAT_CODES,
    _CATEGORY_MAESTRO,
    compliance_summary,
    controls_for_category,
    FRAMEWORKS,
)


class TestCategoryCoverage(unittest.TestCase):
    def test_all_20_categories_mapped(self):
        for i in range(1, 11):
            self.assertIn("MCP%02d" % i, CATEGORY_CONTROLS)
            self.assertIn("ASI%02d" % i, CATEGORY_CONTROLS)

    def test_every_category_has_all_frameworks(self):
        """FRAMEWORKS 目前是 4 个（NIST/ISO/PCI + MAESTRO），漏一个 = 报告盲区。"""
        self.assertEqual(FRAMEWORKS, ("nist_csf", "iso27001", "pci_dss", "maestro"))
        for cat, m in CATEGORY_CONTROLS.items():
            for fw in FRAMEWORKS:
                self.assertTrue(m.get(fw), f"{cat} 缺 {fw} 映射")

    def test_control_codes_look_sane(self):
        """锚定检查：防止手滑写出错误体系的控制项编号。"""
        for m in CATEGORY_CONTROLS.values():
            for code in m["iso27001"]:
                self.assertTrue(code.startswith("A."), f"ISO 控制项格式异常: {code}")
            for code in m["nist_csf"]:
                self.assertRegex(code, r"^[A-Z]{2}\.[A-Z]{2}-\d+$", msg=code)


class TestMaestroMapping(unittest.TestCase):
    """CSA MAESTRO 7 层（+ OWASP 表内单列的 Cross-Layer 第 8 层）映射锚定。

    这是 2026-09-17 从 OWASP GenAI Security Project「Multi-Agentic system
    Threat Modelling Guide」v1.0 采纳的第 4 个框架。它回答的问题与
    NIST/ISO/PCI 不同：不是"上哪条控制"，而是"这条风险落在哪一层信任边界"。
    """

    def test_layer_names_are_the_eight_layers(self):
        self.assertEqual(
            sorted(MAESTRO_LAYER_NAMES),
            ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"])
        self.assertEqual(MAESTRO_LAYER_NAMES["L1"], "Foundation Model")
        self.assertEqual(MAESTRO_LAYER_NAMES["L8"], "Cross-Layer (Emergent)")

    def test_every_category_maps_to_a_valid_layer(self):
        for cat, layers in _CATEGORY_MAESTRO.items():
            self.assertTrue(layers, f"{cat} 未映射 MAESTRO 层")
            for layer in layers:
                self.assertIn(layer, MAESTRO_LAYER_NAMES,
                              f"{cat} 的 {layer} 不在 MAESTRO_LAYER_NAMES")

    def test_every_category_has_threat_codes(self):
        """T1–T15 是 OWASP 官方威胁编号；每类至少给一个锚点。"""
        for cat, codes in MAESTRO_THREAT_CODES.items():
            self.assertTrue(codes, f"{cat} 缺 T-code")
            for c in codes:
                self.assertRegex(c, r"^T\d{1,2}$", msg=f"{cat} 的 {c} 格式异常")

    def test_all_owasp_threat_codes_reachable(self):
        """T1–T15 每条都至少被一个类别引用 —— 否则 OWASP 有威胁我们无锚点。"""
        referenced = {c for codes in MAESTRO_THREAT_CODES.values() for c in codes}
        expected = {f"T{i}" for i in range(1, 16)}
        self.assertEqual(expected - referenced, set(),
                         f"OWASP 威胁未被任何类别覆盖: {sorted(expected - referenced)}")

    def test_category_keys_align_with_controls(self):
        """两张表必须覆盖同一批类别，否则单点查询会漏锚点。"""
        self.assertEqual(set(_CATEGORY_MAESTRO), set(MAESTRO_THREAT_CODES))

    def test_maestro_aggregates_into_summary(self):
        r = compliance_summary([{"owasp_category": "ASI04", "severity": "high"}])
        controls = r["frameworks"]["maestro"]["controls"]
        for layer in ("L2", "L8"):
            self.assertIn(layer, controls)
            self.assertEqual(controls[layer]["max_severity"], "high")

    def test_multi_layer_takes_highest_severity(self):
        findings = [
            {"owasp_category": "ASI04", "severity": "low"},     # L2, L8
            {"owasp_category": "ASI09", "severity": "critical"},  # L8, L7
        ]
        r = compliance_summary(findings)
        self.assertEqual(r["frameworks"]["maestro"]["controls"]["L8"]["max_severity"],
                         "critical")

    def test_cross_layer_is_distinct_from_ecosystem(self):
        """L7（生态）与 L8（跨层涌现）必须分开计数，否则多 agent 级联风险被埋掉。"""
        r = compliance_summary([{"owasp_category": "ASI09", "severity": "medium"}])
        controls = r["frameworks"]["maestro"]["controls"]
        self.assertIn("L7", controls)
        self.assertIn("L8", controls)

    def test_maestro_codes_are_layer_ids_only(self):
        """码只应是 L1–L8，不要把层名拼进去（与 NIST/ISO 的裸编号风格保持一致）。"""
        for m in CATEGORY_CONTROLS.values():
            for code in m["maestro"]:
                self.assertRegex(code, r"^L[1-8]$", msg=code)


class TestSummary(unittest.TestCase):
    def test_deterministic(self):
        findings = [{"owasp_category": "MCP01", "severity": "high"},
                    {"owasp_category": "MCP01", "severity": "critical"}]
        a = compliance_summary(list(findings))
        b = compliance_summary(list(reversed(findings)))
        # 聚合语义（计数/最高严重度）与顺序无关
        self.assertEqual(a["frameworks"], b["frameworks"])

    def test_counts_and_max_severity(self):
        findings = [
            {"owasp_category": "MCP05", "severity": "critical"},
            {"owasp_category": "MCP05", "severity": "medium"},
            {"owasp_category": "MCP04", "severity": "high"},
        ]
        r = compliance_summary(findings)
        self.assertEqual(r["categories_mapped"], 2)
        pci = r["frameworks"]["pci_dss"]["controls"]
        self.assertEqual(pci["6.2.4"]["findings_count"], 2)
        self.assertEqual(pci["6.2.4"]["max_severity"], "critical")

    def test_unmapped_counted_not_crash(self):
        findings = [{"type": "x"}, {"owasp_category": "MCP99", "severity": "low"}]
        r = compliance_summary(findings)
        self.assertEqual(r["findings_unmapped"], 2)
        self.assertEqual(r["categories_mapped"], 0)

    def test_empty_input(self):
        r = compliance_summary([])
        self.assertEqual(r["categories_mapped"], 0)
        self.assertEqual(r["findings_unmapped"], 0)
        for fw in FRAMEWORKS:
            self.assertEqual(r["frameworks"][fw]["controls_hit"], 0)

    def test_none_finding_items_tolerated(self):
        r = compliance_summary([None, "junk", {"owasp_category": "MCP08"}])
        self.assertEqual(r["categories_mapped"], 1)

    def test_no_compliance_verdict(self):
        """中性红线：输出里不得出现合规分数/通过结论。"""
        import json
        r = compliance_summary([{"owasp_category": "MCP01", "severity": "low"}])
        text = json.dumps(r, ensure_ascii=False)
        for banned in ("compliant", "score", "passed", "合规分数"):
            self.assertNotIn(banned, text.lower() if banned.isascii() else text)


class TestSingleQuery(unittest.TestCase):
    def test_known(self):
        m = controls_for_category("ASI03")
        self.assertIn("PR.AA-05", m["nist_csf"])

    def test_unknown_returns_empty(self):
        m = controls_for_category("MCP99")
        self.assertEqual(m, {fw: [] for fw in FRAMEWORKS})


if __name__ == "__main__":
    unittest.main()
