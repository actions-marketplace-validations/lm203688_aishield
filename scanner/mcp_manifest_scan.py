# -*- coding: utf-8 -*-
"""
MCP SEP-2640 manifest 结构化校验（Skills as first-class MCP extension）

背景：MCP SEP-2640（2025-09-13 Final）把 Skills 正式纳入 MCP 官方仓库，
一个 skill 可以附带 `.mcp/manifest.json` 声明它需要哪些工具/scope、
附带哪些 prompt、依赖哪些其他 MCP server，以及安装命令。

这引入了新的攻击面：
  1. 过度代理：requiredScopes 里包含 wallet/finance/desktop/admin，
     但 manifest 未声明 approval/consent 要求（AIsa AgentPay Guard 的核心原则）
  2. 供应链执行：installCommands 里出现 curl|sh、bash<(wget) 类
  3. 凭据硬编码：mcpServers 段里 auth/token/apiKey 直接明文
  4. 横向信任放大：requiredTools 引用外部未审计的 MCP server
  5. 签名缺失：无 signature/proof/DID，发布者不可信

本模块对 {filepath: content} 里的 SEP-2640 manifest 做结构化校验：
  - 文件名启发式（manifest.json / .mcp/manifest.json / *.manifest.json）
    或 JSON 里含 manifestVersion / capabilities / requiredScopes 等强标记
  - 仅对"看起来像 manifest"的 JSON 生效，避免误伤普通配置
  - 纯本地 JSON 解析，不联网、不 spawn

对应 OWASP 类别：MCP07（身份与授权）、MCP04（凭证管理）、MCP08（供应链）
"""

import json
import re

# 与 agentcard_scan 一致：默认归到授权类；具体 finding 按类型分派
_OWASP_AUTHZ = "MCP07"
_OWASP_SECRET = "MCP04"
_OWASP_SUPPLY = "MCP08"

# 强标记：只要 JSON 里出现以下键之一，就认为它是 SEP-2640 manifest
_MANIFEST_MARKERS = {
    "manifestVersion", "schemaVersion", "mcpManifest", "skillManifest",
    "requiredScopes", "requiredTools", "installCommands",
}

# 危险 scope 关键词：出现即视为过度代理
_DANGEROUS_SCOPE_KEYWORDS = (
    "wallet", "payment", "spend", "finance", "x402", "stablecoin",
    "desktop", "screen", "mouse", "keyboard", "computeruse",
    "admin", "root", "sudo", "privileged", "system", "shell",
    "credential", "secret", "privatekey", "private_key",
)

# 良性 scope（用于判定"仅有良性 scope 时不报警"）
_BENIGN_SCOPE_KEYWORDS = (
    "read", "list", "search", "view", "profile", "public",
)

# installCommands 里的供应链执行模式
_SUPPLY_INSTALL_RE = re.compile(
    r"(curl|wget|fetch)[^|;&]{0,80}(\|\s*(ba)?sh|>\s*\S+\.(sh|ps1)|&&\s*(ba)?sh)"
    r"|\$\(\s*(curl|wget)\s"
    r"|(?:sh|bash|zsh)\s*<\(\s*(?:https?://|(?:curl|wget)\s)"
    r"|powershell\s+-command\s+.*iwr"
    r"|iex\s*\(\s*\(new-object",
    re.IGNORECASE,
)

# mcpServers 段里明文凭据的模式
_CREDENTIAL_IN_SERVER_RE = re.compile(
    r'"(api[_-]?key|secret|token|password|authorization|bearer)"\s*:\s*"'
    r'(?!\$|<|\{)[^"<>\s]{8,}"',
    re.IGNORECASE,
)


def _looks_like_manifest(obj, filepath=""):
    """仅当 JSON 含 SEP-2640 强标记时视为 manifest。"""
    if not isinstance(obj, dict):
        return False
    # 支持嵌套：{ "manifest": {...} } 或 { "mcpManifest": {...} }
    candidates = [obj]
    for wrapper in ("manifest", "mcpManifest", "skillManifest", "skill"):
        inner = obj.get(wrapper)
        if isinstance(inner, dict):
            candidates.append(inner)
    for c in candidates:
        if _MANIFEST_MARKERS & set(c.keys()):
            return True
    # 文件名启发式兜底（.mcp/manifest.json 或 *.manifest.json）
    fp = filepath.lower()
    if "manifest.json" in fp and ".mcp/" in fp:
        return True
    return False


def _flatten_manifest(obj):
    """把 manifest 内容规整成一个可查询的 dict。"""
    for wrapper in ("manifest", "mcpManifest", "skillManifest", "skill"):
        inner = obj.get(wrapper)
        if isinstance(inner, dict) and _MANIFEST_MARKERS & set(inner.keys()):
            return inner
    return obj


def _normalize_scopes(scopes):
    """把 scopes 字段规整成 list[str]，兼容多种写法。"""
    if scopes is None:
        return []
    if isinstance(scopes, str):
        # 兼容空格分隔写法（OIDC 风格）
        return [s.strip() for s in scopes.split() if s.strip()]
    if isinstance(scopes, list):
        out = []
        for s in scopes:
            if isinstance(s, str):
                out.append(s)
            elif isinstance(s, dict):
                # 兼容 {scope, reason} 结构
                for k in ("scope", "name", "id"):
                    v = s.get(k)
                    if isinstance(v, str):
                        out.append(v)
                        break
        return out
    return []


