# AIShield Agent 生态 5 支柱落地 · 实施手册

> **日期**：2026-09-24
> **状态**：R1 首批落地 · 全部本地测试通过（1307 passed / 4 legacy fails）
> **对应方向**：`docs/aishield-direction-2026-09-research.md`（研发导向开源 agent 生态统一服务平台）

## 一、本轮交付总览

| 层 | 支柱 | 新增/修改文件 | 状态 |
|---|---|---|---|
| L1 信任认证 | 签名 Agent Card | `eco/agent_card.py`（既有）+ `api/ecosystem_api.py` + MCP 新工具 | ✅ |
| L2 专业注册 | Specialist Registry（8 域） | `eco/specialist_registry.py` + API + 种子数据 | ✅ |
| L3 中立身份 | KYA SD-JWT + Web Bot Auth + ERC-8004 | `eco/kyad_compat.py` + API | ✅ |
| L4 责任链 | Responsibility Chain | `eco/responsibility_chain.py`（既有）+ API 接入 | ✅ |
| L5 协议翻译 | MCP ⇄ A2A ⇄ ACP ⇄ AP2 | `eco/protocol_bridge.py`（既有）+ API 接入 | ✅ |
| 发布门禁 | `aishield ship` CLI | `scripts/ship_gate.py` | ✅ |
| 分发 | MCP 6 个新工具 | `mcp-server/mcp.json` → **v4.5.0** | ✅ |
| 测试 | 28 项新增自证 | `tests/test_ecosystem_activation.py` | ✅ 28/28 |

## 二、API 端点清单

所有端点走 `api/server.py` 路由分发到 `api/ecosystem_api.py`。

### 2.1 Agent Card 签名（L1）
```
GET  /api/v1/agent-card/pubkey             → 获取签发公钥
POST /api/v1/agent-card/sign               → 对 Agent Card 签名
POST /api/v1/agent-card/verify             → 验证签名（篡改即拒）
POST /api/v1/agent-card/identity           → 一站式导出 KYA + Web Bot Auth 身份
```

### 2.2 Specialist Registry（L2 · 8 专业域）
```
GET  /api/v1/specialist/domains            → 8 域目录 + 每域 agent 计数
GET  /api/v1/specialist/agents?domain=…    → 按域列出（含 lapsed）
GET  /api/v1/specialist/agents/{agent_id}  → 查询单个 agent
POST /api/v1/specialist/agents             → 注册 agent
POST /api/v1/specialist/agents/{id}/renew  → 续期 90 天
POST /api/v1/specialist/agents/{id}/revoke → 吊销
```

**8 专业域**（对齐 OWASP AIUC-1 场景 + 2026 生态主流赛道）：
| 域 | 典型能力标签 |
|---|---|
| legal       | contract / compliance / dispute / review |
| medical     | diagnosis / drug / imaging / genomics |
| finance     | risk / trading / audit / payment |
| education   | tutor / assessment / curriculum / mentor |
| engineering | coding / devops / debugging / architecture |
| design      | writing / art / video / branding |
| research    | analysis / literature / simulation / visualization |
| civic       | public-service / social-welfare / urban / tax |

### 2.3 中立身份（L3 · KYA / Web Bot Auth / ERC-8004）
```
POST /api/v1/identity/kyad/export         → Agent Card → KYA SD-JWT claims
POST /api/v1/identity/erc8004/wrap        → Wallet 地址 → DID:ERC-8004
GET  /api/v1/identity/wallets             → 文档指引
```

### 2.4 责任链（L4 · 硬骨头 #1）
```
POST /api/v1/chain                        → 创建链（或指定 chain_id）
POST /api/v1/chain/{id}/append            → 追加一条调用证据
GET  /api/v1/chain/{id}                   → 导出链
GET  /api/v1/chain/{id}/entries           → 同上（别名）
GET  /api/v1/chain/{id}/verify            → 校验完整性
GET  /api/v1/chain/{id}/trace?output_ref=…→ 溯源 + 定位首因
```

### 2.5 协议翻译（L5 · 硬骨头 #5）
```
POST /api/v1/protocol/normalize           → 任意协议 → UniversalAgent
POST /api/v1/protocol/translate           → from_protocol → target 协议
```

### 2.6 发布门禁 CLI（L1 · 差异化）
```bash
# 单文件扫描
python scripts/ship_gate.py --file ./mcp-server/mcp.json --json

# 目录扫描 + 生成 Trust Attestation
python scripts/ship_gate.py --path ./eco/my_skill/ \
  --json --fail-on-warn \
  --emit-attestation dist/attestation.json

# CI 集成（GitHub Action）
- run: python scripts/ship_gate.py --path . --json --fail-on-warn
```

