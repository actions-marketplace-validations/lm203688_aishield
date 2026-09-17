# aishield.tools — Cloudflare Bot / 爬虫放行配置

> 本文档取代通用模板 `cf-bot-fight-config.md`（后者以 genetech.tools 为对象，且其
> "方案C：Page Rule" 已失效，见 §5）。所有结论均基于 2026-09-15 对线上
> `aishield.tools` 的实测，不含任何密钥或 token。

---

## 1. 现状（2026-09-15 13:35 UTC 实测）

实测命令与结果：

```bash
curl -s -D - -o /dev/null https://aishield.tools/        # HTTP/1.1 200 OK
curl -s -o /dev/null -w "%{http_code}" https://aishield.tools/api/v1/health   # 200
```

| 观测项 | 实测结果 | 结论 |
|---|---|---|
| `Server` | `cloudflare` | 站点确实在 Cloudflare 代理后面 |
| `CF-RAY` | `a3b80379a93994eb-LHR` | 边缘节点正常工作 |
| `cf-cache-status`（`/`） | `DYNAMIC` | 首页**未被边缘缓存** |
| `Transfer-Encoding`（`/`） | `chunked` | 源站未给 Content-Length |
| challenge 标记（`cf-mitigated` / `cf-chl` / turnstile / challenge） | `/`、`/agent.html`、`/pricing`、`/api/v1/health` 全部 **0 处** | **Bot Fight Mode 当前没有在拦截任何东西** |
| `HEAD /` | **501 Not Implemented** | 已修复，见 §6 |
| 线上 `/llms.txt`、`/.well-known/agent.json`、`/geo-faqs.json` | **404** | 资产已修复，见 `docs/agent-native-distribution-playbook.md` |
| 线上 `/robots.txt` | 200 | 但为修复前旧版本 |

**关键推论：当前不是"Bot Fight Mode 在拦爬虫"，而是"资产根本还没上线"。**
通用模板假设的 403 JS Challenge 在 aishield.tools 上今天并不发生。照模板
"关掉 Bot Fight Mode" 是无害的空操作，但它会让你错过真正的问题。

---

## 2. 为什么这对 AIShield 格外重要

AIShield 是一个**安全扫描器**，它的默认使用者恰恰是"会启用安全开关的人"。
这产生一个反直觉的陷阱：

> **Cloudflare 的 "Block AI bots" 管理规则在所有套餐上都有，且它优先于
> "Allow verified bots"。** 即使你同时开了"放行验证爬虫"，被分类为 AI Search /
> AI Assistant / AI Crawler / Archiver 的**验证 AI 爬虫仍会被拦掉**。

也就是说：一个出于安全直觉把 "Block AI bots" 打开的运维者，可以在不知情的
情况下**一次性切断 AIShield 的整个 Agent 发现面**（GPTBot、ClaudeBot、
PerplexityBot、CommonCrawl 全部被拒），而 `robots.txt` 明明写着全部允许。
症状依然是"提交成功、收录为零"——和"资产没上线"无法区分。

这是本文档存在的**第一理由**：把"不许开 Block AI bots"变成一条有名字、可审计
的规则，而不是靠记忆。

---

## 3. 路径分级

不要做全站放行。按「机器可读资产必须开、写接口必须防」分三级：

### A 级 — 必须无条件放行（永远不 Challenge、不 Block）

Agent 发现与 AI 索引的命脉。被拦 = 整个分发链路断裂。

```
/llms.txt
/llms-full.txt
/agent-discovery.json
/geo-faqs.json
/openapi.json
/.well-known/agent.json
/.well-known/ai-plugin.json
/.well-known/agent-card.json
/.well-known/security.txt
/.well-known/mcp/server-card.json
/robots.txt
/sitemap.xml
/feeds.xml
/humans.txt
/api/v1/health
/api/v1/stats
```

### B 级 — 允许但限流

只读、可被 Agent 调用、但要防止被刷。

```
/api/v1/agent/setup
/api/v1/monitor/list
/api/v1/proxy/tools
/api/v1/proxy/stats
```

### C 级 — 唯一真正的攻击面（严格限制）

AIShield 自身执行安全扫描，`POST /api/v1`（扫描入口）与信任/支付/治理写接口
是唯一需要防御的对象：

```
POST /api/v1                    ← 扫描入口，最大消耗
POST /api/v1/trust/*            ← 信任评分写入
POST /api/v1/scan/*             ← 攻击路径生成
POST /api/v1/registry/*         ← 注册中心写入
/api/v1/pay/*                   ← 虎皮椒支付回调，**必须放行**
/api/v1/governance/*            ← 治理审计写入
```

> ⚠️ `/api/v1/pay/*` 是**支付回调**。任何"拦非浏览器请求"的规则如果覆盖它，
> 会直接吃掉真实付款。它必须在 A 级或独立的 Allow 规则里。

