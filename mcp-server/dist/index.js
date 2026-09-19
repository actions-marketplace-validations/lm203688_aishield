#!/usr/bin/env node
"use strict";
/**
 * AIShield MCP Server
 *
 * OWASP MCP Top 10 aligned security scanner.
 * 7 tools: scan / guardrail / prompt_check / banned_words / rug_pull / handshake / digest
 *
 * Usage:
 *   npx aishield-mcp-server
 *
 * Env:
 *   AISHIELD_API_URL  — backend API URL (default: https://api.aishield.tools)
 *   AISHIELD_API_KEY  — optional API key for higher rate limits
 */
Object.defineProperty(exports, "__esModule", { value: true });
const mcp_js_1 = require("@modelcontextprotocol/sdk/server/mcp.js");
const stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
const zod_1 = require("zod");
// 版本单一真源。由 scripts/sync_version.py 统一维护，CI 的版本一致性门禁会校验它，
// 因此这里不再手写数字 —— 硬编码的 '3.0.0' 曾与已发布的 4.2.x 差了一个大版本。
const SERVER_VERSION = '4.3.0';
const API_BASE = process.env.AISHIELD_API_URL || 'https://api.aishield.tools';
const API_KEY = process.env.AISHIELD_API_KEY || '';
// ── API Helper ──
async function apiCall(path, body, timeoutMs = 30000) {
    const url = `${API_BASE}${path}`;
    const headers = {
        'Content-Type': 'application/json',
        'User-Agent': `AIShield-MCP-Server/${SERVER_VERSION}`,
    };
    if (API_KEY)
        headers['Authorization'] = `Bearer ${API_KEY}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers,
            body: JSON.stringify(body),
            signal: controller.signal,
        });
        if (!res.ok) {
            const text = await res.text().catch(() => '');
            throw new Error(`AIShield API ${res.status}: ${text.slice(0, 200)}`);
        }
        return await res.json();
    }
    finally {
        clearTimeout(timer);
    }
}
// ── Audit response unwrapping ──
//
// /api/v1/audit 的成功响应形状是：
//   { success, score, badge_level, risk_level, report: { overall_score, findings, ... } }
// 顶层只有三个便捷字段，五维分数 / findings / owasp_coverage 全都在 report 里。
//
// 早期版本直接读 data.overall_score —— 这个键在顶层根本不存在，于是每次扫描都显示
// "Score: 0/100"、五维全 0、findings 为空；guardrail 更糟：score 恒为 0 就永远走到
// BLOCK 分支，对再干净的仓库也判"不要安装"。一个对什么都报警的安全工具，
// 和没有安全工具是一回事，甚至更坏 —— 用户会直接卸载它。
//
// 这里统一解包，同时兼容「扁平响应」的老部署（自建 API 可能还没升级）。
function unwrapAudit(data) {
    const hasNested = data && typeof data.report === 'object' && data.report !== null;
    const report = hasNested ? data.report : (data || {});
    // 顶层 score 优先（API 承诺与 report.overall_score 恒等），回退到嵌套值。
    const score = toNum(data?.score, toNum(report?.overall_score, 0));
    return { report, score };
}
function toNum(v, fallback) {
    return typeof v === 'number' && Number.isFinite(v) ? v : fallback;
}
// ── Create Server ──
const server = new mcp_js_1.McpServer({
    name: 'AIShield Security Scanner',
    version: SERVER_VERSION,
    description: 'OWASP MCP Top 10 + Agentic AI Top 10 aligned security scanner — 235 rules, 5-dimension scoring, tool poisoning & supply chain detection, per-finding file:line:col anchors with remediation',
});
// ══════════════════════════════════════════════════════════════
// Tool 1: Full Security Scan
// ══════════════════════════════════════════════════════════════
server.tool('aishield_scan', `AIShield安全扫描 — 扫描MCP Server/AI工具的安全风险。

对齐OWASP MCP Top 10 (2025 v0.1) 与 Agentic AI Top 10，235条规则覆盖两套风险分类。
5维评分: 安全(40%)/权限(20%)/数据处理(20%)/供应链(10%)/可靠性(10%)
返回: 评分 + 风险等级 + OWASP合规矩阵 + 修复建议
每条 finding 带 file:line:col 精确锚点 + 证据片段 + 稳定 rule_id + 具体修复动作`, {
    source_url: zod_1.z.string().describe('GitHub repo URL of the tool to scan'),
    tool_type: zod_1.z.enum(['mcp', 'skill', 'gpt', 'prompt']).default('mcp').describe('Tool type'),
    name: zod_1.z.string().optional().describe('Tool name (optional)'),
}, async ({ source_url, tool_type, name }) => {
    try {
        const data = await apiCall('/api/v1/audit', { source_url, tool_type, name });
        return formatScanResult(data);
    }
    catch (e) {
        return { content: [{ type: 'text', text: `AIShield scan failed: ${e.message}` }] };
    }
});
// ══════════════════════════════════════════════════════════════
// Tool 2: Pre-install Guardrail
// ══════════════════════════════════════════════════════════════
server.tool('aishield_guardrail', `AIShield安装前安全检查 — 在安装任何MCP/AI工具前调用此工具。

返回pass/block判定 + 评分 + OWASP合规矩阵。
建议在安装任何第三方MCP Server前自动调用此工具。`, {
    source_url: zod_1.z.string().describe('GitHub repo URL of the tool to check'),
    auto_block: zod_1.z.boolean().default(true).describe('If true, return block verdict for unsafe tools'),
}, async ({ source_url, auto_block }) => {
    try {
        const raw = await apiCall('/api/v1/audit', { source_url, tool_type: 'mcp', auto_block });
        const { report: data, score } = unwrapAudit(raw);
        const risk = raw?.risk_level || data.risk_level || 'unknown';
        const badge = raw?.badge_level || data.badge_level || 'none';
        let verdict;
        if (score >= 70) {
            verdict = '✅ PASS — Safe to install';
        }
        else if (score >= 55 && !auto_block) {
            verdict = '⚠️ WARN — Review recommended before installing';
        }
        else {
            verdict = '❌ BLOCK — Security risks detected, DO NOT install';
        }
        const owasp = data.owasp_coverage || {};
        const covered = (owasp.covered || []).join(', ') || 'None';
        const summary = [
            `AIShield Guardrail Verdict: ${verdict}`,
            ``,
            `Score: ${score}/100 | Risk: ${risk} | Badge: ${badge}`,
            `OWASP Categories Covered: ${covered} (${owasp.covered_count || 0}/10)`,
            `Findings: ${data.total_findings || 0} issues`,
            ``,
            `Recommendations:`,
            ...(data.recommendations || []).map((r) => `  • ${r}`),
        ].join('\n');
        return { content: [{ type: 'text', text: summary }] };
    }
    catch (e) {
        return { content: [{ type: 'text', text: `Guardrail check failed: ${e.message}. CAUTION: Do not install until verified.` }] };
    }
});
// ══════════════════════════════════════════════════════════════
// Tool 3: Prompt Injection Detection
// ══════════════════════════════════════════════════════════════
server.tool('aishield_prompt_check', `Prompt安全检测 — 检测用户输入的Prompt是否存在注入/越狱/数据外传风险。

支持中文和英文，覆盖: 越狱指令/身份切换/系统提示窃取/数据外传/角色扮演注入/零宽字符/Unicode编码`, {
    prompt: zod_1.z.string().min(10).describe('待检测的Prompt文本（至少10个字符）'),
}, async ({ prompt }) => {
    try {
        const data = await apiCall('/api/v1/prompt-check', { prompt });
        const safe = data.safe ? '✅ SAFE' : '❌ UNSAFE';
        const summary = [
            `Prompt安全检测结果: ${safe}`,
            `评分: ${data.score}/100 | 风险: ${data.risk || 'unknown'}`,
            ``,
            data.summary || '',
            ``,
            `发现的问题:`,
            ...(data.findings || []).map((f) => formatFinding(f)),
        ].join('\n');
        return { content: [{ type: 'text', text: summary }] };
    }
    catch (e) {
        return { content: [{ type: 'text', text: `Prompt检测失败: ${e.message}` }] };
    }
});
// ══════════════════════════════════════════════════════════════
// Tool 4: Chinese Banned Words Check
// ══════════════════════════════════════════════════════════════
server.tool('aishield_banned_words', `中文违禁词检测 — 检测文本中的违禁词/敏感词。

覆盖6大平台: 微信/抖音/小红书/B站/知乎/微博
返回: 违禁词列表 + 法律条文 + 罚款金额 + 替换建议`, {
    text: zod_1.z.string().describe('待检测文本'),
    platform: zod_1.z.enum(['douyin', 'xiaohongshu', 'wechat', 'weibo', 'bilibili', 'kuaishou', 'all']).default('all').describe('目标平台'),
}, async ({ text, platform }) => {
    try {
        const data = await apiCall('/api/v1/banned-words', { text, platform });
        return { content: [{ type: 'text', text: JSON.stringify(data, null, 2) }] };
    }
    catch (e) {
        return { content: [{ type: 'text', text: `违禁词检测失败: ${e.message}` }] };
    }
});
// ══════════════════════════════════════════════════════════════
// Tool 5: Rug Pull Detection
// ══════════════════════════════════════════════════════════════
server.tool('aishield_rug_pull', `Rug Pull检测 — 检查MCP工具是否在版本更新中移除安全代码或新增可疑网络请求。

对比最近commit diff，检测: 安全代码删除、新增网络请求、权限扩大、大量代码删除。
返回风险等级(critical/high/medium/low/safe)和具体发现。`, {
    source_url: zod_1.z.string().describe('GitHub repo URL'),
}, async ({ source_url }) => {
    try {
        const data = await apiCall('/api/v1/rug-pull', { source_url });
        const risk = data.rug_pull_risk || 'unknown';
        const score = data.rug_pull_score || 0;
        const lines = [
            `AIShield Rug Pull Detection`,
            `${'═'.repeat(40)}`,
            `Risk: ${risk} | Score: ${score}/100`,
            `Commits analyzed: ${data.commits_analyzed || 0}`,
            `Findings: ${data.total_findings || 0}`,
        ];
        if (data.findings && data.findings.length > 0) {
            lines.push('', '── Findings ──');
            for (const f of data.findings.slice(0, 10)) {
                lines.push(formatFinding(f));
            }
        }
        return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
    catch (e) {
        return { content: [{ type: 'text', text: `Rug pull check failed: ${e.message}` }] };
    }
});
// ══════════════════════════════════════════════════════════════
// Tool 6: MCP Handshake Verification
// ══════════════════════════════════════════════════════════════
server.tool('aishield_handshake', `MCP握手验证 — 分析MCP配置、检测npx自动安装风险、敏感环境变量、工具描述异常长度。

提取README/package.json中的MCP配置，分析: npx -y风险、敏感env变量、远程URL安全性、
工具描述长度（>500字符可能隐藏指令）。如果是HTTP类型MCP，尝试实际握手。`, {
    source_url: zod_1.z.string().describe('GitHub repo URL'),
}, async ({ source_url }) => {
    try {
        const data = await apiCall('/api/v1/handshake', { source_url });
        const status = data.handshake_status || 'unknown';
        const lines = [
            `AIShield MCP Handshake Verification`,
            `${'═'.repeat(40)}`,
            `Status: ${status}`,
            `Configs found: ${data.configs_found || 0}`,
            `Files analyzed: ${data.files_analyzed || 0}`,
            `Findings: ${data.total_findings || 0}`,
        ];
        if (data.findings && data.findings.length > 0) {
            lines.push('', '── Findings ──');
            for (const f of data.findings.slice(0, 10)) {
                lines.push(formatFinding(f));
            }
        }
        if (data.configs && data.configs.length > 0) {
            lines.push('', '── MCP Configs ──');
            for (const c of data.configs.slice(0, 3)) {
                lines.push(`  ${JSON.stringify(c).slice(0, 100)}`);
            }
        }
        return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
    catch (e) {
        return { content: [{ type: 'text', text: `Handshake check failed: ${e.message}` }] };
    }
});
// ══════════════════════════════════════════════════════════════
// Tool 7: Compact Trust Digest
// ══════════════════════════════════════════════════════════════
//
// 一个 agent 每轮对话都要回答同一个问题「这个东西我能不能信」。完整裁决信封
// 里有一个字段能用、二十个字段用不上，每次都拉一遍等于把同一份不变的内容反复
// 塞进上下文。这个工具只回几百字节 + 一个内容指纹：指纹没变就不必再拉。
//
// 借的是 Cache-to-Cache 那条观察（紧凑的语义载体优于整份文本重传），落地为纯
// 工程压缩 —— 不动模型内部，不需要任何模型侧配合。
server.tool('aishield_digest', `AIShield紧凑信任摘要 — 几百字节拿到结论，适合每轮都要判断"能不能信"的 agent。

输入三选一:
  configs     — {path: 文件内容} 的 MCP 客户端配置映射（静态分析，绝不执行其中命令）
  source_url  — 只要一个远程仓库 URL，取现成的信任裁决
  scan_result — 已有扫描结果，只做压缩

返回: 分数 + 风险等级 + 严重度分布 + 首 N 条 + content fingerprint。
指纹对同一份配置恒定不变 —— 存下来，下一轮先比指纹，没变就不必重复拉取。`, {
    source_url: zod_1.z.string().optional().describe('GitHub repo URL — return the current verdict as a digest'),
    configs: zod_1.z.record(zod_1.z.any()).optional().describe('{path: file content} MCP client config map (static analysis only)'),
    scan_result: zod_1.z.record(zod_1.z.any()).optional().describe('An existing scan result to compress'),
    max_findings: zod_1.z.number().int().min(0).max(20).default(3).describe('How many top findings to include'),
}, async ({ source_url, configs, scan_result, max_findings }) => {
    try {
        const body = { max_findings: max_findings ?? 3 };
        if (configs)
            body.configs = configs;
        else if (scan_result)
            body.scan_result = scan_result;
        else if (source_url)
            body.source_url = source_url;
        else {
            return {
                content: [{ type: 'text', text: 'Provide one of: configs, scan_result, source_url' }],
            };
        }
        const d = await apiCall('/api/v1/trust/digest', body);
        const counts = d.severity_counts || {};
        const lines = [
            `AIShield Trust Digest (${d.schema || 'aishield-digest/v1'})`,
            `${'─'.repeat(44)}`,
            `Score:   ${d.score === null || d.score === undefined ? 'n/a' : d.score} / 100`,
            `Risk:    ${d.risk || 'unknown'}`,
            `Subject: ${d.subject || 'n/a'}`,
            `Findings: ${d.findings_total === null || d.findings_total === undefined ? 'n/a' : d.findings_total}  ${JSON.stringify(counts)}`,
            `Fingerprint: ${d.fingerprint || 'n/a'}`,
        ];
        if (Array.isArray(d.top) && d.top.length > 0) {
            lines.push('', '── Top ──');
            for (const t of d.top) {
                lines.push(`  [${t.severity || '?'}] ${t.type || '?'}${t.owasp ? ' (' + t.owasp + ')' : ''}`);
            }
        }
        lines.push('', 'Cache on the fingerprint: same fingerprint = same verdict, no need to re-fetch.');
        return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
    catch (e) {
        return { content: [{ type: 'text', text: `Digest failed: ${e.message}` }] };
    }
});
// ── Helper ──
function formatScanResult(raw) {
    const { report: data, score } = unwrapAudit(raw);
    const badge = raw?.badge_level || data.badge_level || 'none';
    const risk = raw?.risk_level || data.risk_level || 'unknown';
    const lines = [
        `AIShield Security Scan Report`,
        `${'═'.repeat(50)}`,
        `Tool: ${data.name || 'N/A'}`,
        `Score: ${score}/100 | Risk: ${risk} | Badge: ${badge}`,
        `Rules: ${data.rules_count || 0} | Findings: ${data.total_findings || 0}`,
        `Scanned: ${data.scanned_at || 'N/A'} | Engine: v${data.scanner_version || '4.0'}`,
        ``,
        `── 5-Dimension Scores ──`,
        `  Security:      ${data.security_score || 0}/100 (40%)`,
        `  Permissions:   ${data.permissions_score || 0}/100 (20%)`,
        `  Data Handling: ${data.data_handling_score || 0}/100 (20%)`,
        `  Supply Chain:  ${data.supply_chain_score || 0}/100 (10%)`,
        `  Reliability:   ${data.reliability_score || 0}/100 (10%)`,
        ``,
        `── OWASP MCP Top 10 Coverage ──`,
    ];
    const owasp = data.owasp_coverage || {};
    const covered = new Set(owasp.covered || []);
    for (let i = 1; i <= 10; i++) {
        const cat = `MCP${String(i).padStart(2, '0')}`;
        const mark = covered.has(cat) ? '✅' : '⬜';
        lines.push(`  ${mark} ${cat}`);
    }
    if (data.findings && data.findings.length > 0) {
        lines.push('');
        lines.push(`── Findings (${data.findings.length}) ──`);
        // Show critical and high only
        const important = data.findings.filter((f) => f.severity === 'critical' || f.severity === 'high');
        for (const f of important.slice(0, 15)) {
            lines.push(formatFinding(f));
        }
        if (important.length > 15) {
            lines.push(`  ... and ${important.length - 15} more`);
        }
    }
    if (data.recommendations && data.recommendations.length > 0) {
        lines.push('');
        lines.push('── Recommendations ──');
        for (const r of data.recommendations) {
            lines.push(`  • ${r}`);
        }
    }
    lines.push('');
    lines.push(`Badge: [![AIShield](https://img.shields.io/badge/AIShield-${badge}-${badge === 'gold' ? 'FFD700' : badge === 'silver' ? 'C0C0C0' : badge === 'bronze' ? 'CD7F32' : '999'})}](https://aishield.tools)`);
    return { content: [{ type: 'text', text: lines.join('\n') }] };
}
// Helper: render a finding with a precise anchor — file:line:col + evidence snippet
// + stable rule id + a concrete fix action. HeyClicky-style: point the user AT the
// exact element, don't just say "you have a vulnerability".
//
// rule_id takes priority over type: for static-pattern findings the type is always
// the useless constant "dangerous_pattern", while rule_id (MCP05-012 / GEN-9A3F) is
// what you actually look a rule up by. type is only a fallback for findings that
// predate the anchor fields.
//
// remediation is per-finding: the global `recommendations` list is only a handful of
// generic sentences and cannot be mapped back to a specific finding.
function formatFinding(f) {
    const sev = String(f?.severity || 'info').toUpperCase();
    const anchorParts = [f?.file, f?.lines].filter(Boolean);
    if (f?.col)
        anchorParts.push(`c${f.col}`);
    if (f?.commit_sha)
        anchorParts.push(`commit ${String(f.commit_sha).slice(0, 8)}`);
    const loc = anchorParts.join(':');
    let s = `  [${sev}] ${f?.description || '(no description)'}`;
    if (loc)
        s += `  @ ${loc}`;
    const rule = f?.rule_id || f?.type;
    if (rule)
        s += `  [${rule}]`;
    if (f?.evidence)
        s += `\n      ↳ ${String(f.evidence).slice(0, 160)}`;
    if (f?.remediation)
        s += `\n      ↪ Fix: ${String(f.remediation).slice(0, 200)}`;
    return s;
}
// ── Start ──
async function main() {
    const transport = new stdio_js_1.StdioServerTransport();
    await server.connect(transport);
    console.error(`AIShield MCP Server v${SERVER_VERSION} — OWASP MCP Top 10 aligned`);
    console.error(`  API: ${API_BASE}`);
    console.error(`  Key: ${API_KEY ? '***' + API_KEY.slice(-4) : '(not set — free tier)'}`);
}
main().catch((err) => {
    console.error('Fatal:', err);
    process.exit(1);
});
