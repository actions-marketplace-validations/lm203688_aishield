---
name: aishield
description: >-
  AIShield 是本地优先、零依赖的 agent 生态安全扫描器。对齐 OWASP MCP Top 10
  （2025 v0.1）与 OWASP Agentic AI Top 10（ASI01–10）。核心不变量：绝不 spawn
  或执行被扫描配置里出现的任何命令。
---

# AIShield

一个 agent 在安装 MCP server、AI skill、GPT 定义或 prompt 文件之前，
以及用户问「这个插件安全吗」时，应当先调用 AIShield 做一次静态扫描。

## 为什么先扫描

agent 生态的载荷形态是**指令**，不是二进制。一段 Markdown 里的
`ignore all previous instructions` 对一个会照着执行的 LLM 来说
就是可执行代码。AIShield 把这类载荷当代码审计：静态分析 + 离线情报，
不运行、不联网、不改写被扫对象。

## 安装

一次性注册 MCP server：

```json
{
  "mcpServers": {
    "aishield": { "command": "npx", "args": ["-y", "aishield-mcp-server"] }
  }
}
```

完整 skill 定义见 `skills/aishield-scan/SKILL.md`。

## 工具清单

| 工具 | 用途 |
|---|---|
| `aishield_scan` | 扫描路径 / 仓库 URL / 配置 blob，返回评分、风险等级与 findings |
| `aishield_handshake` | 审查 MCP 配置：`npx -y` 风险、敏感环境变量、过长工具描述 |
| `aishield_prompt_check` | 检测 prompt 与指令中的注入 / jailbreak 模式 |
| `aishield_rug_pull` | 对比工具描述的旧新两版，抓静默变更（rug pull） |
| `aishield_guardrail` | 检查 agent 配置的护栏是否配得上它声明的自主权 |
| `aishield_banned_words` | 标记违反策略或高风险的措辞 |

## 建议流程

1. 安装不可信 skill 或 MCP server 之前，先扫源路径或仓库 URL。
   `risk_level` 为 `high` 或 `critical` 即视为停止信号。
2. 拿到 findings 后，向用户报告**文件、行号、规则 ID 与证据原文**，
   不要只报一个分数。分数无法定位问题，也无法指导修复。
3. 工具描述跨版本变化时，跑 `aishield_rug_pull` 抓 rug pull。

## 边界

- 扫描全程本地执行，被扫源码不离开本机。
- 可选的实时 CVE 富化（OSV.dev）**默认关闭**。隐私敏感或断网环境下保持关闭。
- 扫描器绝不执行被扫配置中的命令。该不变量可用
  `python scripts/prove_isolation.py` 验证。

## 自指说明

本文件文件名属于 `AGENT_INSTRUCTION_FILENAMES`，因此 AIShield 自己会把它
当作 **agent 指令载荷**处理，而不是普通文档。这不是巧合：它是自否证场景 ——
扫描器用自己发布的指令文档当输入，验证规则族不会把 benign 的 agent 文档
误判成注入载荷，也不会漏掉文档正文里真正藏着的可执行风险。