---

## 4. 规则配置（WAF Custom Ruleset）

路径：Dashboard → 选择 `aishield.tools` → **Security → WAF → Custom rulesets**
→ 选择一个 custom ruleset → **Add rule**。**规则按你在列表中的顺序自上而下执行**，
所以顺序就是优先级。

### 规则 1 — 验证爬虫无条件放行（放最上面）

用 `cf.verified_bot_category`，该字段**所有套餐可用**（不需要 Enterprise
Bot Management 的 `cf.bot_management.*` 字段）。

```
Expression:
  cf.verified_bot_category in {
    "AI Search", "AI Assistant", "AI Crawler", "Archiver",
    "Search Engine Crawler", "Search Engine Optimization"
  }
Action: Allow
```

> 说明：Cloudflare 已验证身份（ASN + IP 反向解析）的机器人才能命中这个字段，
> 因此放行它不等同于"放行所有自称 GPTBot 的 UA"。想按 UA 放行请先读 §5.3。

### 规则 2 — 机器可读资产对所有人开放

```
Expression:
  (
    http.request.uri.path in {
      "/llms.txt", "/llms-full.txt", "/agent-discovery.json",
      "/geo-faqs.json", "/openapi.json", "/robots.txt", "/sitemap.xml",
      "/feeds.xml", "/humans.txt", "/api/v1/health", "/api/v1/stats"
    }
    or http.request.uri.path starts_with "/.well-known/"
  )
Action: Allow
```

### 规则 3 — 放行支付回调（不要与规则 4 的 Skip 混淆）

```
Expression:
  http.request.uri.path starts_with "/api/v1/pay/"
Action: Allow
```

### 规则 4 — 对 A 级路径跳过后续全部规则

放在规则 1–3 之后，保证 A 级路径不会被后面任何 Block / Challenge 命中：

```
Expression:
  (
    http.request.uri.path in {
      "/llms.txt", "/llms-full.txt", "/agent-discovery.json",
      "/geo-faqs.json", "/openapi.json", "/robots.txt", "/sitemap.xml"
    }
    or http.request.uri.path starts_with "/.well-known/"
    or http.request.uri.path starts_with "/api/v1/health"
    or http.request.uri.path starts_with "/api/v1/pay/"
  )
Action: Skip
Skip what: All remaining custom rules and all managed rules
```

### 规则 5 — 扫描入口限流（Advanced Rate limiting）

路径：**Security → WAF → Rate limiting rules → Add rule**

```
Expression:
  http.request.method eq "POST" and http.request.uri.path eq "/api/v1"
Rate:      30 requests / minute / IP
Action:    Managed Challenge（首次）→ 超阈值 Block
```

如果免费套餐没有 Rate limiting，退化为 Advanced Rate limiting 手动计数，或直接
在源站用应用层限流（AIShield 已在 `_send_json` 返回
`X-RateLimit-Remaining` 头）。

---

## 5. 三条硬性"不要做"

### 5.1 不要开启 "Block AI bots"

Security → Bots → **确认 Block AI bots 保持关闭**。它是所有套餐可见的托管规则，
**优先于** verified-bots 放行规则，会直接砍掉 GPTBot / ClaudeBot /
PerplexityBot / CommonCrawl。AIShield 的商业模式是"被 AI 检索到并引用"，
开启它等于主动关闭分发入口。

若你确实担心 LLM 训练用途的抓取，正确做法是**只拦 "Archiver"** 一类，而不是
全关：

```
Expression: cf.verified_bot_category eq "Archiver"
Action:     Block
```

### 5.2 不要用 Page Rules

通用模板里的"方案C：Page Rule → Security Level Essentially Off"**已失效**：

- Page Rules 的 **API 端点已于 2025-01-06 下线**
  （`/zones/:zone_id/pagerules` 全系列已 deprecated）；
- Page Rules 的 **"Disable Security" 设置项已被弃用且不会自动迁移**；
- Cloudflare 计划 2025 年底或之后把现有 Page Rules 自动迁到 Ruleset 引擎。

新建任何规则都走 §4 的 Custom rulesets。

### 5.3 不要只按 User-Agent 放行

GPTBot 的 UA 字符串可以被任意伪造，仅凭 UA 放行 = 给攻击者一条绕过限流的通道。
UA 判断只能作为**辅助过滤**，且必须搭配验证字段：

```
# 仅作辅助，不单独作为 Allow 条件
cf.user_agent.startswith("GPTBot")
```

---

## 6. 边缘缓存：一个实测发现的真实损耗

实测 `GET /` 返回 `Transfer-Encoding: chunked` + `cf-cache-status: DYNAMIC`
+ 无 `Cache-Control`。三者叠加意味着：

