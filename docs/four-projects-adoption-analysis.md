# 四项目借鉴分析：ezl-keygraph / Shannon / ECC / PenguinHarness

> 触发：2026-09-16 归档 `大数据与模型包_20260915.zip` 扫描。归档本体里**没有**这四个项目
> （346MB，1506 条目：`projects-review/` 1033 + `backup/` 402 + `swarmlabs_ml_models/` 61，
> 主体是 13 站知识库备份、swarmlabs 40+ 化学/生物 ML 模型 pkl/pt、oraclemind 与含密钥的
> `全局配置_TOOLS.md`/`密码与密钥汇总.txt`）——四个名字均为**外部生态项目**，需联网核实。
> 归档里唯一相关的收获是 `projects-review/agent-trust/weekly-suggestions/` 下 3 份竞品分析，
> 其**方法论**可复用、其**数据已过期**（详见 §5）。

## 0. 归档本身：什么能引用、什么不能

| 归档内容 | 处置 | 理由 |
|---|---|---|
| `projects-review/agent-trust/weekly-suggestions/*.md`（6 份） | **方法论引用** | 竞品对位 + adopt/defend 拆解的写法可复用；数据过期（见 §5） |
| `backup/02_AIShield安全平台.zip`（我们自己 6 月旧备份） | **不引用** | 旧版本（`api/server_flask.py` 56KB，当前是 `api/server.py`），且 `data/api_keys.json` 含密钥 |
| `swarmlabs_ml_models/*.pkl`（40+ 文件） | **排除** | sklearn pickle / torch .pt 模型，与 MCP 安全扫描无关；反序列化本身是攻击面 |
| `swarmlabs_*_data.json`（6 份大数据集） | **排除** | QM9/ToxCast/bio-chem 化学数据集，非本项目域 |
| `*.tar.gz`（14 站知识库 ×2 备份）、`genetech-13sites-full.tar.gz` | **排除** | 上一轮归档已确认 303 站点文件不可直接引用 |
| `backup/密码与密钥汇总.txt`、`全局配置_TOOLS.md`/`USER.md`/`.env` | **绝不进项目** | 活跃 PAT / CF token / 支付密钥 |
| `git-unpushed.bundle` | **忽略** | 2026-06-25 的未推送 commit，主分支早已远超 |

**结论：本轮无代码资产可直接搬运。** 有价值的只有两类——外部四个项目的**机制借鉴**
（本文 §1–4），和归档竞品文档暴露的**方法论缺陷**（§5）。

---

## 1. ezl-keygraph / Shannon 3.0（KeygraphHQ/shannon）

**事实**：ezl-keygraph 是 Shannon 的 maintainer（GitHub 账号 `ezl-keygraph`，邮箱
`ezhil@keygraph.io`）。Shannon = AI pentester，28.7k★ / 294 commits / TypeScript，
XBOW Benchmark **hint-free 96.15%**。3.0 主线新增十阶段 Agentic SAST + SARIF/PDF 输出 +
Temporal 持久化。

### 1.1 直接可借鉴（执行硬化）

| 借鉴项 | Shannon 原做法 | AIShield 现状 | 处置 |
|---|---|---|---|
| **拒绝 root/sudo 运行** | `feat(cli): block running shannon with sudo or as root`（#323） | `api/server.py` 无 geteuid 检查 | **P0 已落地**：`assert_not_root()`，`AISHIELD_ALLOW_ROOT=1` 可绕过（容器场景） |
| **preflight 失败外显** | #454 "hold start until preflight passes and surface its failure"、"surface pre-workflow worker failures instead of dying silently" | 已有「假绿三层」铁律 + `indexnow_submit.py` 退出码区分 | **P2**：同类原则的独立验证，无需新代码 |
| **静态挂载替代逐次动态挂载** | #107 用固定 `./repos:/repos` 替代每任务动态 bind mount，解决切目标时的 stale mount | 无同类问题 | 参考，暂不适用 |
| **preflight 拦截云元数据段** | #337 "block cloud metadata range in target URL check" | 已有 `169.254.169.254`/`metadata.google.internal`/CGNAT 规则（`rules.py:297-299`） | **已覆盖**，无需新增 |
| **配置键遮蔽拒绝** | "reject a shell credential that shadows a gateway config.toml key" | 已有命名空间遮蔽检测 | **已覆盖** |
| **产物分仓避 AV 误报** | 基准报告移出主仓：Windows Defender 对渗透报告误报，迫使每个 Windows 用户加排除项 | `tests/` 正样本含攻击 payload，规模尚小 | **P2**：正样本增至数百条时考虑 `tests/corpus/` 独立子目录 + `.gitattributes -text` |
| **日志脱敏** | "redact base URL and target URL from preflight info logs" | 日志未系统脱敏 | **P2**：扫描结果里会带被扫路径与密钥片段 |

