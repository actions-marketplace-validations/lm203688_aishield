# -*- coding: utf-8 -*-
"""
契约测试：部署脚本里不允许出现任何硬编码的 Cloudflare token。

背景（2026-09-15 修复）
-----------------------
`scripts/deploy-named-tunnel.sh:20` 与 `scripts/deploy-quick-tunnel.sh:156`
曾把一个 base64 编码的 Cloudflare API token inline 解码。本仓库是 public 的，
而 base64 不是加密 —— 任何人 clone 仓库一行命令就能拿到那个 token，它拥有
aishield.tools 的 Zone Read + DNS Records Edit + Zone Settings Edit，
足以把域名 CNAME 劫持到攻击者服务器。

修复后 token 由 `scripts/cf-token-loader.sh` 在运行期解析：
  1. env  $CF_TUNNEL_TOKEN
  2. 文件 /root/.aishield/cf-token（由 install-cf-token.yml 写入）

本测试把该不变量钉死，防止回归。
"""
import base64
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'scripts')


def _read(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


# base64( 任意以 cfut_ / cfun_ 开头的 Cloudflare token ) 必然包含该前缀
# 的 base64 编码片段；这里用一个宽松匹配再逐个解码验证，避免误报。
_B64_LITERAL = re.compile(r"""['"][A-Za-z0-9+/=]{16,}['"]""")
_CF_TOKEN = re.compile(r'^cfu[tn]_[A-Za-z0-9]{10,}$')


class TestNoHardcodedCfToken(unittest.TestCase):

    def test_no_cf_token_literal_anywhere_in_scripts(self):
        """scripts/ 下任何文本里都不允许出现明文的 Cloudflare token。"""
        hits = []
        for path in glob.glob(os.path.join(SCRIPTS, '**', '*'), recursive=True):
            if not os.path.isfile(path):
                continue
            if os.path.getsize(path) > 5 * 1024 * 1024:
                continue
            try:
                text = _read(path)
            except (OSError, UnicodeError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if _CF_TOKEN.search(line.strip()):
                    hits.append('%s:%d' % (os.path.relpath(path, ROOT), i))
        self.assertEqual(
            hits, [],
            'scripts/ 下发现了明文 Cloudflare token（cfut_/cfun_ 前缀）：%s' % hits)

    def test_no_decodable_cf_token_in_deploy_scripts(self):
        """部署脚本里任何 base64 字面量都不允许解码成 Cloudflare token。"""
        offenders = []
        for name in ('deploy-named-tunnel.sh', 'deploy-quick-tunnel.sh',
                     'cf-token-loader.sh'):
            path = os.path.join(SCRIPTS, name)
            if not os.path.exists(path):
                continue
            text = _read(path)
            for literal in _B64_LITERAL.findall(text):
                try:
                    decoded = base64.b64decode(literal).decode('utf-8', 'replace')
                except Exception:
                    continue
                if _CF_TOKEN.search(decoded.strip()):
                    offenders.append('%s -> %s...' % (name, decoded[:12]))
        self.assertEqual(
            offenders, [],
            '部署脚本里仍有可解码的 Cloudflare token：%s' % offenders)

    def test_deploy_scripts_use_the_loader(self):
        """两个 deploy 脚本都必须引用 loader，而不是自己解码 token。"""
        for name in ('deploy-named-tunnel.sh', 'deploy-quick-tunnel.sh'):
            text = _read(os.path.join(SCRIPTS, name))
            self.assertIn(
                'cf-token-loader.sh', text,
                '%s 未引用 cf-token-loader.sh —— token 来源不明' % name)
            self.assertIn('load_cf_token', text,
                          '%s 未调用 load_cf_token' % name)
            self.assertNotIn('base64 -d', text,
                             '%s 仍在 inline 解码 base64' % name)

    def test_loader_exists_and_is_sourced_safely(self):
        path = os.path.join(SCRIPTS, 'cf-token-loader.sh')
        self.assertTrue(os.path.exists(path), '缺少 scripts/cf-token-loader.sh')
        text = _read(path)
        self.assertIn('CF_TUNNEL_TOKEN', text)
        self.assertIn('CF_TOKEN_FILE', text)
        self.assertIn('load_cf_token()', text)

    def test_loader_prefers_env_over_file(self):
        """运行期行为：env 优先于文件；两者都缺时返回非 0。"""
        raw_loader = os.path.join(SCRIPTS, 'cf-token-loader.sh')
        if not os.path.exists(raw_loader):
            self.skipTest('loader 不存在')
        if subprocess.run(['bash', '-n', raw_loader]).returncode != 0:
            self.fail('cf-token-loader.sh 语法错误')

        # MSYS2/Cygwin bash 把 Windows 路径的反斜杠当转义字符吃掉，
        # 所以传给 bash -c 的路径必须转成 POSIX 风格。
        # 注意：MSYS2 的 /tmp 与 C:/Windows/Temp 是**不同的**目录，
        # 因此测试统一从 Python 的 tempfile.gettempdir() 出发来回转换。
        def _posix(p):
            p = p.replace('\\', '/')
            return re.sub(r'^([A-Za-z]):', r'/\1', p).lower()

        loader = _posix(os.path.abspath(raw_loader))

        def _base_env():
            env = dict(os.environ)
            for k in ('CF_TOKEN_FILE', 'CF_TUNNEL_TOKEN', 'CF_API_TOKEN'):
                env.pop(k, None)
            return env

        def _run(cmd, env):
            return subprocess.run(['bash', '-c', cmd], env=env,
                                  capture_output=True, text=True)

        rawdir = os.path.abspath(tempfile.gettempdir())
        raw = os.path.join(rawdir, 'aishield-cf-test-%d' % os.getpid(), 'cf-token')
        os.makedirs(os.path.dirname(raw), exist_ok=True)
        try:
            with open(raw, 'w') as fh:
                fh.write('FILE_TOKEN_VALUE\n')
            tokfile = _posix(raw)
            empty = _base_env()

            # 1) 两者都缺 -> 非 0
            r = _run('. %s; load_cf_token; echo "rc=$?"' % loader, empty)
            self.assertIn('rc=1', r.stdout,
                          '两者都缺时 load_cf_token 应返回 1：\n%s' % r.stdout)

            # 2) 只有文件（POSIX 路径）
            env2 = dict(empty)
            env2['CF_TOKEN_FILE'] = tokfile
            r = _run('. %s; load_cf_token && printf "%%s" "$CF_API_TOKEN"'
                     % loader, env2)
            self.assertEqual(r.stdout.strip(), 'FILE_TOKEN_VALUE',
                             '文件模式未解析：%r (stderr=%r)'
                             % (r.stdout, r.stderr))

            # 2b) 只有文件（Windows 风格路径，仅 Windows 有意义）
            if os.name == 'nt':
                env2b = dict(empty)
                env2b['CF_TOKEN_FILE'] = raw.replace('/', os.sep)
                r = _run('. %s; load_cf_token && printf "%%s" "$CF_API_TOKEN"'
                         % loader, env2b)
                self.assertEqual(
                    r.stdout.strip(), 'FILE_TOKEN_VALUE',
                    'Windows 风格 CF_TOKEN_FILE 未被转换解析：%r'
                    % (r.stdout,))

            # 3) env 优先于文件
            env3 = dict(env2)
            env3['CF_TUNNEL_TOKEN'] = 'ENV_TOKEN_VALUE'
            r = _run('. %s; load_cf_token && printf "%%s" "$CF_API_TOKEN"'
                     % loader, env3)
            self.assertEqual(r.stdout.strip(), 'ENV_TOKEN_VALUE',
                             'env 未优先于文件：%r' % r.stdout)

            # 4) $CF_API_TOKEN 已设置时直接采用（最高优先）
            env4 = dict(env2)
            env4['CF_API_TOKEN'] = 'PRESET_TOKEN_VALUE'
            env4['CF_TUNNEL_TOKEN'] = 'ENV_TOKEN_VALUE'
            r = _run('. %s; load_cf_token && printf "%%s" "$CF_API_TOKEN"'
                     % loader, env4)
            self.assertEqual(r.stdout.strip(), 'PRESET_TOKEN_VALUE',
                             '已设置的 $CF_API_TOKEN 被覆盖：%r' % r.stdout)

            # 5) cf_token_source 不泄露 token 值
            r = _run('. %s; load_cf_token; cf_token_source' % loader, env3)
            self.assertNotIn('ENV_TOKEN_VALUE', r.stdout,
                             'cf_token_source 泄露了 token 值：%r' % r.stdout)
            self.assertIn('CF_TUNNEL_TOKEN', r.stdout,
                          'cf_token_source 未标注来源：%r' % r.stdout)
        finally:
            shutil.rmtree(os.path.dirname(raw), ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
