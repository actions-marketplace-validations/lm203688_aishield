# OWASP Agentic 分类对齐说明

> 状态：2026-09-17 核实并修正 · 代码真源 `scanner/compliance.py`
> 一句话：**报告中 `owasp_category` 的 `ASI01–ASI10` 是本库内部编号，不等于 OWASP 官方编号。**

---

## 1. 问题

本库对外一直写"对齐 OWASP Agentic ASI01–10"。这个措辞容易被读成
"我们的编号 == OWASP 的编号"。**实际不是。**

OWASP GenAI Security Project 于 **2025-12-09** 发布 *Top 10 for Agentic Applications 2026*。
本库的 ASI01–ASI10 是更早建立的自建归纳，10 个编号里只有 3 个与官方恰好同号，
**4 个指向官方不同的类别，2 个在官方没有独立类别**。

最危险的一个：本库 `ASI04` = 记忆操纵与投毒，官方 `ASI04` = Agentic Supply Chain。
如果客户拿着我们的报告去查 OWASP 官方文档，会读到完全不相干的风险条目。

## 2. OWASP 官方 Top 10 for Agentic Applications 2026

| 官方 ID | 官方名称 |
|---|---|
| ASI01 | Agent Goal Hijack |
| ASI02 | Tool Misuse & Exploitation |
| ASI03 | Identity & Privilege Abuse |
| ASI04 | Agentic Supply Chain Vulnerabilities |
| ASI05 | Unexpected Code Execution |
| ASI06 | Memory & Context Poisoning |
| ASI07 | Insecure Inter-Agent Communication |
| ASI08 | Cascading Failures |
| ASI09 | Human-Agent Trust Exploitation |
| ASI10 | Rogue Agents |

配套威胁条目清单为 *Agentic AI – Threats and Mitigations*，**T1–T17 共 17 条**
（T16 Insecure Inter-Agent Protocol Abuse 与 T17 Supply Chain Compromise 是后补条目）。

## 3. 交叉表

| 本库内部 ID | 本库含义 | → 官方 ID | 官方名称 |
|---|---|---|---|
| ASI01 | 目标与指令操纵（提示注入） | ASI01 | Agent Goal Hijack |
| ASI02 | 工具滥用 | ASI02 | Tool Misuse & Exploitation |
| ASI03 | 过度代理 / 凭证外泄 | ASI03 | Identity & Privilege Abuse |
| **ASI04** | **记忆操纵与投毒** | **ASI06** | **Memory & Context Poisoning** |
| ASI05 | 智能体身份与信任 | ASI03 | Identity & Privilege Abuse |
| ASI06 | 智能体通信与供应链 | ASI07 + ASI04 | 两条（官方拆开） |
| ASI07 | 资源无界消耗 | — | 官方无独立类别（折叠进 ASI02 的 T4 Resource Overload） |
| ASI08 | 可观测性缺口 | — | 官方无独立类别（T8 Repudiation & Untraceability 相关） |
| **ASI09** | **级联失效与多智能体风险** | **ASI08** | **Cascading Failures** |
| ASI10 | 流氓智能体 / 人机边界 | ASI10 + ASI09 | 两条 |

**官方有、本库无独立内部类别**：`ASI05 Unexpected Code Execution`。
这是能力缺口而非编号问题——命令注入 / eval / 反序列化等检测目前归在
MCP 侧规则与通用代码扫描里，没有单独的 ASI 类别锚点。

## 4. 为什么不做静默重编号

`owasp_category` 是对外报告的**公开字段**，出现在 API 响应、SARIF 输出、
MCP 工具返回值、agent-card 里。直接改编号 = 破坏性变更：

- 消费方按 `owasp_category == "ASI04"` 过滤的代码全部失效
- 历史报告与新报告无法对比
- 需要版本号大跳 + 迁移说明

所以采用**加法式**修正：保留内部编号不动，补齐权威目录与交叉表，
并让机器可读输出自带命名空间声明。静默重编号留到下一个主版本。

## 5. 代码侧已落地

`scanner/compliance.py`：