### 1.2 不要抄

- **Temporal 持久化工作流**：Shannon 为了跨重启 resume 扫描引入 Temporal + Docker worker +
  cosign 签名镜像。我们的模型是**单次静态扫描**，无长时状态机需求。加这套是纯负债。
- **ephemeral worker 容器**：我们的核心不变量是「绝不 spawn 被扫配置」。起 worker 容器去
  跑东西与立论直接冲突。
- **真实 exploit 执行**：品类不同，且与本项目的"只读静态"承诺互斥。

---

## 2. AgentShield（内含于 affaan-m/ECC）—— 最接近的竞品

**事实**：Claude Code Hackathon 2026-02 出品。**102 静态规则 / 1282 测试 / 98% 覆盖**，
5 类目：密钥检测（14 pattern）、权限审计、hook 注入分析、MCP server 风险画像、agent 配置审查。
扫描面：`CLAUDE.md`、`settings.json`、MCP 配置、hooks、agent 定义、skills。输出 terminal
(A–F 分级) / JSON / Markdown / HTML，critical 发现 exit code 2 供 CI 门禁。
`--opus` 高级模式起三个并行 Opus 4.6：红队（找利用链）、蓝队（评防护）、审计员（综合排序）。

### 2.1 竞争结论

**扫描面几乎完全重叠，测试量级碾压（1282 vs 我们全套 830）。** 这决定了：

- 对外**绝不能主打规则数或测试数**。要打三条结构性差异：**双维覆盖**
  （MCP01–10 + ASI01–10，它只有 agent 配置 5 类目）、**信任层**
  （L1–L3 + 0–100 分 + badge + Trust API + x402，它无）、**绝不 spawn 被扫配置**
  （它纯静态所以也不 spawn，这条打不平，需靠前两条拉开）。
- 我们独有且可量化：离线 slopsquat 检测（它 14 种密钥 pattern，无幻觉包/依赖混淆）、
  rug-pull 版本漂移、攻击路径最小移除集、SBOM/SARIF。

### 2.2 值得抄的两条

1. **Runner provenance 声明**——它写得极清楚：*"Registry publication alone does not
   establish an audit… Record the selected release, reviewed source and verified package
   integrity in your installation record. Do not substitute an unversioned one-shot download."*
   我们 npm `aishield-mcp-server` + Official MCP Registry 分发同样需要这段表述，
   否则用户会把"能装上"误当"可信"。**P1 待办**。

2. **A–F 字母分级**——我们已有 0–100 分 + Gold/Silver 徽章（旧备份
   `popular_mcp_security_report.md` 即此形态），但 CI 场景下 `exit code 2 on critical`
   比分数更直接。需确认我们的 `action_entrypoint.py` 是否已有严重度门禁。**P1 待办**。

### 2.3 不要抄

- **三 Opus 对抗流水线**：红/蓝/审计员并行是好设计，但依赖付费 Anthropic API，
  与"零依赖、可离线"不变量冲突。我们的 `radar_effect.ATTACK_SAMPLES`
  正样本门禁 + 「误报比没有规则更糟」原则，是同一目标下的零依赖实现——**保持**。

---

## 3. ECC 的"完整组件树"

