# AIShield × 四参考项目借鉴映射

> 日期：2026-09-19 · 触发：用户要求「完成下一步 + androidworld / collector / prime agent / cache-to-cache 参考」
> 方法沿用 `agent-ecology-evolution-directions.md` 的 adopt / defend 范式：逐项给出「是什么 → 可 adopt 的具体机制 → 与 AIShield 现有能力的映射 → defend（差异） → 落地项与优先级」。
> **不变式不动**：本地 / 双维覆盖 / 中性信任机构 / 不改名。

---

## 0. 四个参考的定位

| 参考 | 是什么 | 可借鉴的核心机制 |
|---|---|---|
| **AndroidWorld**<br>`google-research/android_world` | Android 自主 agent 的**环境 + 基准**：116 个任务 / 20 应用，**动态参数化**（→ 百万级变体），**durable reward signals**（奖励由系统状态推导，不随实现变化失效），公开排行榜，可扩展任务设计 | 可复现基准 + **持久奖励信号** + 公开排行榜 + 任务参数化 |
| **Collector**<br>`microsoft/project-telescope` | **本地优先的 AI agent 可观测性**：`Collector` trait（manifest + 定时 `collect()`）、**规范化内部标记事件 schema**、本地 IPC（named pipe / unix socket）；内置 GitHub Copilot / Claude Code JSONL 采集器与 **MCP Proxy 实时拦截**采集器 | **collector 插件架构** + canonical event schema + 本地优先 |
| **Prime Agent**<br>`PrimeIntellect-ai/prime-agent`（arXiv 2608.23552） | **自改进 RLM harness**：持久 IPython REPL、**Continual Harness**（histories / memories / skills / prompts / subagent specs 的**版本化精炼**，每次写入带 trigger + intended effect 且可回滚）、递归子代理、标准化 **execution / recovery / verification / resource accounting** | 版本化持续精炼 + **标准化验证** + skills-as-packages |
| **Cache-to-Cache (C2C)**<br>`thu-nics/C2C`（arXiv 2510.03215，ICLR'26） | LLM 之间**绕过文本**、直接以 **KV-cache** 做语义通信；核心观察是「紧凑的语义载体优于逐 token 的文本重传」 | **用紧凑语义载体替代冗长文本传输** → 降 token、降延迟 |

**一个观察**：四个参考都不约而同地在解决同一个问题——**如何让 agent 产物可验证、可复用、可低成本消费**。AIShield 的产品面（扫描 / 信任判定）天然就是这条链路里的「验证」一节；四个参考分别给出了验证之外的四种基础设施做法。

---

## 1. 逐项 adopt / defend

### 1.1 AndroidWorld → 「基准 + 持久奖励信号 + 排行榜」

**可 adopt**

1. **持久奖励信号**：AndroidWorld 的奖励从**系统状态**推导而非比对人工演示，因此实现一变奖励不失效。我们的对应物是 `data/state/radar_effect.json`（catch 正样本命中 / false_positive 良性误报）——同属「信号不随实现漂移」，但**缺一个固定、可复现、第三方可跑的基准集**。
2. **动态任务实例化**：把一个任务参数化成无限变体。我们已有 `BENIGN_CORPUS` + 恶意样本，但样本多为单点、非参数化 → 容易过拟合。
3. **公开排行榜**：把「某资产的安全分」变成**可引用的公开数字**，是使用率与外部引用的天然引擎。

**与现有能力映射**：`docs/agent-security-benchmark-2026.md`（10 恶意 + 10 健康）、`tests/test_capability_full_scan.py`（40 cases）、`scripts/radar_effect.py`。

**defend**：AndroidWorld 评的是「agent **能否完成任务**」（能力），我们评的是「资产**是否可信**」（信任）。我们是**安全基准**，不是任务基准——不与之竞争，而是它需要的互补面（同族信号见雷达收录的 `MobileWorldSafety`，GUI agent 安全基准 arXiv 2608.17659）。

