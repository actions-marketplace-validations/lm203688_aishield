"""Agent 基础设施开源生态接入层（v4.8.2）。

对 laya / nasiko / agent-desktop 等 agent-infra 类开源项目做：
  平台开源扫描(scanner.engine) → 封装(MCP 适配器骨架) → 二次研发清单

设计原则（对齐 AIShield 零依赖、可离线）：
  - 在线：repo_url → scanner.engine.scan（经 api.github.com 拉源码）
  - 离线：local_path / 内存 files → 直接复用 engine 的静态/依赖/密钥分析 + 评分
"""
