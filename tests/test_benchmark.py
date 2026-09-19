"""
tests/test_benchmark.py — 安全基准 v1 的契约测试

被测对象：scripts/benchmark.py（基准语料 + 参数化矩阵 + 计分）。

基准这种东西最容易退化成一页好看的数字。所以这里钉住的不是「能跑」，而是四件
让它保持可信的性质：

  1. **确定性** —— 同一份代码跑两次必须得到完全相同的 JSON。只要有人引入随机
     采样或时间戳，数字就不再可比，基准也就不再是基准。
  2. **口径不可悄悄放宽** —— 召回下限与误报上限被写死在测试里。想降低标准就得
     改测试，改测试就会出现在 diff 里，藏不住。
  3. **语料不可悄悄缩减** —— 正负样本数有下限。删掉几个难缠的样本能让数字变好看，
     这条测试专门堵住这条路。
  4. **对照组保持干净** —— 良性样本里不得出现 `npx -y` / `--privileged` /
     `bash -c` 这类**本身就有风险**的写法。2026-09-19 首轮就把这个坑踩了：把风险
     启动器照搬进对照组，3 例真实检出被当成扫描器的误报记了一笔。

另外做了一次**隔离不变量**的源码级断言：基准脚本不得引入 socket / urllib /
requests / subprocess。一个"基准"如果能联网或执行被测对象，它测的就不是扫描器。
"""

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import benchmark as B  # noqa: E402


# 目标准入门槛（当前实测值：recall 0.96 / fp 0.0）。
# 留出一点余量，但不留太多 —— 门禁的意义是"退步就红"，不是"随便怎样都绿"。
MIN_RECALL = 0.95
MAX_FALSE_POSITIVE_RATE = 0.0

# 语料规模下限。删样本可以让任何指标变好看，这里堵住。
MIN_POSITIVES = 50
MIN_NEGATIVES = 30


class TestDeterminism(unittest.TestCase):
    def test_two_runs_produce_identical_json(self):
        a = json.dumps(B.run(), ensure_ascii=False, sort_keys=True)
        b = json.dumps(B.run(), ensure_ascii=False, sort_keys=True)
        self.assertEqual(a, b, '基准不确定 —— 数字不可比，基准失去意义')

    def test_corpus_builders_are_pure(self):
        """语料构造不能依赖全局状态：调两次结果必须一致。"""
        self.assertEqual(B.malicious_config_samples(), B.malicious_config_samples())
        self.assertEqual(B.benign_config_samples(), B.benign_config_samples())

    def test_result_declares_its_invariants(self):
        inv = B.run()["invariants"]
        self.assertFalse(inv["network_calls"])
        self.assertFalse(inv["executes_scanned_configs"])
        self.assertTrue(inv["deterministic"])


class TestQualityGates(unittest.TestCase):
    """把当前的质量水平锁住：退步就红。"""

    def setUp(self):
        self.result = B.run()
        self.summary = self.result["summary"]

    def test_recall_does_not_regress(self):
        self.assertGreaterEqual(
            self.summary["recall"], MIN_RECALL,
            '召回退化到 %.4f（下限 %.2f）' % (self.summary["recall"], MIN_RECALL))

    def test_false_positive_rate_does_not_regress(self):
        self.assertLessEqual(
            self.summary["false_positive_rate"], MAX_FALSE_POSITIVE_RATE,
            '误报率上升到 %.4f —— 误报比漏报更伤信任' % self.summary["false_positive_rate"])

    def test_no_serious_finding_fires_on_any_negative(self):
        """逐条点名：任何负样本上的 critical/high 都是缺陷，不是"统计噪声"。"""
        offenders = []
        for p in self.result["planes"]:
            offenders.extend(p.get("false_positive_ids") or [])
            offenders.extend("instruction_sample_#%d" % i
                             for i in p.get("false_positive_indices") or [])
        self.assertEqual(offenders, [], '负样本被误判：%s' % offenders)

    def test_corpus_has_not_been_shrunk(self):
        self.assertGreaterEqual(self.summary["positives"], MIN_POSITIVES,
                                '正样本被删到 %d 条（下限 %d）' % (self.summary["positives"], MIN_POSITIVES))
        self.assertGreaterEqual(self.summary["negatives"], MIN_NEGATIVES,
                                '负样本被删到 %d 条（下限 %d）' % (self.summary["negatives"], MIN_NEGATIVES))


