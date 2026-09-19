"""
LangChain 适配器 — 在 bind_tools / 注册自定义 Tool 前做安全门禁。

用法：
    from distribution.framework_adapters.langchain_adapter import gate_before_bind

    # 假设你的 MCP 配置以文本形式提供给客户端
    cfg = open("claude_desktop_config.json").read()
    gate_before_bind(cfg, fail_on="high")   # 不通过会抛 RuntimeError

设计：LangChain 的 Tool / MCP 绑定本身不暴露「配置源码」，因此这里对
*生成这些工具所用的 MCP 配置文本* 做门禁，确保上线的工具来自安全配置。
框架 import 延迟进行，未安装 LangChain 不影响 `gate_mcp_config` 本体。
"""

from . import gate_mcp_config, GateResult


def gate_before_bind(
    config_text: str,
    config_name: str = "langchain-mcp.json",
    fail_on: str = "high",
    min_score: int = 0,
    raise_on_block: bool = True,
) -> GateResult:
    """在把工具绑定到 LangChain Agent 前调用。默认门禁失败即抛错。"""
    result = gate_mcp_config(config_text, config_name, fail_on=fail_on, min_score=min_score)
    if not result.ok and raise_on_block:
        detail = "; ".join(result.errors) or f"{result.findings_total} 条风险"
        raise RuntimeError(f"[AIShield] LangChain 工具未通过安全门禁: {detail}")
    return result


def make_safe_tool(tool_factory, config_text: str, **gate_kwargs):
    """
    装饰器式封装：先门禁配置，通过再调用 tool_factory 产出 LangChain Tool。
    tool_factory 签名: () -> LangChain Tool
    """
    result = gate_before_bind(config_text, raise_on_block=True, **gate_kwargs)
    return tool_factory()
