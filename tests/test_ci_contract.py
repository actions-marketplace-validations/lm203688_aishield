"""
CI 门禁契约测试 — 锁定「门禁能读到分数」这条链路

背景（真实事故，2026-08-05）:
  security-scan.yml 用 `d.get('score', 0)` 读 /api/v1/audit 响应，
  但当时响应只有 `report.overall_score`，顶层无 score →
  门禁恒得 0 分 → 连红 17 次 / 48h，而被守护对象其实是健康的。

教训: 门禁连红时先怀疑门禁自己。
不变量: 门禁读取的每一个分数键，API 都必须真实提供。

本文件为纯静态契约测试，不依赖运行中的服务器、不依赖网络。
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PY = os.path.join(ROOT, 'api', 'server.py')
WORKFLOW = os.path.join(ROOT, '.github', 'workflows', 'security-scan.yml')

# API 承诺提供的分数取值路径（顶层键 / 嵌套容器键）
API_SCORE_KEYS = {'score', 'report', 'overall_score', 'badge_level', 'risk_level'}


def _read(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


class TestAuditResponseContract(unittest.TestCase):
    """/api/v1/audit 响应形状契约"""

    def setUp(self):
        self.src = _read(SERVER_PY)

    def test_audit_response_exposes_top_level_score(self):
        """顶层 score 字段存在且取自 overall_score —— CI 门禁的直接依赖"""
        self.assertRegex(
            self.src,
            r'"score":\s*result\.get\(\s*"overall_score"',
            "audit 响应缺少顶层 score 字段 —— CI 门禁将恒得 0 分",
        )

    def test_audit_response_keeps_nested_report(self):
        """report 嵌套结构不得被移除（既有消费方依赖）"""
        self.assertIn('"report": result,', self.src)

    def test_top_level_convenience_fields_present(self):
        """badge_level / risk_level 同步提升到顶层，便于 Agent 直读"""
        for key in ('"badge_level"', '"risk_level"'):
            self.assertIn(f'{key}: result.get(', self.src,
                          f'顶层缺少便捷字段 {key}')


class TestSecurityGateReadsRealKeys(unittest.TestCase):
    """门禁读取的键必须被 API 真实提供（跨文件一致性）"""

    def setUp(self):
        if not os.path.exists(WORKFLOW):
            self.skipTest('security-scan.yml 不存在')
        self.wf = _read(WORKFLOW)

    def _score_keys(self):
        """抽取门禁从 JSON 报告中读取的所有键名"""
        keys = set(re.findall(r"get\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]", self.wf))
        keys |= set(re.findall(r"d\.([A-Za-z_][A-Za-z0-9_]*)\s*\?\?", self.wf))
        return keys

    def test_every_key_the_gate_reads_is_served_by_api(self):
        """门禁读的键不能是 API 里不存在的幻觉字段（历史事故根因）"""
        unknown = self._score_keys() - API_SCORE_KEYS
        self.assertEqual(
            unknown, set(),
            f"门禁读取了 API 未提供的键 {sorted(unknown)} —— 会静默取到默认值",
        )

    def test_gate_reads_at_least_one_score_key(self):
        """门禁必须真的读分数，而不是空跑"""
        self.assertTrue(
            self._score_keys() & {'score', 'overall_score'},
            '门禁未引用任何分数字段',
        )

    def test_gate_threshold_is_explicit(self):
        """阈值必须写死在门禁里，便于审计"""
        self.assertRegex(self.wf, r'-lt\s+\d+|<\s*\d+|>=\s*\d+',
                         '门禁缺少显式分数阈值')


class TestActionEntrypointSeverityGate(unittest.TestCase):
    """GitHub Action 门禁的风险档推导 —— 锁定 fail_on=critical 可达

    背景（2026-09-16 自查，非历史事故）:
      旧 verdict_from 只从三档 overall_assessment 反推
      （danger->high / review->medium / 其余->safe），risk 永远到不了 critical。
      用户写 `fail_on: critical` 期望拿到更宽松的门禁，实际拿到一个永不触发的门禁
      （RISK_ORDER[high] < RISK_ORDER[critical]，而 risk 恒为 safe/medium/high）。
      这正是「门禁自己坏掉、被守护对象其实是健康的」这一类故障。
    """

    @classmethod
    def setUpClass(cls):
        import action_entrypoint as ae  # noqa: WPS433
        cls.ae = ae

    @staticmethod
    def _report(assess='safe', risk_level=None, findings=None):
        """构造一份最小合法 preflight 报告形状"""
        risky = bool(findings) or assess in ('review', 'danger')
        return {
            'summary': {
                'overall_assessment': assess,
                'overall_score': 40 if risky else 95,
                'risk_level': risk_level,
            },
            'aggregate_findings': findings or [],
        }

    def test_critical_finding_reaches_critical_risk(self):
        """critical 级 finding 必须把整体风险档顶到 critical"""
        _, risk = self.ae.verdict_from(
            self._report(assess='danger', findings=[{'severity': 'critical'}]))
        self.assertEqual(risk, 'critical')

    def test_fail_on_critical_is_reachable(self):
        """旧实现下此断言必然失败 —— risk 到不了 critical"""
        _, risk = self.ae.verdict_from(
            self._report(assess='danger', findings=[{'severity': 'critical'}]))
        self.assertGreaterEqual(
            self.ae.RISK_ORDER.get(risk, 0),
            self.ae.RISK_ORDER['critical'],
            'fail_on=critical 永不触发 —— 门禁静默失效',
        )

    def test_danger_assessment_still_maps_to_high(self):
        """向后兼容：无 finding 明细时仍按 assessment 兜底到 high"""
        _, risk = self.ae.verdict_from(self._report(assess='danger'))
        self.assertEqual(risk, 'high')

    def test_clean_scan_stays_safe(self):
        """干净扫描不得被误升档"""
        _, risk = self.ae.verdict_from(self._report())
        self.assertEqual(risk, 'safe')

    def test_verdict_only_escalates(self):
        """多来源取最高档，单调只升不降 —— finding 明细不得把高档降下来"""
        _, risk = self.ae.verdict_from(
            self._report(assess='danger', risk_level='critical',
                         findings=[{'severity': 'low'}]))
        self.assertEqual(risk, 'critical')

    def test_legacy_thresholds_unchanged(self):
        """既有 fail_on=high 语义不得改变（防回归）"""
        ae = self.ae
        for risk in ('medium', 'low', 'safe'):
            self.assertLess(ae.RISK_ORDER[risk], ae.RISK_ORDER['high'],
                            '%s 不应触发 fail_on=high' % risk)
        self.assertGreaterEqual(ae.RISK_ORDER['high'], ae.RISK_ORDER['high'])
        self.assertGreaterEqual(ae.RISK_ORDER['critical'], ae.RISK_ORDER['high'])

    def test_sarif_version_not_hardcoded_stale(self):
        """SARIF 版本的兜底值不得是写死的字面量 —— 会盖上一个不存在的版本号"""
        src = _read(os.path.join(ROOT, 'action_entrypoint.py'))
        self.assertRegex(
            src,
            r'build_sarif\(report,\s*report\.get\(\s*["\']scanner_version["\']\s*\)\s*or\s+SCANNER_VERSION',
            'SARIF 版本未从引擎常量兜底 —— 可能写死成过期字符串')
        # 调用点不得带字面量版本号兜底
        self.assertNotRegex(
            src,
            r'build_sarif\(report,\s*report\.get\([^)]*"[0-9]',
            'build_sarif 调用点存在硬编码版本兜底')

    def test_fail_on_typo_is_loud(self):
        """fail_on 拼错必须显式告警，不得静默按 high 处理"""
        src = _read(os.path.join(ROOT, 'action_entrypoint.py'))
        self.assertIn('不是合法风险档', src, 'fail_on 校验缺失')


class TestRunnerCoverage(unittest.TestCase):
    """run_all.py 的测试清单是硬编码的 —— 新文件未登记就会被静默跳过。

    背景（2026-09-16 自查，非历史事故）:
      tests/test_geo.py、tests/test_indexnow.py、tests/test_gap_fill.py
      长期不在清单里。run_all 照报"全绿"，但从未执行过它们 —— 本地绿而
      这些测试根本没跑，属于典型的假绿。
    """

    def _registered(self):
        src = _read(os.path.join(ROOT, 'tests', 'run_all.py'))
        names = re.findall(r"^\s*'tests\.([A-Za-z0-9_]+)',\s*$", src, re.M)
        self.assertTrue(names, 'run_all.py 未解析出任何测试模块')
        return set(names)

    @staticmethod
    def _on_disk():
        d = os.path.join(ROOT, 'tests')
        return {os.path.splitext(f)[0] for f in os.listdir(d)
                if f.startswith('test_') and f.endswith('.py')}

    def test_every_test_file_is_registered_in_runner(self):
        missing = self._on_disk() - self._registered()
        self.assertEqual(
            missing, set(),
            '下列测试文件存在但 run_all.py 从不执行（静默跳过 = 假绿）：\n  '
            + '\n  '.join(sorted(missing)))

    def test_runner_has_no_dangling_entries(self):
        """清单里不得登记不存在的文件（会被静默跳过，掩盖配置错误）"""
        dangling = self._registered() - self._on_disk()
        self.assertEqual(dangling, set(),
                         'run_all.py 登记了不存在的测试文件：' + ', '.join(sorted(dangling)))

    def test_runner_has_no_duplicate_entries(self):
        """清单不得重复登记同一模块。

        重复登记会让该模块整段跑两遍：拖慢 CI，更糟的是单个失败会在日志里
        重复出现两次，被误读成两个独立缺陷。2026-09-17 的 root 护栏事故正是
        这个假象 —— CI 连续全红，日志里「FAIL: test_root_refused」重复两次，
        看起来像两个问题，实际只有一个，而且掩盖了它其实是环境问题。
        上面 _registered() 返回 set 会自动去重，抓不到这种情况，所以这里
        直接比对原始列表。
        """
        src = _read(os.path.join(ROOT, 'tests', 'run_all.py'))
        names = re.findall(r"^\s*'tests\.([A-Za-z0-9_]+)',\s*$", src, re.M)
        dupes = sorted({n for n in names if names.count(n) > 1})
        self.assertEqual(dupes, [],
                         'run_all.py 重复登记了这些测试模块（会整段跑两遍）：'
                         + ', '.join('tests.' + d for d in dupes))


class TestMemoryBoundary(unittest.TestCase):
    """AIShield 自己的记忆目录不得出现凭证。

    背景（2026-09-16 自查，事实锚定）:
      `.workbuddy/memory/` 未被 .gitignore 排除，15 个文件已被推到公开仓库
      main 分支。内容属策略层泄露（竞品情报、决策理由）—— 已公开，清理需要
      rewrite history，属破坏性操作，留给人拍板。

      但凭证泄露是可拦截的那一类：本测试把 `.workbuddy/memory/` 全量扫一遍，
      把 fail-open 的危害从"泄露策略"降级为"泄露凭证会被 CI 拦下"。
      原则见 docs/memory-boundaries.md（记忆是上下文，不是可执行策略）。
    """

    # 与 scripts/indexnow_submit.py 的密钥处理、归档中被排除的文件同源。
    # 注意：这里写的是"模式"，任何真实取值都不得出现在仓库里。
    SECRET_PATTERNS = [
        r'ghp_[A-Za-z0-9]{20,}',          # GitHub PAT
        r'sk-[A-Za-z0-9]{20,}',           # OpenAI 类 key
        r'xox[baprs]-[A-Za-z0-9-]{10,}',  # Slack token
        r'AKIA[0-9A-Z]{16}',              # AWS access key
        r'CF_API_TOKEN\s*=\s*\S+',        # Cloudflare token 赋值
        r'aishield2026indexnowkey',       # 本项目 IndexNow key（曾泄露过一次）
        r'kb3f8a2c9d7e1f4b6a5d8c3e7f9a2b4d',  # 归档里另一份 IndexNow key
        r'private_key\s*=\s*0x[0-9a-fA-F]{20,}',
        r'seed_phrase',
        r'password\s*[:=]\s*\S+',
    ]

    def setUp(self):
        self.mem = os.path.join(ROOT, '.workbuddy', 'memory')

    def _files(self):
        out = []
        if not os.path.isdir(self.mem):
            return out
        for dirpath, _dirs, files in os.walk(self.mem):
            for f in files:
                out.append(os.path.join(dirpath, f))
        return out

    def test_memory_directory_has_no_credentials(self):
        """记忆目录必须零凭证 —— 记忆会被直接喂进模型，泄露即越权"""
        files = self._files()
        self.assertTrue(files, '.workbuddy/memory/ 应当存在（测试自身依赖它）')
        hits = []
        for p in files:
            with open(p, encoding='utf-8', errors='replace') as fh:
                text = fh.read()
            for pat in self.SECRET_PATTERNS:
                for m in re.finditer(pat, text, re.IGNORECASE):
                    hits.append('%s -> %r' % (os.path.relpath(p, ROOT),
                                              m.group(0)))
        self.assertEqual(
            hits, [],
            '.workbuddy/memory/ 出现凭证（该目录在公开仓库中）：\n  '
            + '\n  '.join(hits[:10]))

    def test_memory_policy_document_exists(self):
        """记忆边界原则必须成文，否则"只记事实不记指令"靠不住"""
        doc = os.path.join(ROOT, 'docs', 'memory-boundaries.md')
        self.assertTrue(os.path.exists(doc),
                        'docs/memory-boundaries.md 缺失 —— 记忆边界无成文依据')
        src = _read(doc)
        self.assertIn('只记事实', src, '文档缺少"只记事实、不记指令"这条核心规则')
        self.assertIn('不记凭证', src, '文档缺少"不记凭证"这条规则')

    def test_gitignore_documents_the_secret_exclusions(self):
        """排除规则必须是显式的 —— 隐式排除等于没有排除"""
        gi = _read(os.path.join(ROOT, '.gitignore'))
        self.assertIn('.secrets.json', gi)
        self.assertIn('*.key', gi)
        # 事实锚定：memory 目录当前**未**被排除（15 个文件已在公开仓库）。
        # 这条断言记录该现状，改成排除前必须先处理 git 历史。
        self.assertNotIn('.workbuddy/memory', gi,
                         '.gitignore 已排除 memory 目录但 git 历史未清理 —— '
                         '公开仓库里仍能取到旧内容')


if __name__ == '__main__':
    unittest.main(verbosity=2)