**落地**：`P1` **AIShield Security Benchmark v1** —— 固定 20+20 样本 + 参数化变体（密钥形态 / 安装源 / 传输）× 可复跑脚本 × 公开分数表，供第三方引用与 CI 回归。

---

### 1.2 Collector → 「AIShield Collector：本地持续观测」✅ 本次已实现

**可 adopt**

1. **collector 插件架构**：manifest（声明这是什么）+ 定时 `collect()` + canonical event schema。
2. **规范化内部标记事件**：`{"type": "...", ...}`，一个消费者即可解析全部事件。
3. **本地优先 + 离线**：以本地 IPC / 文件为传输，不上云——与 AIShield 的根本差异化完全同频。

**与现有能力映射**：AIShield 目前是「**跑一次扫描**」；已有 `scanner/batch_scanner.py`（批量入库）、`/fleet` 页、`eco/blackboard.py`（append-only `security_events` 流），但**缺一个持续、变更感知、事件化的前门**。

**defend**：telescope 做**行为可观测性**（工具调用 / token / 成本 / 错误），**不做内容信任判定**；AIShield 做内容信任判定，不做全量遥测。二者是**互补的两个平面**——telescope 记录「agent 做了什么」，AIShield 记录「它被配置成相信的东西该不该信」。telescope 的 MCP Proxy 是**流量代理**，AIShield 是**静态信任判定**。

**落地**：`P0` ✅ **本次已实现** `collector/`：

```
discover local MCP configs ─► static scan (no spawn) ─► canonical events (JSONL)
                                                   └─► compact trust digest
```

- `collector/aishield_collector.py`：`manifest()` / `canonical_event()` / `collect_once()` / `collect_from_configs()` / `run_watch()` / `summarize()`。
- 事件类型：`CollectorStarted` / `ConfigDiscovered` / `FindingRaised` / `ScanCompleted` / `CollectorHeartbeat`。
- **不 spawn、不联网、零依赖、指纹幂等**（配置不变 → 指纹不变 → 只发 heartbeat 不重复告警）。
- 复用 `scanner.client_discovery.discover_and_scan`，不引入第二个扫描器。
- 契约测试 `tests/test_collector.py`（20 项），含**源码级断言**：模块不得出现 `subprocess` / `socket` / `urllib` / `Popen`。

---

### 1.3 Prime Agent → 「AIShield 作为验证 harness + 版本化精炼」

**可 adopt**

1. **Continual Harness 的版本化精炼**：每次对 prompts / skills / memories 的写入都带 **trigger + intended effect** 且可回滚。我们的雷达规则晋升已有 `provenance`（来源可追溯），但**缺 intended effect 记录与一键回滚**。
2. **标准化 execution / recovery / verification**：Prime Agent 把它做成协议。我们的 `promote_rule` 六道闸门 + 良性语料零误报 + M9 监控，**就是这个 verification 层**，只是没有对外命名与文档化。
3. **skills-as-packages**：skill 是可导入的 Python 包。我们**已扫** skill；可反向提供「安全 skill 包」给 harness 直接装载。

**与现有能力映射**：`scripts/promote_rule.py`（六道闸门）、`data/radar_rules.json`（`rules` + `provenance`）、`scripts/radar_effect.py`、`docs/aishield-trust-standard-v0.1.md`。

**defend**：Prime Agent 是**能力** harness（让模型更强），我们是**信任** harness（让 agent 更可信）。目标正交——它是 harness 生态里需要被验证的一方，我们是验证方。

**落地**：
- `P2` `docs/aishield-verification-harness.md`：把「六道闸门 + 零误报 + 效果度量 + 回滚」正式命名为 AIShield 的 verification 层，对齐 Prime Agent 的术语，便于外部引用。
- `P2` 给 `data/radar_rules.json` 的 `provenance` 增加 `trigger` / `intended_effect` 字段（向后兼容，缺失即视为 legacy）。