1. 源站没有 `Content-Length` → Cloudflare 无法把响应存入边缘缓存；
2. 没有 `Cache-Control` → 即使能缓存也走默认 TTL；
3. 每个请求都回源到 VPS。

对比之下，§3 的 A 级 JSON/文本资产已经通过 `api/server.py` 的 `_GEO_ASSETS`
路由表返回 `Cache-Control: public, max-age=3600` + 明确的 `Content-Length`，
**这些是可以在边缘缓存的**。

后续改进项（未在本次改动内）：给 HTML 页面路由（`/`、`/agent.html`、
`/pricing` 等）补 `Content-Length` 与 `Cache-Control`，让首页也能边缘缓存。
优先级低于修复路由本身——页面能被抓到是前提，缓存只是成本优化。

### 顺带修掉的：HEAD 返回 501

实测发现 `GET /` 是 200，但 **`HEAD /` 返回 501 Not Implemented**。

`BaseHTTPRequestHandler` 对没有 `do_<METHOD>` 的方法一律返回 501。大量 AI 爬虫、
链接检查器、CDN 预取器与提交前校验工具会**先发 HEAD 做存活预检**，收到 501
即判定 URL 不可用并放弃抓取。

已在 `api/server.py` 实现 `do_HEAD()`：复用 `do_GET()` 的完整路由逻辑，仅在
`end_headers()` 之后丢弃响应体（响应头与 `Content-Length` 保留）。
正确性依赖的不变量——"所有 `self.wfile.write` 都紧跟在 `self.end_headers()`
之后"——已由 `tests/test_geo.py::TestHeadMethodSupported::test_all_wfile_writes_follow_end_headers`
钉死，未来若有人破坏该假设，CI 会立刻报红。

---

## 7. 验证清单

配置完成后逐条执行。任一失败即说明配置有误。

```bash
# 1. 无 challenge 标记（应全部输出 0）
for p in / /agent.html /pricing /api/v1/health /llms.txt /sitemap.xml; do
  echo -n "$p: "
  curl -s -D - -o /dev/null --ssl-no-revoke --tlsv1.3 "https://aishield.tools$p" \
    | grep -icE "cf-mitigated|cf-chl|turnstile|challenge"
done

# 2. 六个发现资产全部 200
for p in /llms.txt /llms-full.txt /agent-discovery.json /geo-faqs.json \
         /.well-known/agent.json /.well-known/ai-plugin.json; do
  curl -s -o /dev/null -w "%{http_code}  $p\n" \
    --ssl-no-revoke --tlsv1.3 "https://aishield.tools$p"
done

# 3. HEAD 不再是 501（应全部 200）
for p in / /llms.txt /.well-known/agent.json /api/v1/health /sitemap.xml; do
  curl -s -o /dev/null -w "%{http_code} HEAD $p\n" -X HEAD \
    --ssl-no-revoke --tlsv1.3 "https://aishield.tools$p"
done

# 4. robots.txt 允许 AI 爬虫（应能看到 5 个 UA 块）
curl -s --ssl-no-revoke --tlsv1.3 https://aishield.tools/robots.txt \
  | grep -cE "User-agent: (GPTBot|ClaudeBot|PerplexityBot|Applebot-Extended|Google-Extended)"

# 5. 健康检查（核对 commit 与 rules_count）
curl -s --ssl-no-revoke --tlsv1.3 https://aishield.tools/api/v1/health \
  | python -c "import sys,json;d=json.load(sys.stdin);print(d['version'],d['rules_count'],d['commit'][:8])"
```

自动化：`.github/workflows/geo-indexnow-submit.yml` 的 `verify` job 每日
09:20 UTC 已覆盖上面第 2、3 条；失败会触发
`notify.py --fingerprint geo-indexnow-broken` 告警，成功则 resolve。

---

## 8. 一个需要先确认的运维前提

`aishield.tools` 的 DNS zone 在账户 `8162aa3b2241c132e43a81f526d7f758` 下，
但该账户里 **`cfd_tunnel=0`**——真正承载流量的 Named Tunnel 注册在**另一个
Cloudflare 账户**。

这意味着：如果你登的是 zone 所属账户，**可能根本没有入口去改 Bot 规则**，或者
改完的 zone 与实际承载流量的 zone 不是同一个。

动手改任何规则前，先确认两件事：

1. 你当前账户下能选到 `aishield.tools` 且能看到 Security → WAF；
2. 该 zone 的 origin 确实指向 cloudflared tunnel（Dashboard → DNS →
   查看 `aishield.tools` 记录类型）。

若两者不一致，先去把账户归属理清（参考 `docs/cf-token-rotation.md` 的轮换流程
定位正确账户），再回来做本文档的配置。
