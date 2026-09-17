# -*- coding: utf-8 -*-
"""
持久记忆完整性 / 信任边界检测（官方 OWASP Agentic ASI06 Memory & Context Poisoning · 威胁 T1）

背景（2026-09-17 采纳）：Princeton 团队对 ElizaOS 的公开研究证明，跨 session
的持久记忆只要**没有写入方完整性校验**，就能被任意有消息权限的一方投毒——
伪造一条"支付已确认"的历史记录，之后的 ``transfer()`` 即便来自合法 owner
也会被劫持。作者 Shaw Walters 的回应是"我们把沙箱与分片隔离留给未来"。

本库既有的 ``memory_scan.py`` 检测的是**注入行为**（有人正在写恶意指令进记忆）。
它管不了另一半：**记忆库本身没有完整性边界**。那是架构缺陷而非注入动作——
没有任何一行代码"正在投毒"，所以按注入模式匹配必然零命中。这正是"本地绿 ≠
架构安全"的典型假绿。

检测两类架构信号（纯静态，零依赖，只读）：
  1. memory_store_without_integrity  —— 存在持久记忆写入，但同文件内看不到任何
     完整性/来源校验机制（HMAC / signature / verify / allow-list / checksum）。
     若同文件还从不可信消息入口取数（discord / webhook / websocket / 请求体），
     升级为 high——那正是 ElizaOS 的初始访问向量。
  2. shared_memory_unpartitioned     —— 多 agent 共享记忆，但看不到租户/命名空间/
     隔离边界（对应 OWASP 官方 ASI07 Insecure Inter-Agent Communication 与
     ASI08 Cascading Failures：一个 agent 被攻破会污染其余全部）。

判定纪律：只报告**存在持久化写入**的文件。没有记忆机制的项目不会被误伤——
"没有记忆"不是一处漏洞。误报面由双条件（存储信号 AND 无完整性信号）共同约束。
"""

import re

_OWASP = "ASI04"   # 本库内部编号：记忆操纵与投毒（= OWASP 官方 ASI06
                    # Memory & Context Poisoning；官方 ASI04 是供应链，勿混淆）

# ── 持久记忆写入信号 ──────────────────────────────────────────────────────
# 分两级：显式记忆 API（强）与通用存储 + 记忆名词（弱，需同行共现）。
_STORE_EXPLICIT = re.compile(
    r'(memory_?store|memoryStore|add_?to_?memory|memory_?add|persist_?memory|'
    r'save_?memory|commit_?to_?memory|store_?in_?memory|write_?to_?memory|'
    r'memory\.add\s*\(|memories?\.save\s*\(|mem0\b|letta\b)', re.I)

# 向量库 / 文档库 / 键值库 —— 只有与"记忆类名词"同行共现才算记忆存储
_STORE_BACKEND = re.compile(
    r'\b(chroma|chromadb|qdrant|weaviate|pinecone|milvus|faiss|pgvector|'
    r'vec_?db|vector_?store)\b', re.I)
_STORE_SQL = re.compile(
    r'INSERT\s+INTO\s+[`"\']?(memory|memories|context|sessions|history|traces)\b', re.I)

_MEM_NOUN = re.compile(
    r'\b(memory|memories|long[\- ]?term|context|session|history|conversation|'
    r'episodic|semantic)\b', re.I)

# 文件型持久记忆（.memory / memory.json / context store）
_MEM_FILE = re.compile(
    r'(memory\.json|\.memory\b|context[_-]?store|long[\- ]?term[\- ]?memory)', re.I)

# ── 完整性 / 来源校验信号（命中即视为已有边界，抑制告警）────────────────
_INTEGRITY = re.compile(
    r'(hmac|signature|signed_|_signature|verify_?sig|verify_?sign|verify_?auth|'
    r'checksum|sha-?256|sha256|digest|attestation|notariz|'
    r'allow_?list|allowlist|block_?list|blocklist|'
    r'trust(ed|worthy)?_(source|origin|channel|sender|author)|is_trusted|'
    r'authorized_writer|signed_?write|mac_?verify)', re.I)

# ── 不可信消息入口（初始访问向量；命中把严重度升一档）────────────────────
_UNTRUSTED_IN = re.compile(
    r'(discord|telegram|slack|wechat|weixin|weibo|weibo|qq\.?com|line\b|signal\b|'
    r'webhook|websocket|/api/message|incoming_?(message|request)|'
    r'request\.json\s*\(|request\.data|body\[\s*["\']?(message|text|content|input))', re.I)

