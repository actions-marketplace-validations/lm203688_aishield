"""
Framework Adapters — 共享门禁逻辑。

核心 `gate_mcp_config` 只依赖 `scanner`（标准库），不 import 任何 Agent 框架，
因此可在 CI / 单元测试里无依赖调用。框架专属适配器放在同名子模块，按需 import。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GateResult:
    ok: bool
    config_score: int
    findings_total: int
    severity_counts: dict
    findings: list
    errors: list
    raw: Optional[dict] = None

    def __str__(self):
        status = "PASS" if self.ok else "BLOCK"
        return (
            f"[{status}] score={self.config_score} "
            f"findings={self.findings_total} {self.severity_counts}"
        )


def _severity_meets(level: str, min_level: str) -> bool:
    order = ["info", "low", "medium", "high", "critical"]
    return order.index(level) >= order.index(min_level)


def gate_mcp_config(
    config_text: str,
    config_name: str = "agent-config.json",
    fail_on: str = "high",
    min_score: int = 0,
) -> GateResult:
    """
    对一段 MCP 配置文本做静态安全门禁。

    - config_text: JSON / JSONC 字符串（mcpServers / servers 均可）。
    - fail_on: 出现该级别及以上风险即拦截（默认 high）。
    - min_score: 配置评分低于该值即拦截（0 = 不限制）。
    返回 GateResult。绝不执行配置里的任何命令。
    """
    errors = []
    try:
        from scanner.client_discovery import scan_client_configs
    except Exception as e:  # pragma: no cover
        return GateResult(False, 0, 0, {}, [], [f"scanner 不可用: {e}"])

    try:
        result = scan_client_configs({config_name: config_text})
    except Exception as e:
        return GateResult(False, 0, 0, {}, [], [f"扫描异常: {e}"])

    summary = result.get("summary", {})
    score = summary.get("config_score", 0)
    counts = summary.get("severity_counts", {})
    findings = result.get("findings", [])

    blocked_by_sev = any(_severity_meets(s, fail_on) for s in counts)
    blocked_by_score = score < min_score if min_score else False

    ok = (not blocked_by_sev) and (not blocked_by_score)
    if not ok:
        if blocked_by_sev:
            errors.append(f"存在 >= {fail_on} 级别的风险")
        if blocked_by_score:
            errors.append(f"配置评分 {score} < 阈值 {min_score}")

    return GateResult(
        ok=ok,
        config_score=score,
        findings_total=summary.get("findings_total", len(findings)),
        severity_counts=counts,
        findings=findings,
        errors=errors,
        raw=result,
    )
