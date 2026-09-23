# AIShield 长期记忆（2026-09-22，限 3K，精简版）
> 细节/坑例见按日日志 `automation-digest/YYYY-MM-DD.md` 与 `automations/*/memory.md`。

## 定位
Agent 原生 AI 工具安全扫描器（MCP/skill/GPTs/prompt），对齐 OWASP MCP Top10 + ASI01–10，零依赖。
`lm203688/aishield`(public)，npm **4.3.0**。
**核心不变量：绝不 spawn 被扫配置里的命令**（自证 `scripts/prove_isolation.py`）。

## 规则数（勿引用旧数）
**235 = 静态 208 + 生成 8 + 雷达 19**（live，看 `/api/v1/health`.`rules_breakdown`）；Skill **262**（SKILL_EXTRA 27 条，2026-09-22 加 Agent 支付/预算攻击面 5 条）。
**规则数已门禁化**：`scripts/rule_count_gate.py`（`--check`/`--sync`，CI 挂 `ci.yml`，47 声明位 + 31 测试）。
声明位坑：散文里 `238` 可能是 `rgba(238,69,96)`；分解行豁免须拆 `ROW_MARKERS`(整行)/`CELL_MARKERS`(单点+CELL_WINDOW=14)。

## 基准（勿引用 96%/98%）
`scripts/benchmark.py` 主口径 **serious_only：45/50=90.0% 召回、0/45=0.0% 误报**；副口径 any_finding：覆盖 50/50=100%。
两平面同口径才可相加。MIN_RECALL=0.85 / MIN_COVERAGE=1.00。
**is_doc 一刀切降级已改**（2026-09-20）：按规则语义豁免 MCP06 注入类 + ASI* 整组；指令面喂样从 `sample.md` 改 `skills/payload_NN.md`。

## SKILL_EXTRA_RULES（27 条，2026-09-22）
七框架：供应链 / 上下文劫持 / Harness 元能力 / 记忆篡改 / 中文变体 + benchmark 声称(info) + 桌面驱动(high×2) + **Agent 支付/预算攻击面**(critical×2 + high + critical×2，借鉴 AIsa AgentPay Guard)。
正则坑：中文汉字在字符类外是 `\w`，边界匹配 ASCII 前必须 `\b`；`绕过(沙箱|安全|护栏|审批)` 会误升 critical，已收窄到 sandbox/approval/credential-scrub 特有词；数字匹配 `\d{4,}` 抓不到带千位分隔符的 $50,000，须 `\d[\d,]*\d{3,}`；「提及 x402/USDC ≠ 执行 x402/USDC」，规则要求 x402 后面必须紧跟 payment/endpoint/wallet 等具体对象或 "to pay/use/call" 动作动词，防御文档中"参考 x402 协议"不算。

## MCP SEP-2640 manifest 扫描器（2026-09-22 新增，独立于 SKILL_EXTRA）
`scanner/mcp_manifest_scan.py` 处理 `.mcp/manifest.json` / `.well-known/mcp.json` / `.well-known/agent-card.json`（SEP-2640 官方收编 Skills 扩展）。
5 项结构化检查：过度代理 scope（critical）/ 供应链执行 installCommands（high）/ mcpServers 明文 token（high）/ 签名缺失（medium）/ 过期缺失（low）。
强标记识别：`manifestVersion`/`schemaVersion`/`requiredScopes`/`requiredTools`/`installCommands`（避免误伤普通 JSON）。
危险 scope 关键词：wallet/payment/spend/finance/x402/stablecoin/desktop/screen/mouse/keyboard/admin/root/sudo/privileged/system/shell/credential/secret/privatekey。
`_has_approval_declared()` 识别 `approval`/`requireApproval`/`consent`/`humanInLoop`（对齐 AIsa AgentPay Guard quote-first）。
集成到 `workspace_scan.py`：`collect_manifest_files()` + MANIFEST_GLOBS 7 项 + ENGINES_REUSED 加 mcp_manifest_analysis，SCANNER_VERSION → 4.0-preflight.4。
27 项测试（tests/test_mcp_manifest_scan.py）全绿，良性样本（SARIF/OWASP/普通 JSON/普通 MCP 配置）均不误判。

## 架构方向：promote 门控 → verifier-based（2026-09-21 立项，未落地）
静态规则表 → 候选经独立 verifier 跑真实环境、通过才沉淀（Mano-P 2.0 实证 verifier 优于规则表）。
**2026-09-23 反证补充**：拿 System One 决策模型（TypeSafe Jev）当 verifier 试过一次，结论是
**一个定型 head 只能裁决一个同构问题，不能统一裁决异质规则族**（实测 6/6 漏判全是"非指令"类
告警：凭证泄露/护栏自改，被拿 `live_instruction` 当通用闸门误杀）。做 verifier 必须**按规则族配问题**。
详见 `docs/harness-measurement/2026-09-23-typesafe-jev-citation-adjudication.md`。

## 外部服务：TypeSafe Jev（System One 决策模型，2026-09-23 起 2 天免费）
`POST https://api.typesafe.ai/v1/systemone`，`Bearer` 密钥存 `~/.config/typesafe/credentials.json`（仓外）。
`choice`≤255 选项 / `score`**≤10 等级（11 直接 400）** / `noul`=P(true)。$42/十亿输入 token，输出免费。
**两个硬坑**：① curl 打不通该域，必须用 Python urllib；② 请求体含**反引号包裹的 `curl`/`wget` + URL**
会被边缘 **Cloudflare 403**（HTML 质询页，非 JSON 错），100% 可复现——即最典型的 agent 供应链攻击
载荷发不进去。客户端 `scripts/typesafe/jev_client.py` 已内置等级守卫与失败分类。

