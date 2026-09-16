# AIShield × 2026-09 Agent 生态 Landscape 评估

> 2026-09-15 用户问询：「OpenAI Agents API、Karpathy、Qwen-UI-Agent、Hyper Research、Theseus RSI L1–L5、CocoLoop/CLS、ponytail、Eliza、QoderWake、SoL-Pi、heyclicky、OpenMausBot、bash+CLI 范式、TeamAI —— 对我们项目有没有帮助？」
> 结论：**绝大多数有帮助**，主要作为扫描目标 / 分发渠道 / 威胁建模输入；只有 2 个是真正竞品（CocoLoop/CLS-Certify 强、TeamAI secret-scan 轻）。没有任何一个能动摇 AIShield 的核心差异化（本地零依赖 / 代码不上云 / 双维覆盖 / 中性信任机构）。

---

## 0. 一句话结论

| 维度 | 判断 |
|------|------|
| 有帮助（adopt） | OpenAI Agents SDK、Hyper Research、ponytail、Eliza、OpenMausBot、QoderWake、TeamAI、CocoLoop、bash+CLI 范式、SoL-Pi、Qwen-UI-Agent、Karpathy autoresearch、Theseus RSI |
| 竞品（defend） | **CocoLoop/CLS-Certify**（强，直接做 skill 安全扫描 + 评级 + 报告）、**TeamAI block-secret hook**（轻，仅密钥扫描） |
| 忽略（ignore） | microVM/沙箱隔离本身、GUI 渲染层 |
| 需澄清 | heyclicky 真实形态与之前描述不符（见 §5.4） |

---

## 1. 逐项目评估表

分类图例：**SCAN** = 扫描目标（AIShield 可扫其配置）；**DIST** = 分发/集成渠道；**COMP** = 竞品；**THREAT** = 威胁建模输入。

| # | 项目 | 形态 / 许可 | 与 AIShield 关系 | 具体帮助 | 优先级 |
|---|------|------------|------------------|----------|--------|
| 1 | **OpenAI Agents SDK / Agents API** | agent 框架，MIT，26k★ | SCAN + THREAT | 扫其 guardrail/handoff/MCP 接线；其「MCP + guardrail」模型直接映射 OWASP MCP Top 10 / ASI01 | adopt（参考/扫描） |
| 2 | **Karpathy autoresearch / nanochat / LLM Council** | 自改进研究 loop，MIT | THREAT | 「agent 改自己代码/配置」是 L5/RSI 风险类的具象 | defend（建模） |
| 3 | **Qwen-UI-Agent** | 真实设备 GUI+CLI agent，开源权重 | SCAN + THREAT | 高权限 GUI+CLI 执行 = 越权/外传面 | defend（规则） |
| 4 | **Hyper Research** | Claude Code 研究 skill，MIT | SCAN + THREAT + DIST | 本身就是可扫 `SKILL.md`；web fetch+子 agent+不可变 prompt = 注入面 | adopt（扫+分发） |
| 5 | **Theseus Labs RSI（L1–L5）** | 研究报告 arXiv 2609.11873 | THREAT | RSI 五级 = ASI01 风险分类锚点；L5 = 递归改「改进机制」 | defend（威胁建模） |
| 6 | **CocoLoop / CLS-Certify** | 技能商店 + 安全扫描，S–D 级 | **COMP** + DIST | CLS-Certify 直接做 skill 安全扫描（六维 + 评级 + 报告）= 最强新竞品；同时是可上架分发渠道 | defend + adopt |
| 7 | **ponytail** | 懒写代码 skill，MIT，113k★ | SCAN + THREAT | 本身是可扫 skill；`-audit` 印证「skills = 攻击面」是真实热门品类 | adopt（扫+分发） |
| 8 | **Eliza / elizaOS** | Web3 agent 框架，MIT，50k+ 部署 agent | SCAN + THREAT | 插件/角色 JSON + 链上调用 = 丰富 MCP/skill 类攻击面 | adopt（扫） |
| 9 | **QoderWake** | 阿里「数字员工」平台，私有 SaaS/CLI | SCAN + DIST | skill/MCP 配置可扫；可托管 MCP/Skills | adopt（分发） |
| 10 | **SoL-Pi** | coding harness 增效（NVlabs），MIT | SCAN + THREAT | 可选「远程 reducer 外泄日志」= 数据泄露类，应在 skill/harness 配置中标红 | defend（规则） |
| 11 | **heyclicky (farzaa/clicky)** | Mac 屏幕感知助手，MIT | SCAN(弱) + THREAT | 屏幕录制 + agent 执行 = 隐私/越权；⚠ 真实形态与之前描述不符（§5.4） | adopt（弱） |
| 12 | **OpenMausBot** | 多 agent 桌面（milind-soni），MIT | SCAN + THREAT | 暴露 MCP stdio server + 本地 computer control + 审批模型 = 典型 MCP/权限面 | adopt（扫） |
| 13 | **bash + CLI 范式** | agent 执行范式（CodeAct 等） | THREAT + SCAN | 任意执行面 = 再次印证「绝不 spawn 被扫命令」立论；`SKILL.md`+二进制可扫 | defend（立论） |
| 14 | **TeamAI（腾讯）** | 团队 harness 分发 CLI，MIT，2.9k★ | DIST + COMP(轻) | 可把 AIShield 作为 skill/hook 分发到 11 种 agent（含 WorkBuddy）；自带 `block-secret` hook（轻竞品） | adopt（分发） |

