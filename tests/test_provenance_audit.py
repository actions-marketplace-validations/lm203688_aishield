"""
tests/test_provenance_audit.py — 雷达规则 provenance 的可审计性契约

背景
----
`data/radar_rules.json` 的 provenance 原本只回答「这条规则从哪来」（情报标题 + URL +
攻击类别）。回答不了另一个问题：**当初为什么觉得该加它，期望它改变什么。**

半年后要判断一条规则是否还该留着，后者才是关键。借鉴 PrimeIntellect prime-agent 的
Continual Harness —— 每一次对 rules / memories 的写入都带 `trigger` 与
`intended_effect`，且可回滚 —— 这里把同一语义落到雷达规则上。

两条必须同时成立、缺一不可的性质：

  1. **新写入必须带全** —— 靠测试把 `promote_rule` 钉死，防止悄悄退回旧格式。
  2. **老数据必须能读** —— 缺失字段视为 legacy，加载器不得报错或隔离。
     一个"加了字段就读不了老文件"的改动，会把一次小升级变成一次事故。
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import promote_rule  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADAR_FILE = os.path.join(ROOT, 'data', 'radar_rules.json')


class TestShippedProvenanceIsComplete(unittest.TestCase):
    """仓库里当前这份数据必须条条可审计。"""

    def setUp(self):
        with open(RADAR_FILE, encoding='utf-8') as fh:
            self.data = json.load(fh)

    def test_every_rule_has_a_provenance_record(self):
        missing = [p for p in self.data['rules'] if p not in self.data.get('provenance', {})]
        self.assertEqual(missing, [], '规则缺少 provenance，无法回答"为什么有这条规则"')

    def test_every_record_carries_trigger_and_intended_effect(self):
        incomplete = []
        for pattern, meta in self.data['provenance'].items():
            if not isinstance(meta, dict):
                incomplete.append((pattern, 'not a dict'))
                continue
            for field in ('trigger', 'intended_effect'):
                if not str(meta.get(field) or '').strip():
                    incomplete.append((pattern[:60], 'missing ' + field))
        self.assertEqual(incomplete, [], 'provenance 缺少 trigger / intended_effect：%s' % incomplete)

    def test_trigger_points_at_a_real_source(self):
        """trigger 必须指向真实来源，不能是一句"因为需要"。

        判据：trigger 里要么带上来源情报标题/URL，要么点名晋升自哪个候选文件。
        """
        bad = []
        for pattern, meta in self.data['provenance'].items():
            trig = str(meta.get('trigger') or '')
            has_source = bool(meta.get('signal_url') or meta.get('signal_title')
                              or meta.get('promoted_from'))
            if not has_source:
                bad.append(pattern[:60])
            elif not (trig.startswith('signal:') or trig.startswith('promotion candidate:')):
                bad.append('%s -> %r' % (pattern[:40], trig[:60]))
        self.assertEqual(bad, [], 'trigger 未指向可核对来源：%s' % bad)


class TestProvenanceEntryBuilder(unittest.TestCase):
    """新建记录：候选自带就用自带的，没带就从真实字段派生。"""

    def test_explicit_candidate_values_win(self):
        entry = promote_rule._provenance_entry({
            'signal': {'title': 'T', 'url': 'U'},
            'attack_category': 'cat',
            'trigger': 'CVE-2026-9999 disclosure',
            'intended_effect': 'block the exploit chain',
        }, 'PROPOSED_x.json')
        self.assertEqual(entry['trigger'], 'CVE-2026-9999 disclosure')
        self.assertEqual(entry['intended_effect'], 'block the exploit chain')

    def test_missing_values_are_derived_not_invented(self):
        """派生值必须来自已有真实字段，不能凭空写一句好话。"""
        entry = promote_rule._provenance_entry({
            'signal': {'title': 'Some paper', 'url': 'https://arxiv.org/abs/1'},
            'attack_category': 'trajectory-poisoning',
        }, 'PROPOSED_y.json')
        self.assertIn('Some paper', entry['trigger'])
        self.assertIn('https://arxiv.org/abs/1', entry['trigger'])
        self.assertIn('trajectory-poisoning', entry['intended_effect'])

    def test_no_signal_falls_back_to_the_candidate_file(self):
        entry = promote_rule._provenance_entry({'attack_category': 'x'}, 'PROPOSED_z.json')
        self.assertIn('PROPOSED_z.json', entry['trigger'])

    def test_both_fields_are_never_empty(self):
        for data in ({}, {'signal': {}}, {'attack_category': ''}, {'signal': {'title': ''}}):
            entry = promote_rule._provenance_entry(data, 'PROPOSED_q.json')
            self.assertTrue(entry['trigger'].strip(), data)
            self.assertTrue(entry['intended_effect'].strip(), data)

    def test_simulate_carries_the_new_fields(self):
        """shadow 模拟也必须产出完整 provenance —— 否则 shadow 与真实晋升口径不一致。"""
        sim = promote_rule.simulate(
            {'rules': {}, 'provenance': {}},
            {'signal': {'title': 'T'}, 'attack_category': 'c',
             'rules': [{'pattern': r'foo\s*bar', 'description': 'd', 'severity': 'high'}]},
        )
        entry = sim['provenance'][r'foo\s*bar']
        self.assertTrue(entry.get('trigger'))
        self.assertTrue(entry.get('intended_effect'))


class TestLegacyDataStillLoads(unittest.TestCase):
    """向后兼容：老记录没有这两个字段，加载器必须照常接受。"""

    def setUp(self):
        import scanner.rules as scanner_rules
        self.rules = scanner_rules
        self.tmp = tempfile.mkdtemp(prefix='aishield_prov_legacy_')
        os.makedirs(os.path.join(self.tmp, 'data'), exist_ok=True)
        self.path = os.path.join(self.tmp, 'data', 'radar_rules.json')
        self._file = scanner_rules.__file__
        scanner_rules.__file__ = os.path.join(self.tmp, 'scanner', 'rules.py')

    def tearDown(self):
        self.rules.__file__ = self._file
        self.rules._load_radar_rules()
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _reload_with(self, provenance):
        with open(self.path, 'w', encoding='utf-8') as fh:
            json.dump({
                'version': 1,
                'rules': {r'legacy\s*rule': ['旧格式规则', 'high']},
                'provenance': provenance,
            }, fh)
        self.rules.RADAR_RULES = {}
        self.rules._load_radar_rules()
        return self.rules.get_radar_load_warnings()

    def test_legacy_provenance_without_new_fields_is_accepted(self):
        warnings = self._reload_with({
            r'legacy\s*rule': {'signal_title': 'old', 'signal_url': 'https://x'},
        })
        self.assertEqual(warnings, {}, '老格式 provenance 被当成问题拒收了')
        self.assertIn(r'legacy\s*rule', self.rules.RADAR_RULES)

    def test_missing_provenance_entirely_is_still_accepted(self):
        warnings = self._reload_with({})
        self.assertEqual(warnings, {})
        self.assertIn(r'legacy\s*rule', self.rules.RADAR_RULES)


if __name__ == '__main__':
    unittest.main(verbosity=2)
