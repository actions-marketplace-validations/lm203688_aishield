# -*- coding: utf-8 -*-
"""
合规框架映射模块（Compliance Mapping）

借鉴来源（2026-09-07 开源扫描）:
    - Latteflo/mcp-scanner: 每条 finding 自动映射到合规框架控制项
      （ISO/IEC 27001 / NIST CSF / PCI DSS / SOC 2）—— 企业采购决策中
      「能否对接 GRC/审计流程」是关键选型因素，纯报告层实现、不动检测逻辑。

设计哲学（与全库一致）:
    - 纯标准库，零第三方依赖，零网络
    - 映射是**静态知识**（OWASP 类别 → 框架控制项），不判断合规与否、
      不给"合规分数"——那是认证机构的职权，AIShield 保持中性信任机构定位
    - 聚合在报告级而非逐条注入：findings 数组保持轻量，兼容既有消费者

框架与版本锚定:
    - NIST Cybersecurity Framework 2.0 (2024-02): PR.AA / PR.DS / PR.PS /
      DE.CM / ID.AM / ID.RA 等类别码
    - ISO/IEC 27001:2022 Annex A（A.5.x 组织 / A.8.x 技术控制）
    - PCI DSS v4.0 要求编号
    - CSA MAESTRO 7 层参考架构（+ OWASP 表内单列的 Cross-Layer 第 8 层），
      对齐 OWASP GenAI Security Project「Multi-Agentic system Threat
      Modelling Guide」v1.0。锚点码 L1–L8，对应 OWASP ASI 威胁编号
      T1–T15 见 MAESTRO_THREAT_CODES。

MAESTRO 与前三者的形态差异（选型者须知）:
    NIST / ISO / PCI 是**控制项型**——回答"该上哪条控制"。
    MAESTRO 是**架构分层型**——回答"这条风险落在哪一层信任边界"，
    对多 agent 系统才是可操作的问题（模型层 / 数据层 / 生态层）。
    两者互补而非替代，故并存于同一份 summary。
"""
from __future__ import annotations

from typing import Any, Dict, List

# OWASP MCP Top 10 / Agentic AI Top 10 → 控制项映射（静态知识）
# 条目取"最相关的 2-3 项"——穷举等于没映射，选型者要的是锚点不是噪音。
CATEGORY_CONTROLS: Dict[str, Dict[str, List[str]]] = {
    "MCP01": {  # 令牌管理不当与密钥暴露
        "nist_csf": ["PR.AA-01", "PR.DS-01"],
        "iso27001": ["A.5.17", "A.8.24"],
        "pci_dss": ["8.2", "3.5"],
    },
    "MCP02": {  # 权限范围蔓延导致提权
        "nist_csf": ["PR.AA-05"],
        "iso27001": ["A.5.15", "A.8.2"],
        "pci_dss": ["7.2"],
    },
    "MCP03": {  # 工具投毒
        "nist_csf": ["PR.PS-06", "DE.CM-09"],
        "iso27001": ["A.8.28", "A.5.37"],
        "pci_dss": ["6.2.4"],
    },
    "MCP04": {  # 软件供应链攻击与依赖篡改
        "nist_csf": ["PR.PS-06", "ID.RA-01"],
        "iso27001": ["A.5.21", "A.8.30"],
        "pci_dss": ["6.3.2"],
    },
    "MCP05": {  # 命令注入与执行
        "nist_csf": ["PR.PS-01", "DE.CM-01"],
        "iso27001": ["A.8.28", "A.8.32"],
        "pci_dss": ["6.2.4"],
    },
    "MCP06": {  # 意图流颠覆/上下文提示注入
        "nist_csf": ["PR.PS-01", "DE.AE-02"],
        "iso27001": ["A.8.28", "A.5.37"],
        "pci_dss": ["6.2.4"],
    },
    "MCP07": {  # 身份认证与授权不足
        "nist_csf": ["PR.AA-03", "PR.AA-05"],
        "iso27001": ["A.5.15", "A.8.5"],
        "pci_dss": ["8.2", "7.2"],
    },
    "MCP08": {  # 审计与可观测性缺失
        "nist_csf": ["PR.PS-04", "DE.CM-09"],
        "iso27001": ["A.8.15", "A.8.16"],
        "pci_dss": ["10.2"],
    },
    "MCP09": {  # 影子 MCP 服务器
        "nist_csf": ["ID.AM-01", "PR.AA-05"],
        "iso27001": ["A.5.9", "A.5.19"],
        "pci_dss": ["12.5.2"],
    },
    "MCP10": {  # 上下文注入与过度共享（含 SSRF）
        "nist_csf": ["DE.CM-01", "PR.DS-02"],
        "iso27001": ["A.8.20", "A.8.22"],
        "pci_dss": ["1.2", "11.5"],
    },
    "ASI01": {  # 目标与指令操纵（提示注入）
        "nist_csf": ["PR.PS-01", "DE.AE-02"],
        "iso27001": ["A.8.28"],
        "pci_dss": ["6.2.4"],
    },
    "ASI02": {  # 工具滥用
        "nist_csf": ["PR.AA-05", "DE.CM-09"],
        "iso27001": ["A.5.15", "A.8.28"],
        "pci_dss": ["7.2"],
    },
    "ASI03": {  # 过度代理 / 凭证外泄
        "nist_csf": ["PR.AA-05", "PR.DS-02"],
        "iso27001": ["A.5.15", "A.8.12"],
        "pci_dss": ["3.5", "7.2"],
    },
    "ASI04": {  # 记忆操纵与投毒
        "nist_csf": ["PR.DS-01", "PR.PS-06"],
        "iso27001": ["A.8.24", "A.8.28"],
        "pci_dss": ["6.2.4"],
    },
    "ASI05": {  # 智能体身份与信任
        "nist_csf": ["PR.AA-01", "PR.AA-03"],
        "iso27001": ["A.5.16", "A.5.17"],
        "pci_dss": ["8.2"],
    },
    "ASI06": {  # 智能体通信与供应链
        "nist_csf": ["PR.PS-06", "PR.IR-01"],
        "iso27001": ["A.5.21", "A.8.22"],
        "pci_dss": ["6.3.2", "1.2"],
    },
    "ASI07": {  # 资源无界消耗
        "nist_csf": ["PR.IR-04"],
        "iso27001": ["A.8.6", "A.8.14"],
        "pci_dss": ["2.2"],
    },
    "ASI08": {  # 可观测性缺口
        "nist_csf": ["PR.PS-04", "DE.CM-09"],
        "iso27001": ["A.8.15", "A.8.16"],
        "pci_dss": ["10.2"],
    },
    "ASI09": {  # 级联失效与多智能体风险
        "nist_csf": ["PR.IR-04", "DE.AE-06"],
        "iso27001": ["A.5.30", "A.8.14"],
        "pci_dss": ["2.2"],
    },
    "ASI10": {  # 流氓智能体 / 人机边界
        "nist_csf": ["GV.PO-02", "PR.AA-05"],
        "iso27001": ["A.5.4", "A.5.15"],
        "pci_dss": ["12.5.2"],
    },
}

