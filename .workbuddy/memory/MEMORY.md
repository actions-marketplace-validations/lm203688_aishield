# AIShield 长期记忆（2026-09-20，限 3K）
> 细节看按日日志。

## 定位
Agent 原生 AI 工具安全扫描器（MCP/skill/GPTs/prompt），对齐 OWASP MCP Top10 + ASI01–10，
零依赖。`lm203688/aishield`(public)，npm **4.3.0**。**不变量：绝不 spawn 被扫配置的命令。**

## 规则数（勿引用旧数）
**235 = 静态 208 + 生成 8 + 雷达 19**（live）；Skill **241**（2026-09-20 实测纠正，旧记 244 是错的）。
看 `/api/v1/health`.`rules_breakdown`。**规则数已门禁化**：`scripts/rule_count_gate.py`
（`--check`/`--sync`，权威值运行时取不写死，CI 已挂 `ci.yml`，47 声明位受约束）+ 31 测试。
坑：声明位须「先锚语境再校数」——散文里 `238` 可能是 `rgba(238,69,96)`；`(?<!Top)` 挡不住
引擎从数字内部起跳（`Top 10`→`Top 1235`），捕获组前缀必须 `(?<!\d)`；分解行豁免须拆
`ROW_MARKERS`（整行）与 `CELL_MARKERS`（单点+CELL_WINDOW=14），否则行内话题提及会把同行
真声明位一起放走（smithery.yaml 假绿）。

## 基准（勿引用 96%/98%）
现行 `scripts/benchmark.py`：**主口径 serious_only：45/50 = 90.0% 召回、0/45 = 0.0% 误报；
副口径 any_finding：规则覆盖 50/50 = 100.0%**。两平面**同口径**（都 serious_only）总分才可相加；
副口径只算覆盖率、不配误报率（良性 low/info 是信息性标注，给它算 fp 会得到 40%+ 的废数）。
指令面 24/28、配置面 21/22；检出缺口 5 条已公开列在 v1.md。
**is_doc 一刀切降级已改**（2026-09-20）：analyze() 原对 .md/.txt 把 critical/high 降 low，
而注入的天然栖息地就是文本 → 指令面 serious-only 召回曾 0/28、旗舰样本只有 low。
现按**规则语义**豁免（MCP06 注入类 + ASI* 整组），**不是按 OWASP 类别** —— MCP06 里混着
「持久化/自启动指令」cron 类，文档给 cron 示例是正常实践，整类豁免会把 guardrail-harness 的
deny 演示样本报成阻断项。引用抑制另补了中文标记（例如/示例/检测/拦截/阻止/威胁模型/测试用例/
测试样本/已知攻击/已知漏洞）：词表此前只有英文，中文防御文档整块盲区。
指令面喂样路径从 `sample.md` 改 `skills/payload_NN.md` —— 生产路径
`server.check_prompt_injection` 对提示词文本不施加文档降级，`sample.md` 测的不是生产行为。
`tests/test_benchmark.py` 的 `--fail-under-recall 1.5` 是**故意**测门禁会红，不是脚本瑕疵
（2026-09-20 守夜报告误诊）。MIN_RECALL=0.85 / MIN_COVERAGE=1.00。

## 线上拓扑
CF Named Tunnel（cloudflared→:8450→api/server.py），前缀 **`/api/v1`**，无 CF Pages。
部署身份 **root** → API 启动路径必须 `AISHIELD_ALLOW_ROOT=1`（漏一处即 502 静默停机）。
**禁 `pkill -f cloudflared`**（会杀 healthlens tunnel）→按 PID 停。
`deploy-server.yml` 仅 `workflow_dispatch`（03:17 spine 调用）；`pages.yml` 走 `push: docs/**`。

## 铁律
- **假绿六层**：吞异常／传输层 `if not res: continue`（退化成 `[]`，最隐蔽）／`| tail` 退出码恒 0
  （需 `pipefail`）／mock 外部 IO 须断言请求路径／`echo "X=$?"` 抢占退出码／`notify()` 恒 0
  （已修 `--fail-on-undelivered`+未送达台账）。**群居的，修一处下一处顶上**。
- 退出码显式传导 `rc=$?`→`exit $rc`；`run_all.py` 共 **1230 tests**（2026-09-20）。
- 契约测试坑：注释字面量致子串断言误报→先剥注释（辅助函数自身需正向对照）；
  `addCleanup(patcher.stop())` 传的是 **None**。
