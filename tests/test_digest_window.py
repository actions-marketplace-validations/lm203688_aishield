#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""契约：项目迭代报告的"最近 24 小时"必须真的是 24 小时。

`gh run list` 本身没有时间窗口。若代码不按 createdAt 过滤，几天前的失败会被
计入"最近 24 小时"，进而让 overall 长期误报 DEGRADED（并且 WeCom 推送跟着误报）。
历史缺陷：`since` 变量被算出来却从未使用（--limit 50 直接当全量）。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows" / "project-digest.yml"


class TestDigestWindow(unittest.TestCase):
    def setUp(self):
        self.text = WF.read_text(encoding="utf-8")

    def test_runs_filtered_by_created_at(self):
        self.assertIn("_parse_ts", self.text, "缺少时间解析辅助")
        self.assertIn(">= cutoff", self.text,
                      "未按 24 小时窗口过滤 → 陈年失败会被当成当前失败并误报 DEGRADED")

    def test_dead_since_variable_removed(self):
        self.assertNotIn("since = (datetime.now(timezone.utc) - timedelta(hours=24))",
                         self.text,
                         "旧写法算了 since 却从未使用，必须替换为真实的 cutoff 过滤")

    def test_window_sample_is_wide_enough(self):
        self.assertIn("'--limit', '100'", self.text,
                      "limit 过小会让 24 小时窗口漏采样，导致统计不完整")

    def test_published_reads_real_ledger(self):
        """已发布数必须读 distribution/published.json。

        data/state/published.json 是空壳 {}，读它会让"已发布"永远是 0。
        """
        self.assertIn("distribution/published.json", self.text,
                      "读错台账 → 已发布数恒为 0")
        self.assertNotIn("pub_path = 'data/state/published.json'", self.text)

    def test_webhook_reuses_single_verdict(self):
        """正文与推送必须共用同一个 overall，避免同一事实算两遍而互相矛盾。"""
        self.assertIn("/tmp/overall.txt", self.text)
        self.assertIn("f.write(overall)", self.text)


if __name__ == "__main__":
    unittest.main()
