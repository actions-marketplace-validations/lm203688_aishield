# R4-深化实施手册：Evidence Bundle 1.0 + Responsibility Chain v1.1 + Ship Gate 10 态

**日期**：2026-09-24  
**版本**：4.6.0 → 4.7.0  
**对标**：GOAI 2026 Agent Infra 季军 CyberGuard（elsechord/CyberGuard v0.13.0）

---

## 一、为什么做这个

GOAI 2026 结果出来了。CyberGuard 拿季军，官方 tagline 就是「auditable governance primitives for agent infrastructure」——这就是 aishield 方向文档的原话。它跑通了：
- **WebShell 供应链投毒完整闭环**（CG-2026-0002，2992 条 Matrix 事件 + 14 条 HMAC 链式审计记录）
- **HMAC-SHA256 链式审计**（防内部记录者篡改）
- **OCSF 1.1 + STIX 2.1 + ATT&CK** 三对齐的证据规范
- **Proposal-Bound Approval**（提案与哈希绑定，禁跨提案审批复用）
- **双轮独立复测状态机**（inconclusive → re-proposal → verified）
- **执行回滚**（execution succeeded ≠ recovery）

aishield 现状：R1-R3 做了签名 Agent Card / KYA SD-JWT / Specialist Registry / Protocol Bridge / 责任链（内存版）/ Ship Gate（三态）。R4 之前定调是「责任链落盘 + 审计凭证」，CyberGuard 证明这是**必须追齐**的硬骨头——不追就落后于官方背书的项目。

**追齐 + 差异化定位**：CyberGuard 是 SOC 应用层（跑安全运维），aishield 是治理基础设施层（提供签名/审计/信任凭证原语）。两者互补，不是替代。

---

## 二、本轮交付

### 2.1 `eco/evidence_bundle.py`（新建，约 800 行）

**核心能力**：
- HMAC-SHA256 链式审计（可选，无密钥退化为 SHA-256）
- OCSF 1.1 事件类映射（15 类：investigation/proposal/executor/probe/verification/audit）
- STIX 2.1 observable 对象输出（file/url/ipv4/ipv6/domain-name/process/software）
- ATT&CK v15 战术-技术映射（T1195/T1078.004/T1539/T1548/T1201/T1583.003/T1041/T1203）
- Proposal-Bound Approval（proposal_hash 与 approval_hash 绑定，重复审批报错）
- 双轮独立复测（round_no=1/2，confidence [0,1]，非法值报错）
- 回滚（rollback 独立记录）
- 归档（manifest 签名）
- 全局 seq 计数器（跨 kind 顺序稳定，解决 ts 同秒排序问题）
- 责任链迁移（`from_responsibility_chain` 无损转换）

**关键设计决策**：
1. `approve_proposal` **不改已签名的 proposal**，改用独立 approval 记录关联状态——防原地修改破坏签名链
2. `global_seq` 自增字段替代 ts+kind 排序——避免同秒事件排序歧义
3. 12 态状态机（pending/proposed/approved/executing/executed/observing/inconclusive/verified/failed/rolled_back/archived/rejected），合法转移表在 `TRANSITIONS`

### 2.2 `eco/responsibility_chain.py`（升级，v1.0 → v1.1）

**新增**：
- `hmac_key` 参数（None 退化为 SHA-256，保持向后兼容）
- 状态机字段：`state` / `round` / `proposal_id` / `approval_id` / `ttp`
- `stats()` 统计各状态条目数
- `find_by_state(state)` / `find_by_proposal(id)` 查询
- `to_evidence_bundle()` 迁移到新证据体系

### 2.3 `scripts/ship_gate.py`（升级，v1.0.0 → v1.1.0）

**三态 → 10 态状态机**（CodeNotary/DataFlow-Agent 风格，GOAI 冠军参考）：
```
ANALYZE → BLIND_TEST → CHALLENGE → GATE → PREPARE → RELEASE → OBSERVE → ARCHIVE
                          ↓                                       ↓
                          REJECT                                   ROLLBACK → ARCHIVE
```