---

### 1.4 Cache-to-Cache → 「信任摘要（compact digest）替代冗长报告」✅ 本次已部分落地

**可 adopt**

C2C 的结论是**工程性**的：紧凑的语义载体优于逐 token 的文本重传。把它搬到 agent 消费安全结论的场景：

- 现状：`scan()` 返回大 JSON，MCP 工具返回长文本，agent **每轮重复扫描** → token 浪费、结论不稳定。
- 目标：默认返回一个**≤ 数百字节**的紧凑信任摘要（分数 + 严重度计数 + 首 N 条 + **指纹**），需要细节再按指纹取全量。

**与现有能力映射**：`scan()` / `scan_client_configs()` 的全量返回、MCP 6 工具的文本返回。

**defend**：C2C 需要改模型内部（投影 / 融合 KV-cache），我们**做不到也不该做**。我们借的是**理念**（语义压缩通信），落地为**结构化摘要 + 指纹缓存**——纯工程、零依赖、不需要模型侧配合。

**落地**：
- `P0` ✅ **本次已落地**：`collector.summarize()` 输出紧凑 digest + `fingerprint()`（sha256）供 agent 缓存与变更检测。已在契约测试中钉死「digest < 1000 字节」。
- `P1` ✅ **本次已落地**：提升为对外端点 `GET|POST /api/v1/trust/digest`（别名 `/api/v1/digest`）+ MCP 工具 `aishield_digest`（第 7 个），让远程 agent 也能低成本消费。裸 `GET` 无参返回 400 + 自描述 `hint`/`schema`；三种输入模式 `configs`（现扫）/ `scan_result`（现压）/ `src`（现判）。实测紧凑载荷 ~519 字节、带 sha256 指纹、同配置指纹稳定（可缓存）。

---

## 2. 与现有方向的关系

这四项与 `docs/agent-ecology-evolution-directions.md` **方向三（Agent 通路信任层）**同源，各自补上一块：

| 参考 | 对应方向三的哪一环 |
|---|---|
| AndroidWorld | 把「信任」变成**可复现、可引用**的基准信号（否则徽章无人信） |
| Collector | 插入点②（Connection）的**运行时侧**：持续、变更感知 |
| Prime Agent | 插入点④（Identity）的**验证与可审计**：verification / recovery |
| C2C | 通路上「**低摩擦消费**」：否则 agent 不会去查信任 |

**不改变核心定位**（本地 / 双维 / 信任机构 / 不改名）。

---

## 3. 本次落地清单

| 项 | 状态 |
|---|---|
| 借鉴映射（本文） | ✅ |
| **AIShield Collector**（P0，telescope 借鉴） | ✅ 已实现（`collector/`，20 项契约测试） |
| **紧凑信任摘要 + 指纹**（P0，C2C 借鉴） | ✅ 已实现（`collector.summarize()` / `fingerprint()`） |
| 首轮 GEO 推广落地（`/scan` 上线公告 + 渠道清单） | ✅ 见 `docs/blog/blog-online-scan-launch-2026-09-19.md` · `distribution/launch-channels-2026-09-19.md` |
| GEO 资产刷新（`docs/llms.txt` 规则数 + `/scan` 入口） | ✅ |
| AIShield Security Benchmark v1（P1，AndroidWorld 借鉴） | ✅ 已实现（`scripts/benchmark.py` · `docs/benchmark/v1.md` · 16 项契约测试） |
| `/api/v1/trust/digest` + `aishield_digest` MCP 工具（P1，C2C 借鉴） | ✅ 已实现（第 7 个 MCP 工具 · 23 项契约测试，含 §3.1 第 4 条 risk 下限回归） |
| `docs/aishield-verification-harness.md`（P2，Prime Agent 借鉴） | ✅ 已交付 |
| `provenance` 增补 `trigger` / `intended_effect`（P2） | ✅ 19/19 已回填，晋升路径同步写入（8 项契约测试） |

