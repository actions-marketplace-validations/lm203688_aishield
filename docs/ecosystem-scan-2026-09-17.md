# 生态扫描决策记录 2026-09-17

一次批量评估：把外部生态里被提名到我们项目的项目逐个过一遍，产出**采纳 / 拒绝 + 理由**。
目的是把"值得借的范式"和"看着时髦但不该抄的"分开，并留下为什么。

结论先行：

- **采纳并已落地 2 项**：OWASP MAESTRO 框架映射、持久记忆完整性扫描（ASI04）。
- **拒绝 10+ 项**，主因三条：依赖付费/托管模型（违背零依赖可离线）、与"绝不 spawn 被扫配置"
  冲突、或与我们品类无关（是 harness/生成器/工具站，不是安全扫描器）。
- **2 个被点名的项目查不到实体**：`milind-soni/openmausbot`、"hyper research"。
  不虚构不存在的引用——查不到就是查不到。

---

## 1. 已采纳并落地

### 1.1 OWASP MAESTRO 多 agent 威胁模型映射

`scanner/compliance.py` 新增第 4 个合规框架 `maestro`，与前三个
（`nist_csf` / `iso27001` / `pci_dss`）并列聚合。

- **8 层架构**（L1 Memory Poisoning → L8 Agent Identity Spoofing）
- **15 条官方威胁条目** T1–T15（*Agentic AI Threats and Mitigations v1.0*）
- `_CATEGORY_MAESTRO` 把我们的 20 个类别（MCP01–10 + ASI01–10）逐一对齐到 MAESTRO 层

为什么值得：我们此前是"双维"（MCP01–10 + ASI01–10）+ 三个合规框架。MAESTRO 是
OWASP 官方的多 agent 威胁分类，接入后对外叙事从"我们的二维 + 三框架"变成
**"我们的二维 + 四框架，且带 OWASP 官方威胁编号锚点"**。这是纯增量、零运行时成本、
零依赖。

锚定纪律：新增 `test_all_owasp_threat_codes_reachable` 断言 T1–T15 **每条都至少被一个
类别引用**，否则等于 OWASP 有威胁我们没锚点。同时修正了两处手滑（MCP09 漏标、
`MCP10` 缺映射），并在 `MAESTRO_THREAT_CODES` docstring 里写明
**"OWASP 的 T 编号体系与本库 ASI01–10 不是同一个编号体系"**——防止后人把两套编号混用。

### 1.2 持久记忆完整性扫描（ASI04）

新增 `scanner/memory_integrity_scan.py`，这是本批里**唯一新增的扫描器**。

**要解决的问题**：ElizaOS 的公开研究表明，跨 session 的持久记忆只要没有写入方完整性校验，
任意有消息权限的一方都能投毒——伪造一条"支付已确认"的历史记录，之后的 `transfer()`
即便来自合法 owner 也会被劫持。作者的回应是"我们把沙箱与分片隔离留给未来"。

我们的 `memory_scan.py` 检测的是**注入行为**（有人正在写恶意指令进记忆）。它管不了
另一半：**记忆库本身没有完整性边界**。那是架构缺陷而非注入动作——没有任何一行代码
"正在投毒"，所以按注入模式匹配**必然零命中**。这正是"本地绿 ≠ 架构安全"的典型假绿。

检测两类架构信号：

| finding | 触发 | 严重度 |
|---|---|---|
| `memory_store_without_integrity` | 存在持久记忆写入，同文件内看不到 HMAC / signature / verify / allow-list / checksum | medium |
| ↑ 同上 + 同文件从不可信消息入口取数（discord / webhook / websocket / 请求体） | ElizaOS 的初始访问向量 | **high** |
| `shared_memory_unpartitioned` | 多 agent 共享记忆，看不到租户/命名空间/隔离边界 | medium |

判定纪律：**只报告存在持久化写入的文件**。"没有记忆"不是一处漏洞——不扫就零命中，
扫了就是误报。误报面由双条件（存储信号 AND 无完整性信号）共同约束。向量库后端名
需与记忆类名词**同行或 ±1 行**共现，避免"用向量库做 RAG 检索"被误判成记忆投毒面。

### 1.3 配套的元数据同步

新增扫描器必须同步三处声明，否则就是漂移：

- `api/static/.well-known/agent-card.json` —— 加入 `memory_integrity_scan` 工具条目
- `docs/project-sbom.cyclonedx.json` —— 加入组件 + 依赖边（stdlib only）
- `scanner/workspace_scan.py` —— 注册到 pipeline + report 键