---

## 2. adopt / defend / ignore 拆解

### 2.1 adopt（应集成 / 分发 / 借鉴）

**分发渠道（最高杠杆、最低成本）**
- **CocoLoop 商店**：**当贝**旗下的 OpenClaw 技能商店（**2026-03-19 上线**；收录规模官方口径不一——站点实测 5000+，部分第三方称 1.3 万–4.7 万）。所有上架技能强制过 **CLS + BSS** 安全审核并给 **S+/S/A/B/C/D** 评级，另提供 VM 级隔离执行。⚠️ 同赛道竞品 **SkillScan**（`/skills/7590`，A 级，"Skill 安全准入网关"）**已在架**。AIShield 可作为「安全类技能」上架（**注册需手机/微信 OTP，须用户本人完成**）。
- **TeamAI（腾讯，git-native）**：把 skills/rules/hooks/MCP 经 Git + MR 审核分发到 Claude Code / Codex / Cursor / **WorkBuddy** / Qoder / Kiro 等 11 种 agent。**无平台账号体系**——「上架」= 把 AIShield 仓库做成合法 source repo（✅ **已完成**：根 `teamai.yaml` 声明 `publicSkills: [aishield-scan]` + `skills/aishield-scan/SKILL.md`）；订阅方一行 `teamai source add https://github.com/lm203688/aishield.git --name aishield`。可选硬门禁 hook 见 `distribution/teamai/teamai-hook.yaml`（真实入口 `action_entrypoint.py`）。
- 各 agent skill 市场（Claude Skill / GPT Store / HuggingFace / DeepSeek Harness / ClawHub 已有骨架）—— 多表面铺货是本项目既定策略。

**威胁建模输入（强化 ASI 论述）**
- **Theseus RSI L5**：L5 = 智能体改进「改进机制本身」。直接落入 **ASI01（agent 身份/越权）** 与 **ASI10（自迭代安全）** 的论述框架；可作为「agent 自我修改」风险的权威引用。
- **Karpathy autoresearch / LLM Council**：agent 自动改自己代码 + 多模型自审，是 L5 风险类的工程具象。
- **Qwen-UI-Agent / bash+CLI 范式**：真实设备高权限执行 + 任意 shell 执行面，是「越权 / 数据外传」最直白的攻击面，可用于对外「你给 agent 的权限有多大」叙事。

**扫描目标类（已有 skill/MCP 检测可覆盖）**
- Eliza 插件 manifest、OpenMausBot / QoderWake 的 MCP server 配置、Hyper Research / ponytail 的 `SKILL.md`、SoL-Pi 的 harness 配置 —— 多数已被现有 MCP/skill 检测覆盖，可补针对性文档或少量规则。

