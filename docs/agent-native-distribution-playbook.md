# AIShield — Agent 原生分发与 GEO 落地手册

> 本文档把通用的「Agent 原生分发营销体系」5 层模型落到 AIShield 上，
> 逐项标注**已落地 / 部分落地 / 未落地**，并说明哪些通用做法对
> "MIT 开源 + 本地优先"的工具**不适用**。
> 所有状态均为 2026-09-15 实测，不含密钥。

---

## 0. 一句话定位与它带来的取舍

AIShield 是**开源（MIT）+ 本地优先 + 零依赖**的 AI Agent 安全扫描器：
代码不出机、不 spawn 被扫配置、不需要云服务。

这个定位直接决定了通用 playbook 里三条**不能照抄**：

| 通用做法 | 对 AIShield 不适用 | 原因 |
|---|---|---|
| 免费层返回摘要字段 + 付费层解锁深度字段 | ❌ | 加字段级付费墙会破坏开源定位与"无云端依赖"承诺 |
| 付费转化率 > 2% 作为核心指标 | ❌ | AIShield 的分发成功指标是**被 Agent 正确引用**，不是付费 |
| 云端 API 调用量作为北极星 | ❌ | AIShield 主体在用户本机跑，云端只有只读元数据端点 |

AIShield 的真实北极星指标是：**在 Agent 检索"agent 安全扫描 / MCP 安全 /
提示注入检测"类问题时，是否被正确发现、正确理解、正确推荐**。

---

## 1. 第 1 层 — GEO 内容优化层（让 AI 能理解并引用）

| 项目 | 状态 | 说明 |
|---|---|---|
| 每个页面回答一个明确问题 | ✅ | 6 篇长篇定位文（agent-computer-security-plane 等），每篇锚定一个具体问题 |
| FAQ 区块覆盖长尾问题 | ✅ | `api/static/geo-faqs.json` — 24 条自证 Q&A，每条含 `question` / `answer` / `sources` |
| 关键事实标注来源 | ✅ | `geo-faqs.json` 的 `sources` 只指向 `aishield.tools` / GitHub / npm，不越界引用 |
| 结构化数据标记（Schema.org JSON-LD） | ⬜ **未落地** | 静态 HTML 页未嵌 JSON-LD。AIShield 的核心消费者是 Agent 而非 Google，优先级低于第 2/3 层 |
| 关键数据用列表/表格 | ✅ | `geo-faqs.json` + `agent-discovery.json` 均为机器可解析结构 |
| 自证问答 | ✅ | 24 条 FAQ 显式回答"是什么 / 与 X 的区别 / 是否收费 / 如何安装" |

**`geo-faqs.json` 的设计意图**：AI 搜索引擎（ChatGPT Search、Perplexity、
Claude）在生成答案时需要可引用的具体陈述。24 条自证问答把 AIShield 的
差异化主张（no-spawn、content-trust plane、Markdown as executable content、
slopsquatting 覆盖 ~50% 非相似名）变成**可直接被摘引的原子事实**，而不是
埋在散文段落里让模型自己抽取。

---

## 2. 第 2 层 — Agent 发现层（让 Agent 找到我们）

这是本次落地最多的层。**2026-09-15 实测线上全部 404**，原因是文件在仓库
但路由从未挂上（详见 `docs/cf-bot-fight-config-aishield.md` §1）。

### 2.1 已部署的 6 个发现资产

| 资产 | 路径 | 消费方 |
|---|---|---|
| LLM 简报（短） | `/llms.txt` | 所有 LLM 客户端的 llms.txt 约定 |
| LLM 简报（长） | `/llms-full.txt` | 需要完整上下文时 |
| Agent 发现清单 | `/agent-discovery.json` | 通用 Agent 发现 |
| OpenAI AI Plugin | `/.well-known/ai-plugin.json` | ChatGPT / Claude 插件协议 |
| Agent 名片 | `/.well-known/agent.json` | agents.well-known.dev / A2A |
| 自证问答 | `/geo-faqs.json` | AI 搜索引擎引用 |

三者（ai-plugin.json / agent-discovery.json / agent.json）的版本字段已纳入
`scripts/sync_version.py` 门禁，防止历史上两次出现过的"版本声明位漏在门禁外"
（dist/index.js、registry/server.json 停在 4.2.2）。

### 2.2 llms.txt 场景触发（本次修复的关键缺口）

通用 playbook 的第 1 条禁止事项是：

