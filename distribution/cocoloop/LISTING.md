# CocoLoop / CLS-Certify 上架草稿（hub.cocoloop.cn）

> 提交方式：在 CocoLoop 商店提交公开 GitHub 仓库，经平台 CLS 安全认证后上架。本草稿直接复制填写即可。

---

**Skill name**: AIShield
**Category**: Security / Supply-chain
**Repository**: https://github.com/lm203688/aishield
**Install**: `npm i -g aishield-mcp-server`（或经 MCP 桥接，在 agent 配置中将 `aishield-mcp-server` 加为 MCP tool provider —— 零安装、零适配）

**Short description** (listing card):
> 本地、离线、零依赖的 AI 工具安全扫描器，专扫 MCP server / agent skills / GPTs / prompts。在 agent 安装或运行不可信工具前，静态检测供应链投毒、prompt 注入、隐藏命令、越权与数据外传 —— 你的代码永不出本机。双维覆盖 OWASP MCP Top 10 与 Agentic AI Top 10（ASI01–10）。

**Why install it** (detail page):
- CocoLoop 的 CLS 认证是上架门槛；AIShield 是开发者**自己**能给技能/插件做「安装前安全门禁」的工具。
- 纯静态推断：绝不执行被扫配置里的任何命令（read-only），避免「为看工具列表先把恶意配置跑一遍」的陷阱。
- 4 维评分（安全/隐私/质量/性能）+ 可选认证 badge；输出 SARIF / CycloneDX SBOM，可直接进 CI 门禁。
- 与 CLS 互补：CLS 用大模型深度检测（需外部 API），AIShield 本地零依赖、可离线、秒级 —— 两者可叠加使用。

**Risk-review note** (honest about what it guarantees):
> AIShield 本身 MIT、完全本地。它扫描目标路径、不运行目标代码。和任何安全工具一样，最终权威仍是源码 —— 锁定版本、亲自阅读。

**Tags**: `security`, `supply-chain`, `mcp`, `scanner`, `local`, `offline`
