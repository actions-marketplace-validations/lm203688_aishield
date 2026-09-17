# -*- coding: utf-8 -*-
"""
持久记忆完整性 / 信任边界扫描测试 — tests/test_memory_integrity_scan.py

红线：
    - **只有真正写了持久记忆的文件才会被判定**——"没有记忆机制"不是漏洞，
      这是本扫描器误报面的唯一来源，也是它必须守住的第一条。
    - 有完整性校验（HMAC / signature / allow-list / verify）必须抑制告警：
      误报比漏报更伤信任（见 scanner/memory_integrity_scan.py 模块说明）。
    - 不可信消息入口（discord / webhook / 请求体）必须把严重度升为 high。
    - 零依赖、只读、确定性；绝不 spawn 任何被扫内容里的命令。
    - 已接入 preflight 流水线（ENGINES_REUSED + 报告键），漏接 = 假绿。
"""
import unittest

from scanner.memory_integrity_scan import memory_integrity_analysis
from scanner.workspace_scan import ENGINES_REUSED, _local_pipeline


# ── 正样本（应命中）──────────────────────────────────────────────────────
_STORE_HIGH = """
import discord
from mem0 import Memory

async def on_message(msg):
    Memory.add(str(msg.content))
"""

_STORE_MEDIUM = """
from letta import Client
client = Client()
client.agent_client.update_memory(memory_blocks)
"""

_STORE_SQL = """
def remember(role, content):
    cur.execute('INSERT INTO memory (role, content) VALUES (?, ?)', (role, content))
"""

_STORE_FILE = """
import json
MEM = 'memory.json'
def save(entry):
    data = json.load(open(MEM))
    data.append(entry)
"""

_STORE_VECTOR = """
client = chromadb.Client()
col = client.create_collection("memory")
col.add(ids=ids, embeddings=emb, metadatas=docs)
"""

_SHARED_UNPARTITIONED = """
shared_memory.update(agent_name, payload)
broadcast_to_agents(payload)
"""

# ── 良性样本（必须零命中）────────────────────────────────────────────────
_CLEAN_NO_MEMORY = """
def main():
    print("hello world")
"""

_CLEAN_HAS_HMAC = """
import hmac
from mem0 import Memory

def on_message(msg):
    if is_trusted(msg.author):
        Memory.add(msg.content)
"""

_CLEAN_HAS_SIGNATURE = """
import hashlib
SIG = verify_signature(entry, author)
store.save_memory(entry)
"""

_CLEAN_HAS_ALLOWLIST = """
ALLOWLIST = {"owner"}
def write(author, text):
    if author in ALLOWLIST:
        add_to_memory(text)
"""

_CLEAN_RAG_ONLY = """
client = chromadb.Client()
col = client.create_collection("docs")
col.add(ids=ids, documents=docs)
col.query(query_embeddings=emb)
"""

_CLEAN_SHARED_PARTITIONED = """
shared_memory.update(agent_name, payload, namespace=tenant)
"""


class TestDetection(unittest.TestCase):
    def test_store_without_integrity_from_discord_is_high(self):
        r = memory_integrity_analysis({"agent/memory.py": _STORE_HIGH})
        types = [(f["type"], f["severity"]) for f in r["findings"]]
        self.assertIn(("memory_store_without_integrity", "high"), types)

    def test_store_without_integrity_plain_is_medium(self):
        r = memory_integrity_analysis({"agent/memory.py": _STORE_MEDIUM})
        self.assertEqual(
            [(f["type"], f["severity"]) for f in r["findings"]],
            [("memory_store_without_integrity", "medium")])

    def test_sql_insert_into_memory_table(self):
        r = memory_integrity_analysis({"agent/db.py": _STORE_SQL})
        self.assertEqual(len(r["findings"]), 1)
        # store_hit 标识写进 description（evidence 会被截断，不能作为断言载体）
        self.assertIn("sql_insert", r["findings"][0]["description"])

    def test_memory_json_file(self):
        r = memory_integrity_analysis({"agent/store.py": _STORE_FILE})
        self.assertEqual(len(r["findings"]), 1)

    def test_vector_store_with_memory_named_collection(self):
        r = memory_integrity_analysis({"agent/rag.py": _STORE_VECTOR})
        self.assertEqual(len(r["findings"]), 1)
        self.assertEqual(r["findings"][0]["owasp_category"], "ASI04")

    def test_shared_memory_without_partition(self):
        r = memory_integrity_analysis({"agent/bus.py": _SHARED_UNPARTITIONED})
        self.assertTrue(
            any(f["type"] == "shared_memory_unpartitioned" for f in r["findings"]),
            "共享记忆无隔离边界应被检出")

    def test_shared_memory_alone_still_reports_missing_integrity(self):
        """shared_memory 本身即持久记忆，缺校验也要报，不能只报隔离。"""
        r = memory_integrity_analysis({"agent/bus.py": _SHARED_UNPARTITIONED})
        self.assertTrue(
            any(f["type"] == "memory_store_without_integrity" for f in r["findings"]))


