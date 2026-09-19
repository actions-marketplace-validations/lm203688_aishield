# Framework Adapters — 把 AIShield 接入你的 Agent 框架

> 借鉴 [agent-audit](https://github.com/adapter/agent-audit) 的思路：安全扫描不该是
> 上线前的「一次性体检」，而应成为 Agent 装配管线里的**常驻闸口**。下面三个适配器演示
> 如何把 AIShield 的零依赖扫描引擎嵌入 LangChain / CrewAI / AutoGen 的工具装配环节。

## 设计原则

- **零新增依赖**：`scanner` 只依赖 Python 标准库。每个适配器在调用框架时再做 `import`，
  框架未安装时跳过，不影响 AIShield 本体。
- **装配即扫描**：在 agent 注册工具 / MCP server 之前先跑一遍 `scan_client_configs`
  或 `engine.scan`，不达标就不让工具上线。
- **fail-closed**：`gate()` 默认「有问题即拦截」，与 CI 门禁语义一致。
- **绝不 spawn 被扫配置的命令**：所有扫描均为静态分析（见 `scanner/client_discovery.py`）。

## 快速开始

```python
from distribution.framework_adapters import gate_mcp_config, GateResult

report = gate_mcp_config("""
{
  "mcpServers": {
    "weather": {"command": "npx", "args": ["-y", "@weather/mcp@latest"]}
  }
}
""")
if not report.ok:
    raise RuntimeError(f"工具未通过安全门禁: {report.findings_total} 条风险")
```

## 适配器一览

| 文件 | 框架 | 触发点 |
|------|------|--------|
| `langchain_adapter.py` | LangChain | `bind_tools` / 自定义 Tool 注册前 |
| `crewai_adapter.py` | CrewAI | `Crew` 装配 `Tool` 前 |
| `autogen_adapter.py` | AutoGen | `AssistantAgent` 注入 `functions` 前 |

## 与 MCP Server / CLI 的关系

- 适配器 = **代码内嵌**扫描（适合 Python Agent 项目）。
- `npx -y aishield-mcp-server` = 把 AIShield 本身作为 MCP 工具暴露给任意客户端。
- `python -m scanner.cli --target <repo>` = 一次性 CLI 扫描。
- 三者共用同一套 238 条规则引擎，结果一致。

> 注意：这些适配器是**集成样例**，用于演示接入模式。生产环境请配合
> `AISHIELD_FAIL_ON=high` 类环境变量做门禁，并把 SARIF 产物上传到你的 SIEM。
