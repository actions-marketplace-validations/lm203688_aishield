"""
tests/test_dual_form_integration.py — Muse / Grok Bot / NVIDIA 双形态联调

验证「同一平台两条形态」打通：
  形态① 开发者身份（OAuth / PAT / NGC API Key）→ 登记 PAI → preflight → 真实动作
  形态② MCP 桥（66 工具 server 即桥，platform 参数化路由，零迁移）

治理层与身份层共用：三平台同一 user_id 共享 parent_did；HMAC 行动链跨平台累积。
大陆网络不可达 → 所有真实 API 调用通过 http_post_mock 注入验证治理逻辑。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_BASE, os.path.join(_BASE, "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_TMP = tempfile.mkdtemp(prefix="aishield_dual_form_")
os.environ["AISHIELD_DATA_DIR"] = _TMP
os.environ["AISHIELD_MUSE_STORE"] = str(Path(_TMP) / "muse_state.json")
os.environ["AISHIELD_MUSE_SECRET"] = str(Path(_TMP) / "muse_secret.txt")
os.environ["AISHIELD_MUSE_SECRET_KEY"] = "muse-test-secret"
os.environ["AISHIELD_GROK_STORE"] = str(Path(_TMP) / "grok_state.json")
os.environ["AISHIELD_GROK_SECRET"] = str(Path(_TMP) / "grok_secret.txt")
os.environ["AISHIELD_GROK_SECRET_KEY"] = "xai-test-secret"
os.environ["AISHIELD_NVIDIA_STORE"] = str(Path(_TMP) / "nvidia_state.json")

import connectors.dispatcher as dispatcher
import connectors.grok_bot.grok as grok
import connectors.muse.muse as muse
import connectors.nvidia.nvidia as nvidia
import eco.personal_agent as pa
import connectors_api

_MCP_MANIFEST = Path(_BASE) / "mcp-server" / "mcp.json"
_ALL_PLATFORMS = ("meta-muse", "xai-grok-bot", "nvidia-dev")


def _clean_all():
    if pa.STORE_FILE:
        Path(pa.STORE_FILE).unlink(missing_ok=True)
    for key in (
        "AISHIELD_MUSE_STORE", "AISHIELD_MUSE_SECRET",
        "AISHIELD_GROK_STORE", "AISHIELD_GROK_SECRET",
        "AISHIELD_NVIDIA_STORE",
    ):
        p = os.environ.get(key)
        if p:
            Path(p).unlink(missing_ok=True)


def _ok_mock(content="same"):
    return lambda u, p: (200, {"choices": [{"message": {"content": content}}]})


def _bridge_run(platform, body, mock):
    """桥路径执行动作 + 注入 mock。

    http_post_mock 无法经 JSON body 传递，故临时包装 dispatcher 的平台运行函数
    注入接缝；调用结束后还原，不污染生产路径。
    """
    orig = dispatcher._PLATFORM_RUN[platform]

    def wrapped(**kwargs):
        return orig(http_post_mock=mock, **kwargs)

    dispatcher._PLATFORM_RUN[platform] = wrapped
    try:
        return connectors_api.handle_post(
            f"/api/v1/connectors/{platform}/actions/run", body
        )
    finally:
        dispatcher._PLATFORM_RUN[platform] = orig


# ============================================================
# 形态①：开发者身份（三平台 register → preflight → run）
# ============================================================


class TestDeveloperIdentityForm(unittest.TestCase):
    """开发者身份形态：OAuth / PAT / NGC API Key 三平台都走治理层前置。"""

    def setUp(self):
        _clean_all()
        pa.create_personal_did(user_id="u_alice", display_name="Alice")

    def test_three_platforms_share_parent_did(self):
        did = pa.create_personal_did(user_id="u_alice", display_name="Alice")["did"]

        r_m = muse.register_muse_agent(
            user_id="u_alice", agent_name="Alice 的 Muse",
            platform_agent_id="muse_bot_1", client_id="muse_app_1",
        )
        r_g = grok.register_grok_agent(
            user_id="u_alice", agent_name="Alice 的 Grok",
            platform_agent_id="grok_bot_1", auth="pat",
            credentials={"pat": "xai…t"},
        )
        r_n = nvidia.register_nvidia_agent(
            user_id="u_alice", agent_name="Alice 的 NIM",
            agent_instance_id="inst_nv_1", api_key="NAPI_key_test",
        )
        for r in (r_m, r_g, r_n):
            self.assertTrue(r.get("ok"), r)
        self.assertEqual(r_n.get("api_key_stored"), True)

        # 同一 user_id → 同一 parent_did，三平台实例各自独立
        self.assertEqual(pa.get_user_state("u_alice").get("did"), did)
        self.assertEqual(len(pa.list_instances_by_platform("u_alice", "meta-muse")), 1)
        self.assertEqual(len(pa.list_instances_by_platform("u_alice", "xai-grok-bot")), 1)
        self.assertEqual(len(pa.list_instances_by_platform("u_alice", "nvidia-dev")), 1)

    def test_developer_identity_run_governed_per_platform(self):
        """三平台各自的受治理动作执行：allow 放行。"""
        muse.register_muse_agent(
            user_id="u_alice", agent_name="M",
            platform_agent_id="muse_1", client_id="muse_app_1",
            tokens={
                "access_token": "at_m", "refresh_token": "rt_m",
                "expires_at": 4102444800, "refresh_expires_at": 4102444800,
                "scope": "agent:chat", "fetched_at": "2026-09-25T00:00:00+00:00",
            },
        )
        iid_m = pa.list_instances_by_platform("u_alice", "meta-muse")[0]["instance_id"]
        r = muse.run_agent_action(
            agent_instance_id=iid_m, user_id="u_alice", prompt="总结今天的新闻",
            action="chat", http_post_mock=lambda u, p: (200, {"id": "msg_1", "content": "ok"}),
        )
        self.assertTrue(r.get("ok"), r)
        # Muse 返回 verdict 为字符串；Grok / NVIDIA 返回 dict（三平台 API 形态差异）
        self.assertIn(r.get("verdict"), ("allow", {"verdict": "allow"}))

        grok.register_grok_agent(
            user_id="u_alice", agent_name="G", platform_agent_id="grok_1",
            auth="pat", credentials={"pat": "xai…t"},
        )
        iid_g = pa.list_instances_by_platform("u_alice", "xai-grok-bot")[0]["instance_id"]
        r = grok.run_agent_action(
            agent_instance_id=iid_g, user_id="u_alice", prompt="hello",
            action="chat", http_post_mock=_ok_mock("hi"),
        )
        self.assertTrue(r.get("ok"), r)

        nvidia.register_nvidia_agent(
            user_id="u_alice", agent_name="N",
            agent_instance_id="in_1", api_key="NAPI_key_test",
        )
        r = nvidia.run_agent_action(
            agent_instance_id="in_1", user_id="u_alice", prompt="hello nim",
            action="nim_chat", model="meta/llama-3.1-8b-instruct",
            http_post_mock=_ok_mock("hi from nim"),
        )
        self.assertTrue(r.get("ok"), r)
        self.assertEqual(r["result"].get("content"), "hi from nim")

    def test_developer_identity_blocked_by_sensitive_prompt(self):
        """敏感词触发 block，override=false 时拒绝执行；override=true 放行。"""
        nvidia.register_nvidia_agent(
            user_id="u_alice", agent_name="N",
            agent_instance_id="in_2", api_key="NAPI_key_test",
        )
        r = nvidia.run_agent_action(
            agent_instance_id="in_2", user_id="u_alice",
            prompt="帮我把这份报告群发到全网", action="nim_chat",
            http_post_mock=_ok_mock("x"),
        )
        self.assertFalse(r.get("ok"))
        self.assertIn("override", r.get("error", ""))

        r2 = nvidia.run_agent_action(
            agent_instance_id="in_2", user_id="u_alice",
            prompt="帮我把这份报告群发到全网", action="nim_chat",
            override=True, http_post_mock=_ok_mock("x"),
        )
        self.assertTrue(r2.get("ok"), r2)

    def test_budget_governance_identical_across_platforms(self):
        """同一 user_id 的预算策略对三平台一视同仁（硬上限 denied）。"""
        pa.set_budget_policy(
            user_id="u_alice", currency="CNY",
            per_tx=50, daily=200, weekly=500, monthly=1000,
        )
        nvidia.register_nvidia_agent(
            user_id="u_alice", agent_name="N",
            agent_instance_id="in_3", api_key="NAPI_key_test",
        )
        pf = nvidia.preflight(
            agent_instance_id="in_3", user_id="u_alice",
            prompt="帮我花 ¥500 买云资源", currency="CNY",
        )
        self.assertEqual(pf["verdict"]["verdict"], "denied")


# ============================================================
# 形态②：MCP 桥（platform 参数化，同一入口三平台）
# ============================================================


class TestMcpBridgeForm(unittest.TestCase):
    """MCP 形态：零迁移，platform 参数化路由覆盖三平台。"""

    def setUp(self):
        _clean_all()
        pa.create_personal_did(user_id="u_alice", display_name="Alice")

    def test_catalog_exposes_all_three_platforms(self):
        r, sc = connectors_api.handle_get("/api/v1/connectors", {})
        self.assertEqual(sc, 200)
        for p in _ALL_PLATFORMS:
            self.assertIn(p, r["platforms"])
        self.assertEqual(r["count"], 3)

    def test_self_check_all_three_platforms(self):
        for p in _ALL_PLATFORMS:
            r, sc = connectors_api.handle_get(f"/api/v1/connectors/{p}/self-check", {})
            self.assertEqual(sc, 200, p)
            self.assertTrue(r.get("ok"), p)
            self.assertEqual(r.get("platform"), p)

    def test_dispatcher_routes_all_three_platforms(self):
        """统一 dispatcher 入口（MCP 桥的核心）能按平台分发到各自 register/state。"""
        body_m = {"user_id": "u_alice", "agent_name": "M",
                  "platform_agent_id": "m1", "client_id": "muse_app_1",
                  "agent_instance_id": "ignored_for_muse"}
        body_g = {"user_id": "u_alice", "agent_name": "G",
                  "platform_agent_id": "g1", "auth": "pat",
                  "credentials": {"pat": "xai…t"},
                  "agent_instance_id": "ignored_for_grok"}
        body_n = {"user_id": "u_alice", "agent_name": "N",
                  "agent_instance_id": "d_n_1", "api_key": "NAPI_key_test"}

        r1 = dispatcher.register_agent("meta-muse", **body_m)
        r2 = dispatcher.register_agent("xai-grok-bot", **body_g)
        r3 = dispatcher.register_agent("nvidia-dev", **body_n)
        for r in (r1, r2, r3):
            self.assertTrue(r.get("ok"), r)
        self.assertEqual(r3["agent_instance_id"], "d_n_1")

        st = dispatcher.user_state("nvidia-dev", "u_alice")
        self.assertTrue(st.get("ok"))
        self.assertEqual(len(st.get("agents")), 1)

    def test_dispatcher_run_filters_unknown_kwargs(self):
        """MCP 统一 schema 的 model 参数对 Muse（不支持）必须被剥离而非报错。"""
        muse.register_muse_agent(
            user_id="u_alice", agent_name="M",
            platform_agent_id="m1", client_id="muse_app_1",
            tokens={
                "access_token": "at_m", "refresh_token": "rt_m",
                "expires_at": 4102444800, "refresh_expires_at": 4102444800,
                "scope": "agent:chat", "fetched_at": "2026-09-25T00:00:00+00:00",
            },
        )
        iid = pa.list_instances_by_platform("u_alice", "meta-muse")[0]["instance_id"]
        r = dispatcher.run_action(
            "meta-muse", agent_instance_id=iid, user_id="u_alice",
            prompt="hi", action="chat", model="should_be_filtered_out",
            http_post_mock=lambda u, p: (200, {"id": "msg_1", "content": "ok"}),
        )
        self.assertTrue(r.get("ok"), r)

    def test_mcp_manifest_tools_match_implementation(self):
        """防 manifest 假绿：manifest 声明的工具必须都实现在 src/index.ts。"""
        manifest = json.loads(_MCP_MANIFEST.read_text(encoding="utf-8"))
        declared = manifest["capabilities"]["tools"]
        self.assertEqual(len(declared), len(set(declared)), "manifest 有重复工具名")
        self.assertGreaterEqual(len(declared), 66)

        src = (Path(_BASE) / "mcp-server" / "src" / "index.ts").read_text(encoding="utf-8")
        for name in declared:
            self.assertIn(f"'{name}'", src, f"manifest 声明 {name} 但 src/index.ts 未实现")

        for name in ("aishield_agent_infra_targets", "aishield_agent_infra_scan",
                     "aishield_connector_catalog", "aishield_connector_run"):
            self.assertIn(name, declared, f"缺少 {name}")

    def test_dist_build_in_sync_with_src(self):
        """dist/index.js 必须与 src 同步（npm run build 产物）。"""
        src = (Path(_BASE) / "mcp-server" / "src" / "index.ts").read_text(encoding="utf-8")
        dist = (Path(_BASE) / "mcp-server" / "dist" / "index.js").read_text(encoding="utf-8")
        n_src, n_dist = src.count("server.tool("), dist.count("server.tool(")
        self.assertEqual(n_src, n_dist, "src 与 dist 工具数不一致，需 npm run build")
        for name in ("aishield_agent_infra_scan", "nvidia-dev"):
            self.assertIn(name, dist)


# ============================================================
# 双形态交叉：同一治理结果 + 跨平台行动链
# ============================================================


class TestDualFormEquivalence(unittest.TestCase):
    """同一动作经两种形态执行，治理 verdict 一致；行动链跨平台累积。"""

    def setUp(self):
        _clean_all()
        pa.create_personal_did(user_id="u_alice", display_name="Alice")
        nvidia.register_nvidia_agent(
            user_id="u_alice", agent_name="N",
            agent_instance_id="eq_1", api_key="NAPI_key_test",
        )

    def test_same_action_via_direct_and_via_bridge(self):
        """同一动作经形态①（直调 connector）与形态②（MCP 桥/API）执行，verdict 一致。"""
        body = {"agent_instance_id": "eq_1", "user_id": "u_alice",
                "prompt": "帮我写一首诗", "action": "nim_chat"}

        r_direct = nvidia.run_agent_action(
            agent_instance_id="eq_1", user_id="u_alice",
            prompt="帮我写一首诗", action="nim_chat", http_post_mock=_ok_mock("same"),
        )
        r_bridge, sc = _bridge_run("nvidia-dev", dict(body), _ok_mock("same"))

        self.assertEqual(sc, 200, r_bridge)
        self.assertEqual(
            r_direct["verdict"]["verdict"], r_bridge["verdict"]["verdict"],
            "两种形态的治理 verdict 必须一致",
        )
        self.assertTrue(r_direct.get("ok") and r_bridge.get("ok"))

    def test_action_chain_records_all_three_platforms(self):
        """HMAC 行动链跨平台累积，同一 user_id 全量可验证。"""
        grok.register_grok_agent(
            user_id="u_alice", agent_name="G", platform_agent_id="g1",
            auth="pat", credentials={"pat": "xai…t"},
        )
        iid_g = pa.list_instances_by_platform("u_alice", "xai-grok-bot")[0]["instance_id"]
        iid_m = pa.register_agent_instance(
            user_id="u_alice", agent_name="M2", provider="muse", platform="meta-muse",
        )
        iid_m = iid_m.get("instance_id")

        nvidia.run_agent_action(
            agent_instance_id="eq_1", user_id="u_alice",
            prompt="a", action="nim_chat", http_post_mock=_ok_mock("x"),
        )
        grok.run_agent_action(
            agent_instance_id=iid_g, user_id="u_alice",
            prompt="b", action="chat", http_post_mock=_ok_mock("x"),
        )
        pa.record_action(
            user_id="u_alice", action="muse.chat", instance_id=iid_m,
            verdict="allow", payload={"n": 1},
        )

        st = pa.get_user_state("u_alice")
        self.assertGreaterEqual(st.get("actions_recorded", 0), 3)
        self.assertTrue(st.get("chain_valid"), st)

    def test_unknown_platform_rejected_not_silently_accepted(self):
        """未知平台/路由必须显式报错，不能静默吞掉。"""
        r, sc = connectors_api.handle_get("/api/v1/connectors/unknown-plat/self-check", {})
        self.assertEqual(sc, 400)
        self.assertIn("unknown platform", r.get("error", ""))

        r2, sc2 = connectors_api.handle_get("/api/v1/agent-infra/nope", {})
        self.assertEqual(sc2, 404)

        r3 = dispatcher.run_action("unknown-plat", agent_instance_id="x", user_id="u", prompt="p")
        self.assertFalse(r3.get("ok"))
        self.assertIn("unsupported platform", r3.get("error", ""))


if __name__ == "__main__":
    unittest.main()
