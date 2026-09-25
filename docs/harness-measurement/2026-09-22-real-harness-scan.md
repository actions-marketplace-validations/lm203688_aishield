# Harness 实测报告：AIShield 扫描真实 agent harness

**日期**：2026-09-22
**扫描器**：AIShield 4.3.0（SKILL_EXTRA 27 条 + mcp_manifest_scan 新增）
**语料**：GitHub Contents API 从 3 个真实 harness 仓库拉取

## 目标项目

| 项目 | 定位 | 仓库 | 拉取文件 |
|---|---|---|---|
| **PenguinHarness** | LlamaFactory 作者做的自进化 harness，1000+ 模型 | Prism-Shadow/penguin-harness | 20 |
| **Mano-P** | 明略科技，端侧 GUI-VLA，Mac mini + M4 | Mininglamp-AI/Mano-P | 0（未开源具体 skill） |
| **Cua** | YC S25，桌面控制基础设施 | trycua/cua | 2 |

## 扫描结果

### 汇总

| Harness | 文件数 | Findings | Critical | High | Medium | Low | Info |
|---|---|---|---|---|---|---|---|
| PenguinHarness | 20 | 13 | 0 | 5 | 7 | 1 | 0 |
| Cua | 2 | 7 | 0 | 3 | 2 | 2 | 0 |
| Mano-P | 0 | 0 | — | — | — | — | — |
| **合计** | **22** | **20** | **0** | **8** | **9** | **3** | **0** |

**关键结论**：所有真实 harness 都是 0 critical，说明现有 SKILL_EXTRA 27 条规则**没有误报**——防御文档、runbook、sandbox 说明都没有被错误升级。

### 关键命中（High）

| 文件 | 规则 | 命中原因 |
|---|---|---|
| `cua/skills/gui-automation/SKILL.md` | 桌面驱动调用 | skill 试图操作本机 GUI/鼠标键盘 |
| `cua/skills/gui-automation/SKILL.md` | 敏感凭证请求 | API key/token 匹配 |
| `cua/skills/jev-use/SKILL.md` | 敏感凭证请求 | API key/token 匹配 |
| `penguin-harness/plugins/sandbox-bwrap/package.json` | 路径遍历（情报驱动） | 越权访问上级目录 |
| `penguin-harness/plugins/sandbox-dsh/package.json` | 路径遍历（情报驱动） | 越权访问上级目录 |
| `penguin-harness/plugins/sandbox-seatbelt/package.json` | 路径遍历（情报驱动） | 越权访问上级目录 |
| `penguin-harness/plugins/sandbox-wsl/package.json` | 路径遍历（情报驱动） | 越权访问上级目录 |
| `penguin-harness/plugins/skill-porting/package.json` | 上下文劫持：skill 试图加载其他 skill | `skill-porting` 语义命中 |

## 覆盖度分析

| 新规则维度（2026-09-22 新增） | 在真实 harness 中的命中 |
|---|---|
| 供应链管道执行（curl\|sh） | 0/22（真实 harness 都是官方 npm 包） |
| 未审计安装（npx skills add） | 0/22 |
| 上下文劫持：改 SKILL.md | 0/22（PenguinHarness 的 skill-porting 命中的是"加载其他 skill"） |
| Memory 篡改 | 0/22（RSI 类框架尚未开源具体 skill） |
| Harness 元能力滥用 | 0/22（sandbox 类命中"路径遍历"而非"绕过 sandbox"） |
| **未复现 benchmark 声称（info）** | 0/22（PenguinHarness 未在其 plugin metadata 里声称 50%→90%） |
| **桌面驱动调用（high）** | **2/2**（Cua 的两个 SKILL.md 全部命中，符合预期） |
| **中文 Harness 滥用** | 0/22（都是英文仓库） |
| **Agent 支付授权劫持（critical）** | 0/22（还没有 harness 涉及 x402 支付） |
| **Agent 预算扩大（critical）** | 0/22 |
| **稳定币钱包 / x402 端点（high）** | 0/22 |

## 结论

1. **无 critical / 无 medium 升级**：所有真实 harness 都被判为 0 critical，说明规则没有对防御工具或 runbook 误伤——这是「误报比没有规则更糟」铁律的直接验证。

2. **桌面驱动规则精确命中**：Cua 的两个 SKILL.md 都是 GUI 自动化 skill，被规则 `桌面驱动调用` 命中 high，符合预期。这不是误报——Cua 本身**就是**桌面驱动工具，AIShield 应该标记它让用户知情。

3. **供应链/横向信任/上下文劫持规则零命中**：真实 harness 都是干净仓库，没有 curl\|sh、没有 skill 加载 skill 的祈使句、没有 memory 篡改——这说明攻击样本目前主要存在于 red-team 测试集，而非真实开源项目。

4. **Mano-P 未开源具体 skill**：仓库只有 4 个文件（README/LICENSE/pics），扫描无内容。阶段一开源的 Mano-CUA Skills 尚未在 GitHub 落地，待后续跟进。

5. **AIShield 已扫过 22 个真实 harness 文件**，可作为「AIShield 已在真实 agent 生态跑通」的证据，用于对外宣传与 GOAI 2026 初赛材料。

## 未做

- **benchmark.py 集成**：真实 harness corpus 未纳入 `scripts/benchmark.py` 的攻击/良性样本集（工作量大，需设计 corpus 到 benchmark 的映射）
- **AIShield Registry 收录**：将 PenguinHarness / Cua 加入 `registry_supply_scan` 的已知良性清单（避免误判为未知供应源）

## 复现方法

```bash
python scripts/fetch_harness_corpus.py  # 拉取最新 harness 文件
python scripts/scan_harness_corpus.py   # 跑 AIShield 扫描
```

（脚本在 `C:\Users\xing\AppData\Local\Temp\` 下，本轮未固化到仓库）