# ── 多 agent 共享记忆（无隔离边界）──────────────────────────────────────
_SHARED = re.compile(
    r'(shared_?memory|common_?memory|global_?memory|broadcast(?:_?to)?_?agent|'
    r'agent_?to_?agent|inter[\- ]?agent|multi[\- ]?agent|federation)', re.I)
_PARTITIONED = re.compile(
    r'(tenant|namespace|partition|isolation|isolat|per[\- ]?user|per[\- ]?agent|'
    r'scope\s*=\s*["\']|compartment)', re.I)


def memory_integrity_analysis(files):
    """返回 {"findings": [...], "summary": {...}}，与同目录其他扫描器同形。"""
    findings = []
    seen = set()

    def add(ftype, sev, desc, filepath, evidence):
        key = f"{ftype}:{filepath}"
        if key in seen:
            return
        seen.add(key)
        findings.append({"type": ftype, "severity": sev, "description": desc,
                         "file": filepath, "evidence": evidence[:140],
                         "owasp_category": _OWASP})

    n_stores = 0
    for fp, content in files.items():
        if not isinstance(content, str) or not content.strip():
            continue

        # 2) 共享记忆但无隔离边界 —— 独立于下面的"是否有存储"判定。
        # 注意：此检查必须在 store_hit 的 `continue` 之前执行，否则
        # "只有 shared_memory、没有显式存储 API" 的文件会永远走不到这里。
        if _SHARED.search(content) and not _PARTITIONED.search(content):
            add("shared_memory_unpartitioned", "medium",
                "多 agent 共享记忆但未见租户/命名空间/隔离边界：单个 agent 被攻破"
                "即污染其余全部（OWASP 威胁模型 Insufficient Isolation Between "
                "Agent Actions）",
                fp, content[:120])

        # 1) 是否真的在写持久记忆？
        store_hit = None
        if _STORE_EXPLICIT.search(content):
            store_hit = "memory_api"
        elif _STORE_SQL.search(content):
            store_hit = "sql_insert"
        elif _MEM_FILE.search(content):
            store_hit = "memory_file"
        elif _SHARED.search(content):
            # shared_memory 语义上就是持久记忆（无需再要求记忆类名词同行共现；
            # \bmemory\b 也匹配不到 shared_memory，因为下划线是单词字符）。
            store_hit = "shared_memory"
        elif _STORE_BACKEND.search(content):
            # 后端名与记忆类名词须"邻近共现"（±3 行窗口），避免"用向量库做
            # RAG 检索"被误判，同时不漏掉真实的
            #     client = chromadb.Client()
            #     col = client.create_collection("memory")
            # 这种跨行的常见写法。
            lines = content.splitlines()
            hits = [i for i, ln in enumerate(lines) if _STORE_BACKEND.search(ln)]
            for i, ln in enumerate(lines):
                if _MEM_NOUN.search(ln):
                    if any(abs(i - h) <= 3 for h in hits):
                        store_hit = "vector_store"
                        break
        if not store_hit:
            continue
        n_stores += 1

        if not _INTEGRITY.search(content):
            if _UNTRUSTED_IN.search(content):
                add("memory_store_without_integrity", "high",
                    "持久记忆写入缺少完整性/来源校验，且数据来自不可信消息入口"
                    "（%s）：任何有消息权限的一方都能写入会被当作历史事实的条目，"
                    "后续合法指令会被其偏置（OWASP ASI T1 · ElizaOS 记忆投毒路径）"
                    % store_hit,
                    fp, content[:120])
            else:
                add("memory_store_without_integrity", "medium",
                    "持久记忆写入（%s）未见完整性/来源校验（HMAC / signature / "
                    "allow-list / verify）：记忆条目无法区分合法历史与伪造注入，"
                    "跨 session 偏置不可检测" % store_hit,
                    fp, content[:120])

    sev_c = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev_c[f["severity"]] = sev_c.get(f["severity"], 0) + 1
    summary = {
        "memory_integrity_findings": len(findings),
        "severity_counts": sev_c,
        "files_with_persistent_memory": n_stores,
        "files_scanned": len(files),
        "note": "持久记忆完整性/信任边界检测（本库内部编号 ASI04 = 官方 OWASP ASI06 · 威胁 T1）",
    }
    return {"findings": findings, "summary": summary}
