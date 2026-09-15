# AIShield × TeamAI（腾讯开源 teamai-cli）匹配策略

> 2026-09-15 用户问询。结论：**TeamAI 是 AIShield 目前最顺手的分发渠道之一**——它把 skills/rules/hooks/MCP 经 Git + MR 审核分发到 11 种 agent（Claude Code / Codex / Cursor / **WorkBuddy** / Qoder / OpenClaw …），且自带 `block-secret` hook 只做密钥扫描（门禁还 `|| true` 永不阻断）。AIShield 正好补它的「全量 skill/MCP 安全门禁」真空。

## 一、为什么匹配

| 条件 | 是否成立 |
|------|----------|
| TeamAI 分发 skills/hooks/MCP | ✅ 原生 |
| TeamAI 生态缺「全量安全门禁」 | ✅ 它只有 `block-secret`（密钥），且 `|| true` 不阻断 |
| AIShield 是标准 MCP server + 可扫 SKILL.md | ✅ 零适配接入 |
| 本地优先 / 零依赖 同频 | ✅ TeamAI 也「无中心服务、用 Git」 |

→ 三件事都成立，不是凑。

## 二、两条接入路径

### 路径 A（推荐，零适配）：MCP 桥接 + teamai skill
- AIShield 已是标准 MCP server（6 个 `aishield_*` 工具，npm `aishield-mcp-server` 4.3.0）。
- 在团队仓库 `skills/aishield/SKILL.md`（见本目录草稿）声明，teamai 自动分发到各 agent 原生目录；agent 在装/跑不可信 MCP/skill 前先调 AIShield 扫一遍。

### 路径 B（强门禁）：`block-unscanned-skill` hook
- 在 `hooks/hooks.yaml` 声明一个 SessionStart hook，扫描团队 `skills/` 与 MCP 配置，低分即阻断。
- 示例见本目录 `teamai-hook.yaml`。
- 关键：hook 调用 `python -m scanner.cli scan` 扫**目标路径**，**绝不执行目标 skill 的任何代码** —— 与「绝不 spawn 被扫配置」不变量一致。

## 三、优先级判断
- 机制真实、成本低（写一份 SKILL.md + 一个 hook yaml）、触达 11 种 agent（含我们自己的 WorkBuddy）。
- 相对其它渠道：比 ClawHub（被 squat）、MCP.so（被同名云 SaaS占）更顺；与 DeepSeek Harness 并列「agent-native 提前占领」最佳落点。

## 四、待办
- **用户**：① `teamai source add` 或 fork teamai-hub 模板，把本目录 `skills/aishield/` + `teamai-hook.yaml` 提 MR；② 实际 `teamai push` 分发。
- **AI 已准备**：本目录 `teamai-hook.yaml`（hook 示例）+ SKILL.md 草稿骨架；并更新 `competitive-landscape.md` §八、对外 GEO 资产（待用户确认发布）。
