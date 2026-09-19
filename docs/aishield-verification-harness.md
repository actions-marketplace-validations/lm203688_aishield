# AIShield Verification Harness

> 版本：v1 · 2026-09-19 · 适用：`data/radar_rules.json` 规则库、静态基线、Skill 规则族
> 定位：把「六道闸门 + 零误报 + 效果度量 + 可回滚」正式命名并文档化，供外部引用。

---

## 1. 这是什么，以及为什么需要给一层东西起名字

AIShield 早就在做验证：一条规则想从情报候选走进 `data/radar_rules.json`，要过六道闸门，
要在良性语料上零误报，要在攻击语料上真能命中，出事了还能一键回滚。但这些能力此前
散落在 `scripts/promote_rule.py`、`scripts/radar_effect.py`、`scripts/audit_rules.py`
和一堆测试里，**没有名字、没有对外契约**。

没有名字的后果是具体的：

- 外部引用不了。别人想写「一个 agent 产出的规则该不该信」时，找不到一个可链接的对象。
- 内部也守不住。哪天有人绕过 `promote_rule` 直接手改 JSON，没有任何文档层面的东西
  被违反 —— 只有测试会红，而测试可以被改成绿色。

命名参照 PrimeIntellect `prime-agent` 的 **Continual Harness**：它把对
`histories / memories / skills / prompts` 的每一次写入都做成**带 trigger + intended
effect 且可回滚**的版本化精炼。本文件把同一套语义落到**规则**上。

一个必须先讲清楚的边界：Prime Agent 是**能力** harness（让模型更强），
AIShield 是**信任** harness（让 agent 更可信）。两者目标正交 —— 它是 harness 生态里
需要被验证的一方，我们是验证方。因此这里**不**借用它的模型侧机制，只借用
「写入必须可解释、可撤销」这一条工程纪律。

---

## 2. 四段式：execution / recovery / verification / resource accounting

沿用 Prime Agent 的标准切法，对应关系如下。

| 段 | 语义 | 本项目落点 |
|---|---|---|
| **Execution** | 一次改动被真正应用 | `promote_rule.promote()` 写入 `data/radar_rules.json` |
| **Verification** | 应用之前先证明它该被应用 | 六道闸门（§3）+ 效果度量（§4） |
| **Recovery** | 应用之后可以撤销 | 晋升前快照 + 一键回滚（§5） |
| **Resource accounting** | 每一次改动有台账 | `ledger_append()` 追加 JSONL 台账（§6） |

---

## 3. Verification：六道闸门

实现在 `scripts/promote_rule.py::validate()`。任一不过，候选**绝不落库**。

| # | 闸门 | 为什么是这一条 |
|---|---|---|
| 1 | `status == "ready"` | 未填完的候选（`draft`）不得进入。人工确认必须是一次显式动作，不能靠"反正它看着挺完整" |
| 2 | 必填字段完整：`signal` / `attack_category` / `rules` | 来源、类别、规则三者缺一不可 —— 缺 `signal` 的规则未来无法回答"为什么有它" |
| 3 | 无 `TODO` 占位符（pattern 与 description） | 占位符进库等于埋一条永远不命中或永远命中的规则 |
| 4 | 严重度 ∈ 合法集合 | 未定义的严重度会污染评分权重 |
| 5 | 正则**可编译**、**不过宽**、长度 ≥ 6 | 「过宽」有客观判据：能匹配空串或单字符 `a` 即判过宽。宁可拒一条窄的，也不放一条到处命中的 |
| 6 | **不与现有规则重复 + 在 `BENIGN_CORPUS` 上零误报** | 决定性闸门。**误报比没有规则更糟** —— 一个总在叫的安全工具会被直接卸载，届时它连真问题也拦不住 |

闸门 6 里的「零误报」不是抽查，是**全量**：`BENIGN_CORPUS` 每一条都要逐个过。
该语料刻意收录了**防御工具的自我描述**（含 `injection` / `jailbreak` / `credential
theft` 等词）。这类文本是误报重灾区 —— 一个讨论 prompt injection 的扫描器文档，
和一个真的在投毒的配置，字面上可以很接近。裸关键字规则必然在这里翻车，这也是
「裸关键字必须配正样本」这条项目铁律的来源。

### 3.1 shadow 与 enforce 双模式

`promote_rule.py --shadow` 允许闸门**只观测、不改变**地连续运行。

三种判定，严格度递增：