def _has_approval_declared(m):
    """检查 manifest 是否声明了审批/确认要求。"""
    for k in ("approval", "approvalPolicy", "requireApproval", "consent",
              "consentRequired", "humanInLoop", "confirmation"):
        if k in m:
            v = m.get(k)
            if v is True or (isinstance(v, str) and v.lower() in
                              ("required", "yes", "on", "true")):
                return True
            if isinstance(v, dict) and v.get("required") is True:
                return True
    return False


def mcp_manifest_analysis(files):
    """对 {filepath: content} 跑 SEP-2640 manifest 结构化校验。"""
    findings = []
    seen = set()

    def add(ftype, sev, desc, filepath, evidence, category=_OWASP_AUTHZ):
        key = f"{ftype}:{desc}:{filepath}"
        if key in seen:
            return
        seen.add(key)
        findings.append({
            "type": ftype,
            "severity": sev,
            "description": desc,
            "file": filepath,
            "evidence": (evidence or "")[:140],
            "owasp_category": category,
        })

    for filepath, content in files.items():
        if not isinstance(content, str) or not content.strip():
            continue
        if not (content.lstrip().startswith("{") or content.lstrip().startswith("[")):
            continue
        try:
            obj = json.loads(content)
        except (ValueError, TypeError):
            continue
        if not _looks_like_manifest(obj, filepath):
            continue

        m = _flatten_manifest(obj)

        # 1) 过度代理：危险 scope 存在但无审批声明
        scopes = _normalize_scopes(
            m.get("requiredScopes") or m.get("scopes")
            or m.get("permissions") or m.get("requiredPermissions")
        )
        # 也扫 capabilities 段里可能的 scope 声明
        caps = m.get("capabilities") or m.get("capability")
        cap_scopes = []
        if isinstance(caps, list):
            for c in caps:
                if isinstance(c, dict):
                    for k in ("scope", "scopes", "requiredScopes"):
                        v = c.get(k)
                        cap_scopes.extend(_normalize_scopes(v))
        scopes = scopes + cap_scopes
        if scopes:
            dangerous = []
            for s in scopes:
                sl = s.lower()
                if any(kw in sl for kw in _DANGEROUS_SCOPE_KEYWORDS):
                    # 若 scope 名同时命中良性关键词（如 "read:public_wallet_docs"），
                    # 仍视为危险，因为钱包 scope 本身需要审批
                    dangerous.append(s)
            if dangerous and not _has_approval_declared(m):
                add("manifest_overprivileged_scope", "critical",
                    f"manifest 声明了高危 scope（{', '.join(dang[:30] for dang in dangerous[:3])}）"
                    f"但未声明 approval/consent 要求——过度代理，"
                    f"对应 AIsa AgentPay Guard 的 quote-first/审批原则",
                    filepath, json.dumps(dangerous[:5])[:140], _OWASP_AUTHZ)

        # 2) 供应链执行：installCommands 里的 curl|sh 类
        install_cmds = m.get("installCommands") or m.get("install") \
            or m.get("setup") or m.get("setupCommands")
        if isinstance(install_cmds, list):
            for cmd in install_cmds:
                if not isinstance(cmd, str):
                    cmd = json.dumps(cmd, ensure_ascii=False)
                if _SUPPLY_INSTALL_RE.search(cmd):
                    add("manifest_supply_install", "high",
                        "manifest 的 installCommands 使用 curl|sh / bash<(wget) "
                        "类供应链执行模式，绕过代码审查",
                        filepath, cmd[:140], _OWASP_SUPPLY)
        elif isinstance(install_cmds, str) and _SUPPLY_INSTALL_RE.search(install_cmds):
            add("manifest_supply_install", "high",
                "manifest 的 installCommands 使用 curl|sh 类供应链执行模式",
                filepath, install_cmds[:140], _OWASP_SUPPLY)

        # 3) 凭据硬编码：mcpServers 段里明文 token
        servers = m.get("mcpServers") or m.get("servers") \
            or m.get("requiredTools") or m.get("dependencies")
        if isinstance(servers, (dict, list)):
            server_blob = json.dumps(servers, ensure_ascii=False)
            if _CREDENTIAL_IN_SERVER_RE.search(server_blob):
                add("manifest_hardcoded_credential", "high",
                    "manifest 的 mcpServers/requiredTools 段硬编码明文 token/apiKey，"
                    "安装即暴露给所有 agent",
                    filepath, server_blob[:140], _OWASP_SECRET)

        # 4) 签名/证明缺失
        sig_present = any(k in m for k in ("signature", "proof", "did",
                                           "verificationMethod", "attestation",
                                           "checksum"))
        # 也检查顶层
        if not sig_present:
            sig_present = any(k in obj for k in ("signature", "proof", "did",
                                                 "verificationMethod"))
        if not sig_present:
            add("manifest_unsigned", "medium",
                "manifest 缺少签名/证明（signature/proof/DID/attestation），"
                "发布者真实性与内容完整性无法验证（AIsa Agent Skills 的信任缺口）",
                filepath, content[:120], _OWASP_AUTHZ)

        # 5) 缺少版本过期（长期有效的 manifest 撤销困难）
        if not any(k in m for k in ("expiration", "validUntil", "notAfter",
                                    "expiresAt", "versionExpiration")):
            add("manifest_no_expiry", "low",
                "manifest 缺少过期时间（expiration/validUntil），长期有效、"
                "撤销困难——建议加 TTL 便于轮换",
                filepath, content[:120], _OWASP_AUTHZ)

    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1

    summary = {
        "mcp_manifest_findings": len(findings),
        "severity_counts": sev_counts,
        "files_scanned": len(files),
        "note": "MCP SEP-2640 manifest 结构化校验：过度代理/供应链执行/凭据硬编码/签名/过期",
    }
    return {"findings": findings, "summary": summary}
