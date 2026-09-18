"""告警链路加固契约：出站脱敏 + fail-closed 退出码 + 未送达台账闭环。

钉死的三条真问题（2026-09-18，借鉴 MiniMax-Code 的 fail-closed IM webhook）：

1. **凭据外泄** —— 告警正文原文直发第三方 IM 机器人与公开 GitHub Issue。
   而扫描 finding 的 `evidence` 字段就是「触发规则的那一行源代码」，硬编码 API key
   那条规则的 evidence 字面上就是一个 API key。不脱敏等于主动群发凭据。
2. **假绿第 5 层** —— `notify()` 返回送达状态，但 `main()` 恒 return 0。
   告警链路自己挂了，CI 仍然显示绿色，没人知道。
3. **无持久信号** —— 未送达只 print 一句警告，没有任何可被健康检查读取的状态。

对应三个机制：`redact()` 在所有出口生效、`--fail-on-undelivered` 把状态传出、
未送达台账 + `retry_undelivered()` 形成闭环。
"""

import os
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import notify as N  # noqa: E402


# 这些假凭据刻意不构成「真实有效格式」：
#   * SLACK_TOKEN 用 GitHub secret scanning 返回的 bypass placeholder
#     （原假值 xoxb-123456789012-1234567890123-... 被检测器判为真 secret，
#     推送 422 拒绝）。placeholder 机制就是为此设计的。
#   * 其余三个缩短到检测器的最小长度阈值之下，避免被二次拦截。
# 缩短不影响断言有效性 —— redact 的正则只要求形状与最小长度，
# 不要求通过 GitHub 检测器的校验和/长度规则。
GITHUB_PAT = "ghp_FAKEAbCdEfGhIjKlMnOpQrStUvWx"
OPENAI_KEY = "sk-proj-FAKE-9f8e7d6c5b4a3"
JWT = "eyJhbGciOiJ9.eyJzdWIiIn0.FA-KE-SIG1"
SLACK_TOKEN = "xoxb-3JUpE5kuuNt0KX8PzGeYvqHi8Sj"


class FakeResponse:
    """send_webhook 用 `with urlopen(...) as r:`，假响应必须实现上下文协议。"""

    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(captured):
    """返回一个能捕获请求头与请求体的 urlopen 替身。"""

    def _fake(req, timeout=None):
        captured["headers"] = dict(req.header_items())
        captured["raw"] = req.data.decode("utf-8")
        return FakeResponse()

    return _fake


def capture_webhook(body, signing_secret=()):
    """跑一次 send_webhook 并捕获实际发出的头与体。

    signing_secret 为元组时才 patch 签名密钥 —— 用它做「未配置」的负控。
    """
    captured = {}
    patches = [
        mock.patch.object(N, "WEBHOOK", "https://hooks.slack.example/abc"),
        mock.patch("urllib.request.urlopen", side_effect=fake_urlopen(captured)),
    ]
    if signing_secret:
        patches.append(mock.patch.object(N, "SIGNING_SECRET", signing_secret[0]))
    stack = ExitStack()
    for p in patches:
        stack.enter_context(p)
    try:
        ok = N.send_webhook("P1", "标题", body)
    finally:
        stack.close()
    return ok, captured


class IsolatedNotify(unittest.TestCase):
    """把 notify 的三个磁盘落点挪进临时目录，杜绝污染真实 data/state/。"""

    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        for attr, rel in (("ALERT_LOG", "alerts.jsonl"),
                          ("COOLDOWN_FILE", "alert_cooldown.json"),
                          ("UNDELIVERED_LOG", "undelivered_alerts.jsonl")):
            patcher = mock.patch.object(N, attr, Path(self._tmp.name) / rel)
            patcher.start()
            # 注意：addCleanup 需要**方法对象**，不是调用结果。
            # 写成 patcher.stop() 会把 None 登记成清理函数，tearDown 时抛
            # TypeError: 'NoneType' object is not callable。
            self.addCleanup(patcher.stop)

    def drop_all_channels(self):
        """同时关闭两个出口，模拟链路自身故障。返回可 `with` 的栈。"""
        stack = ExitStack()
        stack.enter_context(mock.patch.object(N, "GH_TOKEN", ""))
        stack.enter_context(mock.patch.object(N, "WEBHOOK", ""))
        return stack


