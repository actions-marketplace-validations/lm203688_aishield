# -*- coding: utf-8 -*-
"""
IndexNow 收录链路测试

覆盖三件事：
  1. key 校验路由必须真的挂在 api/server.py 上（此前 indexnow-key.txt 躺在仓库里
     但从未被服务，key 不可校验，IndexNow 提交被搜索引擎静默拒收）。
  2. scripts/indexnow_submit.py 的行为契约：key 解析顺序、sitemap 解析、
     重试判据、退出码语义（网络失败绝不能算成功）。
  3. key 不能硬编码进提交脚本 / workflow —— 归档里那份 seo-submit.sh 就是反面教材。
  4. Bing sitemap ping 是 IndexNow 之外的第二条通知通道，两条都挂时必须都投。
  5. geo-faqs.json 每条 Q&A 必须自证（够长、带来源、来源不越界、无密钥）。
"""

import json
import os
import re
import sys
import unittest
from unittest import mock

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

import indexnow_submit as inow  # noqa: E402

STATIC = os.path.join(ROOT, 'api', 'static')
WORKFLOWS = os.path.join(ROOT, '.github', 'workflows')


def _port():
    return int(os.environ.get('AISHIELD_PORT', os.environ.get('PORT', 8450)))


def _server_up():
    """CI 不跑本地服务器时端点测试自动 skip；源码断言不受影响。"""
    import urllib.request
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{_port()}/api/v1/health',
                                    timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


class TestKeyFile(unittest.TestCase):
    """IndexNow key 文件必须存在、非空、且不是别的站点的 key。"""

    def test_key_file_exists(self):
        self.assertTrue(os.path.exists(inow.KEY_FILE),
                        "缺少 %s" % os.path.relpath(inow.KEY_FILE, ROOT))

    def test_key_file_non_empty(self):
        key = inow.KEY_FILE.read_text(encoding='utf-8').strip()
        self.assertGreater(len(key), 8)
        self.assertFalse(re.search(r'[\r\n]', key), "key 文件必须只有 key 原文")

    def test_key_is_not_the_archived_genetech_key(self):
        """归档里 13 站共用那个 key 不能被搬进来（跨站 key 会让提交被拒）。"""
        key = inow.KEY_FILE.read_text(encoding='utf-8').strip()
        self.assertNotEqual(key, 'kb3f8a2c9d7e1f4b6a5d8c3e7f9a2b4d')

    def test_host_is_aishield(self):
        self.assertEqual(inow.HOST, 'aishield.tools')