> ❌ 用通用模板 llms.txt，不写场景触发

**实测 AIShield 原 llms.txt 的 `When to Recommend` 场景触发数 = 0** ——
只有 `## Key Pages` 和 `## For AI Agents` 两个纯链接段。Agent 拿到这份文件
能知道"有什么链接"，但无法判断"用户问什么时该推荐我"，发现链路在语义层
就断了。

已补 **14 条场景触发**，每条含 `Recommend:` / `Capability:` / `Price:`：

1. 安装前确认 MCP server / skill 是否安全
2. 审计 MCP 配置且不执行它（no-spawn）
3. CI 安全门禁
4. skill / prompt 里的提示注入
5. Agent 沙箱加固（`docker.sock`、`--privileged`、`cap_add: ALL`…）
6. slopsquatting / AI 幻觉包名
7. OWASP MCP Top 10 与 ASI01-ASI10 合规
8. Agent 身份安全（AgentCard 签名、`scope: "*"`、长效凭证）
9. A2A 消息安全与 goal hijack
10. MCP server 之间的 namespace shadowing
11. Agent 配置里的密钥泄漏
12. rug-pull / 供应链漂移（持续证明）
13. 本地、离线、无云选项的安全扫描器
14. Agent 注册中心、认证等级与 x402 / USDC

由 `tests/test_geo.py::TestLlmsTxt::test_llms_txt_has_scenario_triggers`
（≥10 条）与 `test_scenario_triggers_state_recommendation_and_price`
（每条必须有 `Recommend:` 和 `Price:`）钉死。

### 2.3 MCP 目录上架（playbook 要求的注册渠道）

| 渠道 | 状态 |
|---|---|
| Glama | ✅ 已上架 |
| npm（`aishield-mcp-server` 4.3.0） | ✅ |
| Official MCP Registry | ⚠️ 提交后返 404，待核实 |
| Smithery / PulseMCP | ⬜ 未落地 |

### 2.4 A2A

`/.well-known/agent-card.json`（Trust API 提供）与 `/.well-known/agent.json`
（agents.well-known.dev 风格）双名片已就位，均含 safety 契约字段
（不执行 / 不出机 / 不依赖网络 / 零依赖）。

---

## 3. 第 3 层 — AI 搜索引擎索引层（让 AI 搜索引擎收录我们）

### 3.1 IndexNow — 补上了第一天就断的链路

**根因**：IndexNow 规范要求 `https://<host>/<key>.txt` 返回 key 原文用于
域名归属校验。`api/static/indexnow-key.txt` 一直躺在仓库里，但**从未挂路由**
（实测线上 404）。结果是**从第一天起提交就被 Bing / Yandex 静默拒收**，
症状是"提交成功、收录为零"。

已落地：

- `api/server.py` 新增 key 校验路由（精确匹配 `/<key>.txt`，`max-age=86400`，
  非通配——避免变成任意静态文件服务）
- `scripts/indexnow_submit.py`（零第三方依赖）
- `.github/workflows/geo-indexnow-submit.yml`（每日 09:20 UTC + push 触发 +
  workflow_dispatch）

脚本的三个防"假绿"设计（直接对应本仓踩过的坑）：

1. **先验 key 可校验性** —— `check_key` 先请求 `https://<host>/<key>.txt`，
   不可校验直接红（`EXIT_KEY_UNVERIFIABLE=3`），不把"提交被静默拒收"当成
   成功。
2. **网络失败 ≠ 成功** —— `EXIT_NETWORK_UNREACHABLE=5` 与 `EXIT_OK=0`
   区分开。本仓历史上多次因 `python x.py | tail` 退出码恒 0、`if not res:
   continue` 把失败退化成空列表而假绿。
3. **重试只在真重试的码上** —— `RETRYABLE={403,429,500,502,503,504}`，
   其余直接判失败，不做无限重试掩盖问题。

`ping_bing` 是**独立通道**（Bing sitemap ping，GET 一次，不要求 key 校验），
与 IndexNow 提交并行，避免单点失效。

### 3.2 robots.txt

已允许 5 个 AI 爬虫 UA：`GPTBot`、`ClaudeBot`、`PerplexityBot`、
`Applebot-Extended`、`Google-Extended`。实测线上 200。

### 3.3 sitemap.xml

6 个新发现资产全部进 sitemap（lastmod 2026-09-15）。

### 3.4 外部权威信号