class TestParameterization(unittest.TestCase):
    """参数化是这一版基准的核心借鉴定：一个意图 × 多种表面写法。"""

    def test_all_four_axes_are_exercised(self):
        axes = set()
        for s in B.malicious_config_samples():
            axes.update(k for k in s if k.startswith("axis_"))
        self.assertIn("axis_launcher", axes)
        self.assertIn("axis_credential", axes)
        self.assertIn("axis_transport", axes)
        self.assertIn("axis_risky_form", axes)

    def test_every_axis_bucket_has_at_least_two_variants(self):
        """每个轴至少两种写法 —— 只有一种写法的"轴"等于没测。

        `axis_risky_form` 是有意每种写法只放一条（它回答的是"仅凭写法够不够判"），
        所以单独豁免。
        """
        buckets = {}
        for s in B.malicious_config_samples():
            for k, v in s.items():
                if k.startswith("axis_"):
                    buckets.setdefault(k, set()).add(v)
        for axis, values in buckets.items():
            if axis == "axis_risky_form":
                continue
            self.assertGreaterEqual(len(values), 2,
                                    '%s 只有一种写法：%s' % (axis, values))

    def test_parameterization_is_not_cosmetic(self):
        """不同写法必须产生不同字节内容，否则"变体"只是标签。"""
        contents = [s["content"] for s in B.malicious_config_samples()]
        self.assertEqual(len(contents), len(set(contents)), '存在内容重复的"变体"')


class TestBenignControlsAreActuallyBenign(unittest.TestCase):
    """对照组必须干净，否则误报统计是假的。

    2026-09-19 首轮把 `npx -y` / `bash -c` / 无鉴权远程 URL 照搬进良性组，扫描器
    正确地报了 high，却被记成 3 例误报。差别不在扫描器，在对照组。
    """

    RISKY_MARKERS = ("npx -y", "-y ", "--privileged", "bash -c", "sh -c")

    def test_benign_configs_avoid_risky_launch_forms(self):
        offenders = []
        for s in B.benign_config_samples():
            low = s["content"].lower()
            for marker in self.RISKY_MARKERS:
                if marker in low:
                    offenders.append('%s 含风险写法 %r' % (s["id"], marker))
        self.assertEqual(offenders, [], '\n'.join(offenders))

    def test_benign_configs_do_not_carry_inline_credentials(self):
        """良性配置里放明文凭证就不是良性配置了 —— 那会制造记账混乱。"""
        for s in B.benign_config_samples():
            low = s["content"].lower()
            self.assertNotIn("ghp_", low, s["id"])
            self.assertNotIn("akia", low, s["id"])

    def test_defense_text_samples_are_present(self):
        """防御工具自述是误报重灾区，必须留在负样本里而不是被"优化"掉。"""
        self.assertGreaterEqual(len(B.DEFENSE_TEXT_SAMPLES), 5)
        joined = " ".join(B.DEFENSE_TEXT_SAMPLES).lower()
        self.assertIn("prompt injection", joined)


class TestBenchmarkIsolation(unittest.TestCase):
    """基准脚本不得联网、不得执行任何东西 —— 否则它测的不是扫描器。"""

    def setUp(self):
        self.src = open(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'benchmark.py'),
                        encoding='utf-8').read()

    def test_no_network_or_subprocess_imports(self):
        for bad in ('import socket', 'import urllib', 'import requests',
                    'import subprocess', 'from socket', 'import http.client'):
            self.assertNotIn(bad, self.src, '基准脚本引入了 %r' % bad)

    def test_marks_itself_as_a_benchmark_not_a_scanner(self):
        self.assertIn('aishield-security-benchmark/v1', self.src)


class TestCliGates(unittest.TestCase):
    def test_fail_flags_are_wired(self):
        """CI 门禁要能真的让退出码变红，不能只是打印。"""
        self.assertIn('--fail-under-recall', self.src_of_main())
        self.assertIn('rc = 1', self.src_of_main())

    def src_of_main(self):
        return open(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'benchmark.py'),
                    encoding='utf-8').read()

    def test_gate_returns_nonzero_on_impossible_threshold(self):
        rc = B.main(['--fail-under-recall', '1.5'])
        self.assertEqual(rc, 1, '不可能达到的阈值也必须让退出码变红')

    def test_gate_returns_zero_when_thresholds_are_satisfied(self):
        rc = B.main(['--fail-under-recall', '0.0', '--fail-over-fp', '1.0'])
        self.assertEqual(rc, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
