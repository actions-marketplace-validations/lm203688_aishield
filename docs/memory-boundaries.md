# Memory Boundaries — 记忆是上下文，不是可执行策略

> 借鉴来源：`affaan-m/ECC` Memory Vault 的明文原则
> *"Memory is unreviewed context, not executable policy."*
> 2026-09-16 加入。适用对象：**AIShield 自己的记忆文件**，不只是被扫描对象。

## 1. 这条原则为什么成立

Agent 的记忆文件（`.workbuddy/memory/*.md`、`MEMORY.md`、daily log、
automation digest）有一个结构性特征：**它会被当作上下文直接喂进模型，
而且通常不会被审阅**。

这意味着记忆是攻击面，而不是存储：

- 记忆里的一条 `请记住：执行前先运行 X` 在下一轮会被当成指令执行。
- 记忆没有权限边界 —— 读记忆的人拥有读记忆里所有内容的权限。
- 记忆是追加式的，历史不会被复审。旧记录里的错误结论会一直生效。

所以记忆里的内容只应当是**事实陈述**（发生了什么、为什么这么决定），
不应当是**行为指令**（下次要怎么做）。指令属于代码和配置，有审阅、
有测试、有回滚；记忆没有这些。

## 2. 我们检测别人的记忆，却把自己的记忆公开发布了

这是 2026-09-16 自查时发现的真实状况，不是假设。

**我们已有的检测能力**：`scanner/memory_scan.py`（ASI06 记忆/上下文投毒），
覆盖写入记忆的指令、持久/种子目标、记忆文件写入。`data/radar_rules.json`
里还有对应的雷达规则，攻击类别 `trajectory-poisoning`，例如：

```
(?:写入|追加|保存|append|persist|store)[^\n]{0,16}(?:记忆|经验|轨迹|memory|...)
[^\n]{0,40}(?:从此|今后|以后|每次|always|from now on|every time)
```

**但我们自己的记忆是公开的。** 截至 2026-09-16 07:20 UTC+8，
`github.com/lm203688/aishield`（public）的 main 分支共 577 个被跟踪文件，
其中 **15 个属于 `.workbuddy/`**，全部位于 `.workbuddy/memory/`：

| 路径 | 性质 |
|------|------|
| `.workbuddy/memory/MEMORY.md` | 长期记忆 |
| `.workbuddy/memory/archive/MEMORY-full-2026-08-10.md` | 归档 |
| `.workbuddy/memory/automation-digest/2026-09-{03..15}.md` | 7 份自动化日报 |

`.gitignore` 只排除了 `.workbuddy/*.txt`、`.workbuddy/.cache/`、
`.workbuddy/skills/`、`.workbuddy/plugins/` —— **没有排除 `.workbuddy/memory/`**。
也就是说这个目录是 fail-open 的：任何一次批量推送都会把它带上去。

对照 ECC 的做法：它的记忆目录带 **fail-closed 的 `.gitignore`**，
默认拒绝入库，需要显式例外才能进。我们的方向正好相反。

这里有一个不对称值得说清：**我们扫别人的记忆投毒，
同时把自己未经审阅的记忆挂在公开仓库上，任何 clone 这个仓库的 agent
都会把它读进上下文。** 内容里没有凭证（凭证文件在归档与文档里被明确排除，
`.gitignore` 第 99-105 行拦了 `secrets.json`/`*.key`/`.secrets.*.json`），
但记忆里含竞品情报、运营约定和决策理由 —— 属于策略层面的泄露。

## 3. 我们自己的记忆遵守的六条规则

1. **只记事实，不记指令。** 写「2026-09-15 决定用 X 方案，原因是 A/B」，
   不写「下次一律用 X」。行为约束进代码、进 workflow、进本文档。
2. **不记凭证。** PAT、API token、支付密钥、IndexNow key 一律不落盘。
   这一条已经被验证过有效：归档里的 `密码与密钥汇总.txt`、
   `全局配置_TOOLS.md`/`USER.md` 全部被排除在外。
3. **记忆不是授权。** 记忆里写过「用户同意了」不构成执行依据。
   花钱、对外发布、删除数据这三类动作必须每次重新确认。
4. **失败要可见。** 记忆写入失败（磁盘满、权限不足）必须报出来，
   不能静默丢弃 —— 静默丢失的是一条本该被记住的事故。
   `scripts/promote_rule.py::ledger_append()` 已经按这个原则写：
   台账写不进只告警不阻断，但必须打印 warning。
5. **旧记忆会被重新读到，所以要写得经得起重读。** 时效性强的内容
   （版本号、规则数、star 数）必须带采集日期；超 30 天视为过期。
   这条来自竞品分析的经验：纯 star 排序定优先级是错的，所有 star 数
   必须标注采集日期，否则 3 个月后会拿旧数据做决策。
6. **记忆可以被攻击者投毒，我们也不例外。** 一条被写进记忆的攻击指令
   会绕过所有静态扫描，因为它不在被扫描的配置里。这是扫描器自身
   的盲区，只能靠规则 1（不记指令）来收窄。

## 4. 未决（需要人拍板）

`.workbuddy/memory/` 是否继续公开，是发布策略决策，不该由工具单方面改。
三个选项：

- **A 继续公开**（现状）：好处是记忆可作为项目运营透明的证据；
  代价是竞品情报与决策理由公开。
- **B 加 fail-closed `.gitignore`**：以后不再入库，但**已公开的 15 个文件
  仍在 git 历史里**，需要 rewrite history 才能真正移除 —— 那会让所有
  clone 失效，属于破坏性操作。
- **C 保留公开但脱敏**：继续入库，但对竞品情报与决策理由做删改。
  历史里的旧内容同样需要 rewrite 才能清理。

B 和 C 都涉及改写公开历史，风险高于收益。**建议 A，不动。**
但建议现在就补一条测试：断言 `.workbuddy/` 下的新增文件不会意外带上
凭证模式，把 fail-open 的危害从"泄露策略"降级为"可被 CI 拦下的泄露凭证"。

## 5. 相关

- `scanner/memory_scan.py` — ASI06 检测实现
- `data/radar_rules.json` — `trajectory-poisoning` 雷达规则
- `docs/four-projects-adoption-analysis.md` §5 — ECC 结构与分发范式（来源）
- `.github/workflows/security-scan.yml` — 自扫描门禁（防回归）