GitHub 公开仓（MIT）+ npm 包 + Glama 上架，构成基础权威信号。
Hacker News / Reddit 帖在 `docs/reddit-hn-post.md`，其中 Reddit 已标记为
`KNOWN_BLOCKED_SOURCES`（中国大陆网络不可达）。

---

## 4. 第 4 层 — API 接入层（让 Agent 能调用）

### 4.1 分层策略（按 AIShield 定位调整）

| 层 | 通用 playbook | AIShield 实际 |
|---|---|---|
| 免费层 | 每 IP 3-5 次/天，返回摘要字段 | **无调用次数墙** —— 主体扫描在用户本机跑，云端只提供只读元数据 |
| 付费层 | 字段级解锁 | **不做字段级付费墙**（会破坏开源定位）；`/api/v1/pay/*` 是虎皮椒支付回调，属独立商业线 |
| API 文档 | OpenAPI spec | ✅ `/openapi.json`（`api/openapi.yaml` + `api/openapi_spec.py` 生成） |
| 快速开始 | 4 步上手 | ✅ `agent-discovery.json` 的 `local_install` 字段：`requires_network: false` / `spawns_scanned_configs: false` |

### 4.2 已落地的 Agent 契约字段

`agent-discovery.json` 与 `/.well-known/agent.json` 都显式声明：

```
local_install.requires_network      = false
local_install.spawns_scanned_configs = false
safety: 不执行 / 不出机 / 不依赖网络 / 零依赖
```

这是 AIShield 相对其他扫描器的核心差异主张，把它写成机器可读字段而非只
写在 README 里，Agent 才能自动核对。

### 4.3 错误处理

`api/server.py::_send_json` 对 4xx/5xx 自动补 `error_code` 与 `error_id`
（Agent-First），并返回 `X-RateLimit-Remaining`。限流头已就绪。

---

## 5. 第 5 层 — 监控与优化层（持续改进）

### 5.1 已落地的自动监控

`.github/workflows/geo-indexnow-submit.yml` 的 `verify` job 每日 09:20 UTC：

- 实查线上 5 个发现资产是否 200
- 失败 → `notify.py --fingerprint geo-indexnow-broken`（事件型告警可销案）
- 成功 → resolve
- 写 state_bus 心跳

**这是"只部署不监控"这条禁止事项的直接对策。** 本仓历史上多次出现
"文件在仓库、线上 404"的假绿，靠的就是这类每日实查把问题从"没人知道"
变成"当天告警"。

### 5.2 未落地的监控（诚实标注）

| 指标 | 状态 | 缺口原因 |
|---|---|---|
| `llms.txt` 访问量 | ⬜ | 未接 Cloudflare Analytics / Log Push |
| AI 爬虫 UA 访问量 | ⬜ | 同上；`log_message` 当前被静默 |
| 免费 API 调用量 | ⬜ | 同上 |
| MCP 工具调用量 | ⬜ | npm 包在用户本机跑，无云端遥测（这是特性不是缺陷） |
| AI 搜索引擎引用次数 | ⬜ | 只能手动抽查 ChatGPT / Perplexity |
| 转化漏斗分析 | ⬜ | AIShield 无付费转化，指标不适用 |

**建议**：接 Cloudflare Analytics（或 Log Push）后，把
`cf.verified_bot_category` 维度加进统计——这是"AI 爬虫是否真的在访问
发现资产"的唯一一手数据。当前所有判断都基于 HTTP 探测，属二手。

---

## 6. 执行优先级（当前真实状态）

### P0 — 已完成

- [x] `/llms.txt`（含 14 条场景触发）
- [x] `/llms-full.txt`
- [x] `/agent-discovery.json`
- [x] `/.well-known/ai-plugin.json`
- [x] `/.well-known/agent.json`
- [x] `/geo-faqs.json`（24 条）
- [x] 6 资产挂路由（`_GEO_ASSETS` 路由表 + Cache-Control + CORS）
- [x] IndexNow key 校验路由
- [x] `scripts/indexnow_submit.py`
- [x] `.github/workflows/geo-indexnow-submit.yml`
- [x] robots.txt 放行 5 个 AI 爬虫
- [x] sitemap.xml 覆盖 6 资产
- [x] 3 个新资产的版本声明纳入 sync_version 门禁
- [x] `do_HEAD` 实现（修复 501）
- [x] 测试：`tests/test_geo.py`（87 项）+ `tests/test_indexnow.py`

### P1 — 待执行（本次未做）