- 禁 `|| true`/2>/dev/null 吞门禁；404 先读 body；实地 curl；本地绿≠CI 绿；
  `paths-ignore` 提交不触发 CI。
- 雷达规则须含 `|` 或有界 `.{n,m}`，裸关键字留 draft；**误报比没有规则更糟**，必配正样本。
  `BENIGN_CORPUS` 含防御工具描述→裸关键字必误报，须区分「话题提及」与「祈使式执行」。
- **结论层铁律**：`risk`/`safe` **不得轻于实际最严重的 finding** —— 取「分数档 vs 最严重
  finding」更重者 + 输出 `worst_severity`；布尔结论须由等级字段派生（勿独立再算 `score>=N`）；
  `low/info` 不设下限。路径 `trust_api._risk_from_score` / `server.check_prompt_injection`。
  **群居缺陷**：修一处必 grep 同类标签一次修完；测试要断言**字段间自洽**而非各自取值。
- GHA `needs` 依赖被跳过的 job 会一并跳过→作业内自闭环；`set +e` 脚本必须 `if ! func; then`；
  删除守卫：`rm`/`os.remove` 被吞、`mv` 不受限。
- 推送用 `_push_batch.py`（多文件一个 commit）；新测试与 `run_all.py` 登记**须原子推送**；
  `gh_push.py` 首参是 message **无 `-m`**；Contents API 无法 amend。根目录探针统一 `_` 前缀。
- **push 与 workflow_dispatch 非原子**：dispatch 部署「那一刻」的 main HEAD。实测 dispatch
  早于目标 commit 25 秒 → run 绿但部署旧 sha，线上仍缺修复。push 后先取 main HEAD 再 dispatch，
  并核对 run `head_sha` 含目标 commit。
- 测试假 token 触发 secret scanning 422 → 用 `bypass_placeholders.placeholder_id`；不得破坏
  `redact()` 最小长度断言。告警出站**每个出口都要脱敏**；台账按 fingerprint **upsert 非 append**。
- 本机**无 `.git`**→`git status`/`check-ignore` 全假阴性；.gitignore 用 Python 语义匹配验证。
  `mcp-server/dist/` 在 .gitignore **但已跟踪**→改动照样要推（`tsc` 重建）。
  MSYS2：argv POSIX 路径被转换、env 里的不会；`/tmp` 不可靠。

## 自动化 / 分发
**20 workflow**，03:17 spine 串行 9 子；5 本地自动化（守夜 08:30 / 竞品 周一 / Radar 02:00 /
分发 周六 / 周报 周日）职责互不重叠无需融合。`self_scan.py` 需 `blocking_unsuppressed=0`
+`stale_allowlist=0`；**不在任何 CI 里** → 守夜是台账外自检唯一执行者。
已上架 Glama+npm；Marketplace 须独立仓 `lm203688/aishield-action`。
- **workflow permissions 铁律**：会 `git push` 的 workflow 必须 `contents: write` ——
  `geo-indexnow` 用 `contents: read` 致心跳 push 403 重试 5 次后 exit 1，9/9 全红
  （核心提交其实都成功）。装饰性心跳 push 加 `|| true`。

## 待办
- 🟡 吊销旧 CF token（曾硬编码进 public 仓历史）+ aishield.tools CF Pages Retry。
- 🟡 4 条 skill 指令载荷候选待评审（`scanner/_proposed/...instruction_payload__c84a4b.json`）；
  `promote_rule.py --shadow` 报 2 条 catch=0 死规则待拍板。
- 🟡 `.workbuddy/memory/` 在 main 被跟踪，清理需 rewrite history。
- 🟡 配置面 `axis_credential=generic_password` 3/4、`axis_launcher=uvx_auto_install` 3/4
  仍 75%：唯一公开检出缺口 `cfg-mal-uvx_auto_install-generic_password`（最高只到 medium）。
- 🟢 已完成（2026-09-20）：规则数门禁（47 声明位 + 31 测试 + CI 挂点）；docs 对外通道
  （`api/docs_render.py` 零依赖渲染 + `server.py` `/docs`、`/docs/<rel>` 路由，102 篇可列）；
  基准语料扩充（BENIGN 20→30、配置良性 6→10）+ 修正 ATTACK_SAMPLES[2] 叙述体误标；
  **基准双口径统一**（serious_only 45/50=90% + any_finding 覆盖 50/50=100%）；
  **is_doc 注入豁免 + 中文引用标记 + 指令面喂样路径修正**（指令面 serious 0/28 → 24/28）。
