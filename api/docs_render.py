#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs 文档渲染器（零依赖 Markdown → HTML）
========================================

背景
----
`docs/` 里有全套技术文档（benchmark 分数表、验证 harness、雷达 shadow gate、
情报简报……），但它们此前**没有任何对外通道**：GitHub Pages 的
`lm203688.github.io/aishield` 被 CNAME 重定向到 `aishield.tools`，Jekyll 构建
产物从未被任何人访问过；而 `aishield.tools` 由 `api/server.py` 托管，它只有
逐页硬编码的静态路由，没有 `docs/` 挂载点。

于是 benchmark 的 96% 召回 / 0% 误报、harness 的复现方法，全部只存在于 git
仓库里 —— 外部用户看不到，等于不存在。

本模块补上这个通道：`/docs/<相对路径>` → 读 `docs/` 下对应文件 → 渲染成
HTML 返回。这样 `https://aishield.tools/docs/benchmark/v1.html` 直接可达。

设计约束
--------
* **零依赖**：项目铁律是不引入任何第三方包，所以这里手写一个覆盖常见
  Markdown 子集（标题 / 表格 / 代码块 / 列表 / 引用 / 粗体 / 行内代码 / 链接）
  的渲染器，而不是 import markdown。
* **先转义后转换**：文档内容来自 git，理论上可信，但它会被渲染进网页。
  渲染顺序必须先把 `<` `>` `&` 转义，再叠加 Markdown 语法，否则文档里
  出现的 `` `<script>` `` 这类示例会变成真实标签。
* **绝不执行**：文档只是文本，任何情况下都不解析成可执行内容。
* **确定性**：同一份文档、同一份代码 → 同一个 HTML。

用法
----
    from api.docs_render import render_markdown, render_index
    html = render_markdown(md_text, title="...", rel="benchmark/v1.md")
