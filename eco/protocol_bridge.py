"""
eco/protocol_bridge.py — 统一协议翻译网关（硬骨头 #5：协议碎片化）

百花齐放时代，agent 用不同协议描述自己：MCP（工具/资源）、A2A（AgentCard）、
ACP（AGNTCY 的 agent 描述）、AP2（Google agent payment）。消费方（编排器 / registry /
LLM 路由）不想为每个协议写一套适配。

本模块提供「统一内部表示 UniversalAgent」+ 双向翻译：
    MCP  ⇄  A2A  ⇄  ACP  ⇄  AP2
任何协议进入即被规范化为 UniversalAgent，再按需翻译成目标协议。

零依赖；纯结构映射，不涉及网络。翻译失败（字段缺失）返回尽量完整的降级结果而非抛错。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UniversalAgent:
    """协议无关的 agent 统一表示。"""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    url: str = ""
    provider: dict = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    skills: list[dict] = field(default_factory=list)
    protocols: list[str] = field(default_factory=list)
    trust: dict = field(default_factory=dict)      # 可选信任元数据
    payment: dict = field(default_factory=dict)    # 可选 AP2 支付元数据
    raw: dict = field(default_factory=dict)        # 原始输入（保留以便回译）

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "url": self.url,
            "provider": self.provider,
            "capabilities": self.capabilities,
            "skills": self.skills,
            "protocols": self.protocols,
            "trust": self.trust,
            "payment": self.payment,
        }


# ── 入口：各协议 → UniversalAgent ──
def from_mcp(mcp: dict) -> UniversalAgent:
    """MCP Server Card（.well-known/mcp.json / MCP manifest）。"""
    tools = mcp.get("tools", []) or []
    skills = []
    caps = []
    for i, t in enumerate(tools):
        skills.append({
            "id": t.get("name", f"tool-{i}"),
            "name": t.get("name", f"tool-{i}"),
            "description": t.get("description", ""),
            "tags": t.get("tags", []) or _schema_tags(t.get("inputSchema")),
            "examples": t.get("examples", []) or [],
        })
        caps.append(t.get("name", f"tool-{i}"))
    return UniversalAgent(
        name=mcp.get("name", mcp.get("serverName", "")),
        description=mcp.get("description", ""),
        version=str(mcp.get("version", mcp.get("schemaVersion", "1.0.0"))),
        url=mcp.get("url", ""),
        provider=mcp.get("provider", {}),
        capabilities=caps,
        skills=skills,
        protocols=["mcp"],
        raw=mcp,
    )


def from_a2a(a2a: dict) -> UniversalAgent:
    """A2A v1.0 AgentCard。"""
    skills = []
    for s in a2a.get("skills", []) or []:
        skills.append({
            "id": s.get("id", ""),
            "name": s.get("name", ""),
            "description": s.get("description", ""),
            "tags": s.get("tags", []) or [],
            "examples": s.get("examples", []) or [],
        })
    caps = []
    c = a2a.get("capabilities")
    if isinstance(c, dict):
        caps = list(c.get("supported", []) or [])
    elif isinstance(c, (list, tuple)):
        caps = list(c)
    return UniversalAgent(
        name=a2a.get("name", ""),
        description=a2a.get("description", ""),
        version=str(a2a.get("version", "1.0.0")),
        url=a2a.get("url", ""),
        provider=a2a.get("provider", {}),
        capabilities=caps,
        skills=skills,
        protocols=["a2a"],
        trust=a2a.get("aishield", {}),
        raw=a2a,
    )


def from_acp(acp: dict) -> UniversalAgent:
    """ACP（AGNTCY Agent Client Protocol）agent 描述。
    与 A2A 高度相似，但用 `agent` 包裹 + `capabilities` 为列表。
    """
    inner = acp.get("agent", acp)
    skills = []
    for i, s in enumerate(inner.get("skills", []) or []):
        if isinstance(s, str):
            skills.append({"id": f"s{i}", "name": s, "description": "", "tags": [], "examples": []})
        else:
            skills.append({
                "id": s.get("id", f"s{i}"),
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "tags": s.get("tags", []) or [],
                "examples": s.get("examples", []) or [],
            })
    return UniversalAgent(
        name=inner.get("name", ""),
        description=inner.get("description", ""),
        version=str(inner.get("version", "1.0.0")),
        url=inner.get("endpoint", inner.get("url", "")),
        provider=inner.get("provider", {}),
        capabilities=list(inner.get("capabilities", []) or []),
        skills=skills,
        protocols=["acp"],
        raw=acp,
    )


def from_ap2(ap2: dict) -> UniversalAgent:
    """AP2（Google Agent Payments Protocol）agent + payment intent。"""
    agent = ap2.get("agent", ap2)
    caps = list(agent.get("capabilities", []) or [])
    if ap2.get("paymentMethods") or ap2.get("supportedNetworks"):
        caps.append("payment")
    skills = []
    for i, s in enumerate(agent.get("skills", []) or []):
        skills.append({
            "id": s.get("id", f"s{i}") if isinstance(s, dict) else f"s{i}",
            "name": s.get("name", "") if isinstance(s, dict) else str(s),
            "description": (s.get("description", "") if isinstance(s, dict) else ""),
            "tags": (s.get("tags", []) or []) if isinstance(s, dict) else [],
            "examples": (s.get("examples", []) or []) if isinstance(s, dict) else [],
        })
    return UniversalAgent(
        name=agent.get("name", ""),
        description=agent.get("description", ""),
        version=str(agent.get("version", "1.0.0")),
        url=agent.get("url", ""),
        provider=agent.get("provider", {}),
        capabilities=caps,
        skills=skills,
        protocols=["ap2"],
        payment={
            "paymentMethods": ap2.get("paymentMethods", []),
            "supportedNetworks": ap2.get("supportedNetworks", []),
            "currency": ap2.get("currency", "USDC"),
        },
        raw=ap2,
    )


# ── 出口：UniversalAgent → 各协议 ──
def to_a2a(ua: UniversalAgent) -> dict:
    return {
        "name": ua.name,
        "description": ua.description,
        "version": ua.version,
        "url": ua.url,
        "provider": ua.provider,
        "capabilities": {"supported": ua.capabilities},
        "skills": ua.skills,
        "aishield": ua.trust or {},
    }


def to_mcp(ua: UniversalAgent) -> dict:
    tools = []
    for s in ua.skills:
        tools.append({
            "name": s.get("name", s.get("id", "")),
            "description": s.get("description", ""),
            "tags": s.get("tags", []),
            "examples": s.get("examples", []),
        })
    return {
        "name": ua.name,
        "description": ua.description,
        "version": ua.version,
        "url": ua.url,
        "provider": ua.provider,
        "tools": tools,
        "capabilities": ua.capabilities,
    }


def to_acp(ua: UniversalAgent) -> dict:
    return {
        "agent": {
            "name": ua.name,
            "description": ua.description,
            "version": ua.version,
            "endpoint": ua.url,
            "provider": ua.provider,
            "capabilities": ua.capabilities,
            "skills": ua.skills,
        }
    }


def to_ap2(ua: UniversalAgent) -> dict:
    out = {
        "agent": {
            "name": ua.name,
            "description": ua.description,
            "version": ua.version,
            "url": ua.url,
            "provider": ua.provider,
            "capabilities": ua.capabilities,
            "skills": ua.skills,
        },
        "paymentMethods": ua.payment.get("paymentMethods", []),
        "supportedNetworks": ua.payment.get("supportedNetworks", []),
        "currency": ua.payment.get("currency", "USDC"),
    }
    return out


_LOADERS = {"mcp": from_mcp, "a2a": from_a2a, "acp": from_acp, "ap2": from_ap2}
_EXPORTERS = {"mcp": to_mcp, "a2a": to_a2a, "acp": to_acp, "ap2": to_ap2}
PROTOCOLS = list(_LOADERS.keys())


def _schema_tags(schema: dict | None) -> list:
    """从 JSON Schema 提取字段名作为粗粒度标签。"""
    if not isinstance(schema, dict):
        return []
    props = schema.get("properties", {})
    return list(props.keys())[:6]


def translate(obj: dict, source: str, target: str) -> dict:
    """协议互译：source → UniversalAgent → target。"""
    source = source.lower()
    target = target.lower()
    if source not in _LOADERS:
        raise ValueError(f"未知源协议: {source}，支持 {PROTOCOLS}")
    if target not in _EXPORTERS:
        raise ValueError(f"未知目标协议: {target}，支持 {PROTOCOLS}")
    ua = _LOADERS[source](obj)
    if source != target:
        ua.protocols = sorted(set(ua.protocols + [source, target]))
    ua.trust = obj.get("aishield", ua.trust)
    return _EXPORTERS[target](ua)


if __name__ == "__main__":
    # MCP → A2A 往返
    mcp_card = {
        "name": "WeatherTool", "description": "天气查询 MCP",
        "version": "1.2.0", "url": "https://mcp.example/weather",
        "tools": [{"name": "get_weather", "description": "查天气",
                   "inputSchema": {"properties": {"city": {"type": "string"}}}}],
    }
    ua = from_mcp(mcp_card)
    print("MCP→UA skills:", [s["name"] for s in ua.skills])
    a2a = to_a2a(ua)
    print("UA→A2A name:", a2a["name"], "| caps:", a2a["capabilities"])

    # A2A → MCP
    a2a_card = {
        "name": "Scanner", "description": "扫描器", "version": "1.0.0",
        "url": "https://a.example/s", "provider": {"name": "X"},
        "capabilities": {"supported": ["scan"]},
        "skills": [{"id": "s1", "name": "security_scan", "tags": ["sec"], "examples": ["scan x"]}],
    }
    back = translate(a2a_card, "a2a", "mcp")
    print("A2A→MCP tools:", [t["name"] for t in back["tools"]])

    # AP2 → A2A（带支付元数据）
    ap2_card = {"agent": {"name": "PayAgent", "description": "可付费 agent",
                          "capabilities": ["translate"]},
                "paymentMethods": ["x402"], "supportedNetworks": ["base"], "currency": "USDC"}
    ap2a = translate(ap2_card, "ap2", "a2a")
    print("AP2→A2A name:", ap2a["name"], "| trust:", ap2a["aishield"])
