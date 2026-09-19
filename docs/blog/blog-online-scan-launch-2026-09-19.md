---
title: "零安装的第一次接触：把「扫一个 MCP server」的成本降到一次粘贴"
date: 2026-09-19
tags: [mcp, security, online-scan, local-first, agent-native, collector]
---

# 零安装的第一次接触

## 一个转化率问题，而不是能力问题

AIShield 的能力一直不缺：235 条 MCP 规则、241 条 skill 规则、OWASP MCP Top 10 + Agentic AI Top 10 双维覆盖、零第三方依赖、扫描时绝不执行被扫配置里的命令。

但用户数不涨。原因不在引擎，而在**第一次接触的摩擦**：

```
看到一篇文章 → 想验证一下自己的配置 → 要先装 Node → npx → 读懂 CLI 参数 → 才有第一个分数
```

这条路径上每一步都会掉人。而一个安全工具的第一次价值交付，本该发生在**用户产生怀疑的那一秒**。

所以这一轮我们做的不是加规则，是**拆掉台阶**。

## `/scan`：粘贴即出分

新上线的在线扫描页 `https://aishield.tools/scan`：把 `claude_desktop_config.json` / `.mcp.json` / Cursor 配置内容粘进去，立刻得到

- **配置安全评分**（0–100）与五个维度的分项
- **严重度分布**（critical / high / medium / low / info）
- **资产清单**：发现了哪些 server、什么传输方式、推断出的能力
- **风险清单**：每条带 OWASP 分类、证据、修复建议
- **SARIF 报告下载**：直接喂给 GitHub Code Scanning 或任何 SARIF 流水线
- **接入 Agent 的命令**：从「看一眼」直接到「接进流程」

零安装、零注册、不需要 API key。

## 它没有新建后端

这是刻意的：`/scan` 页复用**已经在跑、已经被测试覆盖**的两个端点：

```
POST /api/v1/scan/client-config   → inventory + findings + summary（含 config_score）
POST /api/v1/export/sarif         → SARIF 2.1.0
```

新增的只有一个静态页和一条路由。**同一个引擎、同一套规则、同一份脱敏逻辑**——在线看到的结果和本地 CLI 跑出来的完全一致，不存在「网页版是演示、真实版在别处」。

## 必须说清楚的边界

在线扫描页是**服务端**在跑静态分析。也就是说：**你粘贴的内容会发送到 aishield.tools**。

这句话必须写在页面上，而不是藏在某段小字里。理由有两个，都很实际：

1. 一个安全工具如果为了转化率去模糊数据流向，它教给用户的第一课就是错的。
2. 「扫一份来路不明的配置，不把自己搭进去」是这个品类的核心承诺；把这条承诺讲清楚，比多留 3% 的转化重要得多。

所以我们做了两件事：**删掉**了页面上原来那句有歧义的「代码不出机」，**加上**了明示披露与替代路径——

> 提示：粘贴的内容会发送到 aishield.tools 进行静态分析（绝不执行其中的命令）。若配置含敏感信息、要求完全本机处理，请改用本地扫描：`npx aishield-mcp-server`，或 `python -m collector.aishield_collector --once`。

注意这里**没有**从「不执行命令」退让半步：无论在线还是本地，AIShield 都**不会 spawn 被扫配置里的 `command`**。这一点在线形式上同样成立——服务端只是解析文本。

## 三档路径，按信任等级自选

| 你的需求 | 用什么 | 数据流向 |
|---|---|---|
| 快速看一眼，配置不含敏感信息 | **`/scan` 在线页** | 配置文本 → aishield.tools（静态分析，不执行） |
| 配置含凭证，或要进 CI | **`npx aishield-mcp-server`**（CLI） | 完全本机，零网络 |
| 想持续盯着，配置一改就重扫 | **AIShield Collector**（`collector/`） | 完全本机，输出 JSONL 事件流 |

第三条是这次一并落地的新能力：`collector` 是一个**本地优先的持续观测器**——发现本机 MCP 客户端配置、变更即重扫、把结果写成**规范化事件流**（`CollectorStarted` / `ConfigDiscovered` / `FindingRaised` / `ScanCompleted` / `CollectorHeartbeat`），并附带一个**按指纹幂等**的紧凑信任摘要（配置不变 → 指纹不变 → 只发心跳，不重复告警）。

```bash
python -m collector.aishield_collector --once --digest
python -m collector.aishield_collector --watch --interval 60 --out events.jsonl
```

它和在线页的关系不是替代，而是**同一条漏斗的下游**：先用 `/scan` 零成本验证价值，再按需要下沉到本地持续化。

## 可以自己复现的数字

| 项 | 值 | 怎么复现 |
|---|---|---|
| 规则覆盖 | 235 MCP / 241 skill | `GET /api/v1/health` → `rules_breakdown` |
| `/scan` 可用性 | HTTP 200 | `curl -sS https://aishield.tools/scan` |
| 静态扫描承诺 | 不执行任何被扫命令 | `tests/test_collector.py` 源码级断言：无 `subprocess` / `socket` / `urllib` |
| 在线/本地结果一致 | 同一引擎 | 两处都调 `scanner.client_discovery` |

## 结语

品类里的竞争，眼下慢慢从「谁规则多」转向「谁被真正用起来」。规则数是可以被追平的，**第一次接触的摩擦不是**。

`/scan` 做的是把摩擦降到一次粘贴；Collector 做的是把「用一次」变成「一直在用」。两件事都指向同一个判断：**可信的东西，必须先够得着。**

- 在线试用：https://aishield.tools/scan
- 本地安装：`npx aishield-mcp-server`
- 源码：https://github.com/lm203688/aishield
