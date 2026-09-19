"""
tests/test_trust_digest.py — 紧凑信任摘要 (aishield-digest/v1) 契约测试

被测对象：api/trust_api.py 的 trust_digest() / _digest_scan_result() / _digest_envelope()
以及它对外的两条路由 GET|POST /api/v1/trust/digest。

这个功能的存在理由只有一条：agent 每轮都要回答「能不能信」，而完整裁决报告
里 95% 的字段它用不上。所以这里的断言不是「能跑」，而是三件具体的事：

  1. **真的小** —— 主载荷几百字节量级。如果它比完整报告还大，这个功能就是
     负优化，不如不做。
  2. **指纹稳定** —— 同一份配置两次调用必须得到同一个指纹（否则「按指纹缓存」
     这个唯一的省钱机制不成立）；配置变了指纹必须变（否则会漏报变更）。
  3. **不泄密** —— 配置里带明文凭证时，摘要里绝不能出现凭证原文。摘要字段少
     是它天然的优势，但这是必须被钉死的不变量，不是可以依赖的巧合。
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

import trust_api  # noqa: E402


# 用拼接构造假凭证：字面量形式的 PAT 会被 push 前的 secret scanning 拦下（422）。
FAKE_PAT = 'ghp_' + ('a' * 30)

EVIL_CONFIG = json.dumps({
    'mcpServers': {
        'evil-mcp': {
            'command': 'npx',
            'args': ['-y', 'evil-mcp', '--token', FAKE_PAT],
        }
    }
})

CLEAN_CONFIG = json.dumps({
    'mcpServers': {
        'safe-mcp': {'command': 'uvx', 'args': ['safe-mcp']},
    }
})


class TestDigestCompactness(unittest.TestCase):
    def test_primary_payload_stays_small(self):
        """主载荷必须显著小于完整裁决 —— 这是整个功能的立足点。"""
        payload, status = trust_api.trust_digest(data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}})
        self.assertEqual(status, 200)
        blob = json.dumps(payload, ensure_ascii=False)
        self.assertLess(len(blob), 900,
                        '摘要 %d 字节，已失去"紧凑"的意义（实际: %s）' % (len(blob), blob[:200]))

    def test_collector_digest_is_not_nested_by_default(self):
        """collector digest 与摘要字段高度重叠，默认嵌进去等于把同一份信息发两遍。"""
        payload, _ = trust_api.trust_digest(data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}})
        self.assertNotIn('collector_digest', payload)
        payload2, _ = trust_api.trust_digest(
            data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}}, include_collector=True
        )
        self.assertIn('collector_digest', payload2)
        self.assertGreater(len(json.dumps(payload2, ensure_ascii=False)),
                           len(json.dumps(payload, ensure_ascii=False)))

    def test_max_findings_is_respected(self):
        payload, _ = trust_api.trust_digest(
            data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}}, max_findings=0
        )
        self.assertEqual(payload['top'], [])
        payload2, _ = trust_api.trust_digest(
            data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}}, max_findings=1
        )
        self.assertLessEqual(len(payload2['top']), 1)


class TestDigestIdentity(unittest.TestCase):
    def test_same_config_yields_same_fingerprint(self):
        """指纹是唯一的缓存钥匙；不稳定则缓存机制不成立。"""
        a, _ = trust_api.trust_digest(data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}})
        b, _ = trust_api.trust_digest(data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}})
        self.assertTrue(a['fingerprint'].startswith('sha256:'))
        self.assertEqual(a['fingerprint'], b['fingerprint'])

    def test_changed_config_changes_fingerprint(self):
        """指纹不变 = 裁决不变。配置变了指纹还不改，等于漏报变更。"""
        a, _ = trust_api.trust_digest(data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}})
        b, _ = trust_api.trust_digest(data={'configs': {'/tmp/mcp.json': CLEAN_CONFIG}})
        self.assertNotEqual(a['fingerprint'], b['fingerprint'])

    def test_envelope_digest_is_deterministic(self):
        """信封里没有 findings，摘要必须诚实地给空、而不是把缺失当零。"""
        p, s = trust_api.trust_digest(src='https://github.com/acme/nothing-here')
        self.assertEqual(s, 200)
        self.assertEqual(p['severity_counts'], {})
        self.assertIsNone(p['findings_total'])
        self.assertEqual(p['top'], [])
        p2, _ = trust_api.trust_digest(src='https://github.com/acme/nothing-here')
        self.assertEqual(p['fingerprint'], p2['fingerprint'])


class TestDigestRedaction(unittest.TestCase):
    def test_plaintext_credential_never_reaches_the_digest(self):
        """配置里有明文凭证时，摘要里不能出现凭证原文。

        摘要天然只有几个字段，但这必须是被钉死的不变量：一旦有人为了"更有用"
        往 top[] 里塞 evidence，这条测试就会红。
        """
        payload, _ = trust_api.trust_digest(data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}})
        blob = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn(FAKE_PAT, blob, '摘要泄露了明文凭证')
        self.assertNotIn(FAKE_PAT[:12], blob, '摘要泄露了凭证前缀')

    def test_digest_carries_its_honesty_flags(self):
        """no_spawn / offline 是给下游看的承诺，不能只在文档里。"""
        payload, _ = trust_api.trust_digest(data={'configs': {'/tmp/mcp.json': EVIL_CONFIG}})
        self.assertTrue(payload['no_spawn_guarantee'])
        self.assertTrue(payload['offline_scan'])
        self.assertEqual(payload['schema'], 'aishield-digest/v1')


class TestDigestRouting(unittest.TestCase):
    def test_get_without_target_is_a_400_not_a_guess(self):
        payload, status = trust_api.handle_get('/api/v1/trust/digest', '')
        self.assertEqual(status, 400)
        self.assertIn('error', payload)

    def test_get_with_src_returns_200(self):
        payload, status = trust_api.handle_get(
            '/api/v1/trust/digest', 'src=https://github.com/acme/thing'
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload['schema'], 'aishield-digest/v1')

    def test_get_max_findings_garbage_falls_back_instead_of_crashing(self):
        payload, status = trust_api.handle_get(
            '/api/v1/trust/digest', 'src=https://github.com/acme/thing&max_findings=notanint'
        )
        self.assertEqual(status, 200)
        self.assertIn('top', payload)

    def test_post_configs(self):
        payload, status = trust_api.handle_post(
            '/api/v1/trust/digest', {'configs': {'/tmp/mcp.json': EVIL_CONFIG}}
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload['schema'], 'aishield-digest/v1')

    def test_post_empty_body_is_a_400(self):
        payload, status = trust_api.handle_post('/api/v1/trust/digest', {})
        self.assertEqual(status, 400)

    def test_post_accepts_a_precomputed_scan_result(self):
        """已经有扫描结果的调用方不该被迫重扫一遍。"""
        fake_result = {
            'summary': {
                'config_score': 55,
                'findings_total': 1,
                'servers_found': 1,
                'severity_counts': {'high': 1},
            },
            'findings': [
                {'severity': 'high', 'type': 'hardcoded_credential', 'owasp_category': 'MCP01'}
            ],
        }
        payload, status = trust_api.handle_post(
            '/api/v1/trust/digest', {'scan_result': fake_result}
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload['score'], 55)
        self.assertEqual(payload['risk'], 'high')
        self.assertEqual(payload['findings_total'], 1)


class TestRiskBanding(unittest.TestCase):
    def test_risk_bands_are_monotone(self):
        """分数带必须单调：不能出现「比它高的分反而更危险」。"""
        cases = [(95, 'safe'), (80, 'safe'), (79, 'medium'), (60, 'medium'),
                 (59, 'high'), (40, 'high'), (39, 'critical'), (0, 'critical')]
        for score, expected in cases:
            self.assertEqual(trust_api._risk_from_score(score), expected,
                             'score=%s 应为 %s' % (score, expected))

    def test_unknown_score_is_unknown_not_safe(self):
        """没有分数时不能说 safe —— 「不知道」不等于「安全」。"""
        self.assertEqual(trust_api._risk_from_score(None), 'unknown')


if __name__ == '__main__':
    unittest.main(verbosity=2)