| 判定 | 条件 | 处置 |
|---|---|---|
| `promote` | 六道闸门全过，且在 `ATTACK_SAMPLES` 上至少命中一条 | 放行 |
| `warn` | 闸门全过，但攻击语料上**零命中**（`catch=false`） | 默认放行 + 大声告警；`--strict` 可收紧为拒绝 |
| `refuse` | 任一闸门失败 | 绝不落库，候选归档到 `shadow-refused/` |

`catch=false` 为什么不直接当拒绝：雷达规则来自**新**信号，而 `ATTACK_SAMPLES` 是
固定语料 —— 全新攻击类型天然不在其中。把零命中一律当硬拒绝会让整个循环停摆
（假阴性陷阱）；当安全问题又是过度收紧。所以它是 warn，不是二元判定。

> 借的是 pi-jev 的**模式区分**，明确不借它的默认值：pi-jev 的错误路径全部
> fail-**open**（缺 key / 超时 / 429 一律放行工具调用）。AIShield 的品牌是 fail-closed，
> 因此 shadow 只用于观测，判定失败永不降级成放行。

---

## 4. Verification 的另一半：效果度量

闸门证明「落地时是对的」，`scripts/radar_effect.py` 回答「落地之后还有效吗」。

| 指标 | 含义 |
|---|---|
| `catch` | 该规则能命中多少条攻击语料 —— 恒为 0 即**死规则**（占着位置，不提供保护） |
| `false_positive` | 该规则在良性语料上命中多少条 —— 必须恒为 0 |
| `stale_allowlist` | 白名单里是否还留着已经不需要豁免的条目 |

`data/state/radar_effect.json` 是这套度量的落点。它和闸门是**互补**的：闸门是
进门时的一次性检查，效果度量是持续回归 —— 语料会扩、外部世界会变，今天 19/19 命中的
规则，明天可能因为语料增补而暴露漏检。

**公开可复跑的第二把尺子**：`scripts/benchmark.py`（安全基准 v1）给出
固定语料 + 参数化变体下的召回与误报率，输出确定性 JSON。任何人都能 clone 下来
得到同一组数字 —— 一个不可复现的分数是宣传语，不是基准。

---

## 5. Recovery：一次误晋升必须可撤销

晋升前先 `snapshot_current()` 把当前 `data/radar_rules.json` 整体快照下来，快照
目录由 `prune_snapshots()` 控制数量上界。这条设计针对的失败模式很具体：

> 一条规则在闸门处表现良好，上线后却在真实流量里频繁误报。此时需要的是
> **回到上一状态**，而不是在线上一边被误报刷屏一边手改正则。

回滚是显式的、可核对的，不是"再改一次把它改回去"。

---

## 6. Resource accounting：每次改动留台账

`ledger_append()` 以 JSONL 追加记录每一次 `promote` / `shadow` / `rollback`：
来自哪个候选文件、落库了哪些 pattern、攻击类别、对应的快照文件名、当时的规则总数。

追加而非覆盖，是为了让**"规则库是怎么长成今天这样的"**成为一条可回溯的序列。
配合 §3 的 `trigger` / `intended_effect` 字段（见下），任何一条规则都能回答三个问题：
它从哪来、当初为什么加、期望它改变什么。

### 6.1 provenance 的字段契约

`data/radar_rules.json` 的 `provenance` 为每条规则记录：

| 字段 | 含义 | 状态 |
|---|---|---|
| `signal_title` / `signal_url` / `source` | 来源情报 | 必需 |
| `attack_category` | 攻击类别 | 必需 |
| `promoted_from` | 晋升自哪个候选文件 | 必需 |
| `drafted_at` | 起草时间 | 必需 |
| `trigger` | **这次写入由什么触发**（来源情报，或"仅凭候选文件"） | 2026-09-19 新增 |
| `intended_effect` | **期望它产生什么效果**（要检出哪类此前漏掉的载荷，且不得误报良性语料） | 2026-09-19 新增 |

### 6.2 结论层的不变量：risk 不得轻于 finding

规则闸门保证的是「规则按标准进入规则库」。但**结论**是另一层：一个分数、一个风险
标签，agent 会直接照它行动。这一层实测出现过一次**假安心**——

`aishield-digest/v1` 的风险标签原本只由分数分档决定（`>= 80` → `safe`）。high 权重
8 分，于是两条 high 的配置得 84 分，摘要输出 `risk: "safe"` 的同时并列
`severity_counts: {"high": 2}`——一份带明文 HTTP 远程传输的配置被标成"安全"。
下游只读 `risk` 字段，读到的就是这个字面意思。