class TestResolveKey(unittest.TestCase):
    """key 解析顺序：env 优先，其次 key 文件，都缺就报错。"""

    def test_env_takes_precedence(self):
        self.assertEqual(inow.resolve_key('FROM_ENV'), 'FROM_ENV')

    def test_falls_back_to_file(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('INDEXNOW_KEY', None)
            key = inow.resolve_key()
        self.assertEqual(key, inow.KEY_FILE.read_text(encoding='utf-8').strip())
        self.assertGreater(len(key), 8)

    def test_missing_key_raises(self):
        """默认参数在函数定义时绑定，必须显式传 key_file 才能替换。"""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('INDEXNOW_KEY', None)
            with self.assertRaises(RuntimeError) as ctx:
                inow.resolve_key(key_file=type(inow.KEY_FILE)('/nonexistent/key.txt'))
        self.assertIn('IndexNow key', str(ctx.exception))

    def test_missing_key_exit_code_is_config_error(self):
        """退出码语义：找不到 key = 2（配置错误），绝不能是 0（成功）。"""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('INDEXNOW_KEY', None)
            with mock.patch.object(inow, 'KEY_FILE',
                                   type(inow.KEY_FILE)('/nonexistent/key.txt')):
                rc = inow.main(['--check-key'])
        self.assertEqual(rc, inow.EXIT_CONFIG)
        self.assertNotEqual(rc, inow.EXIT_OK)


class TestSitemapParsing(unittest.TestCase):
    def test_urls_extracted_from_real_sitemap(self):
        urls = inow.urls_from_sitemap(inow.DEFAULT_SITEMAP)
        self.assertGreater(len(urls), 5)
        for u in urls:
            self.assertTrue(u.startswith('https://aishield.tools'))

    def test_geo_assets_are_in_sitemap(self):
        """新加的发现资产必须进 sitemap，否则 IndexNow 永远不会通知到它们。"""
        urls = set(inow.urls_from_sitemap(inow.DEFAULT_SITEMAP))
        for path in ('/llms.txt', '/llms-full.txt', '/agent-discovery.json',
                     '/.well-known/ai-plugin.json', '/.well-known/agent.json'):
            self.assertIn('https://aishield.tools' + path, urls,
                          "sitemap 缺少 %s" % path)

    def test_missing_sitemap_raises(self):
        with self.assertRaises(RuntimeError):
            inow.urls_from_sitemap(type(inow.DEFAULT_SITEMAP)('/nonexistent.xml'))


class TestRetrySemantics(unittest.TestCase):
    """重试只针对 5xx/429/403；成功/明确失败不重试；网络失败不算成功。"""

    def test_retryable_set(self):
        self.assertEqual(inow.RETRYABLE, {403, 429, 500, 502, 503, 504})

    def test_status_404_is_not_retryable(self):
        self.assertNotIn(404, inow.RETRYABLE)
        self.assertNotIn(400, inow.RETRYABLE)

    def test_exit_codes_are_documented_and_distinct(self):
        codes = {inow.EXIT_OK, inow.EXIT_CONFIG, inow.EXIT_KEY_UNVERIFIABLE,
                 inow.EXIT_ALL_FAILED, inow.EXIT_NETWORK_UNREACHABLE}
        self.assertEqual(len(codes), 5, "退出码必须互不相同，否则调用方无法区分")
        self.assertNotEqual(inow.EXIT_OK, 0 - 1)
        # 关键：网络不可达与提交成功必须是不同退出码 —— 假绿的根因
        self.assertNotEqual(inow.EXIT_NETWORK_UNREACHABLE, inow.EXIT_OK)

    def test_submit_marks_429_and_202_correctly(self):
        with mock.patch.object(inow, '_open', side_effect=[
            (429, 'rate limited'),
            (200, 'ok'),
            (202, 'accepted'),
            (500, 'boom'),
            (None, 'unreachable'),
        ]), mock.patch.object(inow, 'time', mock.Mock(sleep=lambda s: None)):
            out = inow.submit(['https://aishield.tools/'], 'k',
                              ['e%d' % i for i in range(5)], 5, False, False)
        statuses = [r['status'] for r in out['results']]
        self.assertEqual(statuses, [429, 200, 202, 500, None])
        oks = [r['ok'] for r in out['results']]
        self.assertEqual(oks, [False, True, True, False, False])
        self.assertEqual(out['submitted'], 1)

    def test_submit_dry_run_makes_no_network_call(self):
        called = {'n': 0}

        def boom(*a, **k):
            called['n'] += 1
            return 200, ''

        with mock.patch.object(inow, '_open', side_effect=boom):
            out = inow.submit(['https://aishield.tools/'], 'k',
                              [inow.ENDPOINT_PRIMARY], 5, False, True)
        self.assertEqual(called['n'], 0, "--dry-run 绝不能发网络请求")
        self.assertTrue(out['dry_run'])
        self.assertEqual(out['payload']['host'], 'aishield.tools')
        self.assertEqual(len(out['payload']['urlList']), 1)


class TestKeyCheck(unittest.TestCase):
    def test_verifiable_only_when_body_matches_key(self):
        with mock.patch.object(inow, '_open', return_value=(200, 'KEYABC')):
            info = inow.check_key('KEYABC', 5, False)
        self.assertTrue(info['verifiable'])
        self.assertIn('https://aishield.tools/KEYABC.txt', info['url'])

    def test_wrong_body_is_not_verifiable(self):
        with mock.patch.object(inow, '_open',
                               return_value=(200, 'SOMETHING ELSE')):
            info = inow.check_key('KEYABC', 5, False)
        self.assertFalse(info['verifiable'])

    def test_404_is_not_verifiable(self):
        """线上当前的真实状态就是 404 —— 提交会被搜索引擎拒收。"""
        with mock.patch.object(inow, '_open',
                               return_value=(404, '{"error": "Not found"}')):
            info = inow.check_key('KEYABC', 5, False)
        self.assertFalse(info['verifiable'])
        self.assertEqual(info['status'], 404)


class TestRoutesWired(unittest.TestCase):
    """静态源码断言：key 校验路由必须真的挂在 server.py 上。

    不验证这个，脚本会永远在 job 1 报红灯，而且没人会去想「是路由没挂」。
    """

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, 'api', 'server.py'), encoding='utf-8') as f:
            cls.source = f.read()

    def test_indexnow_route_serves_key_at_expected_path(self):
        self.assertIn('indexnow-key.txt', self.source)
        self.assertIn('".txt"', self.source)
        self.assertIn('"text/plain; charset=utf-8"', self.source)

    def test_indexnow_route_is_not_a_wildcard(self):
        """必须是「key 原文 + .txt」的精确匹配，不能演变成任意静态文件服务。"""
        self.assertIn('_in_key and path == "/" + _in_key + ".txt"', self.source)

    def test_indexnow_route_has_cache_control(self):
        self.assertIn('max-age=86400', self.source)


