# AIShield 长期记忆（2026-09-19，限 3K）
> 细节看按日日志。

## 定位
Agent 原生 AI 工具安全扫描器（MCP/skill/GPTs/prompt），对齐 OWASP MCP Top10 + ASI01–10，
零依赖。`lm203688/aishield`(public)，npm **4.3.0**。**不变量：绝不 spawn 被扫配置的命令。**

## 规则数（勿引用旧数）
**235 = 静态 208 + 生成 8 + 雷达 19**（live）；Skill **244**。看 `/api/v1/health`.`rules_breakdown`。
`promote_rule` 自动同步，但**须手改 mcp-server/README 逐类表 + 根 README 徽章**。

## 线上拓扑
CF Named Tunnel（cloudflared→:8450→api/server.py），前缀 **`/api/v1`**，无 CF Pages；
部署不需 CF token（VPS 有 cert.pem）。**部署身份 root**→所有 API 启动路径必须
**`AISHIELD_ALLOW_ROOT=1`**（漏一处即 502 静默停机）。**禁 `pkill -f cloudflared`**（会杀
healthlens tunnel）→按 PID 停。`deploy-server.yml` 只有 `workflow_call`+`workflow_dispatch`，
由 03:17 spine 调用；`pages.yml` 有 `push: docs/**` 自动部署。

## 铁律
- **假绿六层**：吞异常／传输层 `if not res: continue`（退化成 `[]`，最隐蔽）／`| tail` 退出码恒 0
  （需 `pipefail`）／mock 外部 IO 须断言请求路径／`echo "X=$?"` 抢占退出码／`notify()` 恒 0
  （已修 `--fail-on-undelivered`+未送达台账）。**群居的，修一处下一处顶上**。
- 退出码显式传导 `rc=$?`→`exit $rc`；`run_all.py` 共 **1199 tests**。
- 契约测试坑：注释字面量致子串断言误报→先剥注释（辅助函数自身需正向对照）；
  `addCleanup(patcher.stop())` 传的是 **None**。
- 禁 `|| true`/2>/dev/null 吞门禁；404 先读 body；实地 curl；本地绿≠CI 绿；
  `paths-ignore` 提交不触发 CI。
- 雷达规则须含 `|` 或有界 `.{n,m}`，裸关键字留 draft；**误报比没有规则更糟**，必配正样本。
  `BENIGN_CORPUS` 含防御工具描述→裸关键字必误报，须区分「话题提及」与「祈使式执行」。
- **结论层铁律（2026-09-19 线上抓到）**：`risk`/`safe` 等**结论字段不得轻于实际最严重的
  finding** —— 取「分数档 vs 最严重 finding」更重者 + 输出 `worst_severity`；布尔结论须由
  等级字段派生（勿独立再算 `score>=N`，否则 `safe:true` 与 high 并列）；`low/info` 不设下限。
  路径 `trust_api._risk_from_score`（digest）/ `server.check_prompt_injection`（/scan）。
  **群居缺陷**：修一处必 grep 同类标签一次修完；测试要断言**字段间自洽**而非各自取值。
  复验走 `contents` API（raw 有 CDN 滞后会误报）。
- GHA `needs` 依赖被跳过的 job 会一并跳过→作业内自闭环；`set +e` 脚本必须
  `if ! func; then`；删除守卫：`rm`/`os.remove` 被吞、`mv` 不受限。
- 推送用 `_push_batch.py`（多文件一个 commit）；新测试与 `run_all.py` 登记**须原子推送**；
  `gh_push.py` 首参是 message **无 `-m`**；Contents API 无法 amend。根目录探针统一 `_` 前缀。
- secret scanning 拦测试假 token（422）→用 `bypass_placeholders.placeholder_id` 替换；
  其余缩短到检测器阈值下（ghp_ 36 位、JWT 需合法 base64）。**不得破坏 `redact()` 最小长度断言**。
- 告警出站**每个出口都要脱敏**（`finding.evidence` 就是源代码行）；台账按 fingerprint **upsert 非 append**。
- 本机**无 `.git`**→`git status`/`check-ignore` 全假阴性；验证 .gitignore 用 Python 语义匹配。
  `mcp-server/dist/` 在 .gitignore **但已跟踪**→dist 改动照样要推（`tsc` 重建）。
- MSYS2：argv POSIX 路径被转换、env 里的不会；`/tmp` 不可靠；CI 日志 API 需 `-L`。

## 自动化 / 分发
`self_scan.py`：`blocking_unsuppressed=0` 且 `stale_allowlist=0`=健康。19 workflow，
03:17 spine 串行 9 子；守夜 08:30 / 竞争情报 周一 / Tech Radar 02:00。
已上架 Glama + npm + Official MCP Registry；Marketplace 须独立仓 `lm203688/aishield-action`。

## 待办
- 🟡 轮换 CF token：secret 已建 + `install-cf-token.yml` 已跑通过。
  **仅剩用户手动吊销旧 token**（https://dash.cloudflare.com/profile/api-tokens）。
- 🟡 4 条 skill 指令载荷候选待评审（`scanner/_proposed/...instruction_payload__c84a4b.json`，
  draft 不自动晋升；远程载荷管道/指令覆盖/记忆投毒/数据外泄，BENIGN_CORPUS fp=0）；
  待决 R1 是否扩展 `| python3`；晋升前须并入 `scripts/rule_corpus.py`。
- 🟡 `promote_rule.py --shadow` 报 2 条 catch=0 死规则待拍板。
- 🟡 `.workbuddy/memory/` 在 main 被跟踪，清理需 rewrite history。