现在 risk 取「分数档」与「实际最严重 finding」中**更重**的一方，并额外输出
`worst_severity` 让调用方看见原因。分数本身照旧输出（它是既有的项目级约定），只是
不再单独决定风险标签。

这条被写成契约测试（`tests/test_trust_digest.py::TestRiskFloor`，7 项），因为它是
**结论层的诚实性**，不是实现细节：我们宁可说"high"，也不说一个下游会照做的谎。

同一缺陷同类也存在于 `/scan` 的 prompt 扫描路径（`api/server.py::check_prompt_injection`）：
单条 critical 只扣 30 分 → 70 分 → 旧分档会给出 risk `"low"`；一条 high（扣 15）单独
出现则 85 分 → `safe: true`。该路径已同样加上下限，且 `safe` 改为由 `risk` 派生
（同一个结论只有一个真值来源，不再独立算一次 `score >= 80`）。
回归断言见 `tests/test_security.py::TestPromptInjectionDetection.test_detect_bypass_security`。

> 这属于本项目的一条经验：**结论层缺陷是群居的**。修掉摘要里的那一处，下一处会
> 在另一个入口顶着 —— 所以发现一处后必须横向扫一遍同类标签，而不是只修被撞见的那一个。

**向后兼容**：缺失 `trigger` / `intended_effect` 的老记录视为 legacy，加载器照常接受、
不隔离、不告警 —— 由 `tests/test_provenance_audit.py::TestLegacyDataStillLoads` 钉住。
一个"加了字段就读不了老文件"的改动，会把小升级变成事故。

---

## 7. 怎么跑

```bash
# 规则晋升（默认 shadow：只观测不落库）
python scripts/promote_rule.py --shadow

# 静态基线审计（同标准复查基线规则）
python scripts/audit_rules.py

# 效果度量：catch / false_positive / 死规则
python scripts/radar_effect.py

# 对抗式评审：候选按同一标准被反向挑刺
python scripts/adversarial_review.py

# 安全基准 v1（确定性，可第三方复跑）
python scripts/benchmark.py --json
python scripts/benchmark.py --markdown --out docs/benchmark/v1.md

# 全量回归（含上述所有契约测试）
python tests/run_all.py
```

---

## 8. 诚实的边界

这一节不是免责声明，是把「这层验证**不**覆盖什么」写清楚，免得被当成它覆盖不了的东西。

1. **不覆盖语义级攻击。** 六道闸门验证的是正则规则。一个措辞完全合规、只在语义层面
   实施操纵的载荷，正则抓不到 —— 那需要模型侧判断，属于另外的层次。
2. **不覆盖运行时行为。** 规则库验证的是「静态文本里能不能看出问题」。agent 运行起来
   之后真的做了什么，不在这一层的视野内（那是 telescope 一类行为可观测性的地盘）。
3. **不宣称第三方审计。** 这是一套**自证**机制：我们的闸门、我们的语料、我们的度量。
   它能证明「我们按一套公开的、可复跑的标准检查了自己」，**不能**替代独立第三方的
   security review。任何把它读成后者的情况都属于误读。
4. **语料是有限的。** `BENIGN_CORPUS` 与 `ATTACK_SAMPLES` 都是固定集合，
   `catch=false` 的 `warn` 判定正是为了不假装它们覆盖了全部现实。
5. **确定性 ≠ 正确性。** `benchmark.py` 保证你跑出和我一样的数字；它不保证那个数字
   本身足以支撑某个安全结论。数字可比，结论仍需人来下。

---

## 9. 引用

对外引用本层时可用的名字与形态：

- 名称：**AIShield Verification Harness**（六道闸门 + 效果度量 + 可回滚 + 台账）
- 机器可读的规则溯源：`data/radar_rules.json` → `provenance`
- 机器可读的规则元信息：`scanner.rules.get_radar_rules_meta()`
- 确定性基线与分数：`docs/benchmark/v1.md`、`python scripts/benchmark.py --json`
- 信任凭证信封：`docs/trust-attestation-spec.md`（`aishield-trust/v1`）
- 紧凑信任摘要：`aishield-digest/v1`，见 `api/trust_api.py::trust_digest`
  - 输出契约：`no_spawn_guarantee` / `offline_scan` 恒真；`top[]` 永不回传 evidence；
    `risk` 不得轻于 `worst_severity`（见 §6.2）
  - 端点：`GET|POST /api/v1/trust/digest`（别名 `/api/v1/digest`）；MCP 工具 `aishield_digest`
