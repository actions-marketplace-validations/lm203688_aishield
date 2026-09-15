# AIShield × TeamAI（腾讯开源 teamai-cli）匹配策略

> 2026-09-15 更新。结论：**TeamAI 是 AIShield 目前最顺手的分发渠道之一**——它把 skills/rules/hooks/MCP 经 Git + MR 审核分发到 11 种 agent（Claude Code / Codex / Cursor / **WorkBuddy** / Qoder / OpenClaw / Kiro …），且自带 `block-secret` hook 只做密钥扫描（且 `|| true`，**永不阻断**）。AIShield 正好补它的「全量 skill/MCP 安全门禁」真空。

## 〇、最重要的更正：TeamAI 不需要注册账号

TeamAI **没有平台账号体系**——它是 **git-native** 的：团队共享仓库本身就是唯一的真相源与分发通道。
所以「上架 TeamAI」= **把 AIShield 仓库做成一个合法的 TeamAI source repo**，任何团队一行命令即可订阅：

```bash
teamai source add https://github.com/lm203688/aishield.git --name aishield
```

**这一步已由 AI 完成（无账号、无需人工）**，落在 AIShield 仓库根：

- `teamai.yaml` —— 声明 `publicSkills: [aishield-scan]`（只有显式列出的 skill 才会分发给订阅方）；
- `skills/aishield-scan/SKILL.md` —— 实际下发的 skill。

> 用户侧唯一可选的额外动作：在**自己团队**的 `hooks/hooks.yaml` 里加上 AIShield 硬门禁（见本目录 `teamai-hook.yaml`）。这不是「注册」，是团队自己的配置。

## 一、为什么匹配

| 条件 | 是否成立 |
|------|----------|
| TeamAI 分发 skills/hooks/MCP | ✅ 原生 |
| TeamAI 生态缺「全量安全门禁」 | ✅ 它只有 `block-secret`（密钥），且 `|| true` 不阻断 |
| AIShield 是标准 MCP server + 可扫 SKILL.md | ✅ 零适配接入 |
| 本地优先 / 零依赖 同频 | ✅ TeamAI 也「无中心服务、用 Git」 |

→ 三件事都成立，不是凑。

## 二、两条接入路径

### 路径 A（推荐，零适配）：MCP 桥接 + TeamAI skill
- AIShield 已是标准 MCP server（6 个 `aishield_*` 工具，npm `aishield-mcp-server` 4.3.0）。
- 已随 AIShield 仓库发布 `skills/aishield-scan/SKILL.md`；订阅方 `teamai pull` 后自动落到各 agent 原生目录（`~/.claude/skills/` 等），agent 在装/跑不可信 MCP/skill 前先调 AIShield 扫一遍。

### 路径 B（强门禁）：`aishield-scan-skills` hook
- 在**团队仓库**的 `hooks/hooks.yaml` 声明一个 `SessionStart` hook，扫描项目 skills 与 MCP 配置，默认仅 **CRITICAL** 阻断。
- 示例见本目录 `teamai-hook.yaml`。
- **真实入口**：hook 调用的是 `action_entrypoint.py` —— AIShield 的 env 驱动一次性 CLI（与 GitHub Action 同源，实测 `exit 0/1` 符合 `fail_on`），**不是**早期草稿里臆造的 `python -m scanner.cli`（该文件不存在）。核心不变量「绝不执行被扫配置里的命令」保持不变。

## 三、优先级判断
- 机制真实、成本低（一份 `teamai.yaml` + 一份 SKILL.md + 一个 hook yaml）、触达 11 种 agent（含我们自己的 WorkBuddy）。
- 相对其它渠道：比 ClawHub（被 squat）、MCP.so（被同名云 SaaS 占）更顺；与 DeepSeek Harness 并列「agent-native 提前占领」最佳落点。

## 四、待办
- ✅ **已完成（AI）**：AIShield 成为合法 TeamAI source（`teamai.yaml` + `skills/aishield-scan/SKILL.md`）+ 修正 hook 为真实入口。
- **用户可选**：若要在自有团队启用硬门禁，把 `teamai-hook.yaml` 内容并入团队仓库 `hooks/hooks.yaml`，然后 `teamai hooks inject`。
- **AI 已准备**：本目录 `teamai-hook.yaml`；并更新 `competitive-landscape.md` 与 `docs/agent-landscape-2026-09.md`。