### 3.1 执行中发现并修掉的问题（副产品）

跑基准的过程本身抓出了三个真空区/漂移点，均已修复：

| 发现 | 性质 | 处置 |
|---|---|---|
| **`ws://` 远程配置零告警** | 检测盲区。原正则只匹配 `https?://`，`ws://` 的 scheme 解析成空串，连带跳过明文传输/通配监听/无鉴权三个分支 —— 一个 websocket 远端 server **一条 finding 都不产生** | 改为通用 scheme 解析 + 远程协议白名单（`http/https/ws/wss/sse`），`ws://` 同 http 判为明文传输；`file://` 等本地协议不受影响 |
| **`docker run --privileged` 配置面不检** | 检测盲区。该 critical 规则存在于文件扫描规则集，但配置面扫描器不跑规则集，特权容器启动的配置只拿到零扣分的 `info` | 在 `analyze_server_entry` 补特权参数检查，按隔离解除程度分级（`--privileged`/`--cap-add=SYS_ADMIN` = critical，`--pid=host`/`--net=host` = high） |
| **`mcp-server/server.json` 版本停在 4.2.2** | 版本漂移。它是 npm `files` 清单里**会被真实发布出去**的 MCP Registry 清单，却不在 `sync_version.py` 的 11 个受检位里 —— registry/ 那份跟着升到 4.3.0，这份无人察觉 | 纳入门禁（第 12 个声明位），已在 `--check` 下对齐 4.3.0 |
| **摘要把带 2 条 high 的配置标成 `risk: "safe"`** | **假安心**（最危险的一类错误）。风险标签只看分数分档（`>=80` → safe），high 权重 8 分 → 两条 high 得 84 分 → 落在 safe 档。于是同一个摘要里 `risk: "safe"` 与 `severity_counts: {"high": 2}` 并列，而该配置同时具有明文 HTTP 远程传输与未锁定版本的启动方式。**下游 agent 只读 risk 字段** | risk 改为取「分数档」与「实际最严重 finding」中更重的一方，并输出 `worst_severity` 说明原因（分数照旧输出，只是不再单独决定标签）。`low`/`info` 不设下限，避免姿态噪音把干净配置抬成风险。7 项契约测试钉死（`TestRiskFloor`） |
| **`/scan` prompt 扫描的同类假安心** | 同一缺陷类的另一处入口：单条 critical 只扣 30 分 → 70 分 → 旧分档标成 risk `"low"`；一条 high（扣 15）单独出现则 85 分 → `safe: true`。"能绕过安全过滤"这类载荷被判 safe | 同一处理：risk 加下限，`safe` 改为由 `risk` 派生（不再独立算一次 `score >= 80`，一个结论一个真值来源）；`test_detect_bypass_security` 从「只断言有 finding」升级为断言 `risk == "high"` / `safe is False` |

基准因此从 **召回 92.0% / 误报 0%** 提升到 **召回 96.0% / 误报 0%**。

> 第 4 条是**上线后实测**抓到的，不是本地测试抓到的 —— 单测里 `risk` 只在
> `scan_result` 路径被断言过分数档，`configs`（现扫）路径从没断言过 risk 与
> severity 的自洽性。这是「本地绿 ≠ 线上对」在本项目的又一次具体形态。


另有一类"疑似误报"经逐条核查后判定为**记账错误而非扫描器缺陷**：首轮把 `npx -y` /
`bash -c` / 无鉴权远程 URL 照搬进良性对照组，扫描器正确报了 high，却被记成 3 例误报。
启动方式这个轴并不与安全性正交 —— 安全的包用危险方式启动仍是危险配置。已重构对照组
（良性一律用 pin 版本 / digest / 带鉴权头），并把这三种写法改判为正样本单独成轴。
