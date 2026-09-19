# Promotion Kit — 2026-09-19（第三轮：零安装在线扫描 + Collector）

**主题**：把「扫一个 MCP server」的成本降到一次粘贴（`/scan`），再加一个本地持续观测器（Collector）
**支撑文章**：`docs/blog/blog-online-scan-launch-2026-09-19.md`
**核心数据锚点**：235 MCP 规则 / 241 skill 规则 · `/scan` HTTP 200 · `npx aishield-mcp-server` v4.3.0 · 全程不执行被扫配置 · Collector 20 项契约测试
**发布状态**：全部为**草稿**（外部连接器均未连接，未自动发布）

---

## 1. 一句话钩子（各平台通用）

> 想扫一个 MCP server 是否安全，你得先装 Node、再学 CLI 参数——大多数人在这两步之间就放弃了。
> 现在只需要粘贴一次。

---

## 2. X / Twitter 线程（英文）

**1/**
Most people who *want* to check whether an MCP config is safe never get to the check.

install Node → `npx` → remember the CLI flags → finally a score.

That's three chances to quit before first value. So we deleted the steps. 🧵

**2/**
New: https://aishield.tools/scan

Paste `claude_desktop_config.json` / `.mcp.json` / your Cursor config → instant report:

· 0–100 config score
· severity breakdown
· server inventory + inferred capabilities
· findings w/ OWASP category
· SARIF download for CI

No install. No signup. No API key.

**3/**
One thing we will not do: fake the data flow.

The hosted page runs the scan **server-side**, so your pasted config **is sent to aishield.tools**. We say that on the page, in the first screenful.

A security tool that blurs data flow teaches its users the wrong first lesson.

**4/**
So we ship three paths, matched to how much you care:

· quick look, nothing sensitive → hosted `/scan`
· config has credentials / CI → `npx aishield-mcp-server` (fully local)
· want it watched → AIShield Collector (`--watch`)

Same engine, same rules, same redaction. Only the data path differs.

**5/**
What did NOT change, in any mode: **AIShield never spawns the `command` in the config it audits.**

Most config scanners have to run the server to read `tools/list`. An MCP `command` is arbitrary code — so for those tools, the audit *is* an execution.

**6/**
Also shipping today: **AIShield Collector** — local-first, continuous.

· discovers local MCP configs
· re-scans on change
· emits canonical JSONL events
· compact trust digest, **idempotent by fingerprint** (unchanged config → heartbeat, not a repeat alert)

```bash
python -m collector.aishield_collector --once --digest
```

**7/**
The invariants are pinned by tests, not by prose: `tests/test_collector.py` asserts at the source level that the collector imports no `subprocess` / `socket` / `urllib`.

No spawn. No network. Zero third-party deps.

**8/**
Coverage: 235 MCP rule categories + 241 skill rule categories, mapped to OWASP MCP Top 10 **and** OWASP Agentic AI Top 10.

Local-first. MIT. Free.

Try it: https://aishield.tools/scan
Code: https://github.com/lm203688/aishield

---

## 3. Hacker News

**标题**：`Show HN: Scan an MCP config in one paste, without executing it`

**正文**：

The hard part of a security scanner is rarely the scanning. It's that people have to install something before they find out whether they wanted it.

So we put the existing engine behind a paste box: https://aishield.tools/scan — drop in `claude_desktop_config.json` / `.mcp.json` / a Cursor config, get a 0–100 config score, severity breakdown, server inventory, findings with OWASP categories, and a SARIF download for CI. No install, no signup, no key.

Two things worth being explicit about:

**The hosted page is server-side, so the pasted config does leave your browser.** That's stated on the page rather than buried. If your config contains credentials you'd rather not send anywhere, the local CLI is the same engine with zero network: `npx aishield-mcp-server`. We'd rather lose a few conversions than teach people that a security tool can be vague about data flow.

**Neither path ever executes the config.** Most MCP config scanners spawn the server to read `tools/list` — and since an MCP `command` is arbitrary code, for those tools auditing a hostile config is itself the attack. We gave up `tools/list` and parse statically instead. The cost is real: no visibility into prompt injection hidden in runtime tool descriptions. The benefit is that scanning a config you don't trust can't compromise the machine doing the scan.

We also added a local-first collector, since "scan once" and "stay safe" aren't the same thing: it discovers local MCP configs, re-scans on change, and emits canonical JSONL events plus a compact digest that's idempotent by fingerprint — an unchanged config produces a heartbeat, not a repeat alert. The no-spawn / no-network invariants are pinned at the source level in the test suite (the module must not import `subprocess`, `socket` or `urllib`).

235 MCP rule categories / 241 skill rule categories, mapped to OWASP MCP Top 10 and OWASP Agentic AI Top 10. Local-first, MIT, zero third-party dependencies.

https://github.com/lm203688/aishield · https://aishield.tools/scan

---

## 4. Reddit r/mcp（英文）

**标题**：`We removed the install step: paste an MCP config, get a report`

**正文**：

Every tool in this space (ours included) asks you to install something before it tells you anything. For a security check that's backwards — the moment you're suspicious is the moment you should get an answer.

So https://aishield.tools/scan takes a pasted `claude_desktop_config.json` / `.mcp.json` / Cursor config and returns a score, severity breakdown, server inventory, findings with OWASP categories, and SARIF for CI.

Disclosure, because it matters: the hosted page scans server-side, so **the pasted config is sent to our server**. It's stated on the page. If that's not acceptable for your config, `npx aishield-mcp-server` runs the identical engine with no network at all.

What's constant across both: we never run the `command` in the config. Config scanners usually have to spawn the server for `tools/list`; an MCP `command` is arbitrary code, so for them the scan is an execution. We skip `tools/list` entirely. Tradeoff: we lose runtime tool-description coverage from this path — said plainly rather than glossed.

Also new: a local collector for people who want the config watched instead of checked once — discovers local configs, re-scans on change, emits JSONL events, dedupes by fingerprint so an unchanged config doesn't re-alert. `python -m collector.aishield_collector --once --digest`.

235 / 241 rules, OWASP MCP Top 10 + Agentic AI Top 10, MIT, zero deps.

---

## 5. Reddit / V2EX / 掘金（中文）

**标题**：`扫一个 MCP server 要装东西？现在粘贴一次就行`

**正文**：

这个品类（包括我们自己）有个共同的毛病：想让它告诉你点什么，你得先装点什么。

对安全工具来说这个顺序是反的——你起疑心的那一刻，就该拿到答案。

所以做了 https://aishield.tools/scan：把 `claude_desktop_config.json` / `.mcp.json` / Cursor 配置粘进去，直接出评分、严重度分布、资产清单、带 OWASP 分类的风险项，以及可喂给 CI 的 SARIF。零安装零注册。

**必须说清楚的一件事**：在线页是服务端在跑分析，**粘贴的内容会发到 aishield.tools**。这句话写在页面上，没藏在脚注里。如果配置里有凭证、你不想发出去，用 `npx aishield-mcp-server`——同一个引擎，全程本地零网络。

两条路径有一个共同点：**都不会执行配置里的 `command`**。多数配置扫描器为了读 `tools/list` 必须先启动 server，而 MCP 的 `command` 就是任意代码——对它们来说，「检查是否恶意」这个动作本身包含「执行」。我们放弃了 `tools/list`，纯静态解析。代价说清楚：这条路看不到运行时工具描述里的提示注入。

另外补了个本地持续观测器 Collector：发现本机 MCP 配置、变更即重扫、输出规范化 JSONL 事件，并按指纹幂等——配置没变就只发心跳，不重复告警。20 项契约测试里有一条是源码级断言：模块不得出现 `subprocess` / `socket` / `urllib`。

235 条 MCP 规则 / 241 条 skill 规则，双维覆盖 MCP Top 10 + Agentic AI Top 10，MIT。

---

## 6. 待发布平台清单

| 平台 | 状态 | 备注 |
|---|---|---|
| X / Twitter | 草稿 | 连接器未连接；线程可直接用第 2 节 |
| Hacker News | 草稿 | 手动发；建议工作日 UTC 14:00–16:00 |
| Reddit r/mcp | 草稿 | 主战场；第 4 节英文版 |
| Reddit r/LocalLLaMA | 草稿 | 强调「本地 CLI / Collector 零网络」那一档 |
| V2EX / 掘金 / 少数派 | 草稿 | 中文版直接用第 5 节 |
| Lobsters | 草稿 | 需邀请码 |
| GitHub Discussions | 草稿 | 自仓 Announcements 发一帖，绑定 Release 说明 |
| Dev.to | 草稿 | 正文可直接用支撑文章（英文翻译） |

> 与既有资产的关系：`distribution/x-twitter-promotion-playbook.md`（账号与节奏）、`distribution/agent-directory-submit.md`（目录提交）、`distribution/listings/SUBMIT.md`（收录站）仍适用，本 kit 只补本轮的两个新钩子（零安装入口 + Collector）。

---

## 7. 不变量自查（发布前必过）

- [x] 未宣称「运行时防护」「网关」等未实现能力
- [x] 未宣称能检出运行时工具描述注入（该局限已在正文明写）
- [x] 未在在线页宣称「代码不出机」（**本轮修正**：在线页会把粘贴内容发到服务端，已明示披露 + 给出本地替代路径；并由 `tests/test_scan_inline_page.py::test_scan_page_does_not_misrepresent_data_flow` 钉死）
- [x] 「不执行被扫配置中的命令」承诺在线/本地一致，且未在任何文案中退让
- [x] 「本地 / 不上云」叙事保留，并明确区分「在线页」与「本地 CLI/Collector」两种数据流向
- [x] 双维（MCP Top 10 + Agentic AI Top 10）叙事保留
- [x] 中性信任机构定位未被稀释
- [x] 未改名，统一 aishield.tools
- [x] 无任何 secret / token / PAT 出现在文案
- [x] 量化数字（235 / 241 / HTTP 200）均可由 `/api/v1/health` 与 `tests/run_all.py` 复现
- [x] 竞品引用为公开 README 原文，未做贬损性推断
