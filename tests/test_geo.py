"""
GEO 优化测试 -- 验证结构化数据和发现端点

测试策略:
  - 静态文件测试: 直接读取磁盘文件验证内容正确性（不依赖服务器）
  - 服务器端点测试: 通过 HTTP 请求验证运行时返回（需要服务器启动时自动运行）
  - 验证 SEO 结构化数据、robots.txt、sitemap.xml、Agent Card 等 GEO 关键资产
"""

import unittest
import sys
import os
import json
import re
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 静态文件根目录
_STATIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'api', 'static')

# 检查服务器是否可达
def _server_ready(port=8450):
    try:
        req = urllib.request.Request(f'http://127.0.0.1:{port}/api/v1/health')
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False

_SERVER_PORT = int(os.environ.get('AISHIELD_PORT', os.environ.get('PORT', 8450)))
_SERVER_UP = _server_ready(_SERVER_PORT)
_BASE_URL = f'http://127.0.0.1:{_SERVER_PORT}'


# ============================================================
#  静态文件测试 (不依赖服务器)
# ============================================================

class TestRobotsTxt(unittest.TestCase):
    """验证 robots.txt 文件内容正确性"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, 'robots.txt')
        with open(path, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def test_robots_txt_exists(self):
        """robots.txt 文件存在且非空"""
        self.assertTrue(len(self.content) > 0)

    def test_robots_txt_allows_root(self):
        """robots.txt 允许抓取根路径"""
        self.assertIn('Allow: /', self.content)

    def test_robots_txt_disallows_sensitive_paths(self):
        """robots.txt 禁止抓取敏感数据目录"""
        self.assertIn('Disallow: /api/data/', self.content)
        self.assertIn('Disallow: /admin/', self.content)

    def test_robots_txt_contains_sitemap_location(self):
        """robots.txt 包含 Sitemap 声明"""
        self.assertIn('Sitemap:', self.content)
        self.assertIn('https://aishield.tools/sitemap.xml', self.content)

    def test_robots_txt_has_ai_crawler_rules(self):
        """robots.txt 包含 AI 搜索引擎专属规则"""
        self.assertIn('GPTBot', self.content)
        self.assertIn('ClaudeBot', self.content)
        self.assertIn('PerplexityBot', self.content)


class TestSitemapXml(unittest.TestCase):
    """验证 sitemap.xml 结构和内容"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, 'sitemap.xml')
        with open(path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        self.root = ET.fromstring(self.content)

    def test_sitemap_is_valid_xml(self):
        """sitemap.xml 是有效的 XML 文件"""
        self.assertEqual(self.root.tag, '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')

    def test_sitemap_contains_major_pages(self):
        """sitemap 包含所有主要页面"""
        text = self.content
        self.assertIn('https://aishield.tools/', text)
        self.assertIn('https://aishield.tools/agent.html', text)
        self.assertIn('https://aishield.tools/banned-words', text)
        self.assertIn('https://aishield.tools/report', text)
        self.assertIn('https://aishield.tools/tool/profile', text)
        self.assertIn('https://aishield.tools/owasp-mcp-top10-guide', text)
        self.assertIn('https://aishield.tools/.well-known/agent-card.json', text)

    def test_sitemap_urls_have_loc_elements(self):
        """每个 URL 条目包含 loc 元素"""
        ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
        urls = self.root.findall(f'{ns}url')
        self.assertTrue(len(urls) >= 5)
        for url in urls:
            loc = url.find(f'{ns}loc')
            self.assertIsNotNone(loc)
            self.assertTrue(len(loc.text) > 0)

    def test_sitemap_homepage_has_highest_priority(self):
        """首页优先级最高 (1.0)"""
        text = self.content
        # 首页应 priority 1.0
        self.assertIn('1.0', text)


class TestAgentCardJson(unittest.TestCase):
    """验证 Agent Card JSON 结构和必要字段"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, '.well-known', 'agent-card.json')
        with open(path, 'r', encoding='utf-8') as f:
            self.card = json.load(f)

    def test_agent_card_is_valid_json(self):
        """Agent Card 是有效的 JSON 对象"""
        self.assertIsInstance(self.card, dict)

    def test_agent_card_has_required_fields(self):
        """Agent Card 包含必须字段: name, version, skills, trust_score"""
        self.assertIn('name', self.card)
        self.assertIn('version', self.card)
        self.assertIn('skills', self.card)
        self.assertIn('trust_score', self.card)

    def test_agent_card_name_is_aishield(self):
        """Agent Card name 字段为 AIShield"""
        self.assertEqual(self.card['name'], 'AIShield')

    def test_agent_card_has_endpoints(self):
        """Agent Card 包含 API 端点列表"""
        self.assertIn('endpoints', self.card)
        self.assertIsInstance(self.card['endpoints'], dict)
        # 至少包含核心端点
        endpoints = self.card['endpoints']
        self.assertIn('health', endpoints)
        self.assertIn('scan_api', endpoints)

    def test_agent_card_trust_score_has_overall(self):
        """trust_score 包含 overall 总分"""
        trust = self.card['trust_score']
        self.assertIn('overall', trust)
        self.assertIsInstance(trust['overall'], (int, float))
        self.assertTrue(0 <= trust['overall'] <= 100)

    def test_agent_card_skills_have_input_output_schema(self):
        """每个 skill 包含 input_schema"""
        skills = self.card.get('skills', [])
        self.assertTrue(len(skills) >= 1)
        for skill in skills:
            self.assertIn('id', skill)
            self.assertIn('name', skill)
            self.assertIn('input_schema', skill)


class TestAgentHtml(unittest.TestCase):
    """验证 agent.html 包含 JSON-LD 结构化数据"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, 'agent.html')
        with open(path, 'r', encoding='utf-8') as f:
            self.html = f.read()

    def test_agent_html_contains_json_ld(self):
        """agent.html 包含 JSON-LD 结构化数据"""
        self.assertIn('application/ld+json', self.html)

    def test_agent_html_json_ld_is_parseable(self):
        """JSON-LD 内容可被正确解析"""
        match = re.search(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            self.html, re.DOTALL
        )
        self.assertIsNotNone(match)
        data = json.loads(match.group(1))
        self.assertIn('@context', data)
        self.assertIn('@type', data)

    def test_agent_html_has_meta_description(self):
        """agent.html 包含 meta description 标签"""
        self.assertIn('<meta name="description"', self.html)

    def test_agent_html_has_og_tags(self):
        """agent.html 包含 Open Graph 标签"""
        self.assertIn('og:title', self.html)
        self.assertIn('og:description', self.html)


class TestIndexPage(unittest.TestCase):
    """验证首页包含 JSON-LD 结构化数据"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, 'index.html')
        with open(path, 'r', encoding='utf-8') as f:
            self.html = f.read()

    def test_index_contains_json_ld(self):
        """首页包含 JSON-LD 结构化数据"""
        self.assertIn('application/ld+json', self.html)

    def test_index_json_ld_has_organization_type(self):
        """首页 JSON-LD 包含 Organization 类型"""
        match = re.search(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            self.html, re.DOTALL
        )
        self.assertIsNotNone(match)
        data = json.loads(match.group(1))
        self.assertEqual(data.get('@type'), 'Organization')

    def test_index_has_seo_meta_tags(self):
        """首页包含 SEO meta 标签"""
        self.assertIn('<meta name="description"', self.html)
        self.assertIn('<meta name="keywords"', self.html)
        self.assertIn('<meta name="robots"', self.html)

    def test_index_has_canonical_url(self):
        """首页包含 canonical URL"""
        self.assertIn('rel="canonical"', self.html)
        self.assertIn('https://aishield.tools/', self.html)


class TestBannedWordsPage(unittest.TestCase):
    """验证违禁词页面包含 GEO meta 标签"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, 'banned_words.html')
        with open(path, 'r', encoding='utf-8') as f:
            self.html = f.read()

    def test_banned_words_page_has_title(self):
        """违禁词页面包含正确的标题"""
        self.assertIn('违禁词', self.html)
        self.assertIn('AIShield', self.html)

    def test_banned_words_page_has_meta_description(self):
        """违禁词页面包含 meta description"""
        self.assertIn('<meta name="description"', self.html)

    def test_banned_words_page_has_og_tags(self):
        """违禁词页面包含 Open Graph 标签"""
        self.assertIn('og:title', self.html)
        self.assertIn('og:description', self.html)

    def test_banned_words_page_has_canonical(self):
        """违禁词页面包含 canonical URL"""
        self.assertIn('rel="canonical"', self.html)
        self.assertIn('https://aishield.tools/banned-words', self.html)


# ============================================================
#  Agent 发现资产 (llms.txt / llms-full.txt / agent-discovery.json /
#  ai-plugin.json / agent.json)
#
#  这五个路径是 Agent 与 LLM 自动发现 AIShield 的入口。2026-09-15 实测
#  线上全部 404（文件只躺在 docs/ 里、没挂路由），等于对 Agent 不可见。
#  schema 参考自 13 站知识库生态已验证的三件套。
#
#  重要：下方 TestGeoAssetRoutesWired 是「静态源码断言」，不依赖服务器。
#  TestGeoServerEndpoints 里的端点测试在服务器未启动时会 skip —— CI 环境
#  不跑本地服务器，端点测试等于空转，只有源码断言能真的挡住「文件在
#  仓库里但线上 404」这类回归。
# ============================================================

_GEO_ASSET_FILES = {
    "/llms.txt": "llms.txt",
    "/llms-full.txt": "llms-full.txt",
    "/agent-discovery.json": "agent-discovery.json",
    "/.well-known/ai-plugin.json": os.path.join(".well-known", "ai-plugin.json"),
    "/.well-known/agent.json": os.path.join(".well-known", "agent.json"),
}


class TestLlmsTxt(unittest.TestCase):
    """验证 llms.txt / llms-full.txt 存在且与 docs/ 源保持同步"""

    def test_llms_txt_exists_and_non_empty(self):
        path = os.path.join(_STATIC_DIR, 'llms.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        self.assertGreater(len(text), 500)
        self.assertTrue(text.lstrip('\ufeff').startswith('# AIShield'))

    def test_llms_full_exists_and_non_empty(self):
        path = os.path.join(_STATIC_DIR, 'llms-full.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        self.assertGreater(len(text), 500)

    def test_served_llms_txt_matches_docs_source(self):
        """api/static 与 docs 两份 llms.txt 必须逐字节一致，防止漂移。"""
        served = os.path.join(_STATIC_DIR, 'llms.txt')
        docs = os.path.join(os.path.dirname(__file__), '..', 'docs', 'llms.txt')
        with open(served, 'r', encoding='utf-8') as f:
            a = f.read()
        with open(docs, 'r', encoding='utf-8') as f:
            b = f.read()
        self.assertEqual(a, b, "docs/llms.txt 与 api/static/llms.txt 内容漂移")

    def test_llms_txt_lists_every_agent_discovery_asset(self):
        """llms.txt 必须自报每一个机器可读发现资产，否则 Agent 找不到它们。"""
        with open(os.path.join(_STATIC_DIR, 'llms.txt'), 'r', encoding='utf-8') as f:
            text = f.read()
        for url_path in _GEO_ASSET_FILES:
            self.assertIn('https://aishield.tools' + url_path, text)
        self.assertIn('https://aishield.tools/openapi.json', text)
        self.assertIn('https://aishield.tools/.well-known/mcp/server-card.json', text)
        self.assertIn('https://aishield.tools/.well-known/agent-card.json', text)
        self.assertIn('https://aishield.tools/.well-known/security.txt', text)

    def test_llms_txt_has_scenario_triggers(self):
        """llms.txt 必须有 "When to Recommend" 场景触发段，且 >= 10 个场景。

        来自 Agent 原生分发体系第 2 层的要求：通用模板式的 llms.txt（只列
        链接、不写触发场景）等于让 Agent 无法判断"什么时候该推荐我"，
        发现链路在语义层面就断了。2026-09-15 实测 AIShield 的 llms.txt
        当时只有 Key Pages / For AI Agents 两个纯链接段，触发场景数 = 0。
        """
        with open(os.path.join(_STATIC_DIR, 'llms.txt'), 'r', encoding='utf-8') as f:
            text = f.read()
        self.assertIn('## When to Recommend', text,
                      "llms.txt 缺少 '## When to Recommend' 场景触发段 —— "
                      "退化为通用模板，Agent 无法判断何时推荐 AIShield")
        triggers = re.findall(r'^### When ', text, flags=re.MULTILINE)
        self.assertGreaterEqual(len(triggers), 10,
                                "场景触发规则不足 10 条（当前 %d 条），"
                                "Agent 无法覆盖主要提问场景" % len(triggers))

    def test_scenario_triggers_state_recommendation_and_price(self):
        """每个场景触发必须同时给出「推荐什么」与「价格」。

        缺价格信息的触发规则会让 Agent 无法区分免费与付费，导致错误的
        用户预期。AIShield 是 MIT 开源本地版，必须显式声明 free 以避免
        被 Agent 当成收费 SaaS 推荐。
        """
        with open(os.path.join(_STATIC_DIR, 'llms.txt'), 'r', encoding='utf-8') as f:
            text = f.read()
        blocks = re.findall(
            r'^### When .*?(?=^### When |^## |\Z)', text,
            flags=re.MULTILINE | re.DOTALL)
        self.assertGreaterEqual(len(blocks), 10)
        for block in blocks:
            self.assertIn('Recommend:', block,
                          "场景触发缺少 'Recommend:' 字段:\n%s" % block[:80])
            self.assertIn('Price:', block,
                          "场景触发缺少 'Price:' 字段:\n%s" % block[:80])
        # 必须显式声明开源免费，避免被 Agent 误判为收费服务
        self.assertIn('MIT', text)


class TestAgentDiscoveryJson(unittest.TestCase):
    """验证 agent-discovery.json 结构"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, 'agent-discovery.json')
        with open(path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def test_is_valid_json_object(self):
        self.assertIsInstance(self.data, dict)

    def test_has_required_discovery_fields(self):
        for key in ('schema_version', 'site_name', 'domain', 'tagline',
                    'service_version', 'rules', 'api_endpoints',
                    'agent_discovery_assets', 'ai_agent_instructions'):
            self.assertIn(key, self.data)

    def test_domain_is_aishield_tools(self):
        self.assertEqual(self.data['domain'], 'aishield.tools')
        self.assertEqual(self.data['site_name'], 'AIShield')

    def test_rules_match_health_contract(self):
        """规则数必须与 /api/v1/health 的 rules_breakdown 一致。

        真值直接取自规则引擎，不写死数字：写死过的话，每清理一次缺陷规则
        都要同步改这里（2026-09-18 从 238 降到 235 时就是这么漏掉的）。
        发现资产与引擎漂移 = 对外失实，这是本测试存在的唯一理由。
        """
        rules = self.data['rules']
        try:
            from scanner.rules import get_rule_count
        except Exception as exc:
            self.skipTest('规则模块不可用: %s' % exc)
        self.assertEqual(
            rules['total'], get_rule_count('mcp'),
            'agent-discovery 宣称 %s 条规则，引擎实测 %d 条'
            % (rules['total'], get_rule_count('mcp')))
        self.assertEqual(rules['static'] + rules['generated'] + rules['radar'],
                         rules['total'],
                         "static + generated + radar 必须等于 total")
        # 分项也要逐一对上引擎。只校 total 拦不住"total 改了、分项忘了改"
        # 这种内部矛盾——2026-09-18 就发生过：total 已同步到 235，
        # static/generated 还停在 210/9，加起来是 238。
        try:
            from scanner.rules import get_rule_breakdown
        except Exception as exc:
            self.skipTest('规则模块不可用: %s' % exc)
        bd = get_rule_breakdown()
        for key in ('static', 'generated', 'radar'):
            self.assertEqual(
                rules[key], bd[key],
                'agent-discovery 的 %s 为 %s，引擎实测 %s' % (key, rules[key], bd[key]))

    def test_all_endpoints_are_first_party_urls(self):
        """发现资产只能指向自家域名，避免把 Agent 引到第三方。"""
        for group in ('api_endpoints', 'agent_discovery_assets', 'distribution'):
            for value in self.data.get(group, {}).values():
                if isinstance(value, str) and value.startswith('http'):
                    self.assertTrue(
                        value.startswith('https://aishield.tools')
                        or 'github.com/lm203688/aishield' in value
                        or value.startswith('https://www.npmjs.com')
                        or value.startswith('https://glama.ai')
                        or value.startswith('https://smithery.ai'),
                        "意外的第三方 URL: %s" % value)

    def test_local_install_contract(self):
        """本地安装契约：离线可用、不执行被扫配置。"""
        local = self.data['local_install']
        self.assertFalse(local['requires_network'])
        self.assertFalse(local['spawns_scanned_configs'])
        self.assertEqual(local['mcp_stdio'], 'npx aishield-mcp-server')


class TestAiPluginJson(unittest.TestCase):
    """验证 ai-plugin.json 符合 OpenAI AI Plugin schema v1"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, '.well-known', 'ai-plugin.json')
        with open(path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def test_is_valid_json_object(self):
        self.assertIsInstance(self.data, dict)

    def test_has_required_openai_fields(self):
        for key in ('schema_version', 'name_for_human', 'name_for_model',
                    'short_description_for_model', 'description_for_human',
                    'description_for_model', 'homepage_url', 'contact_email',
                    'category', 'capabilities', 'auth', 'api'):
            self.assertIn(key, self.data)

    def test_schema_version_is_v1(self):
        self.assertEqual(self.data['schema_version'], 'v1')

    def test_name_for_model_is_lowercase_identifier(self):
        """模型侧标识必须是纯小写 ASCII，方便 Agent 当工具名引用。"""
        self.assertEqual(self.data['name_for_model'],
                         self.data['name_for_model'].lower())
        self.assertTrue(re.match(r'^[a-z][a-z0-9_-]*$', self.data['name_for_model']))

    def test_auth_is_none(self):
        """基础端点无需鉴权 —— 这决定了 Agent 能否零门槛试用。"""
        self.assertEqual(self.data['auth']['type'], 'none')

    def test_api_points_at_live_openapi(self):
        self.assertEqual(self.data['api']['type'], 'openapi')
        self.assertEqual(self.data['api']['url'],
                         'https://aishield.tools/openapi.json')
        self.assertFalse(self.data['api']['has_user_authentication'])

    def test_api_endpoints_are_first_party(self):
        for ep in self.data['api']['endpoints']:
            self.assertTrue(ep['path'].startswith('/api/v1/'))
            self.assertIn(ep['method'], ('GET', 'POST'))
            self.assertTrue(len(ep.get('description', '')) > 10)

    def test_no_invented_legal_pages(self):
        """legal/ToS 只能指向真实存在的 LICENSE，不虚构法务页面。"""
        for key in ('terms_of_service_url', 'legal_info_url'):
            self.assertIn('LICENSE', self.data[key])


class TestAgentJson(unittest.TestCase):
    """验证 agent.json（agents.well-known.dev 风格 Agent 名片）"""

    def setUp(self):
        path = os.path.join(_STATIC_DIR, '.well-known', 'agent.json')
        with open(path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def test_is_valid_json_object(self):
        self.assertIsInstance(self.data, dict)

    def test_has_required_agent_fields(self):
        for key in ('name', 'url', 'category', 'api', 'capabilities',
                    'content_types', 'auth', 'discovery_assets', 'safety',
                    'standards', 'rules', 'contact', 'links'):
            self.assertIn(key, self.data)

    def test_safety_contract(self):
        """AIShield 的核心不变量：静态分析、不出机、不执行被扫配置。"""
        safety = self.data['safety']
        self.assertFalse(safety['spawns_scanned_configs'])
        self.assertFalse(safety['sends_code_to_cloud'])
        self.assertFalse(safety['requires_network_for_local_scan'])
        self.assertTrue(safety['zero_dependency'])

    def test_discovery_assets_all_resolve_to_aishield(self):
        for rel, href in self.data['discovery_assets'].items():
            self.assertTrue(href.startswith('https://aishield.tools'),
                            "%s 指向了非 aishield.tools: %s" % (rel, href))

    def test_capabilities_are_non_empty(self):
        self.assertGreater(len(self.data['capabilities']), 5)
        self.assertIn('prompt_injection_detection', self.data['capabilities'])
        self.assertIn('rug_pull_detection', self.data['capabilities'])

    def test_links_have_rel_and_href(self):
        self.assertGreater(len(self.data['links']), 3)
        for link in self.data['links']:
            self.assertIn('rel', link)
            self.assertIn('href', link)
            self.assertTrue(link['href'].startswith('https://'))


class TestGeoAssetNoSecrets(unittest.TestCase):
    """移植自归档的代码绝不能把密钥带进发现资产。

    归档里 kb-workflow/scripts/seo-submit.sh 硬编码了一个 IndexNow key，
    TOOLS.md / USER.md 里含活跃 PAT 与 CF token —— 这类内容一个都不许进来。
    """

    _SECRET_PATTERNS = [
        r'ghp_[A-Za-z0-9]{20,}',       # GitHub PAT
        r'gho_[A-Za-z0-9]{20,}',
        r'github_pat_[A-Za-z0-9_]{20,}',
        r'sk-[A-Za-z0-9]{20,}',        # OpenAI / API key
        r'eyJ[A-Za-z0-9_-]{20,}',      # JWT
        r'indexnowkey',                # IndexNow key（已知值 aishield2026indexnowkey）
        r'kb3f8a2c9d7e1f4b6a5d8c3e7f9a2b4d',  # 归档里的 13 站 IndexNow key
        r'sto_[A-Za-z0-9]{10,}',       # Creem store id
        r'Bearer\s+[A-Za-z0-9._-]{10,}',
        r'(?:CF_|CFD_)[A-Za-z0-9]{20,}',
        r'(?i)password\s*[:=]\s*\S+',
    ]

    def test_no_secrets_in_any_geo_asset(self):
        for rel in _GEO_ASSET_FILES.values():
            path = os.path.join(_STATIC_DIR, rel)
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            for pattern in self._SECRET_PATTERNS:
                self.assertIsNone(
                    re.search(pattern, text),
                    "%s 命中密钥模式 %s" % (rel, pattern))


class TestGeoAssetRoutesWired(unittest.TestCase):
    """静态源码断言：五个发现资产的路由必须真的挂在 api/server.py 上。

    只测「文件存在于仓库」而不去验证路由，就是 2026-09-15 线上 404 的直接
    根因 —— docs/llms.txt 一直在仓库里，但 /llms.txt 从未被服务过。
    """

    @classmethod
    def setUpClass(cls):
        server_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'server.py')
        with open(server_path, 'r', encoding='utf-8') as f:
            cls.source = f.read()

    def test_route_table_declares_all_five_assets(self):
        self.assertIn('_GEO_ASSETS', self.source)
        for url_path in _GEO_ASSET_FILES:
            self.assertIn('"%s"' % url_path, self.source,
                          "路由表缺少 %s" % url_path)

    def test_route_table_maps_to_the_right_files(self):
        """路由表里每个条目都必须指向真实存在的静态文件名。"""
        for rel in _GEO_ASSET_FILES.values():
            filename = os.path.basename(rel)
            self.assertIn('"%s"' % filename, self.source,
                          "路由表缺少 %s 的文件映射" % filename)
            self.assertTrue(
                os.path.exists(os.path.join(_STATIC_DIR, rel)),
                "路由指向的静态文件不存在: %s" % rel)

    def test_route_serves_with_cache_control(self):
        """发现资产应带 Cache-Control，Agent 侧才有稳定的缓存语义。"""
        self.assertIn('Cache-Control', self.source)

    def test_docs_llms_source_is_not_a_dead_copy(self):
        """docs/llms.txt 与 api/static/llms.txt 都必须在 TARGETS 之外但内容同步。"""
        self.assertTrue(os.path.exists(os.path.join(_STATIC_DIR, 'llms.txt')))
        self.assertTrue(os.path.exists(
            os.path.join(os.path.dirname(__file__), '..', 'docs', 'llms.txt')))


class TestHeadMethodSupported(unittest.TestCase):
    """api/server.py 必须实现 do_HEAD。

    BaseHTTPRequestHandler 对没有 do_<METHOD> 的方法返回 501 Not Implemented。
    2026-09-15 实测线上：GET / 与 /api/v1/health 返回 200，但 HEAD 同一 URL
    返回 501。大量 AI 爬虫、链接检查器、CDN 预取与提交前校验工具会先发 HEAD
    做存活预检，收到 501 即判定 URL 不可用并放弃抓取——症状与"文件在仓库、
    提交成功、收录为零"完全一致。这是第二层假绿（第一层是路由没挂上）。

    只测源码，不依赖服务器：CI 无本地 server 时仍能拦住回归。
    """

    @classmethod
    def setUpClass(cls):
        server_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'server.py')
        with open(server_path, 'r', encoding='utf-8') as f:
            cls.source = f.read()

    def test_do_head_is_defined(self):
        self.assertIn('def do_HEAD(self)', self.source,
                      "api/server.py 缺少 do_HEAD —— HEAD 请求会返回 501，"
                      "AI 爬虫预检会直接放弃该 URL")

    def test_do_head_delegates_to_get(self):
        """HEAD 必须复用 do_GET 的路由逻辑，而不是另写一份（否则必然漂移）。"""
        idx = self.source.index('def do_HEAD(self)')
        nxt = self.source.index('def do_GET(self)', idx)
        block = self.source[idx:nxt]
        self.assertIn('self.do_GET()', block,
                      "do_HEAD 必须调用 self.do_GET()，不能重写一份路由分支")

    def test_do_head_suppresses_body_only(self):
        """必须只丢弃响应体，响应头（含 Content-Length）必须保留。

        正确做法是 end_headers() 之后才翻转丢弃开关。如果无条件丢弃 wfile 写入，
        会把响应头一起丢掉，客户端收到空响应（HTTP/1.0 下无法判断状态）。
        """
        idx = self.source.index('def do_HEAD(self)')
        nxt = self.source.index('def do_GET(self)', idx)
        block = self.source[idx:nxt]
        self.assertIn('end_headers', block,
                      "do_HEAD 必须在 end_headers 之后才丢弃响应体，"
                      "否则响应头也会被吞掉")
        # 必须恢复现场，避免污染同一个 handler 后续请求
        self.assertIn('_real_wfile', block)
        self.assertIn('finally', block,
                      "do_HEAD 必须用 finally 恢复 wfile / end_headers")

    def test_all_wfile_writes_follow_end_headers(self):
        """do_HEAD 的正确性依赖一个不变量：所有 body 写入都紧跟 end_headers()。

        这条测试把该不变量钉死。若未来有人在 end_headers() 之前插入
        wfile.write，HEAD 会把那段内容误判为响应头并写到 socket 上，
        必须立刻暴露。
        """
        lines = self.source.splitlines()
        violations = []
        for i, line in enumerate(lines):
            if 'self.wfile.write' not in line:
                continue
            # 向前找最近的 end_headers 调用
            j = i - 1
            while j >= 0 and lines[j].strip() == '':
                j -= 1
            if j < 0 or 'end_headers' not in lines[j]:
                violations.append(i + 1)
        self.assertEqual(violations, [],
                         "第 %s 行的 wfile.write 前面不是 end_headers() —— "
                         "do_HEAD 的丢弃时机假设已被破坏" % violations)


class TestVersionDeclarationsGated(unittest.TestCase):
    """新增发现资产里的版本声明必须纳入 sync_version 门禁。

    仓库历史上两次栽在「版本声明位漏在门禁外」上（dist/index.js 停在 4.2.2、
    registry/server.json 停在 4.2.2）。新加的 ai-plugin.json / agent-discovery.json
    / agent.json 各自带一个版本字段，若不入门禁就会立刻开始漂移。
    """

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        import sync_version
        cls.targets = [t[0] for t in sync_version.TARGETS]

    def test_ai_plugin_version_gated(self):
        self.assertIn('api/static/.well-known/ai-plugin.json', self.targets)

    def test_agent_discovery_version_gated(self):
        self.assertIn('api/static/agent-discovery.json', self.targets)

    def test_agent_json_version_gated(self):
        self.assertIn('api/static/.well-known/agent.json', self.targets)

    def test_targets_files_all_exist(self):
        root = os.path.join(os.path.dirname(__file__), '..')
        for rel in self.targets:
            self.assertTrue(os.path.exists(os.path.join(root, rel)),
                            "TARGETS 里登记了仓库中不存在的文件: %s" % rel)


class TestSitemapAndRobotsCoverage(unittest.TestCase):
    """新增发现资产必须同时进入 sitemap.xml 与 robots.txt"""

    def test_sitemap_contains_all_geo_assets(self):
        with open(os.path.join(_STATIC_DIR, 'sitemap.xml'), 'r', encoding='utf-8') as f:
            text = f.read()
        for url_path in _GEO_ASSET_FILES:
            self.assertIn('https://aishield.tools' + url_path, text)

    def test_sitemap_still_valid_xml(self):
        with open(os.path.join(_STATIC_DIR, 'sitemap.xml'), 'r', encoding='utf-8') as f:
            root = ET.fromstring(f.read())
        self.assertEqual(root.tag, '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')

    def test_robots_allows_all_geo_assets(self):
        with open(os.path.join(_STATIC_DIR, 'robots.txt'), 'r', encoding='utf-8') as f:
            text = f.read()
        for url_path in _GEO_ASSET_FILES:
            self.assertIn('Allow: %s' % url_path, text)
        self.assertIn('Allow: /.well-known/security.txt', text)
        self.assertIn('Allow: /openapi.json', text)


# ============================================================
#  服务器端点测试 (需要服务器启动)
# ============================================================

class TestGeoServerEndpoints(unittest.TestCase):
    """通过 HTTP 验证 GEO 端点的运行时行为"""

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_robots_txt_returns_200(self):
        """GET /robots.txt 返回 200 和 text/plain"""
        req = urllib.request.Request(f'{_BASE_URL}/robots.txt')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            ct = resp.headers.get('Content-Type', '')
            self.assertIn('text/plain', ct)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_sitemap_xml_returns_200(self):
        """GET /sitemap.xml 返回 200 和 application/xml"""
        req = urllib.request.Request(f'{_BASE_URL}/sitemap.xml')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            ct = resp.headers.get('Content-Type', '')
            self.assertIn('xml', ct)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_agent_card_returns_200(self):
        """GET /.well-known/agent-card.json 返回 200 和 JSON"""
        req = urllib.request.Request(f'{_BASE_URL}/.well-known/agent-card.json')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertIn('name', data)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_agent_html_returns_200(self):
        """GET /agent.html 返回 200 和 HTML"""
        req = urllib.request.Request(f'{_BASE_URL}/agent.html')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            ct = resp.headers.get('Content-Type', '')
            self.assertIn('text/html', ct)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_index_returns_html_with_json_ld(self):
        """GET / 首页返回包含 JSON-LD 的 HTML"""
        req = urllib.request.Request(f'{_BASE_URL}/')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode()
            self.assertIn('application/ld+json', html)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_banned_words_returns_html(self):
        """GET /banned-words 返回 200 和 HTML"""
        req = urllib.request.Request(f'{_BASE_URL}/banned-words')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            ct = resp.headers.get('Content-Type', '')
            self.assertIn('text/html', ct)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_llms_txt_returns_200(self):
        """GET /llms.txt 返回 200 和 text/plain"""
        req = urllib.request.Request(f'{_BASE_URL}/llms.txt')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn('text/plain', resp.headers.get('Content-Type', ''))
            self.assertIn('AIShield', resp.read().decode())

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_llms_full_txt_returns_200(self):
        """GET /llms-full.txt 返回 200 和 text/plain"""
        req = urllib.request.Request(f'{_BASE_URL}/llms-full.txt')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn('text/plain', resp.headers.get('Content-Type', ''))

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_agent_discovery_returns_200(self):
        """GET /agent-discovery.json 返回 200 和 JSON"""
        req = urllib.request.Request(f'{_BASE_URL}/agent-discovery.json')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn('application/json', resp.headers.get('Content-Type', ''))
            data = json.loads(resp.read().decode())
            self.assertEqual(data['domain'], 'aishield.tools')

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_ai_plugin_returns_200(self):
        """GET /.well-known/ai-plugin.json 返回 200 和 JSON"""
        req = urllib.request.Request(f'{_BASE_URL}/.well-known/ai-plugin.json')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn('application/json', resp.headers.get('Content-Type', ''))
            data = json.loads(resp.read().decode())
            self.assertEqual(data['schema_version'], 'v1')

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_agent_json_returns_200(self):
        """GET /.well-known/agent.json 返回 200 和 JSON"""
        req = urllib.request.Request(f'{_BASE_URL}/.well-known/agent.json')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn('application/json', resp.headers.get('Content-Type', ''))
            data = json.loads(resp.read().decode())
            self.assertEqual(data['name'], 'AIShield')

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_geo_assets_have_cache_control(self):
        """发现资产响应必须带 Cache-Control 与 CORS 头"""
        for url_path in _GEO_ASSET_FILES:
            req = urllib.request.Request(f'{_BASE_URL}{url_path}')
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn('max-age', resp.headers.get('Cache-Control', ''))
                self.assertEqual(resp.headers.get('Access-Control-Allow-Origin'), '*')

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_head_not_501(self):
        """HEAD 必须返回 200，不能是 501 Not Implemented。

        501 = BaseHTTPRequestHandler 没有 do_HEAD，爬虫预检会判定 URL 不可用。
        """
        req = urllib.request.Request(f'{_BASE_URL}/llms.txt', method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertNotEqual(resp.status, 501,
                                "HEAD 返回 501 —— do_HEAD 未实现，"
                                "AI 爬虫预检会放弃该 URL")
            self.assertEqual(resp.status, 200)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_head_status_matches_get(self):
        """HEAD 与 GET 的状态码、Content-Type、Content-Length 必须一致。

        只对**静态发现资产**做逐字节长度断言：这些文件内容不变，HEAD 报的
        Content-Length 必须与 GET 完全相同，任何偏差都说明丢弃逻辑出错。
        """
        # 静态资产：内容不变，HEAD/GET 长度必须逐字节相等
        static_paths = list(_GEO_ASSET_FILES) + ['/sitemap.xml', '/robots.txt']
        for url_path in static_paths:
            with urllib.request.urlopen(
                    urllib.request.Request(f'{_BASE_URL}{url_path}'), timeout=5) as get_resp:
                get_status = get_resp.status
                get_len = get_resp.headers.get('Content-Length')
                get_ct = get_resp.headers.get('Content-Type', '')
                get_resp.read()
            req = urllib.request.Request(f'{_BASE_URL}{url_path}', method='HEAD')
            with urllib.request.urlopen(req, timeout=5) as head_resp:
                self.assertEqual(head_resp.status, get_status,
                                 "HEAD %s 状态码与 GET 不一致" % url_path)
                self.assertEqual(head_resp.headers.get('Content-Type', ''), get_ct,
                                 "HEAD %s Content-Type 与 GET 不一致" % url_path)
                self.assertEqual(head_resp.headers.get('Content-Length'), get_len,
                                 "HEAD %s Content-Length 与 GET 不一致 —— "
                                 "静态资产内容不变，长度必然相等" % url_path)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_head_dynamic_endpoints_status_and_type(self):
        """动态端点（响应体按请求重新生成）只断言状态码与 Content-Type。

        /api/v1/health 的 uptime 是浮点，repr 长度会随边界变化（实测出现过
        338/339 抖动），对动态端点做逐字节长度断言是错的断言，会制造假红。
        """
        for url_path in ['/api/v1/health']:
            with urllib.request.urlopen(
                    urllib.request.Request(f'{_BASE_URL}{url_path}'), timeout=5) as get_resp:
                get_status = get_resp.status
                get_ct = get_resp.headers.get('Content-Type', '')
                get_resp.read()
            req = urllib.request.Request(f'{_BASE_URL}{url_path}', method='HEAD')
            with urllib.request.urlopen(req, timeout=5) as head_resp:
                self.assertEqual(head_resp.status, get_status,
                                 "HEAD %s 状态码与 GET 不一致" % url_path)
                self.assertEqual(head_resp.headers.get('Content-Type', ''), get_ct,
                                 "HEAD %s Content-Type 与 GET 不一致" % url_path)
                # Content-Length 必须存在且为正整数（不能是 0 或缺失）
                cl = head_resp.headers.get('Content-Length')
                self.assertTrue(cl and int(cl) > 0,
                                "HEAD %s 缺少有效的 Content-Length: %r" % (url_path, cl))

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_head_body_is_empty(self):
        """HEAD 绝不能带响应体（RFC 9112 §2.1.1）。"""
        req = urllib.request.Request(f'{_BASE_URL}/geo-faqs.json', method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read()
            self.assertEqual(body, b'',
                             "HEAD 泄漏了响应体 —— do_HEAD 的丢弃逻辑写错了")

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_head_404_not_501(self):
        """HEAD 一个不存在的 URL 应返回 404，不能是 501。"""
        req = urllib.request.Request(
            f'{_BASE_URL}/definitely-not-a-real-page-{os.getpid()}', method='HEAD')
        try:
            urllib.request.urlopen(req, timeout=5)
            self.fail("不存在的 URL 不应返回 2xx")
        except urllib.error.HTTPError as e:
            self.assertNotEqual(e.code, 501,
                                "HEAD 404 路径返回 501 —— do_HEAD 未实现")
            self.assertEqual(e.code, 404)

    @unittest.skipUnless(_SERVER_UP, "服务器未启动")
    def test_get_and_options_unaffected(self):
        """加了 do_HEAD 之后 GET 和 OPTIONS 不能受影响（回归护栏）。"""
        with urllib.request.urlopen(
                urllib.request.Request(f'{_BASE_URL}/llms.txt'), timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read()
            self.assertGreater(len(body), 1000, "GET 响应体被意外清空")
        req = urllib.request.Request(f'{_BASE_URL}/llms.txt', method='OPTIONS')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 204)


class TestNotRootGuard(unittest.TestCase):
    """api/server.py 必须拒绝以 root 运行（借鉴 KeygraphHQ/shannon #323）。

    AIShield 以用户权限遍历 workspace 读取配置/密钥/SSH 目录；以 root 跑时
    这些读取面被放大到整机。安全工具自身的运行姿态必须先正确。
    """

    def _load(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from api import server
        return server

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(os.path.dirname(__file__), '..', 'api', 'server.py'),
                  'r', encoding='utf-8') as f:
            cls.source = f.read()

    def test_guard_defined(self):
        self.assertIn('def assert_not_root()', self.source)

    def test_main_calls_guard(self):
        idx = self.source.index('def main():')
        block = self.source[idx:idx + 400]
        self.assertIn('assert_not_root()', block,
                      "main() 未调用 assert_not_root() —— root 护栏被绕过")

    def test_root_detection_present(self):
        self.assertIn('geteuid', self.source)

    def test_override_escape_hatch_present(self):
        """容器场景需要 root 时必须有显式绕过，且默认关闭。"""
        self.assertIn('AISHIELD_ALLOW_ROOT', self.source)

    def _patch(self, srv):
        """强制 geteuid()==0 并清空绕过开关，返回原函数以便还原。

        必须**始终**打桩，不能只判断 hasattr：Windows 没有 geteuid 所以要挂载，
        而 Linux 上 geteuid 确实存在、真实 uid 却未必是 0（GitHub Actions 的
        runner 是 uid 1001）。只判断 hasattr 会让 test_root_refused 在非 root 的
        Linux CI 上测到真实 uid、护栏正确不触发，于是误报「SystemExit not raised」
        —— 2026-09-17 起 CI/CD 因此每次必红。
        """
        old = getattr(srv.os, 'geteuid', None)
        srv.os.geteuid = lambda: 0
        return old, srv.os.environ.pop('AISHIELD_ALLOW_ROOT', None)

    def _unpatch(self, srv, old_geteuid, allow_root):
        if old_geteuid is None:
            try:
                del srv.os.geteuid
            except AttributeError:
                pass
        else:
            srv.os.geteuid = old_geteuid
        if allow_root is not None:
            srv.os.environ['AISHIELD_ALLOW_ROOT'] = allow_root

    def test_root_refused(self):
        """模拟 geteuid()==0：必须 sys.exit(2)，不得静默放行。"""
        srv = self._load()
        had_g, allow_root = self._patch(srv)
        try:
            with self.assertRaises(SystemExit) as cm:
                srv.assert_not_root()
            self.assertEqual(cm.exception.code, 2)
        finally:
            self._unpatch(srv, had_g, allow_root)

    def test_override_allows_root(self):
        """AISHIELD_ALLOW_ROOT=1 是显式、可记录的绕过，容器场景需要。"""
        srv = self._load()
        had_g, allow_root = self._patch(srv)
        try:
            srv.os.environ['AISHIELD_ALLOW_ROOT'] = '1'
            srv.assert_not_root()  # 不得抛异常
        finally:
            self._unpatch(srv, had_g, allow_root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