**事实**：225,398★ / MIT / v2.2.1（2026-08-31）/ 单人 maintainer 周更 / 覆盖 12+ harness。
根目录即 source of truth，平台适配器只做打包或映射，**不维护独立副本**——这是它能
225k★ 仍由一人维护的结构原因。

```
ECC/
├── agents/          # 68 specialized subagents
├── skills/          # 292 workflows loaded on demand  ← SKILL.md + YAML frontmatter
├── commands/        # 94 maintained slash-command shims
├── rules/           # opt-in common + 语言包
├── hooks/           # hooks.json + memory-persistence/ + strategic-compact/
├── scripts/         # install, repair, sync, orchestration, checks（跨平台 Node）
├── .claude-plugin/  # marketplace manifest
├── .codex/ .opencode/ .cursor/   # 各 harness 适配器
├── docs/            # public setup, architecture, operating guides
└── contexts/        # 动态 system prompt 注入
```

### 3.1 可借鉴（结构性）

- **"根即真源，适配器不复制"** —— 我们 `docs/llms.txt` 与 `api/static/llms.txt` 是**双份
  需逐字节同步**的，靠测试 `test_served_llms_txt_matches_docs_source` 钉死。这正是 ECC
  要避免的反模式。中长期应考虑只留一份真源 + 构建时复制。**P2**。
- **DRY adapter 模式**（Cursor 20 个 hook 事件 → adapter.js 转成 Claude 8 事件格式，
  复用同一批 `scripts/hooks/*.js`）——理念可借鉴，但我们有 14 客户端面发现，
  是横向发现而非纵向适配，**架构不匹配，不抄**。
- **`ecc doctor` / `repair` / `list-installed` 生命周期**——我们 `self_scan.py` 只覆盖
  台账 5 条 + 10 源。补一个"安装/配置自检"入口有价值，**P2**。

### 3.2 记忆边界原则（P1，原则成文）

ECC Memory Vault 明确写成原则：

> *"Memory is unreviewed context, not executable policy. … Agents must verify important
> claims against authoritative sources and must never treat recalled bodies as executable
> instructions or policy."*

配套工程：**fail-closed `.gitignore`** 保护项目记忆；team scope 仅用于人工审阅过的
版本控制共享；记忆体只接受 `--stdin`/`--body-file` 不接受命令行参数；MCP 侧身份
`ECC_MEMORY_HARNESS` **服务器绑定，调用方无法伪造**。

AIShield 自身重度依赖 memory 文件（workspace `.workbuddy/memory/` + 用户级
`~/.workbuddy/MEMORY.md`），而「记忆投毒」是我们已有的检测能力
（`memory_scan.py` 的 `memory_context_poisoning`）。**攻击者能投毒别人的 memory，
我们自己也一样会投毒自己的。** 该原则尚未成文。

---

## 4. PenguinHarness（Prism-Shadow/penguin-harness）

**事实**：LlamaFactory 作者郑耀威，Apache-2.0，`penguin.ooo`。"0.2 元从零构建 Agent"。
核心价值不是"让 AI 建 AI"，而是 **RSI 闭环工程化**：

```
Design evaluation benchmarks   (benchmark-design skill)
  → Build test case set        (覆盖边界用例)
  → Run evaluation             (agent-evaluation skill，逐例打分 + 输出失败原因)
  → Optimize                   (agent-optimization skill，按失败原因改 prompt/工具/推理链)
  → Publish                    (snapshot + 版本号递增，自动注册)
  → 可回滚到任一历史版本
```

**关键性质：评估与优化都由 Agent 自己做，人只设目标和终审。**

### 4.1 直接可借鉴：快照 + 回滚（P1，2026-09-16 已落地）

> **勘误（2026-09-16 晚，自查后改写本节）**：本节原稿写"promote_rule 门禁只验
> 正样本命中，不度量新规则是否在良性语料上引入误报"。**这句话是错的。**
> `scripts/promote_rule.py` 一直有 `BENIGN_CORPUS`（12 条）在闸门处拦误报，
> `scripts/radar_effect.py` 一直有 `ATTACK_SAMPLES`（30 条）度量召回。
> 真正的缺口是下面三条 —— 已逐项落地。

