# Theseus RSI L1–L5 → AIShield 检测映射（正式化）

> 目的：把 Theseus Labs《RSI report》的五级自主权框架，从「一篇被雷达读到的论文」
> 变成**引擎里可分类、可起草、可晋升、可度量**的威胁类别，闭合
> signal → draft → promote → effect 全链。
>
> 状态：**已落地**（2026-09-15）。radar 规则 17 → 19，线上口径 236 → 238。

## 1. 五级自主权框架（Theseus RSI）

| 级别 | 含义 | 危险等级 |
|---|---|---|
| **L1** | 人在循环中，每一步需批准 | 低 |
| **L2** | 人设定目标，agent 在固定规则内自行执行 | 低 |
| **L3** | agent 在固定规则内**优化**自身行为 | 中 |
| **L4** | agent 在固定规则内自主迭代（规则仍由人设定） | 中 |
| **L5** | agent **递归改进「改进机制本身」** —— 规则、奖励、监督面都成为它的可写对象 | **高** |

L1–L4 的关键约束是「固定规则内优化」：无论 agent 怎么迭代，**约束它的那层机制**
不在它的可写范围内。**L5 打破的正是这条线** —— 它把改进机制本身纳入优化目标，
于是自我改进与自我豁免无法再被区分。

参考：Theseus Labs RSI 报告（SJTU + Theseus Labs），arXiv `2609.11873`。

## 2. 为什么 AIShield 必须单独建模 L5

同一个 L5 信号在旧逻辑里会**被系统自己的过滤器吃掉**，这是本次修复的核心：

1. 旧 `ATTACK_PATTERNS` 里能命中它的只有 `self[- ]evolving\s+agent`（归到
   `trajectory-poisoning`）；
2. 但 `CAPABILITY_INDICATORS` 含 `self-improv`，`_is_capability_side()` 会把
   「自我改进」类信号**一律抑制为 `none`**（R4-capability 抑制，2026-09-03 设计）；
3. 结果：一篇标题写着「recursive self-improvement of the safety mechanism」的论文
   —— 字面就是 L5 威胁 —— 被判为「良性能力研究」，**永不进入起草队列**。

R4-capability 抑制本身是对的（它挡掉了大量「拿攻击当动机」的能力论文），
但它需要一条**例外**：当研究对象就是「agent 颠覆自己的约束」时，
这不是能力研究，**这就是威胁本身**。

## 3. 映射表

| AIShield 类别 | OWASP Agentic | L5 语义 | 检测的动作 |
|---|---|---|---|
| `guardrail-self-modification` | **ASI01**（目标/计划篡改） | agent 把「约束自己的那层」变成可写对象 | 覆写 / 禁用 / 删除**自己的**护栏、安全策略、约束 |
| `oversight-tampering` | **ASI10**（Rogue Agent） | agent 关掉监督者以逃脱约束 | 关闭 / 致盲 验证器、监督器、审计日志、评审器 |

两级合起来覆盖 L5 的两条独立路径：**改规则**（ASI01）与**关监督**（ASI10）。
只覆盖其一都不足以判定「L5 已发生」。

## 4. 结构性具体：为什么这两条正则是「动作型」而非「关键词型」

本项目铁律：**误报比没有规则更糟**。雷达自己的日报满篇写着
`prompt injection` / `MCP attack` / `guardrail`，一条关键词规则会命中
**我们自己的仓库**，污染夜间自扫描门禁。

因此这两条规则只匹配**动作**，不匹配**描述**：

| 输入 | 是否命中 | 原因 |
|---|---|---|
| `the agent rewrites its own guardrail to remove the constraint` | ✅ | 动词 + 自指所有格 + 控制面名词 = 真实动作 |
| `disable the verifier and blind the monitor` | ✅ | 动词 + 监督面名词 |
| `Recursive self-improvement of the guardrail mechanism` | ❌ | 仅**描述**该威胁，无动作 |
| `A survey of guardrail self-modification risks` | ❌ | 研究/防御语境 |
| `This MCP server is a defensive guardrail: it detects …` | ❌ | 良性样本，零误报 |

`_is_specific()` 要求「有 `|` 交替或有界间隔」，两条规则都是用 `|` 枚举具体
动词与目标名词，天然满足；且实测在 **644 个自有文件** 上零命中。

## 5. 附带修的一处分类缺陷

`DEFENSE_INDICATORS` 含 `guard`（本意是 `guardrail` / `guardian`），
于是新类别的**目标名词**「guardrail」会把信号误判为 defense 侧 → 永不起草。
修法：`R4_EXEMPT_CATEGORIES` 中的类别改用窄口径的 `_R4_DEFENSE_MARKERS`
（`defen` / `detect` / `benchmark` / `survey` …），只有显式的研究/防御词
才降级 —— 「We detect agents that disable their own guardrails」仍是 defense，
而真实攻击动作仍是 attack。

## 6. 闭环证据

| 环节 | 产物 |
|---|---|
| 分类 | `scripts/tech_radar.py` `ATTACK_PATTERNS` + `R4_EXEMPT_CATEGORIES` |
| 起草 | `scanner/_proposed/PROPOSED_20260915_theseus_rsi_l5_*.json`（2 条，ready） |
| 晋升 | `data/radar_rules.json`（+2，含 `provenance` 溯源） |
| 效果 | `scripts/radar_effect.py` `ATTACK_SAMPLES`（+4 正样本）；实测 **19/19 命中，0 误报** |
| 契约 | `tests/test_tech_radar.py`（分类/抑制豁免）、`tests/test_radar_effect.py`（覆盖） |

> 注意：L1–L4 不需要新规则。它们是「固定规则内」的行为，已被现有的
> `excessive-agency` / `confused-deputy` / `mcp-attack` 等类别覆盖。
> 本次新增**只针对 L5 那条越界**。