## 竞争者对位（Agent Infra）
- **OpenSquilla**：开源 harness，最强对位。
- **PenguinHarness**：自进化 harness，benchmark 未开源（可公开质疑，已折进 benchmark 声称规则）。
- **Mano-P 2.0**：端侧 GUI-VLA，OSWorld 58.2% 第一。
- **Cua**：桌面控制基础设施，Driver 后台 + MCP = 新攻击面（已折进桌面驱动规则）。
- **AIsa (aisa.one)**：unified gateway + Agent Skills + x402 支付，撞 ATEX Gateway 与 swarmlabs-plugins 分发。2026-09-22 深化：**AgentPay Guard**（9/10 发布，quote-first / per-request/per-task/per-time 三层限额 / cost 无法封顶就不执行 / 付费端点禁止测试）+ **MCP SEP-2640**（9/13 Final，Skills 官方收编）+ AIsa Connect 一键装 agent。已折 5 条支付/预算攻击面规则进 SKILL_EXTRA（22→27），攻击 15/15 命中、良性 0/11 误报。SwarmLabs 侧长期选项：license 售卖走 x402 通道 + 发布 A2A agent card。

## 真实 harness 实测证据（2026-09-22）
通过 GitHub Contents API 拉取 3 个真实开源 harness 共 22 文件跑 AIShield 扫描：
- **PenguinHarness**（Prism-Shadow/penguin-harness）：20 文件 / 13 findings（0C 5H 7M 1L）
- **Cua**（trycua/cua）：2 文件 / 7 findings（0C 3H 2M 2L），gui-automation SKILL.md 精确命中"桌面驱动调用"
- **Mano-P**（Mininglamp-AI/Mano-P）：0 文件（未开源具体 skill，只有 README/LICENSE/pics）
- **合计 0 critical** —— 规则没有对真实开源项目误报，验证"误报比没有规则更糟"铁律
- Agent 支付/x402 规则 0/22 命中（真实 harness 尚未涉及 x402 支付，属早期生态空白）
- 报告：`docs/harness-measurement/2026-09-22-real-harness-scan.md`
- 可作为 GOAI 2026 初赛"已在真实 agent 生态跑通"的证据

## 线上拓扑
CF Named Tunnel（cloudflared→:8450→api/server.py），前缀 `/api/v1`，无 CF Pages。部署身份 root → `AISHIELD_ALLOW_ROOT=1`。
**禁 `pkill -f cloudflared`**（会杀 healthlens tunnel），按 PID 停。`deploy-server.yml` 仅 `workflow_dispatch`（03:17 spine 调）。

## 铁律（精简）
- **假绿六层**：吞异常／`if not res: continue` 退 []／`| tail` 退出码恒 0（需 pipefail）／mock 外部 IO 须断言请求路径／`echo "X=$?"` 抢退出码／`notify()` 恒 0。
- 退出码显式 `rc=$?`→`exit $rc`；禁 `|| true`/2>/dev/null 吞门禁。
- **结论层铁律**：`risk`/`safe` 不得轻于最严重 finding（取分数档 vs worst_severity 更重 + 输出 worst_severity）；布尔结论由等级字段派生。
- 雷达规则须含 `|` 或有界 `.{n,m}`，裸关键字留 draft；`BENIGN_CORPUS` 含防御工具描述，须区分「话题提及」与「祈使式执行」。
- 推送：`_push_batch.py`（多文件一 commit，原子）/`gh_push.py` 首参 message 无 `-m`；Contents API 无法 amend；本机无 `.git` 致 git status 全假阴性。
- push 与 workflow_dispatch 非原子：push 后先取 main HEAD 再 dispatch，核 run head_sha 含目标 commit。
- 测试假 token 触发 secret scanning 422 → 用 `bypass_placeholders.placeholder_id`；告警出站每出口脱敏；台账按 fingerprint upsert。

## 自动化 / 分发
20 workflow，03:17 spine 串行 9 子；5 本地自动化（守夜 08:30 / 竞品 周一 / Radar 02:00 / 分发 周六 / 周报 周日）职责不重叠。
`self_scan.py` 需 `blocking_unsuppressed=0`+`stale_allowlist=0`，不在 CI 里。已上架 Glama+npm。
workflow permissions 铁律：会 push 必须 `contents: write`。

## 待办
- 🟡 吊销旧 CF token（曾硬编码进 public 仓历史）+ aishield.tools CF Pages Retry。
- 🟡 4 条 skill 指令载荷候选待评审；`promote_rule.py --shadow` 报 2 条 catch=0 死规则待拍板。
- 🟡 `.workbuddy/memory/` 在 main 被跟踪，清理需 rewrite history。
- 🟡 配置面 `axis_credential=generic_password` 3/4、`axis_launcher=uvx_auto_install` 3/4 仍 75%（缺口 `cfg-mal-uvx_auto_install-generic_password`）。
- 🟢 已完成（2026-09-20）：规则数门禁 + docs 零依赖渲染通道 + 基准双口径统一 + is_doc 注入豁免/中文引用标记/指令面喂样修正（24/28）。
