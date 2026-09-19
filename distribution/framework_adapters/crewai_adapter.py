"""
CrewAI 适配器 — 在 Crew 装配 Tool 前做安全门禁。

用法：
    from distribution.framework_adapters.crewai_adapter import gate_before_crew

    cfg = open(".mcp.json").read()
    gate_before_crew(cfg, fail_on="high")

CrewAI 通过 `crewai_tools` 包装 MCP / 自定义工具。这里同样对「工具来源配置」
做静态门禁，确保进入团队的 Tool 不携带提权启动、明文凭证、rug-pull 拉包等风险。
"""

from . import gate_mcp_config, GateResult


def gate_before_crew(
    config_text: str,
    config_name: str = "crewai-mcp.json",
    fail_on: str = "high",
    min_score: int = 0,
    raise_on_block: bool = True,
) -> GateResult:
    """在 Crew 装配 Tool 前调用。默认门禁失败即抛错。"""
    result = gate_mcp_config(config_text, config_name, fail_on=fail_on, min_score=min_score)
    if not result.ok and raise_on_block:
        detail = "; ".join(result.errors) or f"{result.findings_total} 条风险"
        raise RuntimeError(f"[AIShield] CrewAI 工具未通过安全门禁: {detail}")
    return result
