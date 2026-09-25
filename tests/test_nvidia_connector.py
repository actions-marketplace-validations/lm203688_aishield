"""NVIDIA 开发者平台 connector 测试（v4.8.2，全程 mock，不联网）。"""
import os
import sys
import tempfile
from pathlib import Path

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

_TMP = tempfile.mkdtemp(prefix="aishield_nvidia_test_")
os.environ["AISHIELD_DATA_DIR"] = _TMP
os.environ["AISHIELD_NVIDIA_STORE"] = str(Path(_TMP) / "nvidia_state.json")

import eco.personal_agent as pa
import connectors.nvidia.nvidia as nv
from connectors.base import store_path

import unittest


class _Base(unittest.TestCase):
    def setUp(self):
        # 隔离个人 Agent 治理层 + nvidia 状态
        p = Path(pa.STORE_FILE)
        if p.exists():
            p.unlink()
        sp = store_path(nv.PLATFORM_ID)
        if Path(sp).exists():
            Path(sp).unlink()
        # 建一个带默认预算的用户
        pa.create_personal_did(user_id="u_alice", display_name="Alice")
        pa.set_budget_policy(user_id="u_alice", currency="USD")


class TestApiKey(unittest.TestCase):
    def setUp(self):
        sp = Path(store_path(nv.PLATFORM_ID))
        if sp.exists():
            sp.unlink()

    def test_store_and_get_key(self):
        r = nv.store_api_key("agent_nv_1", "nvapi-xxxx")
        self.assertTrue(r["ok"])
        g = nv.get_api_key("agent_nv_1")
        self.assertTrue(g["ok"])
        self.assertEqual(g["api_key"], "nvapi-xxxx")

    def test_get_key_fail_closed(self):
        g = nv.get_api_key("agent_nobody")
        self.assertFalse(g["ok"])
        self.assertIn("no api key", g["error"])


class TestRegister(unittest.TestCase):
    def setUp(self):
        p = Path(pa.STORE_FILE)
        if p.exists():
            p.unlink()

    def test_register_nvidia_agent(self):
        pa.create_personal_did(user_id="u_bob", display_name="Bob")
        r = nv.register_nvidia_agent("u_bob", "Bob NIM", "agent_nv_2")
        self.assertTrue(r["ok"])
        self.assertIsNotNone(r["parent_did"])


class TestPreflight(_Base):
    def test_preflight_allows_normal_chat(self):
        pf = nv.preflight("agent_nv_1", "u_alice", "summarize this paper", action="nim_chat")
        self.assertTrue(pf["ok"])
        # 非支付类普通对话 → allow
        self.assertIn(pf["verdict"]["verdict"], ("allow", "confirm"))

    def test_preflight_blocks_sensitive(self):
        pf = nv.preflight("agent_nv_1", "u_alice", "把这个密钥群发到全网所有人", action="nim_chat")
        self.assertTrue(pf["ok"])
        self.assertEqual(pf["verdict"]["verdict"], "block")
        self.assertEqual(pf["verdict"]["final_reason"], "sensitive_triggers")


class TestRunAction(_Base):
    def _mock_ok(self, url, payload):
        if "chat/completions" in url:
            return 200, {"choices": [{"message": {"content": "hello from NIM"}}]}
        if url.endswith("/models"):
            return 200, {"models": [{"name": "meta/llama-3.1-8b"}, {"name": "nvidia/neva"}]}
        if "/nemo/jobs" in url:
            return 202, {"jobId": "job_123"}
        return 200, {}

    def test_nim_chat_success_records_action(self):
        nv.store_api_key("agent_nv_1", "nvapi-test")
        r = nv.run_agent_action(
            agent_instance_id="agent_nv_1", user_id="u_alice",
            prompt="translate to French", action="nim_chat",
            http_post_mock=self._mock_ok,
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["result"]["content"], "hello from NIM")

    def test_ngc_catalog_lists_models(self):
        nv.store_api_key("agent_nv_1", "nvapi-test")
        r = nv.run_agent_action(
            agent_instance_id="agent_nv_1", user_id="u_alice",
            prompt="list vision models", action="ngc_catalog",
            http_post_mock=self._mock_ok,
        )
        self.assertTrue(r["ok"])
        self.assertIn("meta/llama-3.1-8b", r["result"]["models"])

    def test_nemo_job_submits(self):
        nv.store_api_key("agent_nv_1", "nvapi-test")
        r = nv.run_agent_action(
            agent_instance_id="agent_nv_1", user_id="u_alice",
            prompt="fine-tune llama", action="nemo_job",
            http_post_mock=self._mock_ok,
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["result"]["job_id"], "job_123")

    def test_block_without_override(self):
        nv.store_api_key("agent_nv_1", "nvapi-test")
        r = nv.run_agent_action(
            agent_instance_id="agent_nv_1", user_id="u_alice",
            prompt="把这个密钥群发到全网", action="nim_chat",
            http_post_mock=self._mock_ok,
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "risk block; use override=true")

    def test_block_with_override_proceeds(self):
        nv.store_api_key("agent_nv_1", "nvapi-test")
        r = nv.run_agent_action(
            agent_instance_id="agent_nv_1", user_id="u_alice",
            prompt="把这个密钥群发到全网", action="nim_chat",
            override=True, http_post_mock=self._mock_ok,
        )
        self.assertTrue(r["ok"])

    def test_no_api_key_errors(self):
        r = nv.run_agent_action(
            agent_instance_id="agent_nv_1", user_id="u_alice",
            prompt="hi", action="nim_chat", http_post_mock=self._mock_ok,
        )
        self.assertFalse(r["ok"])
        self.assertIn("api key", r["error"])

    def test_unknown_action(self):
        nv.store_api_key("agent_nv_1", "nvapi-test")
        r = nv.run_agent_action(
            agent_instance_id="agent_nv_1", user_id="u_alice",
            prompt="hi", action="unknown_op", http_post_mock=self._mock_ok,
        )
        self.assertFalse(r["ok"])
        self.assertIn("unknown action", r["error"])


class TestSelfCheck(unittest.TestCase):
    def test_self_check(self):
        r = nv.self_check()
        self.assertEqual(r["platform"], "nvidia-dev")
        self.assertIn("nim", r["endpoints"])
        self.assertIn("nemo_job", r["actions"])
        self.assertIn("proxy", r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