class TestNoFalsePositives(unittest.TestCase):
    """误报面是本扫描器唯一真实风险；逐条钉死。"""

    def test_project_with_no_memory_at_all(self):
        r = memory_integrity_analysis({"main.py": _CLEAN_NO_MEMORY})
        self.assertEqual(r["findings"], [])
        self.assertEqual(r["summary"]["files_with_persistent_memory"], 0)

    def test_hmac_suppresses(self):
        r = memory_integrity_analysis({"agent/memory.py": _CLEAN_HAS_HMAC})
        self.assertEqual(r["findings"], [])

    def test_signature_suppresses(self):
        r = memory_integrity_analysis({"agent/memory.py": _CLEAN_HAS_SIGNATURE})
        self.assertEqual(r["findings"], [])

    def test_allowlist_suppresses(self):
        r = memory_integrity_analysis({"agent/memory.py": _CLEAN_HAS_ALLOWLIST})
        self.assertEqual(r["findings"], [])

    def test_rag_vector_store_is_not_memory(self):
        """向量库做 RAG 检索不等于持久记忆，不能报。"""
        r = memory_integrity_analysis({"agent/rag.py": _CLEAN_RAG_ONLY})
        self.assertEqual(r["findings"], [])

    def test_partitioned_shared_memory_suppresses_isolation_finding(self):
        r = memory_integrity_analysis({"agent/bus.py": _CLEAN_SHARED_PARTITIONED})
        self.assertFalse(
            any(f["type"] == "shared_memory_unpartitioned" for f in r["findings"]))

    def test_insert_into_unrelated_table(self):
        r = memory_integrity_analysis(
            {"a/db.py": 'cur.execute("INSERT INTO orders (id, qty) VALUES (?, ?)")'})
        self.assertEqual(r["findings"], [])

    def test_empty_and_binary_content_ignored(self):
        r = memory_integrity_analysis({"a/x": "", "b/y": None, "c/z": "\x00\x01"})
        self.assertEqual(r["findings"], [])


class TestSummaryShape(unittest.TestCase):
    def test_summary_fields(self):
        r = memory_integrity_analysis({"a/x.py": _STORE_HIGH})
        s = r["summary"]
        for key in ("memory_integrity_findings", "severity_counts",
                    "files_with_persistent_memory", "files_scanned", "note"):
            self.assertIn(key, s)
        self.assertEqual(s["memory_integrity_findings"], len(r["findings"]))
        self.assertEqual(s["files_scanned"], 1)
        self.assertEqual(s["files_with_persistent_memory"], 1)
        self.assertEqual(sum(s["severity_counts"].values()), len(r["findings"]))

    def test_deterministic(self):
        a = memory_integrity_analysis({"a.py": _STORE_MEDIUM})
        b = memory_integrity_analysis({"a.py": _STORE_MEDIUM})
        self.assertEqual(a, b)

    def test_dedup_per_file_per_type(self):
        r = memory_integrity_analysis({"a.py": _STORE_HIGH})
        types = [f["type"] for f in r["findings"]]
        self.assertEqual(len(types), len(set(types)), "同文件同类型不得重复报告")

    def test_evidence_truncated(self):
        long = _STORE_MEDIUM + "\n" + ("x" * 400)
        for f in memory_integrity_analysis({"a.py": long})["findings"]:
            self.assertLessEqual(len(f["evidence"]), 140)


class TestPipelineIntegration(unittest.TestCase):
    def test_registered_in_engines_reused(self):
        self.assertIn("memory_integrity_analysis", ENGINES_REUSED)

    def test_report_exposes_scanner_key(self):
        rep = _local_pipeline({"a/memory.py": _STORE_MEDIUM}, name="t", tool_type="mcp")
        self.assertIn("memory_integrity_scan", rep)
        self.assertEqual(len(rep["memory_integrity_scan"]["findings"]), 1)

    def test_findings_flow_into_total(self):
        rep = _local_pipeline({"a/memory.py": _STORE_MEDIUM}, name="t", tool_type="mcp")
        types = [f["type"] for f in rep["findings"]]
        self.assertIn("memory_store_without_integrity", types)

    def test_clean_pipeline_no_new_findings(self):
        rep = _local_pipeline(
            {"<skill>/SKILL.md": "---\nname: web-search\n---\nA search skill.\n"},
            name="clean", tool_type="skill")
        self.assertEqual(rep["memory_integrity_scan"]["findings"], [])


if __name__ == "__main__":
    unittest.main()
