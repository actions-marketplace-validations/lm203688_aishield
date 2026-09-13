#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""契约：stale bot 不得关掉"内容渠道"与"未解决告警"。

两类 Issue 的正文本身就是资产或信号：
  · blog/content —— 发布渠道（正文即文章，可被检索/引用）
  · auto-alert   —— 未解决故障；被"长期无活动"关闭会伪装成已恢复（假绿）
stale bot 默认会把 30 天无活动的 Issue 标 stale、再过 7 天直接关闭。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows" / "stale.yml"

REQUIRED_EXEMPT = ("blog", "content", "auto-alert", "digest")


class TestStaleExemptions(unittest.TestCase):
    def setUp(self):
        self.text = WF.read_text(encoding="utf-8")

    def _exempt_labels(self):
        m = re.search(r"exempt-issue-labels:\s*'([^']*)'", self.text)
        self.assertIsNotNone(m, "缺少 exempt-issue-labels 配置")
        return {x.strip() for x in m.group(1).split(",")}

    def test_content_and_alert_labels_are_exempt(self):
        labels = self._exempt_labels()
        missing = [x for x in REQUIRED_EXEMPT if x not in labels]
        self.assertEqual(missing, [],
                         f"这些标签必须豁免，否则会被误关：{missing}")

    def test_alerts_are_not_closed_as_stale(self):
        # auto-alert 必须显式在豁免列表里（而非依赖 days-before-* 调大）
        self.assertIn("auto-alert", self._exempt_labels(),
                      "未解决告警被 stale bot 关闭 = 把故障伪装成已恢复")


if __name__ == "__main__":
    unittest.main()