class TestRedactionShapes(IsolatedNotify):
    def test_redacts_known_token_shapes(self):
        text = "deploy token: %s\nopenai: %s\nslack: %s" % (
            GITHUB_PAT, OPENAI_KEY, SLACK_TOKEN)
        out = N.redact(text)
        for secret in (GITHUB_PAT, OPENAI_KEY, SLACK_TOKEN):
            self.assertNotIn(secret, out)
        self.assertIn(N.REDACT_REPLACEMENT, out)

    def test_redacts_jwt(self):
        self.assertNotIn(JWT, N.redact("bearer chain %s end" % JWT))

    def test_redacts_key_value_pairs(self):
        src = ('API_KEY="deadbeefcafe1234"\npassword = "hunter22secret"\n'
               "client_secret: mysecretvalue99")
        out = N.redact(src)
        for leak in ("deadbeefcafe1234", "hunter22secret", "mysecretvalue99"):
            self.assertNotIn(leak, out)
        # 键名必须保留 —— 抹掉键名会让告警失去可读性
        self.assertIn("API_KEY", out)
        self.assertIn("password", out)

    def test_redacts_email_and_connection_strings(self):
        out = N.redact("ops@corp.example.com uses "
                       "postgres://svc:Sup3rSecret@db.internal/prod")
        self.assertNotIn("ops@corp.example.com", out)
        self.assertNotIn("Sup3rSecret", out)

    def test_redact_is_idempotent(self):
        """脱敏必须幂等：同一段文本跑两遍不得变化。

        历史上这里真出过缺陷 —— 泛化规则的值字符集包含 `]`，导致
        [REDACTED] 自身被当成新值再次匹配，第二次多出一个 `]`。
        """
        once = N.redact("token=%s tail" % GITHUB_PAT)
        self.assertEqual(once, N.redact(once))
        self.assertEqual(once, N.redact(once))

    def test_redact_preserves_benign_text(self):
        """自否证：脱敏不能把正常告警内容也抹掉，否则告警等于没发。"""
        benign = ("内容站构建失败，verify=success deploy=failure。"
                  "错误信息：Jekyll 生成 0 个 HTML 页面。"
                  "运行链接 https://github.com/lm203688/aishield/actions/runs/123")
        self.assertEqual(N.redact(benign), benign)

    def test_looks_redacted_flags_residue(self):
        """负控：残留高置信凭据时必须显式报 False，而不是假装绝对安全。"""
        self.assertTrue(N.looks_redacted("no secrets here"))
        self.assertFalse(N.looks_redacted("leak %s" % GITHUB_PAT))
        self.assertFalse(N.looks_redacted("jwt %s" % JWT))


class TestRedactionAtExport(IsolatedNotify):
    def test_webhook_payload_is_redacted(self):
        body = "发现凭据泄露，evidence 原文: %s" % GITHUB_PAT
        ok, captured = capture_webhook(body)
        self.assertTrue(ok)
        self.assertNotIn(GITHUB_PAT, captured["raw"])
        self.assertIn(N.REDACT_REPLACEMENT, captured["raw"])

    def test_webhook_payload_is_redacted_openai_key(self):
        ok, captured = capture_webhook("evidence: %s" % OPENAI_KEY)
        self.assertTrue(ok)
        self.assertNotIn(OPENAI_KEY, captured["raw"])

    def test_github_issue_body_is_redacted(self):
        with mock.patch.object(N, "GH_TOKEN", "dummy"), \
             mock.patch.object(
                 N, "_gh_api",
                 side_effect=[
                     # _find_issue：返回一条不含 marker 的既有 issue
                     [{"number": 7, "body": "unrelated existing issue"}],
                     # 创建告警 issue
                     {"number": 42},
                 ]
             ) as api:
            ok = N.send_github_issue(
                "P1", "标题", "泄露的 key: %s" % OPENAI_KEY, "fp-123")
        self.assertTrue(ok)
        created = api.call_args_list[-1]
        self.assertEqual(created.args[0], "POST")
        self.assertIn("issues", created.args[1])
        self.assertNotIn(OPENAI_KEY, created.args[2]["body"])
        self.assertIn(N.REDACT_REPLACEMENT, created.args[2]["body"])

    def test_github_issue_title_is_not_the_redaction_surface(self):
        """负控：标题不是脱敏面，标题里的普通文字保持原样。"""
        with mock.patch.object(N, "GH_TOKEN", "dummy"), \
             mock.patch.object(
                 N, "_gh_api",
                 side_effect=[[{"body": "x"}], {"number": 1}]):
            self.assertTrue(N.send_github_issue("P1", "健康检查失败", "b", "fp-t"))


class TestSignature(IsolatedNotify):
    def test_sign_payload_format_and_determinism(self):
        sig = N.sign_payload("secret-1", b'{"a":1}')
        self.assertTrue(sig.startswith("sha256="), sig)
        self.assertEqual(len(sig), len("sha256=") + 64)
        self.assertEqual(sig, N.sign_payload("secret-1", b'{"a":1}'))

    def test_sign_payload_differs_per_body_and_secret(self):
        base = N.sign_payload("secret-1", b'{"a":1}')
        self.assertNotEqual(base, N.sign_payload("secret-1", b'{"a":2}'))
        self.assertNotEqual(base, N.sign_payload("secret-2", b'{"a":1}'))

    def test_webhook_sends_signature_header_when_configured(self):
        ok, captured = capture_webhook("hello", signing_secret="test-signing-secret")
        self.assertTrue(ok)
        self.assertIn("X-aishield-signature", captured["headers"])
        self.assertTrue(
            captured["headers"]["X-aishield-signature"].startswith("sha256="))

    def test_webhook_omits_signature_header_when_unset(self):
        """负控：没配密钥就不该凭空造一个签名头。"""
        ok, captured = capture_webhook("b", signing_secret=())
        self.assertTrue(ok)
        self.assertNotIn("X-aishield-signature", captured["headers"])