class TestKeyRouteLive(unittest.TestCase):
    """服务器启动时验证 key 校验路由真的返回 key 原文。"""

    @unittest.skipUnless(_server_up(), "服务器未启动")
    def test_key_verification_url_returns_key(self):
        import urllib.request
        key = inow.KEY_FILE.read_text(encoding='utf-8').strip()
        with urllib.request.urlopen(
                f'http://127.0.0.1:{_port()}/{key}.txt', timeout=5) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.read().decode().strip(), key)

    @unittest.skipUnless(_server_up(), "服务器未启动")
    def test_wrong_key_url_is_404(self):
        """不能把任意 .txt 都当 key 文件返回 —— 必须精确匹配。"""
        import urllib.request
        import urllib.error
        try:
            urllib.request.urlopen(
                f'http://127.0.0.1:{_port()}/not-the-real-key.txt', timeout=5)
            self.fail("错误 key 路径竟然返回了 2xx")
        except urllib.error.HTTPError as e:
            self.assertNotIn(e.code, (200, 202))


class TestNoHardcodedSecrets(unittest.TestCase):
    """归档里的 seo-submit.sh 把 IndexNow key 硬编码进了脚本，不能重犯。"""

    _PATTERNS = [r'aishield2026indexnowkey', r'kb3f8a2c9d7e1f4b6a5d8c3e7f9a2b4d']

    def test_script_does_not_hardcode_any_key(self):
        script = os.path.join(ROOT, 'scripts', 'indexnow_submit.py')
        with open(script, encoding='utf-8') as f:
            text = f.read()
        for pattern in self._PATTERNS:
            self.assertNotIn(pattern, text)
        self.assertIn('INDEXNOW_KEY', text, "脚本必须支持从 env 读 key")

    def test_workflow_does_not_hardcode_any_key(self):
        wf = os.path.join(WORKFLOWS, 'geo-indexnow-submit.yml')
        self.assertTrue(os.path.exists(wf), "缺少 geo-indexnow-submit.yml")
        with open(wf, encoding='utf-8') as f:
            text = f.read()
        for pattern in self._PATTERNS:
            self.assertNotIn(pattern, text)

    def test_workflow_does_not_swallow_gate_failures(self):
        """提交与 key 校验步骤不能用 || true 吞掉失败。"""
        with open(os.path.join(WORKFLOWS, 'geo-indexnow-submit.yml'),
                  encoding='utf-8') as f:
            text = f.read()
        self.assertNotIn('indexnow_submit.py || true', text)
        self.assertNotIn('--check-key || true', text)
        self.assertNotIn('indexnow_submit.py 2>/dev/null', text)


