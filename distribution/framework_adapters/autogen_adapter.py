"""
AutoGen 适配器 — 在 AssistantAgent 注入 functions 前做安全门禁。

用法：
    from distribution.framework_adapters.autogen_adapter import gate_before_inject

    cfg = open("autogen-mcp.json").read()
    gate_before_inject(cfg, fail_on="high")

AutoGen 的 `AssistantAgent` 通过 `functions` / `tools` 注入可调用能力。这里对
「函数来源配置」做静态门禁，阻断危险启动命令、非注册表来源代码加载等风险。
"""

from . import gate_mcp_config, GateResult


def gate_before_inject(
    config_text: str,
    config_name: str = "autogen-mcp.json",
    fail_on: str = "high",
    min_score: int = 0,
    raise_on_block: bool = True,
) -> GateResult:
    """在把 functions 注入 AutoGen Agent 前调用。默认门禁失败即抛错。"""
    result = gate_mcp_config(config_text, config_name, fail_on=fail_on, min_score=min_score)
    if not result.ok and raise_on_block:
        detail = "; ".join(result.errors) or f"{result.findings_total} 条风险"
        raise RuntimeError(f"[AIShield] AutoGen 函数未通过安全门禁: {detail}")
    return result