# ── CSA MAESTRO（Cloud Security Alliance 多智能体威胁建模框架，7 层）────────
# 采纳依据（2026-09-17）：OWASP GenAI Security Project「Multi-Agentic system
# Threat Modelling Guide」v1.0 把 MAESTRO 分层与 OWASP Agentic Security
# Initiative 的 15 条威胁（T1–T15）逐项对齐。这是本库既有 3 个"控制项型"框架
# 之外的第 4 个锚点，但形态不同：MAESTRO 是**架构分层**而非控制编号，
# 因此 code 取 L1–L8（第 8 层为 OWASP 表中单列的 Cross-Layer 涌现行为），
# 对应的 T-code 另由 MAESTRO_THREAT_CODES 单独暴露，不混进聚合视图。
#
# 用途：多 agent 系统里"这条 finding 属于哪一层信任边界"是选型者真正要问的
# 问题（NIST/ISO 回答不了"是模型层还是生态层"）。
MAESTRO_LAYER_NAMES = {
    "L1": "Foundation Model",
    "L2": "Data Operations",
    "L3": "Agent Framework",
    "L4": "Deployment Infrastructure",
    "L5": "Evaluation & Observability",
    "L6": "Security & Compliance",
    "L7": "Agent Ecosystem",
    "L8": "Cross-Layer (Emergent)",
}

# OWASP ASI Threat → 主要 MAESTRO 层（取每类别最相关的 2–3 层，避免噪音）
_CATEGORY_MAESTRO = {
    "MCP01": ["L4", "L6"],
    "MCP02": ["L4", "L6"],
    "MCP03": ["L3", "L6"],
    "MCP04": ["L6", "L8"],
    "MCP05": ["L3", "L4"],
    "MCP06": ["L1", "L3"],
    "MCP07": ["L4", "L7"],
    "MCP08": ["L5"],
    "MCP09": ["L7"],
    "MCP10": ["L3", "L4"],
    "ASI01": ["L1", "L3"],
    "ASI02": ["L3", "L4"],
    "ASI03": ["L4", "L6"],
    "ASI04": ["L2", "L8"],
    "ASI05": ["L4", "L7"],
    "ASI06": ["L3", "L8"],
    "ASI07": ["L4", "L5"],
    "ASI08": ["L5"],
    "ASI09": ["L8", "L7"],
    "ASI10": ["L3", "L7", "L8"],
}