class TestWorkflowShape(unittest.TestCase):
    """workflow 结构必须完整：先验 key、再提交、失败要告警。"""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(WORKFLOWS, 'geo-indexnow-submit.yml'),
                  encoding='utf-8') as f:
            cls.text = f.read()

    def test_has_daily_schedule(self):
        self.assertIn('schedule:', self.text)
        self.assertIn('cron:', self.text)

    def test_key_check_runs_before_submit(self):
        self.assertLess(self.text.index('key-check:'), self.text.index('submit:'))
        self.assertIn('needs: key-check', self.text)

    def test_escalates_failure_and_resolves_on_success(self):
        self.assertIn('--fingerprint geo-indexnow-broken', self.text)
        self.assertIn('--resolve', self.text)

    def test_state_bus_heartbeat(self):
        self.assertIn('state_bus.py set distribution', self.text)
        self.assertIn('--source geo-indexnow', self.text)

    def test_reacts_to_geo_asset_pushes(self):
        for path in ('api/static/llms.txt', 'api/static/robots.txt',
                     'api/static/agent-discovery.json',
                     'api/static/.well-known/ai-plugin.json',
                     'api/static/.well-known/agent.json',
                     'api/static/geo-faqs.json',
                     'api/static/indexnow-key.txt'):
            self.assertIn(path, self.text)

    def test_also_pings_bing(self):
        """IndexNow 之外的第二条通知通道：Bing sitemap ping。

        两者互不替代 —— IndexNow 校验 key 归属、失败会静默拒收；Bing ping 只做
        通知。都投，覆盖面更全。
        """
        self.assertIn('--ping-bing', self.text)


class TestBingPing(unittest.TestCase):
    """Bing sitemap ping —— 独立于 IndexNow 的通知通道。"""

    def test_ping_url_is_the_live_sitemap_not_a_local_path(self):
        """ping 必须指向线上 sitemap；搜索引擎读不到本地文件路径。"""
        called = {}

        def fake_open(url, method, body, headers, timeout, insecure):
            called['url'] = url
            called['method'] = method
            return 200, 'pong'

        with mock.patch.object(inow, '_open', side_effect=fake_open):
            res = inow.ping_bing('https://aishield.tools/sitemap.xml',
                                 5, False, dry_run=False)
        self.assertEqual(called['method'], 'GET')
        self.assertIn('https%3A%2F%2Faishield.tools%2Fsitemap.xml', called['url'])
        self.assertTrue(res['ok'])
        self.assertEqual(res['status'], 200)

    def test_ping_dry_run_does_not_call_network(self):
        with mock.patch.object(inow, '_open',
                               side_effect=AssertionError('dry-run 不应发请求')):
            res = inow.ping_bing('https://aishield.tools/sitemap.xml',
                                 5, False, dry_run=True)
        self.assertTrue(res['dry_run'])

    def test_ping_is_not_retryable_swallowed_as_success(self):
        """500 不应被判 ok。"""
        with mock.patch.object(inow, '_open', return_value=(500, 'boom')):
            res = inow.ping_bing('https://aishield.tools/sitemap.xml',
                                 5, False, dry_run=False)
        self.assertFalse(res['ok'])

    def test_bing_ping_can_rescue_all_failed_indexnow(self):
        """IndexNow 全挂但 Bing ping 成功 → 链路可用，不判 ALL_FAILED。"""
        key = inow.KEY_FILE.read_text(encoding='utf-8').strip()
        with mock.patch.object(inow, 'resolve_key', return_value=key), \
             mock.patch.object(inow, 'submit', return_value={
                 'dry_run': False, 'submitted': 2,
                 'results': [{'status': 500, 'ok': False}]}) as _s, \
             mock.patch.object(inow, 'ping_bing',
                               return_value={'ok': True, 'status': 200}) as pb:
            rc = inow.main(['--url', 'https://aishield.tools/',
                            '--ping-bing'])
        self.assertEqual(rc, inow.EXIT_OK)
        self.assertEqual(pb.call_count, 1)

    def test_all_failed_when_both_channels_fail(self):
        key = inow.KEY_FILE.read_text(encoding='utf-8').strip()
        with mock.patch.object(inow, 'resolve_key', return_value=key), \
             mock.patch.object(inow, 'submit', return_value={
                 'dry_run': False, 'submitted': 2,
                 'results': [{'status': 500, 'ok': False}]}), \
             mock.patch.object(inow, 'ping_bing',
                               return_value={'ok': False, 'status': 500}):
            rc = inow.main(['--url', 'https://aishield.tools/',
                            '--ping-bing'])
        self.assertEqual(rc, inow.EXIT_ALL_FAILED)