### 2.2 defend（需差异化对抗的竞品）

**① CocoLoop / CLS-Certify（最强新竞品）**
- 它做什么：对 Agent Skill 做六维安全分析（静态代码 / 动态行为 / 依赖 / 网络 / 隐私 / 威胁情报），输出 S+/S/A/B/C/D 评级 + HTML/PDF/SARIF 报告；并作为商店上架门槛。
- 重叠点：skill 安全扫描 + 评级 + 报告，与 AIShield 的「4 维评分 + badge」正面撞车。
- 它的问题（我们的差异化话术）：
  - 依赖**大模型深度检测 + 外部 API**（CVE/威胁情报依赖商业 API，无网环境落不了地）；AIShield **本地零依赖、代码不上云**。
  - 是**平台**（上架需过其认证），我们是**中立第三方信任机构** + 可嵌入 badge + Trust API + x402 计量。
  - 实测 `threat-scan.sh` 对千行 SKILL.md **60s 内跑不完**（逐行×逐模式 fork grep 性能问题）；我们是静态规则引擎，秒级。
  - 覆盖偏「skill」，我们是 **MCP + skill + GPT + prompt 双维（MCP Top 10 + ASI01–10）**。
- 结论：把它当「国内 skill 安全扫描的占位者」来打 —— 话术主线 = 「本地不上云 + 双维 + 中性信任 + CI 门禁」。

**② TeamAI `block-secret` hook（轻竞品）**
- 它只做**密钥扫描**（`scan-secret.sh || true`），且 `|| true` 让它**永不阻断**（门禁自毁，正是本项目红线反例）。
- AIShield 远超：密钥只是 1 类，我们覆盖 tool poisoning / prompt injection / 越权 / 供应链 / ASI01–10。
- 更好定位：不做竞品，做 **TeamAI 上的安全 skill/hook**（它缺的正是「全量 skill/MCP 安全门禁」）。

### 2.3 ignore（与我们无关）
- microVM / 容器隔离技术（forgevm / Cube / Cloudflare Sandboxes 的活）—— 不是 AIShield 的活，做也打不过。
- GUI 渲染层本身（Kitesurf 类）—— 我们只做内容信任层。

---

## 3. 对 AIShield 核心定位的印证

1. **「绝不 spawn 被扫命令」再次被印证**：bash+CLI 范式（单个 `run(command)` 任意执行面）和 SoL-Pi（可选远程 reducer 把日志外泄）恰好说明 —— agent 的执行面越大，越需要「只读静态审计、绝不执行被扫配置」的安全层。这是一句话就能讲清、且对方短期难掉头的结构性优势。
2. **「内容安全平面」叙事补强**：Theseus RSI L5 + Karpathy autoresearch 把「agent 自我修改」推到前沿，而 agent 自我修改的第一步就是改自己的 skill/MCP/配置 —— 正是 AIShield 的扫描对象。话术可升级为：「当 agent 开始改自己，先让 AIShield 扫一遍它要改的东西。」

---

## 4. 已起草的低杠杆资产（可直接进「待发布清单」）

- `distribution/teamai/README.md` + `teamai-hook.yaml`：AIShield 作为 teamai skill/hook 的分发草稿（含 `block-unscanned-skill` hook 示例，SessionStart 扫描团队 skills/MCP 并低分阻断）。
- `distribution/cocoloop/LISTING.md`：CLS 商店上架草稿（占 security 类目）。
- 建议（待用户确认发布）：在 `docs/llms.txt` 增加「AIShield as a TeamAI hook / CocoLoop certifier」联合定位，强化 agent-native 露出。

---

## 5. 未完事项状态 + 交接（「以上未完成」）