**真实缺口（已修）**

1. **无快照、无回滚。** `promote()` 直接 `open("w")` 覆盖 `data/radar_rules.json`，
   且 `_evaluate_effect()` 是**事后** best-effort 告警（其 docstring 明写
   "effect measurement must never break promotion"）—— 一条误报规则会先落库
   成为线上规则，然后才被报告为误报，届时已无回滚手段。
   → 已加 `snapshot_current()`（覆盖写之前留回滚点）、`rollback()`
   （先快照当前状态再回滚，回错方向也可撤销）、`--rollback` /
   `--list-snapshots` / `--ledger` 三个子命令，`KEEP_SNAPSHOTS=20`。
   裁剪用 `os.replace` 移入 `.pruned/` 而非删除（删除类 API 在沙箱里被守卫吞掉）。

2. **语料镜像漂移。** `BENIGN_CORPUS` 在 `promote_rule.py` 与 `radar_effect.py`
   各存一份，两文件互写"mirrors the other"。覆盖率断言只查 effect 侧，
   2026-09-12 的三次加固必须手工在两边各改一遍。
   → 已收口到 `scripts/rule_corpus.py` 单一真源；
   `tests/test_rule_promotion_rollback.py::TestCorpusSingleSource` 用**对象同一性**
   （`is`）钉死，并断言两个消费方不再内联字面量。

3. **`run_all.py` 静默跳过测试文件。** 该文件用硬编码清单，
   `tests/test_geo.py`、`tests/test_indexnow.py`、`tests/test_gap_fill.py`
   **长期不在清单里** —— run_all 照报"全绿"，但这三个文件从未被执行。
   测试数从 844 变成 1028 就是证据（184 个测试此前根本不在跑）。
   → 已补登记，并加 `TestRunnerCoverage` 断言：`tests/test_*.py` 与清单双向一致，
   缺登记或登记了不存在的文件都会红。

**仍然不做（明确放弃）**

- `bench/corpus/` 独立目录 + `scripts/bench_rule.py` 的 FP/FN 矩阵。
  `rule_corpus.py` 已经把正反样本固化成单一真源，再拆一个 `bench/` 目录
  是重复造结构；真到需要按规则族细分精确率/召回率时再拆不迟。
  现在的度量是二元（catch / false_positive），不是精确率/召回率 ——
  这个局限是真实的，记录在此，不粉饰。

### 4.2 不要抄

- **Agent 自动构建 Agent**：品类无关。
- **1000+ 模型路由**：我们是安全扫描器，不是推理平台。
- **OpenShell 权限治理 shell**：这是运行时层，与"绝不 spawn 被扫配置"冲突。

---

## 5. 归档里唯一可用的资产：`agent-trust/weekly-suggestions/`

三份文件（`2026-06-18-ecosystem-analysis.md`、`2026-06-22-competitive-analysis.md`、
`2026-06-29.md`）是 AgentTrust 项目的每周竞品扫描。**方法论可复用，数据必须弃用**：

| 缺陷 | 证据 | 教训 |
|---|---|---|
| **纯 star 排序定优先级** | `2026-06-29.md` 把 `Snailclimb/JavaGuide`（静态 Java 知识库）列入 P2 待办，自己备注"与动态 Agent 信任协议无直接集成价值"却仍排在 Top 5 | 排序权重必须是**契合度 × 集成难度**，star 只是曝光代理 |
| **数据快速过期** | `06-18` 记 ECC 198k★ → 实测 225,398；`anthropics/skills` 138k→156k；`obra/superpowers` 240k | 所有 star 数须带**采集日期**，超 30 天视为过期 |
| **自动生成的话术不可直接对外** | "推荐方式：在其文档或 Wiki 中添加安全章节，引用协议规范"——等于请求别人改文档 | 对外材料须人工重写 |
| **健康度评分失真** | `生态健康度 15/100 —— 项目处于零活跃状态（0星0叉）` | 单指标（0 star）不足以支撑 0–100 评分 |