| 常量 | 内容 |
|---|---|
| `OWASP_AGENTIC_2026` | 官方 10 类权威名称（逐字锚定，测试防漂移） |
| `OWASP_AGENTIC_THREATS` | 官方 T1–T17 威胁条目 |
| `OWASP_AGENTIC_ASI_TO_THREATS` | 官方 ASI→T 映射（用于推导，勿手写） |
| `INTERNAL_ASI_TO_OWASP` | 本库→官方交叉表（对外只读） |
| `OWASP_AGENTIC_UNCOVERED` | 官方有、本库无独立类别：`["ASI05"]` |
| `MAESTRO_THREAT_CODES` | MCP01–10 手工锚点；ASI01–10 **由交叉表推导**，不再手写 |

`compliance_summary()` 输出新增四个键：

```json
{
  "category_id_namespace": "aishield-internal",
  "owasp_agentic_2026": { "ASI01": "Agent Goal Hijack", "...": "..." },
  "internal_to_owasp_agentic": { "ASI04": ["ASI06"], "...": "..." },
  "owasp_agentic_uncovered": ["ASI05"]
}
```

消费方只要读 `category_id_namespace` 就知道报告里的编号属于哪套体系。

## 6. 顺手修掉的另一个错

本库原先声称威胁目录是 **T1–T15**。实际官方是 **T1–T17**——漏了 T16 / T17。
测试 `test_all_owasp_threat_codes_reachable` 现在锚定全部 17 条，
且 `test_every_category_has_threat_codes` 会拦截任何不在官方目录内的 T 编号。

另一个有趣的事实：**OWASP 自己的 ASI→T 映射里 T9（Identity Spoofing & Impersonation）
一条都没引用**。本库靠 `MCP07 → T9` 的手工锚点补上了这个空档。

## 7. 已知遗留

以下文件仍使用"ASI01–10"这类宽泛措辞，未逐处改写。
内容上它们指的都是本库内部编号，**事实判断没有错，只是措辞可能引起误读**：

`docs/` 下 30+ 份分析/博客/情报文档、`distribution/` 下 10+ 份渠道投递文案、
`mcp-server/{mcp.json,server.json}`、`docs/index.md`、`skills/aishield-scan/SKILL.md`、
`AGENTS.md`、`smithery.yaml`、`action.yml`。

已精确修正的高可见度入口：`README.md`、`api/static/llms.txt`、`docs/llms.txt`、
`api/static/.well-known/{agent-card.json,agent.json,ai-plugin.json,agent-discovery.json}`、
`mcp-server/README.md`。

剩余文件的批量改写属文案工作，不影响任何检测逻辑或报告数值——
留给后续一次性 sweep，不需要紧急处理。

## 8. 补充：报告里实际发的编号有两个命名空间

写 §1 时只发现"内部 ASI ≠ 官方 ASI"。继续核对扫描器实发值时又发现一层：

**11 个 Agentic 扫描器里 10 个发的其实是 `MCP0x`，只有 1 个发 `ASI0x`。**

| 模块 | 实发 `owasp_category` |
|---|---|
| goal_hijack_scan / dark_pattern_scan / slop_scan | `MCP06` |
| least_agency_scan / mcp_oauth_scan / scope_composition_scan / identity_scan / payment_scan | `MCP02` |
| memory_scan / antitamper_scan | `MCP03` |
| provenance_scan / registry_supply_scan | `MCP04` |
| authentik_scan | `MCP07` |
| **memory_integrity_scan** | **`ASI04`（唯一的 ASI 发射者）** |

含义：

- `owasp_category` 是**混用字段**。`MCP01–MCP10` 是官方 OWASP MCP Top 10 编号，
  `ASI01–ASI10` 是本库内部编号。§1 讲的"内部 ASI ≠ 官方 ASI"只描述后半段。
- **按 `ASI0x` 过滤报告会漏掉绝大多数 Agentic 命中。**这是消费方最容易踩的坑，
  已写进 `llms.txt` 的命名空间说明。
- 模块文档里的"ASI0x"话题标签用的是**官方**编号（`memory_scan.py` 标注 ASI06 =
  Memory & Context Poisoning，与官方一致），不是本库内部编号。
  `memory_integrity_scan.py` 原先是唯一用内部编号写标签的离群者，已改回官方编号；
  它实发的 `ASI04` 保持不变（公开字段，不动）。
- 测试 `TestEmittedCategoryNamespace` 把"唯一 ASI 发射者"这个事实钉死，
  新增 ASI0x 发射者必须同时改测试与本文件，否则 CI 红。