**判定规则**：
| 条件 | verdict | 退出码 |
|---|---|---|
| trust_score ≥ 70 且无 critical | **ship** | 0 |
| 有 critical 或 score < 40 | **break** | 1 |
| 其他 | **hold** | 0 / 2（--fail-on-warn 时） |

## 三、MCP 新工具（v4.5.0）

在 `mcp-server/mcp.json` 的 `capabilities.tools` 添加 8 个新工具：

| 工具 | 对应端点 | 用途 |
|---|---|---|
| `aishield_sign_agent_card`      | POST /agent-card/sign     | 对 Agent Card 签名 |
| `aishield_verify_agent_card`    | POST /agent-card/verify   | 验证签名（防篡改） |
| `aishield_export_identity`      | POST /agent-card/identity | 导出 KYA + Web Bot Auth |
| `aishield_register_specialist`  | POST /specialist/agents   | 注册专业 agent |
| `aishield_list_specialist_domains` | GET /specialist/domains | 查询 8 域 |
| `aishield_chain_append`         | POST /chain/{id}/append   | 追加责任链 |
| `aishield_chain_trace`          | GET  /chain/{id}/trace    | 责任链溯源 |
| `aishield_protocol_translate`   | POST /protocol/translate  | 协议翻译 |

## 四、测试覆盖（28 项全绿）

`tests/test_ecosystem_activation.py` 分 4 个测试类：

- **SpecialistRegistryTest**（5 项）：8 域注册 / 查询 / 续期 / 吊销 / 非法域拒绝 / 空能力拒绝
- **KyadCompatTest**（5 项）：KYA claims 结构 / Web Bot Auth headers / ERC-8004 双向转换 / 非法地址拒绝 / 完整导出
- **EcosystemApiTest**（13 项）：Agent Card 签名验证 + **篡改检测**（防"拿到签名后偷改 card"的关键场景）/ 责任链 create-append-verify-trace / 协议桥 normalize-translate / 路由分发 404 / KYA 导出 / ERC-8004 wrap
- **ShipGateTest**（5 项）：判定规则映射 / 退出码映射 / attestation 输出结构

**全量回归**：1307 passed / 4 legacy fails（均为老 CI 契约问题，与本次改动无关）
**隔离不变量**：`scripts/prove_isolation.py` ✅ PASS

## 五、下一步（R2 → R5 队列）

- **R2（第 3-4 周）**：Public Trust Leaderboard + 规则贡献者激励
- **R3（第 5-8 周）**：内核级沙箱升级（整合 OpenShell / mcpguard）
- **R4（第 9-12 周）**：完整责任链落盘 + 审计凭证签发
- **R5（持续）**：中立身份服务商业化（KYA / Web Bot Auth / ERC-8004 三协议兼容层作为开源基础设施）

## 六、明确不做

- 不自研协议（MCP / A2A / KYA / Web Bot Auth / ERC-8004 都整合不重造）
- 不做通用 agent 平台（Anthropic/OpenAI 已占）
- 不做 MCP 目录竞品（Glama / OpenClaw 已占）
- 不做 x402 / KYA 自建服务（做**兼容层**，服务中立身份）
- 不碰其他项目（swarmlabs / roboparts / healthlens / oraclemind）
- 不追求竞赛奖金线

## 七、快速本地验证（3 条命令）

```bash
cd aishield
# 1. 跑 5 支柱 API 自证
python api/ecosystem_api.py

# 2. 跑 28 项新测试
python tests/test_ecosystem_activation.py

# 3. 试 ship CLI（对某个目录做发布门禁）
python scripts/ship_gate.py --path . --json
```

## 八、诚实风险

- **未推 main**：本次改动仅在本地，需通过 `scripts/_push_batch.py` 走 GitHub Contents API 推上去才能进 CI
- **4 个 legacy CI 失败**：`test_arena_join_gate` 未登记、memory 有 credentials、gate 阈值缺失等 —— 与本轮无关但会影响 CI 绿灯
- **签名密钥持久化**：`api/data/agent_card_key.json` 首次运行自动生成，HMAC 模式服务端持有私钥；部署到 CF Pages 需换 Ed25519 + 持久化卷
- **KYA SD-JWT 完整版**：`to_sd_jwt_compact` 生成的是**结构骨架**（未做 ES256 签名），消费方接入 KYA 完整生态时需自己补签名或走 Web Bot Auth