"""
from __future__ import annotations

import html
import os
import re
from typing import List, Tuple

# 渲染器的样式：刻意走极简的静态 CSS，不引任何外链资源。
# 原因同"零网络"不变量 —— 文档页离线打开也必须是可读的。
_CSS = """
body{font-family:-apple-system,system-ui,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
     margin:0;background:#0f172a;color:#e2e8f0;line-height:1.65}
.wrap{max-width:920px;margin:0 auto;padding:40px 24px 80px}
a{color:#7dd3fc}
a:hover{color:#bae6fd}
h1{font-size:30px;border-bottom:1px solid #334155;padding-bottom:10px;margin-top:8px}
h2{font-size:23px;margin-top:34px;border-bottom:1px solid #1e293b;padding-bottom:6px}
h3{font-size:19px;margin-top:26px}
p{margin:12px 0}
code{background:#1e293b;padding:1px 6px;border-radius:4px;font-size:.9em;
     font-family:"SFMono-Regular",Consolas,Menlo,monospace;color:#fbbf24}
pre{background:#020617;border:1px solid #1e293b;border-radius:8px;
    padding:16px;overflow-x:auto}
pre code{background:none;padding:0;color:#e2e8f0;font-size:13px}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14px}
th,td{border:1px solid #334155;padding:8px 12px;text-align:left}
th{background:#1e293b}
tr:nth-child(even) td{background:#111c2e}
blockquote{border-left:3px solid #f59e0b;background:#1a1409;
            margin:14px 0;padding:10px 18px;color:#fcd34d}
ul,ol{padding-left:26px}
li{margin:4px 0}
.meta{color:#94a3b8;font-size:13px;margin-bottom:28px}
.badge{display:inline-block;background:#064e3b;color:#6ee7b7;border:1px solid #059669;
       border-radius:999px;padding:2px 12px;font-size:12px;margin-right:8px}
.doclist{list-style:none;padding:0}
.doclist li{margin:7px 0;padding:8px 12px;background:#111c2e;border-radius:6px}
.doclist a{font-family:"SFMono-Regular",Consolas,Menlo,monospace;font-size:13px}
.back{display:inline-block;margin-bottom:22px}
""".strip()


# ── 路径安全 ─────────────────────────────────────────────────────────
def safe_doc_path(root: str, rel: str) -> str | None:
    """把 `/docs/<rel>` 解析成磁盘路径；任何越界返回 None。

    为什么不简单用 os.path.join：`rel = "../secret"` 或 `rel = "/etc/passwd"`
    都能绕出去。resolve 之后必须仍然落在 docs 目录内，否则一律拒绝。
    """
    root_abs = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_abs, rel.lstrip("/")))
    if target == root_abs:
        return None
    if not target.startswith(root_abs + os.sep):
        return None
    if not os.path.isfile(target):
        return None
    return target


# ── 行内语法 ─────────────────────────────────────────────────────────
def _inline(text: str) -> str:
    """处理已转义文本里的行内语法：粗体 / 斜体 / 行内代码 / 链接。"""
    # 行内代码优先且内容不再参与其它转换：先抽出来占位，最后回填。
    codes: List[str] = []

    def _stash(m: re.Match) -> str:
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", _stash, text)

    # 粗体（** 与 __ 两种写法）
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    # 斜体（避开已成对的 **）
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    # 链接：保留转义后的文本，href 里去掉空格
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>',
        text,
    )

    # 回填行内代码（已转义，直接包 code 标签）
    def _restore(m: re.Match) -> str:
        return f"<code>{codes[int(m.group(1))]}</code>"

    return re.sub(r"\x00(\d+)\x00", _restore, text)


# ── 块级渲染 ─────────────────────────────────────────────────────────
def _render_table(rows: List[List[str]]) -> str:
    """把表格行（已按 | 拆分）渲染成 <table>。"""
    if not rows:
        return ""
    head = rows[0]
    out = ["<table>", "<thead>", "<tr>"]
    out.extend(f"<th>{_inline(html.escape(c))}</th>" for c in head)
    out += ["</tr>", "</thead>", "<tbody>"]
    for row in rows[1:]:
        out.append("<tr>")
        # 补齐/截断到表头列数，避免 Markdown 表格列数不齐时错位
        cells = (row + [""] * len(head))[: len(head)]
        out.extend(f"<td>{_inline(html.escape(c))}</td>" for c in cells)
        out.append("</tr>")
    out += ["</tbody>", "</table>"]
    return "\n".join(out)


def extract_title(md: str, fallback: str = "") -> str:
    """从正文提取第一个 `# ` 一级标题。

    为什么不直接用 front matter 标题：`docs/benchmark/v1.md` 没有 YAML 头，
    标题写在正文第一行 `# AIShield Security Benchmark v1`。只认 front matter
    会让 benchmark 页的 `<title>` 退化成文件名 "v1" —— 搜索引擎抓到的就是
    "v1 — AIShield"，等于白做了 SEO。
    """
    for ln in md.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", ln)
        if m:
            return m.group(1).strip()
    return fallback


def strip_front_matter(md: str) -> Tuple[str, str]:
    """剥离 Jekyll YAML front matter，返回 (正文, 标题)。

    docs/blog/ 下的文章带 `---\\nlayout: default\\ntitle: xxx\\n---` 头。
    不剥离的话 `---` 会被渲染成水平线、字段被渲染成段落，页面开头一片乱码。
    """
    lines = md.splitlines()
    if lines and lines[0].strip() == "---":
        for k in range(1, len(lines)):
            if lines[k].strip() == "---":
                title = ""
                for ln in lines[1:k]:
                    m = re.match(r"^\s*title\s*:\s*(.+?)\s*$", ln)
                    if m:
                        title = m.group(1).strip().strip('"').strip("'")
                        break
                return "\n".join(lines[k + 1:]), title
    return md, ""


def render_markdown(md: str, title: str = "AIShield 文档", rel: str = "") -> str:
    """Markdown → 完整 HTML 页面。"""
    md, fm_title = strip_front_matter(md)
    # 标题优先级：显式传入 > front matter > 正文首个 `# ` 标题 > 默认
    if title in ("AIShield 文档", ""):
        title = fm_title or extract_title(md, fallback="AIShield 文档")
    lines = md.splitlines()
    out: List[str] = []
    i = 0
    n = len(lines)
    # 表格缓冲
    table_buf: List[List[str]] = []

    def flush_table() -> None:
        nonlocal table_buf
        if table_buf:
            out.append(_render_table(table_buf))
            table_buf = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 代码块（围栏）
        if stripped.startswith("```"):
            flush_table()
            lang = stripped[3:].strip()
            buf: List[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(buf))
            lang_attr = f' class="lang-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{lang_attr}>{code}</code></pre>")
            continue

        # 表格行
        if stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 2:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # 分隔行 |---|---| 跳过，但保留"上一行是表头"的语义
            if all(re.fullmatch(r":?-{2,}:?", c or "") for c in cells):
                i += 1
                continue
            table_buf.append(cells)
            i += 1
            continue
        flush_table()

        # 空行
        if not stripped:
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(html.escape(m.group(2)))}</h{lvl}>")
            i += 1
            continue

        # 引用
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote>{_inline(html.escape(' '.join(buf)))}</blockquote>")
            continue

        # 无序列表
        if re.match(r"^[-*+]\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s+", "", lines[i]).strip())
                i += 1
            out.append("<ul>" + "".join(
                f"<li>{_inline(html.escape(it))}</li>" for it in items
            ) + "</ul>")
            continue

        # 有序列表
        if re.match(r"^\d+[.)]\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.)]\s+", "", lines[i]).strip())
                i += 1
            out.append("<ol>" + "".join(
                f"<li>{_inline(html.escape(it))}</li>" for it in items
            ) + "</ol>")
            continue

        # 水平线
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        # 普通段落：合并连续非空行
        buf = [stripped]
        i += 1
        while (
            i < n
            and lines[i].strip()
            and not lines[i].strip().startswith(("#", ">", "|", "```"))
            and not re.match(r"^[-*+]\s+|^\d+[.)]\s+", lines[i].strip())
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(html.escape(' '.join(buf)))}</p>")

    flush_table()
    body = "\n".join(out)
    crumbs = f'<span class="badge">docs</span><span class="badge">{html.escape(rel)}</span>' if rel else ""
    return (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"<title>{html.escape(title)} — AIShield</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n<div class=\"wrap\">\n"
        '<a class="back" href="/docs/">← 全部文档</a>\n'
        f"{crumbs}\n{body}\n"
        '<hr><p class="meta">来源：'
        '<a href="https://github.com/lm203688/aishield/tree/main/docs">docs/'
        + html.escape(rel or "index")
        + "</a> · 由 aishield.tools 直接渲染，零外链依赖</p>\n"
        "</div>\n</body>\n</html>"
    )


def list_docs(root: str) -> List[Tuple[str, str]]:
    """列出 docs/ 下所有可渲染文档，返回 (相对路径, 标题)。"""
    items: List[Tuple[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("_") and d != "node_modules")
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if fn.startswith("_") or fn == "CNAME":
                continue
            if fn.endswith(".md"):
                # 标题取正文首个 `# ` 行，没有则用文件名
                title = fn[:-3].replace("-", " ").replace("_", " ")
                try:
                    with open(full, "r", encoding="utf-8") as f:
                        title = extract_title(f.read(), fallback=title)
                except OSError:
                    pass
                items.append((rel, title))
            elif fn.endswith((".html", ".svg", ".txt", ".json", ".png")):
                items.append((rel, fn))
    return items


def render_index(root: str) -> str:
    """`/docs/` 首页：全部文档的目录。"""
    items = list_docs(root)
    groups: dict = {}
    for rel, title in items:
        folder = rel.split("/")[0] if "/" in rel else "(根目录)"
        groups.setdefault(folder, []).append((rel, title))

    blocks: List[str] = []
    for folder in sorted(groups):
        rows = "".join(
            f'<li><a href="/docs/{html.escape(rel)}">{html.escape(title)}</a></li>'
            for rel, title in groups[folder]
        )
        blocks.append(
            f"<h2>{html.escape(folder)}</h2><ul class=\"doclist\">{rows}</ul>"
        )

    body = (
        "<h1>AIShield 技术文档</h1>"
        "<p>benchmark 分数、验证 harness、雷达 shadow gate、情报简报与全部设计文档。"
        "全部内容从 git 仓库实时渲染，零外链依赖。</p>"
        + "".join(blocks)
    )
    return (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>AIShield 技术文档</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n<div class=\"wrap\">\n{body}\n"
        '<hr><p class="meta">仓库：<a href="https://github.com/lm203688/aishield">'
        "github.com/lm203688/aishield</a> · 共 "
        + str(len(items))
        + " 份文档</p>\n</div>\n</body>\n</html>"
    )
