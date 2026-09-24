"""
tests/test_evidence_bundle.py — Evidence Bundle 1.0 + Responsibility Chain v1.1 + ship_gate 10 态测试

覆盖：
  - HMAC 链式审计（含篡改检测、密钥正确性）
  - OCSF / STIX / ATT&CK 映射
  - Proposal-Bound Approval
  - 双轮独立复测状态机
  - 回滚与归档
  - 离线 verify_bundle_payload
  - responsibility_chain 迁移到 bundle
  - ship_gate 10 态状态机转移合法性 + 拒绝/接受争议分支
  - 向后兼容（无 HMAC 时退化为 SHA-256）

运行：
    python tests/test_evidence_bundle.py
    python -m pytest tests/test_evidence_bundle.py -x
"""
from __future__ import annotations

import os
import sys
import unittest

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)


class TestEvidenceBundleCore(unittest.TestCase):
    """Evidence Bundle 核心：HMAC 链 + 基本事件。"""

    def test_empty_bundle_verify_ok(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(title="empty")
        v = b.verify()
        self.assertTrue(v["valid"])
        self.assertEqual(v["events"], 0)

    def test_single_event_hmac(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="test-key-2026")
        e = b.add_event(event_type="audit.record", agent_id="a", action="x")
        self.assertTrue(b.verify()["valid"])
        self.assertEqual(e["kind"], "event")
        self.assertEqual(e["seq"], 1)
        self.assertEqual(e["global_seq"], 1)
        self.assertEqual(e["prev_hash"], "0" * 64)

    def test_multi_event_chain(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        for i in range(5):
            b.add_event(event_type="audit.record", agent_id="a",
                        action=f"step-{i}")
        v = b.verify()
        self.assertTrue(v["valid"])
        self.assertEqual(v["events"], 5)

    def test_tamper_detection_body(self):
        """篡改事件内容应导致 verify 失败。"""
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        b.add_event(event_type="audit.record", agent_id="a", action="x")
        b.events[0]["agent_id"] = "hacker"  # 篡改
        v = b.verify()
        self.assertFalse(v["valid"])
        self.assertIn("signature mismatch", v["reason"])

    def test_tamper_detection_prev_hash(self):
        """篡改 prev_hash 应导致 verify 失败。"""
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        b.add_event(event_type="audit.record", agent_id="a", action="x")
        b.add_event(event_type="audit.record", agent_id="a", action="y")
        b.events[1]["prev_hash"] = "f" * 64  # 篡改 prev_hash
        v = b.verify()
        self.assertFalse(v["valid"])
        self.assertIn("prev_hash mismatch", v["reason"])

    def test_no_hmac_degrades_to_sha(self):
        """无密钥时应退化为 SHA-256，仍能校验。"""
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(title="no hmac")
        b.add_event(event_type="audit.record", agent_id="a", action="x")
        v = b.verify()
        self.assertTrue(v["valid"])
        self.assertFalse(v["hmac"])


class TestEvidenceBundleApproval(unittest.TestCase):
    """Proposal-Bound Approval 机制。"""

    def test_proposal_approval_roundtrip(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        prop = b.create_proposal(agent_id="p", action="kill", target={"pid": 1})
        self.assertEqual(prop["status"], "proposed")
        appr = b.approve_proposal(proposal_id=prop["proposal_id"],
                                  approver_id="h", scope="task")
        self.assertEqual(appr["approval_hash"], appr["approval_hash"])
        # 关键：proposal_hash 必须被 approval 引用
        self.assertEqual(appr["proposal_hash"], prop["proposal_hash"])
        self.assertTrue(b.verify()["valid"])

    def test_duplicate_approval_rejected(self):
        """同一 proposal 重复审批应报错。"""
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        prop = b.create_proposal(agent_id="p", action="x", target={"n": "y"})
        b.approve_proposal(proposal_id=prop["proposal_id"], approver_id="h")
        with self.assertRaises(ValueError):
            b.approve_proposal(proposal_id=prop["proposal_id"], approver_id="h2")

    def test_approval_nonexistent_proposal(self):
        """审批不存在的 proposal 应报错。"""
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        with self.assertRaises(ValueError):
            b.approve_proposal(proposal_id="prop-nonexistent",
                               approver_id="h")

    def test_reject_proposal(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        prop = b.create_proposal(agent_id="p", action="x", target={"n": "y"})
        b.reject_proposal(proposal_id=prop["proposal_id"],
                          approver_id="h", reason="not allowed")
        self.assertTrue(b.verify()["valid"])
        # approvals 数组里应有 rejection 记录
        self.assertEqual(len(b.approvals), 1)
        self.assertEqual(b.approvals[0]["kind"], "rejection")

    def test_dispatch_requires_valid_approval(self):
        """dispatch 必须有有效 approval。"""
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        with self.assertRaises(ValueError):
            b.dispatch(approval_id="appr-nonexistent", executor_id="e")


class TestEvidenceBundleVerification(unittest.TestCase):
    """双轮独立复测状态机。"""

    def test_double_round_verify(self):
        """CyberGuard 双轮独立复测：round1 inconclusive → round2 verified。"""
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        prop = b.create_proposal(agent_id="p", action="kill", target={"n": "x"})
        appr = b.approve_proposal(proposal_id=prop["proposal_id"],
                                  approver_id="h")
        b.dispatch(approval_id=appr["approval_id"], executor_id="e")
        obs1 = b.observe(approval_id=appr["approval_id"],
                         observer_id="obs-A", round_no=1, passed=False,
                         confidence=0.7)
        self.assertFalse(obs1["passed"])
        obs2 = b.observe(approval_id=appr["approval_id"],
                         observer_id="obs-B", round_no=2, passed=True,
                         confidence=0.98)
        self.assertTrue(obs2["passed"])
        self.assertTrue(b.verify()["valid"])

    def test_invalid_round_rejected(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        prop = b.create_proposal(agent_id="p", action="x", target={"n": "y"})
        appr = b.approve_proposal(proposal_id=prop["proposal_id"],
                                  approver_id="h")
        b.dispatch(approval_id=appr["approval_id"], executor_id="e")
        with self.assertRaises(ValueError):
            b.observe(approval_id=appr["approval_id"],
                      observer_id="o", round_no=3, passed=True)

    def test_invalid_confidence_rejected(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        prop = b.create_proposal(agent_id="p", action="x", target={"n": "y"})
        appr = b.approve_proposal(proposal_id=prop["proposal_id"],
                                  approver_id="h")
        b.dispatch(approval_id=appr["approval_id"], executor_id="e")
        with self.assertRaises(ValueError):
            b.observe(approval_id=appr["approval_id"],
                      observer_id="o", round_no=1, passed=True,
                      confidence=1.5)


class TestEvidenceBundleRollbackArchive(unittest.TestCase):
    """回滚与归档。"""

    def test_rollback_flow(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k")
        prop = b.create_proposal(agent_id="p", action="x", target={"n": "y"})
        appr = b.approve_proposal(proposal_id=prop["proposal_id"],
                                  approver_id="h")
        b.dispatch(approval_id=appr["approval_id"], executor_id="e")
        rb = b.rollback(approval_id=appr["approval_id"], operator_id="o",
                        reason="compensating")
        self.assertEqual(rb["kind"], "rollback")
        self.assertTrue(b.verify()["valid"])
        self.assertEqual(len(b.rollbacks), 1)

    def test_archive_signs_manifest(self):
        from eco.evidence_bundle import EvidenceBundle
        b = EvidenceBundle(hmac_secret="k", title="t")
        b.add_event(event_type="audit.record", agent_id="a", action="x")
        manifest = b.archive(archiver_id="arch-bot")
        self.assertIn("signature", manifest)
        self.assertEqual(len(b.signatures), 1)
        self.assertTrue(manifest["counts"]["events"] >= 1)


class TestEvidenceBundleExport(unittest.TestCase):
    """导出 + 离线验证。"""

    def test_export_and_verify_offline(self):
        from eco.evidence_bundle import (EvidenceBundle, verify_bundle_payload)
        b = EvidenceBundle(hmac_secret="k", title="t")
        b.add_event(event_type="audit.record", agent_id="a", action="x")
        prop = b.create_proposal(agent_id="p", action="y", target={"n": "z"})
        appr = b.approve_proposal(proposal_id=prop["proposal_id"],
                                  approver_id="h")
        exported = b.export()
        result = verify_bundle_payload(exported, hmac_secret="k")
        self.assertTrue(result["valid"])
        self.assertEqual(result["run_id"], b.run_id)

    def test_offline_verify_detects_tamper(self):
        from eco.evidence_bundle import (EvidenceBundle, verify_bundle_payload)
        b = EvidenceBundle(hmac_secret="k", title="t")
        b.add_event(event_type="audit.record", agent_id="a", action="x")
        b.add_event(event_type="audit.record", agent_id="b", action="y")
        exported = b.export()
        # 篡改导出的内容
        exported["events"][0]["agent_id"] = "attacker"
        result = verify_bundle_payload(exported, hmac_secret="k")
        self.assertFalse(result["valid"])
        self.assertIn("signature mismatch", result["reason"])

    def test_wrong_hmac_secret_rejected(self):
        from eco.evidence_bundle import (EvidenceBundle, verify_bundle_payload)
        b = EvidenceBundle(hmac_secret="correct-key")
        b.add_event(event_type="audit.record", agent_id="a", action="x")
        exported = b.export()
        result = verify_bundle_payload(exported, hmac_secret="wrong-key")
        self.assertFalse(result["valid"])

    def test_unsupported_schema(self):
        from eco.evidence_bundle import verify_bundle_payload
        result = verify_bundle_payload({"schema": "unknown/0.1"})
        self.assertFalse(result["valid"])
        self.assertIn("unsupported schema", result["reason"])

    def test_not_dict_input(self):
        from eco.evidence_bundle import verify_bundle_payload
        self.assertFalse(verify_bundle_payload([])["valid"])
        self.assertFalse(verify_bundle_payload("string")["valid"])


class TestEvidenceBundleOCSFStix(unittest.TestCase):
    """OCSF / STIX / ATT&CK 映射。"""

    def test_ocsf_mapping(self):
        from eco.evidence_bundle import to_ocsf
        o = to_ocsf("executor.dispatch",
                    {"agent_id": "a", "action": "x",
                     "outcome": "successful"})
        self.assertEqual(o["class_name"], "Process")
        self.assertEqual(o["action_name"], "dispatch")
        self.assertEqual(o["result"], True)

    def test_stix_observables(self):
        from eco.evidence_bundle import to_stix_observables
        obs = to_stix_observables({
            "files": [{"name": "a.js", "sha256": "a" * 64}],
            "urls": ["https://evil.example"],
            "ips": ["1.2.3.4", "2001:db8::1"],
            "domains": ["evil.example"],
            "processes": [{"name": "miner", "pid": 42}],
            "software": [{"name": "miner-x", "version": "1.0"}],
        })
        types = [o["type"] for o in obs]
        self.assertIn("file", types)
        self.assertIn("url", types)
        self.assertIn("ipv4-addr", types)
        self.assertIn("ipv6-addr", types)
        self.assertIn("domain-name", types)
        self.assertIn("process", types)
        self.assertIn("software", types)
        for o in obs:
            self.assertEqual(o["spec_version"], "2.1")

    def test_attack_mapping(self):
        from eco.evidence_bundle import to_attack_mapping
        m = to_attack_mapping("supply_chain")
        self.assertEqual(m["mitre_attack_technique"], "T1195")
        m2 = to_attack_mapping("prompt_injection")
        self.assertEqual(m2["mitre_attack_technique"], "T1078.004")
        self.assertIsNone(to_attack_mapping("unknown_ttp"))


class TestResponsibilityChainUpgrade(unittest.TestCase):
    """responsibility_chain v1.1 升级测试。"""

    def test_hmac_chain_verify(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain(hmac_key="k")
        c.record(agent_id="a", action="x")
        self.assertTrue(c.hmac_enabled)
        self.assertTrue(c.verify()["valid"])

    def test_backward_compat_no_hmac(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain()
        e1 = c.record(agent_id="a", action="x",
                      input_ref="user", output_ref={"k": 1})
        e2 = c.record(agent_id="b", action="y", parent_seq=e1["seq"],
                      input_ref=e1["output_ref"])
        self.assertFalse(c.hmac_enabled)
        self.assertTrue(c.verify()["valid"])

    def test_invalid_state_rejected(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain()
        with self.assertRaises(ValueError):
            c.record(agent_id="a", action="x", state="invalid_state")

    def test_invalid_round_rejected(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain()
        with self.assertRaises(ValueError):
            c.record(agent_id="a", action="x", round_no=3)

    def test_find_by_state(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain()
        c.record(agent_id="a", action="x", state="verified")
        c.record(agent_id="b", action="y", state="inconclusive")
        c.record(agent_id="c", action="z", state="inconclusive")
        self.assertEqual(len(c.find_by_state("inconclusive")), 2)
        self.assertEqual(len(c.find_by_state("verified")), 1)

    def test_find_by_proposal(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain()
        c.record(agent_id="a", action="x", proposal_id="prop-1")
        c.record(agent_id="b", action="y", proposal_id="prop-2")
        c.record(agent_id="c", action="z", proposal_id="prop-1")
        self.assertEqual(len(c.find_by_proposal("prop-1")), 2)

    def test_stats(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain()
        c.record(agent_id="a", action="x", state="verified")
        c.record(agent_id="b", action="y", state="verified")
        c.record(agent_id="c", action="z", state="failed")
        stats = c.stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_state"]["verified"], 2)
        self.assertEqual(stats["by_state"]["failed"], 1)

    def test_migrate_to_evidence_bundle(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain(hmac_key="k")
        c.record(agent_id="a", action="x", state="verified")
        c.record(agent_id="b", action="y", state="inconclusive",
                 proposal_id="p-1", approval_id="a-1")
        c.record(agent_id="c", action="z", state="failed")
        bundle = c.to_evidence_bundle(hmac_secret="k", title="migrated")
        v = bundle.verify()
        self.assertTrue(v["valid"])
        self.assertEqual(v["events"], 3)

    def test_trace_and_root_cause(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain()
        e1 = c.record(agent_id="planner", action="plan",
                      input_ref="u", output_ref={"sub": ["a"]})
        e2 = c.record(agent_id="scanner", action="scan",
                      parent_seq=e1["seq"],
                      input_ref=e1["output_ref"], output_ref={"findings": []})
        chain = c.trace(e2["output_ref"])
        self.assertEqual(chain[0]["agent_id"], "planner")
        self.assertEqual(c.root_cause(e2["output_ref"])["agent_id"], "planner")

    def test_tamper_detection(self):
        from eco.responsibility_chain import ResponsibilityChain
        c = ResponsibilityChain(hmac_key="k")
        c.record(agent_id="a", action="x")
        c.entries[0]["action"] = "tampered"
        v = c.verify()
        self.assertFalse(v["valid"])
        self.assertEqual(v["reason"], "记录被篡改")


class TestShipGateStateMachine(unittest.TestCase):
    """ship_gate 10 态状态机。"""

    def test_state_defs_complete(self):
        from scripts.ship_gate import STATE_DEFS, STATE_TRANSITIONS
        # 10 个状态
        self.assertEqual(len(STATE_DEFS), 10)
        # 每个状态都在转移表里
        for s in STATE_DEFS:
            self.assertIn(s, STATE_TRANSITIONS)

    def test_terminal_states_have_no_outgoing(self):
        from scripts.ship_gate import STATE_TRANSITIONS
        # ARCHIVE 和 REJECT 是终态
        self.assertEqual(STATE_TRANSITIONS["ARCHIVE"], set())
        self.assertEqual(STATE_TRANSITIONS["REJECT"], set())

    def test_ship_happy_path(self):
        """ship 走 BLIND_TEST → GATE → PREPARE。"""
        from scripts.ship_gate import StateMachine
        sm = StateMachine()
        result = sm.run({"findings": [], "target": "t", "files_scanned": 1})
        self.assertEqual(result["verdict"], "ship")
        self.assertEqual(result["score"], 100)
        self.assertIn("PREPARE", result["state_history"])

    def test_full_lifecycle_ship(self):
        """--full-lifecycle 走完整 10 态。"""
        from scripts.ship_gate import StateMachine
        sm = StateMachine()
        result = sm.run({"findings": [], "target": "t", "files_scanned": 1},
                        full_lifecycle=True)
        self.assertEqual(result["final_state"], "ARCHIVE")
        for expected in ["BLIND_TEST", "GATE", "PREPARE", "RELEASE",
                         "OBSERVE", "ARCHIVE"]:
            self.assertIn(expected, result["state_history"])
        self.assertEqual(result["observation_window_days"], 30)

    def test_hold_with_fail_on_warn_rejects(self):
        """hold + --fail-on-warn 应转 REJECT。"""
        from scripts.ship_gate import StateMachine
        sm = StateMachine(fail_on_warn=True)
        # 1 个 high → score 85, 有 high → verdict=hold
        result = sm.run({"findings": [{"severity": "high"}],
                         "target": "t", "files_scanned": 1})
        self.assertEqual(result["verdict"], "break")  # REJECT 强制 break
        self.assertEqual(result["final_state"], "REJECT")

    def test_hold_without_fail_on_warn_archives(self):
        """hold 不 fail 时归档。"""
        from scripts.ship_gate import StateMachine
        sm = StateMachine(fail_on_warn=False)
        result = sm.run({"findings": [{"severity": "high"}],
                         "target": "t", "files_scanned": 1})
        self.assertEqual(result["final_state"], "ARCHIVE")
        self.assertEqual(result["verdict"], "hold")

    def test_break_goes_to_rollback_then_archive(self):
        """有 critical → break → ROLLBACK → ARCHIVE。"""
        from scripts.ship_gate import StateMachine
        sm = StateMachine()
        result = sm.run({"findings": [{"severity": "critical"}],
                         "target": "t", "files_scanned": 1})
        self.assertEqual(result["verdict"], "break")
        self.assertIn("ROLLBACK", result["state_history"])
        self.assertEqual(result["final_state"], "ARCHIVE")

    def test_no_auto_accept_rejects_hold(self):
        """争议不自动接受时应 reject（但只针对低分/high 无 critical 场景）。"""
        from scripts.ship_gate import StateMachine
        sm = StateMachine(auto_accept_challenge=False, fail_on_warn=False)
        # 1 high → 触发 CHALLENGE，无 auto_accept → REJECT
        result = sm.run({"findings": [{"severity": "high"}],
                         "target": "t", "files_scanned": 1})
        self.assertEqual(result["final_state"], "REJECT")

    def test_illegal_transition_raises(self):
        """非法状态转移应报错。"""
        from scripts.ship_gate import StateMachine
        sm = StateMachine()
        with self.assertRaises(ValueError):
            sm._enter("ARCHIVE", reason="skipping")  # ANALYZE 不能直接到 ARCHIVE

    def test_transition_records_history(self):
        from scripts.ship_gate import StateMachine
        sm = StateMachine()
        sm.run({"findings": [], "target": "t", "files_scanned": 1})
        self.assertGreater(len(sm.transitions), 0)
        for t in sm.transitions:
            self.assertIn("from", t)
            self.assertIn("to", t)
            self.assertIn("ts", t)


class TestShipGateEvidenceBundleIntegration(unittest.TestCase):
    """ship_gate 与 evidence_bundle 集成。"""

    def test_make_evidence_bundle(self):
        from scripts.ship_gate import StateMachine, _make_evidence_bundle
        sm = StateMachine(hmac_secret="k")
        sm_result = sm.run({"findings": [], "target": "t", "files_scanned": 1})
        bundle = _make_evidence_bundle(
            {"target": "t", "findings": []}, sm_result, hmac_secret="k")
        self.assertIsNotNone(bundle)
        self.assertTrue(bundle["verification"]["valid"])
        self.assertTrue(bundle["hmac"])
        # 至少 1 条事件（final verdict）+ 状态转移事件
        self.assertGreaterEqual(len(bundle["events"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
