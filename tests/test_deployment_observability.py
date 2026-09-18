# -*- coding: utf-8 -*-
r"""
契约测试：部署与自愈链路的退出码必须如实传导，诊断语句不得抢占它。

背景（2026-09-18 事故，详见 docs/postmortem-2026-09-18-502.md）
----------------------------------------------------------------
那次 20.5 小时静默 502 里，真正让故障不可见的不是任何一个单点 bug，而是
四层同形状的假绿叠加：

  1. `ssh ... | tail -60 || echo "REPAIR_SSH_FAILED"` —— 管道让退出码取自 tail
  2. `deploy-named-tunnel.sh` 结尾无条件 `exit 0` —— API FAIL 也报 success
  3. `tail -40` 截掉 STEP 1 —— 故障恰在启动段，日志里永远看不到
  4. `escalate` 只判 test/verify —— repair 失败时它们是 `skipped`，不告警

以及第 5 层（本轮新发现）：`deploy-server.yml` 的远端脚本结尾是
`echo "DEPLOY_EXIT_CODE=$?"`。echo 的退出码恒为 0，而它是最后一条命令，
于是远端脚本整体退出码恒为 0 —— **诊断语句抢占了部署脚本的 exit 1**，
job 照样报 success。形状与第 1、2 层完全一致：把结论打印出来 ≠ 把结论传出去。

本测试把这五条不变量钉死，并含自否证。

检测器说明
----------
远端 shell 命令是嵌在 YAML 里的 shell 字符串，里面的 `$?` / `$rc` 都被转义成
`\$?` / `\$rc`（避免外层 shell 展开）。因此本测试**不尝试**解析引号嵌套，而是用
两种与转义无关的判定：

  - 退出码被抢占：一条回显 `$?` 的语句之后还有别的命令语句 —— 它的 `$?` 记录的是
    上一条命令的结果，而它自己的退出码（0）成了新基线，上一条命令的失败就此丢失。
  - 退出码已传出：正文里存在位于语句起始的 `exit $rc`（未被 `\` 转义的形式）。
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_DIR = os.path.join(ROOT, '.github', 'workflows')
DEPLOY_WF = os.path.join(W_DIR, 'deploy-server.yml')
HEAL_WF = os.path.join(W_DIR, 'self-heal-closed-loop.yml')
DEPLOY_SH = os.path.join(ROOT, 'scripts', 'deploy-named-tunnel.sh')


def _read(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def _indent(line):
    return len(line) - len(line.lstrip(' '))


def _step_block(text, step_name):
    """按 `- name:` 文本切出一个 step 的 YAML 块（零依赖，不引入 yaml 解析）。"""
    lines = text.splitlines()
    start = None
    for i, l in enumerate(lines):
        if l.strip().startswith('- name:') and step_name in l:
            start = i
            break
    if start is None:
        return None
    base = _indent(lines[start])
    end = len(lines)
    for j in range(start + 1, len(lines)):
        l = lines[j]
        if not l.strip():
            continue
        if _indent(l) <= base and l.lstrip().startswith(
                ('- name:', 'uses:', 'permissions:', 'env:')):
            end = j
            break
    return '\n'.join(lines[start:end])


def _job_block(text, job_name):
    """切出一个 job 的 YAML 块（key 顶格在 `jobs:` 下，缩进 2 空格）。"""
    lines = text.splitlines()
    start = None
    for i, l in enumerate(lines):
        if re.match(r'^\s{2}%s:\s*$' % re.escape(job_name), l):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r'^\s{2}\S', lines[j]):
            end = j
            break
    return '\n'.join(lines[start:end])


def _run_body(block, key):
    """从 step 块里取出 `run: |` 或 `script: |` 的正文。"""
    lines = block.splitlines()
    start = None
    key_indent = None
    for i, l in enumerate(lines):
        if l.strip().startswith(key + ':'):
            start = i + 1
            key_indent = _indent(l)
            break
    if start is None:
        return None
    body = []
    for l in lines[start:]:
        if not l.strip():
            body.append('')
            continue
        if _indent(l) <= key_indent:
            break
        body.append(l)
    return '\n'.join(body)


def _code_lines(body):
    """去掉空行与注释行，返回 [(原行号, 代码文本)]。"""
    out = []
    for i, l in enumerate(body.splitlines(), 1):
        stripped = l.strip()
        if not stripped or stripped.startswith('#'):
            continue
        out.append((i, stripped))
    return out


def _code_body(body):
    """剥掉注释行后的正文。

    子串断言必须用它：工作流里用注释记录「旧写法是什么、为什么错」是好事，
    那些字面量（`REPAIR_SSH_FAILED`、`| tail -60`）本身就成了误报来源 ——
    这与「注释里的 AISHIELD_ALLOW_ROOT=1 骗过检测器」是同一种假绿形状。
    """
    return '\n'.join(code for _n, code in _code_lines(body))


def find_exit_code_swallowed(body):
    """返回所有「回显 $?」的语句行号。

    这是假绿的核心形状：`echo "X=$?"` 只是把上一条命令的结论**打印**出来，
    而它自己的退出码（0）成了新的基线 —— 上一条命令失败了也没人知道。
    所以只要回显了 $?，就必须紧跟一条 `exit $?` 或 `exit $rc` 把结论传出去；
    检测器报出该语句即意味着需要检查其后续是否为 exit。
    """
    return [lineno for lineno, line in _code_lines(body)
            if line.startswith('echo ') and '$?' in line]


def has_exit_of_variable(body, var='$rc'):
    """是否存在位于语句起始、未被转义的 `exit <var>`。"""
    for _n, line in _code_lines(body):
        m = re.match(r'exit\s+(\$\w+)', line)
        if m and m.group(1) == var:
            return True
    return False


def has_capture(body, target='rc'):
    """是否存在 `target=$?`（未被转义、位于语句起始）。"""
    for _n, line in _code_lines(body):
        if re.match(r'%s=\$\?' % re.escape(target), line):
            return True
    return False


class TestDeployExitCodePropagation(unittest.TestCase):
    """deploy-server.yml：部署脚本的退出码必须原样传出远端脚本。"""

    def setUp(self):
        self.assertTrue(os.path.exists(DEPLOY_WF), '缺少 deploy-server.yml')
        block = _step_block(_read(DEPLOY_WF), 'Deploy via SSH')
        self.assertIsNotNone(block, '找不到 "Deploy via SSH" step')
        self.body = _run_body(block, 'script')
        self.assertIsNotNone(self.body, '"Deploy via SSH" step 里没有 script 正文')

    def test_deploy_script_exit_code_is_captured(self):
        self.assertTrue(has_capture(self.body, 'rc'),
                        '部署脚本的退出码没有被取到 rc —— 后续无法如实传出')

    def test_remote_script_exits_with_the_captured_code(self):
        self.assertTrue(has_exit_of_variable(self.body, '$rc'),
                        '远端脚本没有 `exit $rc` —— 部署失败会被判成成功')

    def test_diagnostic_echo_does_not_own_the_exit_code(self):
        swallowed = find_exit_code_swallowed(self.body)
        self.assertEqual(
            swallowed, [],
            '以下语句回显 $? 但之后还有别的命令，它的退出码(0)覆盖了部署脚本的'
            '退出码 —— 部署失败会被报成成功（与 2026-09-18 五层假绿同款）：%s'
            % swallowed)

    def test_self_falsification_detector_flags_the_old_pattern(self):
        """负对照：用历史反模式喂检测器，必须报红。

        这是 09-18 事故的原始写法：部署脚本跑完后用 echo 回显 $?，
        然后 echo 的退出码 0 成为远端脚本的退出码。
        """
        old_style = (
            '    set -o pipefail\n'
            '    bash scripts/deploy-named-tunnel.sh 2>&1\n'
            '    echo "DEPLOY_EXIT_CODE=$?"\n'
        )
        self.assertEqual(
            find_exit_code_swallowed(old_style), [3],
            '检测器没有识别出历史反模式（echo 回显 $? 且没有 exit $rc）')

    def test_old_pattern_is_absent_from_current_workflow(self):
        """回归哨兵：历史反模式的字面量不得回到工作流里。"""
        self.assertNotIn('DEPLOY_EXIT_CODE=$?', _code_body(self.body),
                         '诊断回显改回了 $? —— 部署失败会被报成成功')


class TestDeployScriptExitGate(unittest.TestCase):
    """deploy-named-tunnel.sh：退出码必须与线上健康结论一致。"""

    def setUp(self):
        self.assertTrue(os.path.exists(DEPLOY_SH), '缺少 deploy-named-tunnel.sh')
        self.text = _read(DEPLOY_SH)
        self.lines = self.text.splitlines()

    def _exit_lines(self, target):
        return [i for i, l in enumerate(self.lines, 1)
                if re.match(r'^\s*exit\s+' + str(target) + r'\s*$', l)]

    def test_script_has_a_failure_exit(self):
        self.assertGreaterEqual(len(self._exit_lines(1)), 1,
                                '脚本没有任何 `exit 1` —— 失败路径不可区分于成功')

    def test_final_success_exit_comes_after_the_failure_exit(self):
        fails, ok = self._exit_lines(1), self._exit_lines(0)
        self.assertGreaterEqual(len(ok), 1, '脚本没有 `exit 0`')
        self.assertGreater(max(ok), max(fails),
                           '最后的 `exit 0` 出现在最后的 `exit 1` 之前 —— '
                           '成功出口先于失败判定，失败会被成功覆盖')

    def test_success_exit_is_gated_on_health_probe(self):
        """最后的 exit 0 之前必须有一个「不健康即 exit 1」的 curl 健康门。"""
        fails, ok = self._exit_lines(1), self._exit_lines(0)
        last_fail = max(fails)
        self.assertGreater(max(ok), last_fail)
        window = '\n'.join(self.lines[max(0, last_fail - 14):last_fail])
        self.assertIn('exit 1', window)
        self.assertRegex(
            window, r'curl\s+-sf.*/api/v1/health',
            '`exit 1` 前 14 行内没有 /api/v1/health 的 curl 健康门 —— '
            '失败判定不是由线上健康状态驱动的')


class TestSelfHealObservability(unittest.TestCase):
    """self-heal-closed-loop.yml：修复环节必须可观测、可失败、可告警。"""

    def setUp(self):
        self.assertTrue(os.path.exists(HEAL_WF), '缺少 self-heal-closed-loop.yml')
        self.text = _read(HEAL_WF)
        block = _step_block(self.text, 'Redeploy to server')
        self.assertIsNotNone(block, '找不到 "Redeploy to server" step')
        self.body = _run_body(block, 'run')
        self.assertIsNotNone(self.body, '"Redeploy to server" step 没有 run 正文')

    def test_repair_step_uses_pipefail(self):
        self.assertIn('set -o pipefail', self.body,
                      '修复 step 未开启 pipefail —— `ssh | tee` 的退出码会取自 tee，'
                      'SSH 断连与部署失败都被吞成 success')

    def test_repair_step_propagates_remote_exit_code(self):
        code = _code_body(self.body)
        self.assertTrue(has_capture(self.body, 'rc'),
                        '外层没有 `rc=$?` —— ssh 的退出码没有被捕获')
        self.assertTrue(has_exit_of_variable(self.body, '$rc'),
                        '外层没有 `exit $rc` —— 修复失败会被报成 success')
        self.assertNotIn('REPAIR_SSH_FAILED', code,
                         '仍存在 `|| echo "REPAIR_SSH_FAILED"` 式的吞错')
        self.assertNotRegex(
            code, r'\|\s*tail\s+-\d+\s+\|\|\s*echo\s+"',
            '仍存在 `| tail -N || echo "..."` 式的管道吞错（失败被提示语覆盖）')

    def test_repair_stdout_is_not_truncated(self):
        code = _code_body(self.body)
        self.assertIn('tee /tmp/repair-artifact/repair.log', code,
                      '修复输出未用 tee 全量落盘 —— 必须完整留证')
        self.assertNotIn('| tail -60', code,
                         '修复输出仍被 tail 截断 —— 09-17 事故里 STEP 1 的启动输出'
                         '正是被截掉的那段，根因因此无人可见')

    def test_repair_logs_are_retained(self):
        self.assertIn('actions/upload-artifact', self.text,
                      '修复日志未上传为 artifact —— 故障定位只能靠口头描述')
        self.assertIn('self-heal-repair-log', self.text,
                      'artifact 名称不对，事后无法按名取回')

    def test_escalate_covers_the_repair_job(self):
        block = _job_block(self.text, 'escalate')
        self.assertIsNotNone(block, '找不到 escalate job')
        self.assertIn('needs.repair.result', block,
                      'escalate 未覆盖 repair 失败 —— repair 挂掉时 test/verify 是 '
                      'skipped 而非 failure，告警永不触发（09-17 事故的直接原因）')
        for j in ('needs.test.result', 'needs.verify.result'):
            self.assertIn(j, block, 'escalate 漏判 %s' % j)

    def test_both_deploy_paths_deliver_tarball_first(self):
        """两条部署路径都必须以 runner tarball 为权威代码源。"""
        for wf in ('deploy-server.yml', 'self-heal-closed-loop.yml'):
            text = _read(os.path.join(W_DIR, wf))
            self.assertIn('aishield-code.tgz', text,
                          '%s 未投递 tarball —— VPS 到 github.com 不通，'
                          '`git pull` 只会同步陈旧代码（用旧代码修旧代码）' % wf)


if __name__ == '__main__':
    unittest.main()