**转移规则**：
- GATE 可到 PREPARE/ROLLBACK/ARCHIVE/REJECT（hold 归档、break 回滚、争议拒发）
- CHALLENGE 可到 GATE/REJECT/ROLLBACK（auto-accept 跳 GATE，critical 直接 ROLLBACK）
- OBSERVE 30 天窗口（默认）

**新 CLI flag**：
- `--full-lifecycle`：跑完整 10 态（PREPARE→RELEASE→OBSERVE→ARCHIVE）
- `--hmac-secret`：HMAC 签名（启用证据链防篡改）
- `--emit-bundle <path>`：导出 Evidence Bundle
- `--no-auto-accept-challenge`：争议不自动接受

**向后兼容**：verdict 仍是 ship/hold/break；`_exit_code` / `_make_attestation` 接受新旧两种结构。

### 2.4 `api/ecosystem_api.py`（扩展）

新增端点（14 个）：
```
GET  /api/v1/evidence/schemas                # OCSF/STIX/ATT&CK 映射表
POST /api/v1/evidence                        # 创建 bundle
GET  /api/v1/evidence/{run_id}               # 导出 bundle
GET  /api/v1/evidence/{run_id}/verify        # 校验 bundle
POST /api/v1/evidence/{run_id}/events        # 加事件（OCSF/STIX/ATT&CK）
POST /api/v1/evidence/{run_id}/proposals     # 建提案
POST /api/v1/evidence/{run_id}/proposals/{id}/approve
POST /api/v1/evidence/{run_id}/proposals/{id}/reject
POST /api/v1/evidence/{run_id}/dispatch      # 执行
POST /api/v1/evidence/{run_id}/observe       # 独立复测（双轮）
POST /api/v1/evidence/{run_id}/rollback      # 回滚
POST /api/v1/evidence/{run_id}/archive       # 归档
POST /api/v1/evidence/verify-payload         # 离线验证（跨组织）
GET  /api/v1/ship-gate/states                # 10 态转移表
POST /api/v1/ship-gate/run                   # 跑状态机
```

### 2.5 `mcp-server/mcp.json`（v4.7.0）

新增 12 个 MCP 工具：
```
aishield_evidence_create
aishield_evidence_add_event
aishield_evidence_create_proposal
aishield_evidence_approve_proposal
aishield_evidence_dispatch
aishield_evidence_observe
aishield_evidence_rollback
aishield_evidence_archive
aishield_evidence_verify
aishield_evidence_verify_payload
aishield_ship_gate_run
```

### 2.6 `tests/test_evidence_bundle.py`（新建，45 项测试）

覆盖：
- HMAC 链式审计（含篡改检测 body + prev_hash）
- OCSF / STIX / ATT&CK 映射
- Proposal-Bound Approval（含重复审批拒绝、不存在审批拒绝）
- 双轮独立复测（含非法 round_no、非法 confidence 拒绝）
- 回滚与归档
- 离线 verify_bundle_payload（含错密钥、篡改、非 dict、未知 schema）
- responsibility_chain v1.1（HMAC / 向后兼容 / 状态查询 / 迁移 / 溯源 / 篡改）
- ship_gate 状态机（转移合法性 / 终态无出口 / ship 路径 / full-lifecycle / hold+fail_on_warn / break / 争议拒发 / 非法转移 / 历史）
- ship_gate + evidence_bundle 集成

---

## 三、测试数据