### 5.1 🔴 P0：CF API Token 硬编码（仍待用户凭证）
- **现状**：`scripts/deploy-named-tunnel.sh:20` 与 `deploy-quick-tunnel.sh:156` 以 base64 硬编码 CF API Token；仓库 public 且该 token **有写权限**（可改 DNS / 页面规则）。
- **为什么不能我擅自改**：改 env 注入必须**同时建仓库 secret**，否则 `deploy-server.yml` 下发生效后部署链断开（cron 03:17 跑必失败）。属安全敏感操作。
- **交接（用户 3 步）**：
  1. CF 后台建**最小权限** token（仅 `Zone:aishield.tools` 的 DNS 读 + Page Rules/Token 必要权限，去掉全局 API 写）；
  2. 仓库 `Settings → Secrets` 建 `CF_TUNNEL_TOKEN`（值 = 新 token）；
  3. 告知「已建好」→ 我把 2 个脚本改成从 `os.environ["CF_TUNNEL_TOKEN"]` 读入并推送，再验证 `/api/v1/health` 部署新鲜度。
- **我已准备的精确改动（不推送，等确认）**：两处 `CF_API_TOKEN_B64="...."` → 改为运行时从 env 派生：
  ```bash
  CF_API_TOKEN_B64=$(python -c "import base64,os;print(base64.b64encode(os.environ['CF_TUNNEL_TOKEN'].encode()).decode())")
  ```

### 5.2 Reddit 源永久误报 DEGRADED（建议标 known-blocked，待拍板）
- **现状**：本机出口对 reddit **结构性不可达**（4 子版全 `HTTP -1`），`consecutive_failures` 单调递增，明日触 3 即永久出 `[health] DEGRADED sources: reddit(3)`。这是 09-12 **有意设计**（宁可判红不假绿）。
- **问题**：但本机确实永远连不上 → 这是「真告警但无行动意义」的噪声，会 **desensitize 监控**（恰恰违背本项目「假绿/假红」铁律）。
- **建议**：把 reddit 标 `known-blocked`（**不是调阈值**），M8 不再对其报警。诚实修复，不动其它源。
- **我可准备的改动**：`scripts/tech_radar.py` 的 `source_health` 增加 `known_blocked` 集合含 `reddit`（或 sources 配置加 `enabled:false`）。等用户确认后改 + 推 + 验 CI。

### 5.3 B5 Presence 范式
- 用户 09-14 选了 **B1+B2+B4+B7+B8**（已交付 c963fdb6，748 passed），B5 未选 → **deferred，非未完成阻塞**。

### 5.4 ⚠ heyclicky 事实偏差（重要更正）
- 本轮子代理复核：真实 `farzaa/clicky` 是 **Mac 屏幕感知语音助手**（Swift / 屏幕热键捕获 / 动画光标 / YC Spring 2026），**并非 MCP 安全导向**。
- 之前会话采用的「7544★ / MIT / 代码冻结 2026-04-28 / MCP 安全导向」描述与真实仓库**不符**（疑似混淆了同名/近似项目）。
- **影响评估**：已落地的 B1–B8 借鉴项是**通用好工程**（精确锚点 `formatFinding`、隔离可验证 `prove_isolation`、agent-native 文档 AGENTS.md/CLAUDE.md、范围纪律、社区台账 COMMUNITY.md），**不依赖 heyclicky 的具体定位** —— 代码不受影响，`c963fdb6` 无需回滚。仅「heyclicky 是 MCP 安全项目」这一**来源叙事**需校正（后续对外材料避免据此表述）。

---

## 6. 下一步（用户决策点）

- [ ] **确认建 CF secret** → 解锁 P0（§5.1）
- [x] **Reddit 标 known-blocked** → 已落地（`KNOWN_BLOCKED_SOURCES`，2026-09-15）
- [x] **TeamAI 分发** → 已落地为 source repo（`teamai.yaml` + `skills/aishield-scan/SKILL.md`，**无需账号**）
- [ ] **CocoLoop 上架** → 文案已就绪（`distribution/cocoloop/LISTING.md`）；**待用户在 hub.cocoloop.cn 注册（手机/微信 OTP）后走「社区投稿」粘贴提交**
- [x] **RSI L5 → ASI 规则映射** → 已正式化为 2 条规则（`docs/rsi-asi-mapping.md`，2026-09-15）
