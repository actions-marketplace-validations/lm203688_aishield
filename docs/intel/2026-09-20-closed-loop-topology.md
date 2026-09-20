# AIShield 闭环拓扑诊断（2026-09-20）

盘点 20 个 GitHub Actions workflow + 5 条本地自动化，判定重叠/空转/脆弱单点，
并直接修掉能修的。

## 一、拓扑总览

### CI 主干（6 条定时）
| Workflow | 定时 | 职责 |
|---|---|---|
| `closed-loop-spine.yml` | 03:17 UTC | 串行编排 9 个子 workflow，是闭环脊柱 |
| `geo-indexnow-submit.yml` | 09:20 UTC | IndexNow 收录提交 + key 校验 |
| `data-scan-flywheel.yml` | spine 调用 | 批量扫描入库 |
| `threat-intel-feed.yml` | spine 调用 | 威胁情报采集 |
| `project-digest.yml` | spine 调用 | 项目摘要回写 |
| `channel-distribution.yml` | spine 调用 | 渠道分发状态同步 |

### 自愈/守门（4 条）
| Workflow | 触发 | 职责 |
|---|---|---|
| `ci.yml` | push/PR | 测试 + 版本门禁 + workflow 校验 |
| `unified-security-scan.yml` | push/PR | 仓库自身安全态势扫描 |
| `self-heal-closed-loop.yml` | schedule+dispatch | 闭环自愈（重跑失败子 workflow） |
| `npm-self-heal.yml` | schedule+dispatch | npm 发布自愈 |

### 发布/分发（4 条）
`publish-npm` / `publish-mcp-registry` / `deploy-server` / `pages`

### 辅助（6 条）
`issue-labeler` / `meta-monitor` / `stale` / `rule-promoter` / `feature-closed-loop` / `install-cf-token`

### 本地自动化（5 条，仅用户机器在线时运行）
| 自动化 | 节奏 | 职责 | 可否迁入 CI |
|---|---|---|---|
| Tech Radar 02:00 | 每日 | 跑 `tech_radar.py` 采集信号 | 否——需 WebSearch/agent 推理 |
| 每日安全守夜 08:30 | 每日 | `self_scan.py` + 全量测试 + 线上存活 | **部分**：self_scan 不在 CI；测试与 ci.yml 重叠（第二意见） |
| 周度竞争情报 周一 | 每周 | WebSearch 竞品 | 否——需 agent 推理 |
| 分发缺口巡检 周六 | 每周 | curl 漂移检测 + 台账更新 | 可，但当前保留（需判断 drift 语义） |
| 反馈合并周报 周日 | 每周 | 读 digest 汇总 | 否——读本地 digest 文件 |

## 二、空转诊断

### ✅ 无真正空转的闭环
5 条自动化职责互不重叠，20 个 workflow 各有明确触发与职责。没有「跑了但产出
为零」的闭环。

### 🟡 命名误导（非故障）
`closed-loop-spine.yml` 第 1 步注释叫「雷达数据采集」，但实际接的是
`data-scan-flywheel.yml`（批量扫描入库），与真正的雷达
（`tech_radar.py`，仅本地自动化跑）不是一回事。已在本文件记录，
不改注释（改注释需动 spine，风险大于收益）。

### 🟡 本地自动化 = 单点依赖
5 条自动化只在用户机器在线时运行。`self_scan.py`（台账外自检）
**不在任何 CI workflow 里**——如果用户机器离线数天，台账外发布物
（npm 源、harness 骨架、Marketplace Action 等）的安全自检会断档。
这是设计取舍（self_scan 需读本地仓库全树 + 本地 allowlist），
不是 bug，但值得知道。

## 三、已修复的红灯（本轮）

### 🟥 `geo-indexnow-submit.yml`：9/9 运行全红（已修）
**根因**：workflow 级 `permissions: contents: read`，心跳步骤的
`git_push_safe.sh` 每次 push 403 → 重试 5 次 → `exit 1` → 整条 job 失败。
核心工作（key-check + submit）**在全部 9 次运行中都成功了**——只是末步
装饰性心跳把绿灯拖成红灯。

**修法（双层）**：
1. `permissions: contents: read → contents: write`，让心跳 push 真能成功。
2. 心跳 push 加 `|| true`：心跳是 best-effort 状态回写，不应盖过
   key-check/submit 的真实红绿灯；下一轮会全量重算快照。

**验证**：`validate_workflows.py` 20/20 通过。

### 横向核查结论
扫描全部 20 个 workflow 的 push 权限匹配：
- `ci.yml`：workflow 级无 permissions，但 push 步骤在 job 级已提权（339/399 行）→ 无问题
- `publish-npm.yml`：`git push` 只出现在注释里，实际不 push → 无问题
- 其余 17 个：要么有 `contents: write`，要么不 push → 无问题

**只有 geo-indexnow 一个真问题。**

## 四、已更新的过期基线

| 自动化 | 旧基线 | 新基线 |
|---|---|---|
| 每日安全守夜 | 测试 670 通过 | **1199 通过 / 26 跳过** |
| 分发缺口巡检 | v4.2.2 / 227 规则 / 6 工具 | **v4.3.0 / 235 规则 / 7 工具** |

过期基线会导致「测试失败数 > 0」误判（实际 0）或「线上版本漂移」误判
（实际 4.3.0 已是最新）。已写入两条自动化的 prompt。

## 五、不需要修的（记录在案）

- **`tech_radar.py` 不被任何 workflow 调用**：by design，它需要
  WebSearch/agent 推理能力，CI 跑不了。spine 的「雷达」注释是误导，
  不是故障。
- **`self_scan.py` 不在 CI**：by design，需读本地全树 + allowlist。
  守夜是唯一执行者，已标注。
- **5 条自动化不可融合**：各自唯一职责（雷达/自检/竞品/分发/周报），
  无重叠可消。

## 六、遗留（需用户本人操作）

- 吊销曾硬编码进 public 仓库历史的旧 Cloudflare token
  （https://dash.cloudflare.com/profile/api-tokens）
- aishield.tools CF Pages Retry（3 个 cfut_ token 权限不足，无法 API 触发）