顺手修掉一处陈旧标注：`agent-card.json` 里 `memory_scan` 标的是 `（ASI06）`，
而代码实际发的是 `MCP03`。

---

## 2. 明确拒绝（附理由）

三条不变量是拒绝依据：**零依赖 / 可离线**、**绝不 spawn 被扫配置**、
**我们是静态扫描器不是 harness**。

| 项目 | 拒绝理由 |
|---|---|
| **Temporal 持久化工作流 + worker 容器** | 直接冲突。起容器跑东西 = spawn 被扫配置。我们是一次性静态扫描 |
| **付费模型驱动的对抗推理流水线**（红/蓝队 + 审计员并行） | 冲突。需要托管付费 API，违背零依赖可离线。我们靠 238 条静态规则 + 雷达，不靠模型判断 |
| **多 harness 适配矩阵** | 品类不符。我们不是 harness，是安全扫描器 |
| **Agent 自构建 / 递归自改系统**（L5 递归自主权） | 冲突。让 agent 改写自己的护栏，与"绝不 spawn 被扫配置"是同一枚硬币的两面 |
| **GUI/桌面操控类 agent** | 品类不符。且需要驱动真实桌面进程，与只读静态扫描相反 |
| **模型路由 / 千模型网关** | 品类不符。我们不调用模型 |
| **独立开发者的工具/模板站** | 无集成面。是给人用的模板集合，不是可嵌入的安全能力 |
| **开源 harness 框架整体** | 冲突。harness 的核心诉求是"让 agent 能干活"，我们的核心诉求是"确保 agent 不能乱干活" |

### 2.1 Theseus Labs L1–L5 五级自主权框架

**不作为扫描器采纳，但作为分级语言参考。** L1–L4 在固定规则内优化、L5 递归自改，
这套描述对"agent 被授权到什么程度"是清晰的。我们的对应物是信任层 L1–L3 + 0–100 分。
**值得学的是命名方式**：把"自主权等级"从模糊形容词变成可枚举的级别编号。

L5（递归自改）我们**明确不实现**——它意味着 agent 能改自己的安全策略，这与我们
`assert_not_root()` 这类"执行身份护栏"是互斥的。

### 2.2 OpenAI Agents API / Codex harness

作为**信号**而非**依赖**采纳。它是 agent 平台的基础设施层（工具调用、护栏、
会话、记忆），方向与我们一致但**不是同类**：它提供运行时的 agent 编排，
我们提供开发时的配置审计。

可借鉴的是它的护栏与工具校验的**分层方式**——但具体实现绑定 OpenAI 托管 API，
接入就违背零依赖。**结论：记为竞争情报，不集成。**

### 2.3 查不到实体的两个名字

- **`milind-soni/openmausbot`** —— 多次检索无匹配仓库。不编造分析。
- **"hyper research 研究智能体"** —— 无对应开源项目，最接近的是某个大模型厂商的
  research 模式（付费托管功能）。不基于不存在的项目写借鉴项。

这两条如实记录，而不是硬凑一段分析。凑出来的"借鉴点"比没有借鉴点更糟——
它会污染后续决策的判断基线。

---

## 3. 落地清单

| 文件 | 变更 |
|---|---|
| `scanner/compliance.py` | +MAESTRO 框架（8 层 / T1–T15 / 20 类映射 / 第 4 个 FRAMEWORKS 成员） |
| `scanner/memory_integrity_scan.py` | **新建**，2 类 finding、ASI04 |
| `scanner/workspace_scan.py` | 注册 pipeline + report 键 |
| `tests/test_memory_integrity_scan.py` | **新建**回归测试 |
| `tests/test_compliance.py` | +MAESTRO 断言（四框架全覆盖 / T1–T15 可达） |
| `tests/run_all.py` | 登记新测试模块 |
| `tests/test_capability_boundary_scan.py` | pipeline 键清单加 `memory_integrity_scan` |
| `api/static/.well-known/agent-card.json` | +`memory_integrity_scan` 工具；修正 `memory_scan` 陈旧标注 |
| `docs/project-sbom.cyclonedx.json` | +组件 + 依赖边 |

## 4. 验证

- `tests/run_all.py`：**1060 tests / 0 failed / 0 error / 44 skipped**
  （44 skipped = 41「服务器未启动」+ 3「security-scan.yml 不存在」，均为既有环境依赖项）
- `scripts/sync_version.py --check`：**通过**，4.3.0 声明位一致
- 变更文件密钥扫描：**0 命中**

**未推送**——需走 `scripts/gh_push.py`（Contents API）。