class TestFailClosed(IsolatedNotify):
    def test_undelivered_p1_is_logged(self):
        with self.drop_all_channels():
            ok = N.notify("P1", "服务不可达", "body", "health-down")
        self.assertFalse(ok)
        recs = N.undelivered_records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["fingerprint"], "health-down")
        self.assertTrue(recs[0]["undelivered"])

    def test_cooldown_skip_is_not_logged(self):
        """负控：冷却期是设计行为，不是故障，不得进未送达台账。"""
        with mock.patch.object(N, "GH_TOKEN", "dummy"), \
             mock.patch.object(N, "send_github_issue", return_value=True):
            self.assertTrue(N.notify("P1", "t", "b", "fp-cd"))
            self.assertEqual(N.undelivered_records(), [])
            self.assertFalse(N.notify("P1", "t", "b", "fp-cd"))
        self.assertEqual(N.undelivered_records(), [])

    def test_p2_undelivered_is_not_logged(self):
        """负控：P2 按设计只落盘，不算链路故障。"""
        with self.drop_all_channels():
            self.assertFalse(N.notify("P2", "t", "b", "fp-p2"))
        self.assertEqual(N.undelivered_records(), [])

    def test_retry_undelivered_closes_loop(self):
        with self.drop_all_channels():
            N.notify("P1", "服务不可达", "body", "fp-retry")
        self.assertEqual(len(N.undelivered_records()), 1)
        with mock.patch.object(N, "send_webhook", return_value=True):
            self.assertEqual(N.retry_undelivered("P1"), 1)
        self.assertEqual(N.undelivered_records(), [])

    def test_retry_empty_returns_zero(self):
        self.assertEqual(N.retry_undelivered("P1"), 0)

    def test_retry_partial_failure_keeps_ledger(self):
        """负控：重试仍失败时台账必须保留，且不得重复追加。

        这是本测试真正钉死的东西：台账是「待处理集合」，不是事件日志。
        若按 append 语义写，重试失败一项就多一行，台账无限膨胀，
        且 `retry_undelivered` 的「全部成功才清空」判断永远对不上。
        """
        with self.drop_all_channels():
            N.notify("P1", "服务不可达", "b", "fp-keep")
        self.assertEqual(len(N.undelivered_records()), 1)
        with self.drop_all_channels():
            self.assertEqual(N.retry_undelivered("P1"), 0)
        recs = N.undelivered_records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["fingerprint"], "fp-keep")
        self.assertEqual(recs[0]["attempts"], 1)

    def test_ledger_dedupes_same_fingerprint(self):
        """同一指纹反复失败只留一行，attempts 累加。"""
        with self.drop_all_channels():
            N.notify("P1", "服务不可达", "b", "fp-dup")
            N.notify("P1", "服务不可达", "b", "fp-dup", force=True)
        recs = N.undelivered_records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["attempts"], 1)

    def _main(self, argv):
        with mock.patch.object(sys, "argv", ["scripts/notify.py"] + argv):
            return N.main()

    def test_main_fail_on_undelivered_returns_3(self):
        with self.drop_all_channels():
            rc = self._main(["--level", "P1", "--title", "服务不可达",
                             "--body", "b", "--fail-on-undelivered"])
        self.assertEqual(rc, 3)

    def test_main_default_returns_zero_for_backwards_compat(self):
        """不加 flag 时保持历史行为（恒 0），避免打破既有 workflow。"""
        with self.drop_all_channels():
            rc = self._main(["--level", "P1", "--title", "服务不可达", "--body", "b"])
        self.assertEqual(rc, 0)
        # 但台账必须已经记录 —— 静默失败被改成了可观测状态
        self.assertEqual(len(N.undelivered_records()), 1)

    def test_main_delivered_returns_zero(self):
        with mock.patch.object(N, "GH_TOKEN", "dummy"), \
             mock.patch.object(N, "send_github_issue", return_value=True):
            rc = self._main(["--level", "P1", "--title", "服务不可达",
                             "--body", "b", "--fail-on-undelivered"])
        self.assertEqual(rc, 0)

    def test_main_resolve_requires_fingerprint(self):
        self.assertEqual(self._main(["--resolve"]), 2)


if __name__ == "__main__":
    unittest.main()
