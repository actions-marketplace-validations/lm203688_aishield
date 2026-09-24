# AIShield for Coze (字节扣子) 接入包（v4.8.1）

**平台**：Coze（字节扣子，coze.cn）
**产品形态**：开发者建 agent → 上架给 C 端
**MCP 支持**：✅ 大陆唯一有官方 MCP 支持的 agent 平台

## 大陆访问状态

- `coze.cn` — ✅ 可达
- `coze.cn/mcp` — ✅ 官方 MCP 市场
- 开发者文档 — ✅

**结论**：Coze 是 AIShield 在大陆**最高优先级**的接入平台。

## 为什么 Coze 需要 AIShield

Coze 已经内置：
- Workspace 隔离
- Bot 发布者审核
- 知识库
- Workflow 构建器

**但缺失**：
| Gap | Coze 覆盖？ | AIShield 补齐 |
|---|---|---|
| 用户级可携带个人身份 | ❌（Coze 内部用户体系） | ✅ PAI DID |
| 用户级 dispute 回执 | ❌（Coze 内部日志） | ✅ HMAC 链 + 用户 dispute |
| Connector 独立第二意见 | ❌（Coze 自审） | ✅ 8 规则独立审核 |

## 接入路径（3 条，按优先级）

### 路径 A：MCP（大陆首选，零改动）

Coze 官方支持 MCP，AIShield 已上架为 MCP server。用户或开发者在
Coze Bot 里加一个 MCP 工具连接即可：

```json
// Coze Bot 里加 MCP 工具
{
  "mcpServers": {
    "aishield": {
      "command": "npx",
      "args": ["-y", "aishield-mcp-server"]
    }
  }
}
```

**能力**：Coze Bot 在处理用户支付/邮件/授权请求前，调用
`aishield_personal_budget_check` / `aishield_personal_action_record`。

### 路径 B：Workflow 节点集成

Coze Workflow 可自定义节点，AIShield 提供 HTTP API，作为自定义节点
被调用：

```python
# Coze Workflow Python 节点
import requests

def check_budget(payload):
    r = requests.post(
        "https://api.aishield.tools/api/v1/personal-agents/budget/check",
        json={
            "user_id": payload["user_id"],
            "action": "purchase",
            "amount": payload["amount"],
            "currency": "CNY",
            "target_url": payload["target_url"],
        },
        timeout=5,
    )
    verdict = r.json().get("verdict")
    # 返回给 Workflow 下一步
    return {"verdict": verdict, "risk_score": r.json().get("risk_score")}
```

### 路径 C：Coze 官方插件（上架）

Coze 有第三方插件市场。AIShield 可提交为一个 Coze 插件：
- 插件类型：**HTTP API 插件**
- 提交入口：coze.cn/developer → 插件创建
- 需材料：产品描述、API 文档、合规声明、隐私政策

## AIShield 补齐的治理能力

### 1. 用户级可携带身份（PAI DID）
Coze Bot 用户 Alice 通过 `aishield_personal_did_create` 拿一个
`did:aishield:pa:*`。之后 Alice 在任何平台都能带这个身份，
不被 Coze 锁定。

### 2. 跨平台行动 dispute
Alice 的 Coze Bot 做了某操作，她可以通过
`aishield_personal_dispute_file` 发起 dispute，拿到 HMAC 回执，
不依赖 Coze 内部日志。

### 3. Bot 上架前独立审核
Alice 建了一个 Coze Bot，上架前通过
`aishield_personal_connector_vet` 做独立审核：
- 危险 scope（`payment.spend` / `wallet.read` / `desktop.screen`）
- 管道安装（`curl | sh`）
- 明文 token
- 签名 / 过期声明
- 权限-描述一致性

## 部署路径

| 用户类型 | 部署方式 | 治理层位置 |
|---|---|---|
| 大陆个人用户 | MCP 或 Workflow 节点 | AIShield SaaS（api.aishield.tools） |
| 大陆企业客户 | 私有化部署 | 客户自有云 |
| 海外 Coze（coze.com） | 同大陆 | AIShield SaaS |

## 快速验证

```bash
# 1. 建用户
curl -X POST https://api.aishield.tools/api/v1/personal-agents/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice@bytedance.com", "display_name": "Alice"}'

# 2. 注册 Coze Bot 实例
curl -X POST https://api.aishield.tools/api/v1/personal-agents/users/alice@bytedance.com/agent-instances \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "My-Shopping-Bot",
    "provider": "ByteDance",
    "platform": "bytedance-coze",
    "platform_tier": "free"
  }'

# 3. Bot 执行下单前，先做预算 + 风险检查
curl -X POST https://api.aishield.tools/api/v1/personal-agents/budget/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice@bytedance.com",
    "action": "purchase",
    "amount": 259,
    "currency": "CNY",
    "target_url": "https://shop.example.com"
  }'

# 4. 记录行动
curl -X POST https://api.aishield.tools/api/v1/personal-agents/users/alice@bytedance.com/actions \
  -H "Content-Type: application/json" \
  -d '{
    "action": "purchase",
    "payload": {"amount": 259, "currency": "CNY", "target_url": "https://shop.example.com"},
    "verdict": "allow"
  }'

# 5. Bot 上架前，独立审核
curl -X POST https://api.aishield.tools/api/v1/personal-agents/users/alice@bytedance.com/connectors/vet \
  -H "Content-Type: application/json" \
  -d '{
    "connector": {
      "name": "My Bot",
      "publisher": "alice@bytedance.com",
      "capabilities": ["checkout", "send_email"],
      "scopes": ["payment.spend", "mail.send"],
      "signature": "signed-hash"
    }
  }'
```

## Coze 平台特性对齐

- **虎皮椒支付**：Coze 支持第三方支付，AIShield 预算守护作为
  支付前置守卫（quote-first）
- **知识库**：AIShield 治理数据（PAI 身份、预算、行动链）可导入
  Coze 知识库供 Bot 查询
- **群聊 Bot**：一个 Alice 的 PAI DID 可关联多个 Coze 群 Bot 实例

## 定位

- **不替代** Coze 内部审核
- **补齐**：用户侧身份 + 预算 + 行动 dispute
- **对位**：Coze 做 Bot 上架 + C 端分发，AIShield 做**用户侧治理层**

## 版本

- AIShield v4.8.1+
- 与 `eco/personal_agent.py` + `eco/platform_registry.py` 完全对齐