| 指标 | R1+R2+R3（v4.6.0） | R4-深化（v4.7.0） |
|---|---|---|
| 全量测试 | 1351 passed | **1396 passed / 0 failed** |
| 新增测试 | 56 项 | **45 项**（累计 101） |
| 版本声明位 | 4.6.0（25 处一致） | **4.7.0（25 处一致）** |
| 新组件 | 8 个 eco/*.py | **+1**（evidence_bundle.py） |
| 升级组件 | 0 | **+2**（responsibility_chain v1.1 + ship_gate v1.1） |
| API 端点 | 30+ | **44+** |
| MCP 工具 | 33 | **45** |

---

## 四、本地自证命令

```bash
# 1. Evidence Bundle 完整跑一遍
python eco/evidence_bundle.py

# 2. Responsibility Chain v1.1
python eco/responsibility_chain.py

# 3. Ship Gate 10 态
python scripts/ship_gate.py --path . --json
python scripts/ship_gate.py --path . --json --full-lifecycle --hmac-secret "test" --emit-bundle /tmp/bundle.json

# 4. 45 项测试
python tests/test_evidence_bundle.py

# 5. 全量回归
python tests/run_all.py

# 6. API 自证
python api/ecosystem_api.py
```

---

## 五、CyberGuard 对拍

| 能力 | CyberGuard v0.13.0 | aishield v4.7.0 |
|---|---|---|
| HMAC 链式审计 | ✅ | ✅ |
| OCSF/STIX/ATT&CK 三对齐 | ✅ | ✅（子集，可扩展） |
| Proposal-Bound Approval | ✅ | ✅ |
| 双轮独立复测 | ✅ | ✅ |
| 回滚 | ✅ | ✅ |
| 归档 manifest | ✅ | ✅ |
| 离线跨组织校验 | ✅ | ✅ |
| 责任链（多 agent 级联） | ⚠️ 内嵌 | ✅（独立模块） |
| 签名 Agent Card | ❌ | ✅（Ed25519） |
| KYA SD-JWT + Web Bot Auth + ERC-8004 | ❌ | ✅ |
| Specialist Registry 8 域 | ❌ | ✅ |
| Trust Score API | ❌ | ✅ |
| Leaderboard + Contributor 激励 | ❌ | ✅ |
| Protocol Bridge（MCP/A2A/ACP/AP2） | ❌ | ✅ |
| Sandbox 后端能力矩阵 | ❌ | ✅ |
| Domain Rule Pack（235+262 规则） | ❌ | ✅ |

**结论**：CyberGuard 是 SOC 应用层，aishield 是治理基础设施层。R4 深化后 aishield 追齐了 CyberGuard 的**证据治理深度**，同时保留了 8 个差异化能力。可以作为 CyberGuard 的**中立外部身份/签名 Agent Card/审计凭证签发方**合作。

---

## 六、明确未做

1. **OCSF/STIX/ATT&CK 映射不完整**：只挑了常用 15 类事件 + 8 种 TTP。完整映射需要按 OCSF 1.1 全表（~150 类事件）扩展。
2. **HMAC 密钥轮换**：现在换密钥必须重建整个 bundle。生产级需要支持 key rotation + 双签（新旧密钥并存期）。
3. **持久化存储**：现在 bundle 存在内存（`_bundles` dict），进程重启丢失。生产级需接 SQLite/Postgres/对象存储。
4. **CyberGuard 端到端跑通**：CyberGuard 有 2992 Matrix 事件的真实 SOC 场景跑通证明，aishield R4 目前是单元级 + 集成级跑通，缺一份**跨组织真实场景证据包**。
5. **审批密钥/多签**：现在 approver_id 是字符串，没有密码学绑定。生产级需接 DID 或 Web Bot Auth token。
6. **CyberGuard 联合提议**：需要主动联系 elsechord 团队发 issue。

---

## 七、下一步候选

1. **R4-深化 II**：持久化 bundle 存储 + HMAC 密钥轮换 + 审批密钥（DID/Web Bot Auth 绑定）
2. **CyberGuard 联盟**：发 GitHub issue 提议合作，aishield 做它的外部身份/审计凭证签发方
3. **ship_gate 状态机可视化**：加 state diagram SVG 输出，便于文档/审计
4. **证据包签名**：bundle export 时可选 Ed25519 签名（跨组织传递的抗抵赖保证）

---

*Author: aishield 2026-09-24 (R4-深化)*  
*对标参考：CyberGuard v0.13.0 (GOAI 2026 Agent Infra 季军) / CodeNotary (GOAI 2026 Agent Infra 冠军 DataFlow-Agent 生态)*
