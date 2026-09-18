# -*- coding: utf-8 -*-
"""
契约测试：部署链路不得让「root 护栏」静默失效。

背景（2026-09-18 事故，详见 docs/postmortem-2026-09-18-502.md）
----------------------------------------------------------------
`api/server.py::assert_not_root()` 在 uid 0 时 `sys.exit(2)`，设计完全正确。
但 VPS 上的部署身份**就是 root**（systemd 服务、`systemctl` 都必须 root），
而整条部署链路从未设置 `AISHIELD_ALLOW_ROOT=1`。结果：API 进程启动即退出，
`:8450` 无监听，cloudflared tunnel 全程存活 → Cloudflare 回 502，静默 20.5 小时。

关键教训：安全护栏与部署现实冲突时，失败模式是「服务不存在」而不是「服务报错」，
因此进程层面的存活检查（cloudflared 活着、tunnel 握手成功）全部通过，
故障完全不可见。

本测试把三条不变量钉死：

  1. 每个启动 `api/server.py` 的位置都必须设置 `AISHIELD_ALLOW_ROOT=1` —— 漏一处就是 502。
  2. 多项目共机时，禁止用裸进程名杀 cloudflared（会杀掉邻居项目的 tunnel）。
  3. cron 存活检查必须探 HTTP，不能探进程名（探进程名会被邻居项目满足 = false-live）。

含自否证（self-falsification）：用一个「删掉 export 行」的临时内容验证检测器
真的会报，防止本测试退化成橡皮图章。

注意：所有判定都先剥掉注释。窗口内 `#   AISHIELD_ALLOW_ROOT=1 inside a container.`
这类说明文字若被计入，会让整条断言被注释骗过 —— 这正是「假绿」的同款形状。
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(ROOT, 'scripts', 'deploy-named-tunnel.sh')
SERVER = os.path.join(ROOT, 'api', 'server.py')

# 启动 api/server.py 的判定：行内含 python 且含 api/server.py，且属于执行语境。
# 排除下载、语法检查、进程查看这三类「提到但不执行」的行。
_EXEC_KEYWORDS = ('nohup', 'exec', 'ExecStart', 'python3', 'python')
_NOT_EXEC = ('curl', 'mv ', 'py_compile', 'grep', 'head ', 'tail ', 'ps aux')


def _read(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def _strip_comments(line):
    """去掉行内注释（尊重引号），避免注释里的字面量满足断言。"""
    out = []
    quote = None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ('"', "'"):
            quote = ch
            out.append(ch)
            continue
        if ch == '#':
            break
        out.append(ch)
    return ''.join(out)


def _code_lines(text):
    return [_strip_comments(l) for l in text.splitlines()]


def _launch_sites(text):
    """返回启动 api/server.py 的 (行号, 行内容) 列表。"""
    sites = []
    for i, raw in enumerate(text.splitlines(), 1):
        code = _strip_comments(raw)
        if 'api/server.py' not in code:
            continue
        if not any(k in code for k in _EXEC_KEYWORDS):
            continue
        if any(k in code for k in _NOT_EXEC):
            continue
        sites.append((i, code.strip()))
    return sites


def find_missing_allow_root(text, window=14):
    """每个启动点附近必须能找到 AISHIELD_ALLOW_ROOT=1（注释不计入）。

    window 取 14 行，覆盖三种真实写法：
      - 紧邻上一行 `export AISHIELD_ALLOW_ROOT=1`（函数内启动）
      - 同一行前缀 `PORT=8450 AISHIELD_ALLOW_ROOT=1 nohup ...`
      - systemd heredoc 里 `Environment=AISHIELD_ALLOW_ROOT=1` 在 ExecStart 上一行
    足够宽以容纳注释，足够窄以在「新增启动点但忘了设 env」时报错。
    """
    codes = _code_lines(text)
    missing = []
    for lineno, _code in _launch_sites(text):
        lo = max(0, lineno - 1 - window)
        hi = lineno + 2
        block = '\n'.join(codes[lo:hi])
        if not re.search(r'AISHIELD_ALLOW_ROOT\s*=\s*1', block):
            missing.append(lineno)
    return missing


class TestRootGuardDeploymentContract(unittest.TestCase):

    def setUp(self):
        self.assertTrue(os.path.exists(DEPLOY), '缺少 scripts/deploy-named-tunnel.sh')
        self.assertTrue(os.path.exists(SERVER), '缺少 api/server.py')
        self.deploy_text = _read(DEPLOY)

    # ── 护栏本身必须存在（正对照：护栏不在时下面的 env 断言就失去意义）────
    def test_guard_exists_in_server(self):
        text = _read(SERVER)
        self.assertIn('def assert_not_root()', text,
                      'api/server.py 缺少 assert_not_root() 护栏')
        self.assertIn('AISHIELD_ALLOW_ROOT', text,
                      '护栏缺少 AISHIELD_ALLOW_ROOT 逃生口 —— 受管主机将无法启动')
        self.assertIn('sys.exit(2)', text, '护栏未真正阻断')

    # ── 自否证 1：检测器必须真的找得到启动点，否则下面全是通过 ──────────
    def test_launch_site_detection_is_not_vacuous(self):
        sites = _launch_sites(self.deploy_text)
        self.assertGreaterEqual(
            len(sites), 4,
            '只找到 %d 个 api/server.py 启动点（预期 >=4：nohup 主路径 + systemd '
            'ExecStart + start-tunnel.sh 两处兜底）。若此断言失败，说明检测器'
            '失效，其余断言将全部退化为空通过。' % len(sites))

    # ── 核心不变量 ────────────────────────────────────────────────────
    def test_every_launch_site_sets_allow_root(self):
        missing = find_missing_allow_root(self.deploy_text)
        self.assertEqual(
            missing, [],
            '以下行启动 api/server.py 但作用域内没有 AISHIELD_ALLOW_ROOT=1，'
            '部署身份为 root 时 API 会 sys.exit(2) 导致 502：%s' % missing)

    # ── 自否证 2：删掉 export 行后检测器必须报红 ──────────────────────
    def test_checker_detects_missing_env(self):
        lines = self.deploy_text.splitlines(True)
        victim = None
        for idx, line in enumerate(lines):
            if re.search(r'AISHIELD_ALLOW_ROOT\s*=\s*1', _strip_comments(line)) \
                    and 'export' in line:
                victim = idx
                break
        self.assertIsNotNone(victim,
                             '找不到可作负对照的 `export AISHIELD_ALLOW_ROOT=1` 行')
        mutated = ''.join(lines[:victim] + lines[victim + 1:])
        # 启动点数量不变（只删了 export，没删启动）
        self.assertEqual(len(_launch_sites(mutated)),
                         len(_launch_sites(self.deploy_text)))
        missing = find_missing_allow_root(mutated)
        self.assertEqual(
            len(missing), 1,
            '负对照失败：删掉 export 行后应恰好报出 1 个缺口，实际 %s。'
            '检测器要么被注释骗过，要么已经失效。' % missing)

    # ── 多项目共机：禁止裸进程名杀 cloudflared ────────────────────────
    def test_no_cross_project_cloudflared_pkill(self):
        offenders = []
        for i, line in enumerate(self.deploy_text.splitlines(), 1):
            code = _strip_comments(line)
            if 'pkill' not in code or 'cloudflared' not in code:
                continue
            stripped = code.strip()
            if 'systemctl' in stripped:
                continue
            # 允许的安全形态：pattern 收窄到本项目自己的 config.yml。
            # 脚本里实际写作 config\.yml（转义点），故先归一化反斜杠再比对，
            # 避免用正则表达式去匹配一个本身就含反斜杠的字面量。
            if 'config.yml' in stripped.replace('\\', ''):
                continue
            offenders.append('%d: %s' % (i, stripped))
        self.assertEqual(
            offenders, [],
            '发现按进程名杀 cloudflared 的写法 —— VPS 是多项目机（aishield-tunnel / '
            'healthlens / healthlens-tunnel），会误杀邻居项目的 tunnel：%s' % offenders)

    # ── cron 存活检查必须探 HTTP ──────────────────────────────────────
    def test_cron_probes_http_not_process_name(self):
        cron_lines = [
            _strip_comments(l).strip()
            for l in self.deploy_text.splitlines()
            if 'CRON_LINE' in l or 'crontab' in l
        ]
        self.assertGreaterEqual(len(cron_lines), 1, '找不到 cron 存活检查行')
        cron_text = '\n'.join(cron_lines)
        self.assertIn('curl', cron_text,
                      'cron 存活检查必须探 HTTP（curl :8450/api/v1/health）')
        for bad in ('pgrep', 'pidof'):
            self.assertNotIn(bad, cron_text,
                             'cron 用进程名探活会被同机其他项目的 tunnel 满足 = '
                             'false-live（本项目挂了也不触发拉起），禁止 %s' % bad)


if __name__ == '__main__':
    unittest.main()