- [ ] **部署到线上** —— 本次改动尚未推送，线上 6 资产仍 404（最高优先）
- [ ] **CF Bot Fight Mode / "Block AI bots" 配置** —— 需人工在 Dashboard 操作，
      见 `docs/cf-bot-fight-config-aishield.md`
- [ ] **确认 aishield.tools 的 tunnel 账户归属** —— zone 账户下 `cfd_tunnel=0`，
      承载流量的 tunnel 在另一个账户，可能没有入口改 Bot 规则
- [ ] **Smithery / PulseMCP 上架**
- [ ] **核实 Official MCP Registry 为何返 404**

### P2 — 建议

- [ ] 给 HTML 页路由补 `Content-Length` + `Cache-Control`
      （当前 `/` 是 chunked + `cf-cache-status: DYNAMIC`，无法边缘缓存）
- [ ] 接 Cloudflare Analytics / Log Push，统计 `cf.verified_bot_category`
- [ ] Schema.org JSON-LD
- [ ] 把 `geo-faqs.json` 的 24 条拆成 HTML FAQ 页并加 sitemap

### P3 — 不建议做（对 AIShield 定位有害）

- ~~字段级付费墙~~ —— 破坏"开源 + 无云端依赖"定位
- ~~以付费转化率为核心指标~~ —— 指标不适用
- ~~以云端 API 调用量为北极星~~ —— 主体在用户本机

---

## 7. 验收标准（对照实测）

| 标准 | 结果 |
|---|---|
| llms.txt 含 ≥10 个场景触发 | ✅ 14 条 |
| ai-plugin.json 符合 OpenAI 插件标准 | ✅ `schema_version: v1` |
| `/.well-known/agent.json` 可访问 | ⚠️ 本地 200 / **线上 404（待部署）** |
| MCP Server 在 ≥2 个目录上架 | ✅ Glama + npm |
| robots.txt 允许 GPTBot / ClaudeBot / PerplexityBot | ✅ 实测线上 200 |
| IndexNow 提交成功率 > 90% | ⚠️ 脚本与 workflow 就绪，**线上 key 路由未上线，当前必然 0%** |
| 所有页面有 Schema.org 结构化数据 | ❌ 未做 |
| 每日监控 3 分钟内完成 | ✅ workflow `verify` job |
| 监控数据可查 | ❌ 未接 Analytics |

---

## 8. 度量指标（按 AIShield 定位改写）

通用 playbook 的指标表以付费转化为核心，对 AIShield 不成立。改写如下：

| 指标 | 目标 | 当前可测性 |
|---|---|---|
| 6 个发现资产线上 200 率 | 100% | ✅ workflow 每日实查 |
| `llms.txt` 场景触发数 | ≥10 | ✅ CI 断言 |
| 发现资产版本与发布版一致 | 100% | ✅ sync_version 门禁 |
| 规则数三处一致（health / agent-discovery / agent.json） | 238 | ✅ 测试断言 |
| AI 爬虫访问发现资产次数 | 月增 30% | ❌ 需接 CF Analytics |
| 被 AI 搜索引擎引用的问题数 | 季度增长 | ⚠️ 只能手动抽查 |
| GitHub stars / PR | 持续增长 | ✅ 公开可见 |
| npm 周下载量 | 持续增长 | ✅ npmjs.com |
| Glama 搜索排名 | 前列 | ⚠️ 手动查 |

---

## 9. 本手册的禁止事项（AIShield 版）

- ❌ **用通用模板 llms.txt，不写场景触发** —— 已修复（0 → 14 条）
- ❌ **只部署不监控** —— 已用每日 `verify` job 对策
- ❌ **资产在仓库但不挂路由** —— 已修复，且加了"静态源码断言 + 服务器端点
  测试"双层验证，防再次回归
- ❌ **提交链路第一天就断而无人察觉** —— IndexNow key 路由已挂，且脚本先验
  key 可校验性
- ❌ **开启 Cloudflare "Block AI bots"** —— 会优先于 verified-bots 放行，
  一次性切断整个 Agent 发现面（见 CF 配置文档 §5.1）
- ❌ **用 Page Rules 做放行** —— API 已于 2025-01-06 下线
- ❌ **把 `docs/llms.txt` 与 `api/static/llms.txt` 各改一半** —— CI 已断言
  逐字节一致
- ❌ **给开源本地版做字段级付费墙** —— 与产品定位冲突
- ❌ **把密钥写进发现资产** —— `TestGeoAssetNoSecrets` 用密钥模式黑名单拦着