# OWASP ASI Threat（T1–T15, Agentic AI Threats and Mitigations v1.0）→ 类别。
# 这是 OWASP 官方的威胁编号；本库的 ASI01–ASI10 是 10 类归纳，两者不是同一个
# 编号体系，此表用于把"我们的类别"翻译成"OWASP 的威胁条目"。
#
# 精度声明（诚实边界）：层映射（L1–L8）由本库类别语义推导，可自证；
# T-code 逐条对应关系依据 OWASP GenAI Security Project 的 Agentic Security
# Initiative 威胁清单整理，属**近似锚点**。对外报告（客户/审计场景）引用具体
# T-code 措辞前，须回到 OWASP 原文核对，不要直接搬运本表里的编号当引用。
MAESTRO_THREAT_CODES = {
    "MCP01": ["T1", "T3"],
    "MCP02": ["T2", "T3"],
    "MCP03": ["T2", "T6"],
    "MCP04": ["T12"],
    "MCP05": ["T2", "T3", "T11"],
    "MCP06": ["T6", "T12", "T7"],
    "MCP07": ["T3", "T9"],
    "MCP08": ["T8", "T10"],
    "MCP09": ["T9", "T13"],
    "MCP10": ["T12", "T3"],
    "ASI01": ["T6", "T1"],
    "ASI02": ["T2"],
    "ASI03": ["T3", "T4"],
    "ASI04": ["T1", "T12"],
    "ASI05": ["T9", "T15"],
    "ASI06": ["T12", "T13"],
    "ASI07": ["T4"],
    "ASI08": ["T8", "T10"],
    "ASI09": ["T5", "T13", "T14"],
    "ASI10": ["T13", "T14", "T15"],
}

# 把 maestro 层锚点注入 CATEGORY_CONTROLS，让 compliance_summary() 无需改动
# 即可把它当作第 4 个框架聚合。code 用裸层号（L1–L8），层名由
# MAESTRO_LAYER_NAMES 单独提供，保持与 NIST/ISO 的"裸编号"风格一致。
for _cat, _layers in _CATEGORY_MAESTRO.items():
    CATEGORY_CONTROLS.setdefault(_cat, {})["maestro"] = list(_layers)

FRAMEWORKS = ("nist_csf", "iso27001", "pci_dss", "maestro")

_SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def compliance_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    把 findings 按 owasp_category 聚合为合规控制项视图。

    Returns:
        {
          "frameworks": {fw: {"controls_hit": n, "controls": {code: {...}}}},
          "categories_mapped": n,     # 有 finding 且可映射的 OWASP 类别数
          "findings_unmapped": n,     # 无 owasp_category 或未知类别的条数
          "note": "映射为审计锚点，不构成合规认证",
        }
    """
    out: Dict[str, Any] = {
        "frameworks": {fw: {} for fw in FRAMEWORKS},
        "categories_mapped": 0,
        "findings_unmapped": 0,
        "note": "映射为审计锚点（select-the-control），不构成合规认证结论",
    }

    seen_categories = set()
    for f in findings or []:
        if not isinstance(f, dict):
            continue
        cat = f.get("owasp_category", "")
        mapping = CATEGORY_CONTROLS.get(cat)
        if not mapping:
            out["findings_unmapped"] += 1
            continue
        seen_categories.add(cat)
        sev = str(f.get("severity", "info")).lower()
        for fw in FRAMEWORKS:
            for code in mapping.get(fw, []):
                slot = out["frameworks"][fw].setdefault(
                    code, {"findings_count": 0, "max_severity": "info"}
                )
                slot["findings_count"] += 1
                if _SEV_RANK.get(sev, 0) > _SEV_RANK.get(slot["max_severity"], 0):
                    slot["max_severity"] = sev

    out["categories_mapped"] = len(seen_categories)
    # frameworks[fw] 变回 {code: {...}} → 顶层再包一层计数，方便渲染摘要
    for fw in FRAMEWORKS:
        out["frameworks"][fw] = {
            "controls_hit": len(out["frameworks"][fw]),
            "controls": out["frameworks"][fw],
        }
    return out


def controls_for_category(category: str) -> Dict[str, List[str]]:
    """单类别查询（报告模板 / API 单点查询用）。未知类别返回空映射。"""
    return CATEGORY_CONTROLS.get(category, {fw: [] for fw in FRAMEWORKS})