class TestGeoFaqsAsset(unittest.TestCase):
    """geo-faqs.json —— 给 AI 搜索引擎引用的 Q&A 资产。

    归档里的 daily-agent-geo.py 用 LLM 现场生成 FAQ。本仓改成静态人工撰写：
    每条答案必须能单独被检索命中并自证，不依赖其他条目。
    """

    def setUp(self):
        p = os.path.join(STATIC, 'geo-faqs.json')
        with open(p, encoding='utf-8') as f:
            self.data = json.load(f)

    def test_schema_and_shape(self):
        self.assertEqual(self.data['schema_version'], '1.0')
        faqs = self.data['faq']
        self.assertGreater(len(faqs), 10)

    def test_every_entry_is_self_contained(self):
        """每条都要有 question / answer / sources；answer 不能是空话。"""
        for i, item in enumerate(self.data['faq']):
            for field in ('category', 'question', 'answer', 'sources'):
                self.assertIn(field, item, f'第 {i} 条缺 {field}')
            self.assertGreater(len(item['answer']), 80,
                               f'第 {i} 条 answer 太短，不够自证')
            self.assertTrue(item['sources'], f'第 {i} 条缺 sources')

    def test_every_source_points_at_aishield_or_github(self):
        """引用源只能是自家域名或自家 GitHub，不指向外部站。"""
        allowed = ('https://aishield.tools',
                   'https://github.com/lm203688/aishield',
                   'https://www.npmjs.com/package/aishield-mcp-server')
        for item in self.data['faq']:
            for src in item['sources']:
                self.assertTrue(any(src.startswith(a) for a in allowed),
                                f'来源越界: {src}')

    def test_no_hardcoded_secrets(self):
        """归档里那个 13 站共用 key 绝不能进资产。"""
        blob = json.dumps(self.data, ensure_ascii=False)
        for secret in ('kb3f8a2c9d7e1f4b6a5d8c3e7f9a2b4d',
                       'xiaowu-internal-2026', 'aishield2026indexnowkey'):
            self.assertNotIn(secret, blob, f'资产里出现了密钥 {secret}')

    def test_route_registered_in_server(self):
        with open(os.path.join(ROOT, 'api', 'server.py'), encoding='utf-8') as f:
            src = f.read()
        self.assertIn('"/geo-faqs.json"', src)
        self.assertIn('geo-faqs.json', src)

    def test_listed_in_sitemap_and_robots(self):
        with open(os.path.join(STATIC, 'sitemap.xml'), encoding='utf-8') as f:
            self.assertIn('https://aishield.tools/geo-faqs.json', f.read())
        with open(os.path.join(STATIC, 'robots.txt'), encoding='utf-8') as f:
            self.assertIn('Allow: /geo-faqs.json', f.read())


if __name__ == '__main__':
    unittest.main(verbosity=2)