这些与我们的**「假绿三层」**铁律同源：**指标好看 ≠ 事情发生了**。已按此校正
`~/.workbuddy/skills/aishield-ops/references/competitive-landscape.md` §7.14 的数据表述。

---

## 6. adopt backlog（按 ROI 排序，2026-09-16 晚更新）

| # | 项目 | 优先级 | 状态 |
|---|---|---|---|
| 1 | **执行身份护栏**（Shannon root-guard） | P0 | **已落地**：`api/server.py::assert_not_root()` + `tests/test_geo.py` 断言 |
| 2 | **快照 + 回滚**（PenguinHarness RSI） | P1 | **已落地**：`snapshot_current()` / `rollback()` / `--rollback` / `--list-snapshots` / `--ledger`，见 §4.1 |
| 3 | **规则语料单真源**（PenguinHarness，自查衍生） | P1 | **已落地**：`scripts/rule_corpus.py`，对象同一性断言钉死 |
| 4 | **Runner provenance 声明**（AgentShield） | P1 | **已落地**：`mcp-server/README.md` 新增 Provenance & verification 段 + 2 条断言。核对发现 `publish-npm.yml` **早已启用** `npm publish --provenance` 且 `id-token: write` 到位 —— 缺的是文档声明与"无签名版本可静默发布"的告警，不是技术链路 |
| 5 | **记忆边界原则成文**（ECC） | P1 | **已落地**：`docs/memory-boundaries.md`。核对发现一个真实反向问题（见下） |
| 6 | **CI 严重度门禁 exit code**（AgentShield exit 2） | P1 | **已修一个真 bug**：`verdict_from()` 只从三档 `overall_assessment` 反推风险，`risk` 永远到不了 `critical`，于是 **`fail_on: critical` 静默失效**。现改为多来源取最高档；并加 `fail_on` 拼写校验与 SARIF 版本从引擎常量兜底（原写死过期串） |
| 7 | **preflight 失败外显 / 日志脱敏**（Shannon） | P2 | 待办 |
| 8 | **单真源消除 llms.txt 双份**（ECC 反模式） | P2 | 待办 |
| 9 | **正样本分仓避 AV 误报**（Shannon） | P2 | 规模触发后再做 |
| 10 | **竞品数据带采集日期**（归档教训） | P2 | 已在 competitive-landscape.md §7.14 执行 |

### 6.1 两个自查中发现的、原计划里没有的问题

**A. `run_all.py` 静默跳过三个测试文件。** `tests/test_geo.py`、
`tests/test_indexnow.py`、`tests.test_gap_fill.py` 长期不在硬编码清单里，
run_all 照报"全绿"。测试总数从 **844 → 1028** 即证据。
已与 §4.1-3 一并修复并加双向断言。

**B. 我们自己的记忆目录是公开的。** `.workbuddy/memory/` 未被 `.gitignore`
排除（那里只排了 `.workbuddy/*.txt` / `.cache/` / `skills/` / `plugins/`），
15 个文件已在 public 仓库 main 分支。ECC 的做法是 **fail-closed**
（默认拒绝入库，显式例外才进），我们恰好相反。

内容里没有凭证（已全量扫描 76 个记忆文件，11 类凭证模式 **0 命中**），
但含竞品情报与决策理由，属策略层泄露。清理需要 rewrite history，
属破坏性操作 —— **留给人拍板，未擅自改 `.gitignore`**。
已加 `TestMemoryBoundary`：把"泄露策略"降级为"泄露凭证会被 CI 拦下"。

**明确不做**：三 Opus 对抗流水线、Temporal 工作流、worker 容器、Agent 自构建、
1000+ 模型路由、多 harness 适配矩阵、OpenShell 权限 shell——均与
「零依赖 / 可离线 / 绝不 spawn 被扫配置」三条不变量冲突。
另：`bench/corpus/` 独立目录 + `scripts/bench_rule.py` 的 FP/FN 矩阵暂不做，
理由见 §4.1"仍然不做"。

