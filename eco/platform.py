"""
eco/platform.py — 五大支柱编排平台（AIShield 生态统一底座）

把分散的能力串成一条 agent 生命周期主线，给「百花齐放的小 agent 创新者」一个统一入口：

    创新者 ──①发现──▶ ②认证 ──▶ ③组合 ──▶ ④执行 ──▶ ⑤鉴证 ──▶ 上线
                 ▲──────────── 持续复扫 / 责任链回写 ────────┘

  ① 发现 (Discovery)   : 跨协议发现 agent（复用 eco.a2a_gateway.AgentDiscovery + protocol_bridge）
  ② 认证 (Attest)      : 计算信任分 + 签发签名 Agent Card（eco.trust_score + eco.agent_card）
  ③ 组合 (Compose)     : 把多个 agent 编排成任务计划，建立责任链骨架（eco.responsibility_chain）
  ④ 执行 (Execute)     : 在沙箱中执行（scanner.sandbox），每步回写责任链
  ⑤ 鉴证 (Witness)     : 校验责任链完整性，产出可审计的鉴证结论

这是 R1–R4 的「胶水层」，证明各硬骨头能组合成一个可用的开放平台。
零依赖（除可选 cryptography）。各支柱内部失败互不拖垮整体（fail-soft）。
"""
from __future__ import annotations

import threading
import uuid

try:
    from eco import trust_score as ts
    from eco import agent_card as ac
    from eco import responsibility_chain as rc
    from eco import protocol_bridge as pb
except ImportError:  # 允许以脚本方式直接运行自测
    import trust_score as ts
    import agent_card as ac
    import responsibility_chain as rc
    import protocol_bridge as pb


