# AIShield 个人 Agent 平台接入层（v4.8.1）

**核心结论**：任何个人 Agent 平台的用户，都可以通过 AIShield 加装独立的
个人身份（PAI DID）、预算守护、行动溯源、Connector 独立审核层。
平台不需要官方上架，MCP / OpenAI 兼容 API 即可零迁移接入。

## 大陆访问状态（2026-09-24 一手核实）

| 状态 | 数量 | 平台 |
|---|---|---|
| **verified_blocked** | 7 | Meta Muse、Grok Bot、Grok API、ChatGPT Agent、OpenAI Operator、Claude、Gemini |
| **reachable** | 20 | Coze、豆包、元宝、文心、通义、Kimi、DeepSeek、GLM、Yi、Minimax 等 |
| **regional_only** | 5 | Vertex / Groq / Cerebras / Fireworks / Together（海外云） |

**关键洞察**：海外头部消费级 agent（Muse / Grok Bot / ChatGPT Agent /
OpenAI Operator）大陆全部不通。AIShield 的定位不是"上架某平台"，而是
**"跨平台中立治理层"** —— 平台只是接入方之一。

## 接入路径分层（5 类）

| 路径 | 隔离度 | 平台需要改动 | AIShield 状态 | 典型场景 |
|---|---|---|---|---|
| **mcp** | 高 | 否 | ready | 平台支持 MCP 即可（Coze / Dify / n8n / ChatGPT MCP） |
| **openai_compat** | 中 | 是 | ready | 平台提供 OpenAI 兼容 API，AIShield 作为上游 guardrail 或工具路由 |
| **browser_agent** | 高 | 否 | ready | Grok Bot / OpenAI Operator 通过浏览器层调用 AIShield 工具 |
| **connector_official** | 低 | 是 | requires_submission | 平台官方 connector 平台（Muse / ChatGPT / Coze / 元宝） |
| **native_sdk** | 低 | 是 | requires_adaptor | 平台私有 SDK（豆包 / 元宝 / 可灵） |

**优先级建议**：MCP > browser_agent > openai_compat > connector_official > native_sdk

理由：MCP 与浏览器代操不需要平台配合，AIShield 侧就能开工；
connector 官方通道依赖平台审核节奏，是**兜底方案**不是主路径。

## 各平台接入包

| 平台 | 接入包 | 大陆可达 | 主接入路径 |
|---|---|---|---|
| **Meta Muse** | [`connectors/muse/`](./muse/) | ❌ | connector_official / MCP |
| **Grok Bot (xAI)** | [`connectors/grok-bot/`](./grok-bot/) | ❌ | openai_compat / browser_agent |
| **字节 Coze** | [`connectors/coze/`](./coze/) | ✅ | **MCP**（大陆优先） |

其他 30+ 平台见 [`eco/platform_registry.py`](../eco/platform_registry.py)，
`docs/personal-agent-platform-matrix.md` 有完整矩阵。

## 定位

与 **CyberGuard**（GOAI 2026 Agent Infra 季军）正交互补：
- CyberGuard：SOC 应用层，管企业 SOC 事件
- AIShield 个人治理层：管**个人 Agent 用户**的身份、预算、行动
- 二者可在同一平台（如 Muse）形成"上层应用 + 底层身份"栈

## 治理缺口覆盖

| 平台治理缺口 | AIShield 补齐 |
|---|---|
| `portable_personal_identity` | PAI DID (`did:aishield:pa:*`)，跨平台可验证 |
| `cumulative_budget_governance` | 4 粒度预算守护（per_tx / daily / weekly / monthly） |
| `target_site_risk_scoring` | 8 因素风险评分 |
| `connector_independent_review` | 8 规则独立审核 |
| `user_level_dispute_receipt` | HMAC-SHA256 行动链 + 用户 dispute 回执 |
| `cross_platform_budget` | 单点治理，任意平台实例都记账 |
| `agent_level_governance` | Capability Ticket（用户对实例的白名单 + TTL） |
| `off_platform_audit_trail` | HMAC 链跨平台可验证，不依赖平台内部日志 |

## 快速验证

```bash
# 平台注册表统计
python eco/platform_registry.py

# 获取大陆用户推荐接入平台
curl -X POST https://api.aishield.tools/api/v1/platforms/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_country": "CN", "capabilities_needed": ["portable_personal_identity"]}'

# 反查某实例的平台治理缺口
curl https://api.aishield.tools/api/v1/personal-agents/users/alice@example.com/agent-instances/inst_xxx
```