class AIShieldPlatform:
    def __init__(self):
        self.signer = ac.AgentCardSigner()
        self.chains = {}
        self._lock = threading.Lock()

    # ── ① 发现 ──
    def discover(self, query=None, skill=None, capability=None, min_reputation=0,
                 protocol=None) -> list:
        """跨协议发现 agent。

        若 protocol 指定（mcp/a2a/acp/ap2），会先经由 protocol_bridge 规范化为统一表示。
        """
        try:
            from eco.a2a_gateway import AgentDiscovery
            disc = AgentDiscovery()
            agents = disc.discover(skill=skill, capability=capability,
                                   min_reputation=min_reputation, name=query)
        except Exception:
            agents = []
        # 若要求某一协议形态，转译后返回（不破坏原 A2A 结构）
        if protocol and protocol.lower() in pb.PROTOCOLS:
            return [pb.translate(a, "a2a", protocol) for a in agents]
        return agents

    # ── ② 认证 ──
    def attest(self, agent_card: dict, scan: dict | None = None,
               attestation: dict | None = None, reputation: int | None = None,
               publish: bool = False) -> dict:
        """计算信任分并签发签名 Agent Card。"""
        score = ts.compute_trust_score(scan=scan, attestation=attestation, reputation=reputation)
        signed = self.signer.sign(agent_card, trust_score=int(score["score"]))
        if publish:
            try:
                self.signer.publish_pubkey()
            except Exception:
                pass
        # 自校验：签完立即验，确保签发链路可信
        verify = self.signer.verify(signed, self.signer.public_key()[1])
        return {
            "trust_score": score,
            "signed_card": signed,
            "self_verified": verify.get("valid", False),
            "signer_did": self.signer.signer_did,
        }

    # ── ③ 组合 ──
    def compose(self, task_description: str, agents: list, chain_id: str | None = None) -> dict:
        """把候选 agent 编排成执行计划，建立责任链骨架。"""
        chain_id = chain_id or f"chain-{uuid.uuid4().hex[:12]}"
        chain = rc.ResponsibilityChain(chain_id)
        with self._lock:
            self.chains[chain_id] = chain
        # 计划：按 agent 顺序级联；第一步为根（parent=None），其余挂前一步
        steps = []
        prev_seq = None
        for i, ag in enumerate(agents):
            ag_id = ag.get("agent_id") or ag.get("name") or f"agent-{i}"
            role = ag.get("role") or (task_description if i == 0 else f"step-{i}")
            seq = chain.record(agent_id=ag_id, action=role, parent_seq=prev_seq,
                               input_ref=task_description if i == 0 else f"step-{i-1}-output")
            steps.append({"seq": seq["seq"], "agent_id": ag_id, "role": role})
            prev_seq = seq["seq"]
        return {
            "chain_id": chain_id,
            "task_description": task_description,
            "plan": steps,
            "depth": chain.depth(),
        }

    # ── ④ 执行 ──
    def execute(self, chain_id: str, results: list | None = None,
                sandbox_profile: str = "balanced") -> dict:
        """执行计划并回写责任链。

        results: 每步的执行结果（任意可哈希内容），按顺序与 plan 对齐；
                 含 `command` 字段的步骤会真的在沙箱中执行。
        无 results 时仅做链路完整性演示（记录占位 output_ref）。
        """
        with self._lock:
            chain = self.chains.get(chain_id)
        if chain is None:
            return {"success": False, "error": "chain not found", "chain_id": chain_id}
        results = results or []
        import os as _os
        import sys as _sys
        _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from scanner import sandbox as sb
        for i, entry in enumerate(chain.entries):
            out = results[i] if i < len(results) else f"step-{i}-output"
            cmd = None
            if isinstance(out, dict):
                cmd = out.get("command")
                out_ref = out.get("output", out)
            else:
                out_ref = out
            if cmd:  # 真在沙箱里跑
                run = sb.run_isolated(cmd[0], cmd[1:] if len(cmd) > 1 else [],
                                      profile=sandbox_profile)
                out_ref = run.get("stdout", "")[:200]
            chain.record(agent_id=entry["agent_id"], action=f"execute:{entry['action']}",
                         parent_seq=entry["seq"], input_ref=entry["output_ref"] or entry["input_ref"],
                         output_ref=out_ref)
        return {
            "success": True,
            "chain_id": chain_id,
            "verified": chain.verify()["valid"],
            "depth": chain.depth(),
            "export": chain.export(),
        }

    # ── ⑤ 鉴证 ──
    def witness(self, chain_id: str) -> dict:
        """校验责任链完整性，产出可审计鉴证结论。"""
        with self._lock:
            chain = self.chains.get(chain_id)
        if chain is None:
            return {"success": False, "error": "chain not found", "chain_id": chain_id}
        v = chain.verify()
        return {
            "success": True,
            "chain_id": chain_id,
            "integrity": v["valid"],
            "entries": v.get("entries"),
            "broken_at": v.get("broken_at"),
            "head_hash": chain.export()["head_hash"],
            "auditable": True,
        }

    def trace_incident(self, chain_id: str, output_ref) -> list:
        with self._lock:
            chain = self.chains.get(chain_id)
        if chain is None:
            return []
        return chain.trace(output_ref)


if __name__ == "__main__":
    p = AIShieldPlatform()
    # ① 发现（无数据时为 []，演示组合直接用给定 agent）
    card = {"name": "Scanner", "url": "https://x/s", "description": "扫描",
            "skills": [{"id": "s", "name": "security_scan", "tags": ["sec"]}],
            "capabilities": ["scan"], "reputation_score": 88}
    # ② 认证
    att = p.attest(card, scan={"overall_score": 92, "risk_level": "low"},
                   attestation={"subscribed": True, "continuously_verified": True, "evidence_entries": 5},
                   reputation=88, publish=True)
    print("信任分:", att["trust_score"]["score"], att["trust_score"]["level"],
          "| 自验:", att["self_verified"])
    # ③ 组合
    plan = p.compose("扫描并生成报告", [
        {"agent_id": "planner", "role": "plan"},
        {"agent_id": "scanner", "role": "scan"},
        {"agent_id": "reporter", "role": "report"},
    ])
    print("组合链:", plan["chain_id"], "深度", plan["depth"])
    # ④ 执行
    ex = p.execute(plan["chain_id"], results=[
        {"output": "tasks:scan,report"},
        {"output": {"score": 90}},
        {"output": "report.md"},
    ])
    print("执行 verified:", ex["verified"])
    # ⑤ 鉴证
    w = p.witness(plan["chain_id"])
    print("鉴证 integrity:", w["integrity"], "| 可审计:", w["auditable"])
