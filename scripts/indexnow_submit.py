#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IndexNow 提交器（GEO 收录加速）
================================

背景
----
GEO 链路的最后一环此前是断的：``scripts/content_pipeline.py`` 里只有一句
「4. 通过 IndexNow 提交新 URL 加速收录」的手动 TODO，仓库里也没有任何提交
实现。归档包（核心工作成果包_20260915）里的 ``kb-workflow/scripts/seo-submit.sh``
提供了可用模式，但那个脚本把 IndexNow key 硬编码进了源码，而且指向的是
genetech.tools 的 13 个站 —— 不能直接搬。

本脚本做两件事它没做的事：
  1. key 不进源码（env → 仓库内的 key 文件 → 报错），密钥不进 git 历史。
  2. 网络失败不算成功（见下方退出码表）。「假绿」是本仓库历史上最深的坑。

另外一个真实根因：IndexNow 规范要求 ``https://<host>/<key>.txt`` 返回 key
原文，否则 Bing/Yandex 会拒绝提交。此前 ``api/static/indexnow-key.txt``
只躺在仓库里、从未挂路由（线上实测 ``/indexnow-key.txt`` 与 ``/<key>.txt``
都是 404），key 不可校验 —— 提交链路从第一天起就是断的。``--check-key``
会先验这件事，避免「提交成功」其实是「搜索引擎拒收」的假绿。

用法
----
  # 读本地 sitemap 提交
  python scripts/indexnow_submit.py

  # 指定 URL
  python scripts/indexnow_submit.py --url https://aishield.tools/docs

  # 同时投 Bing sitemap ping（独立于 IndexNow 的第二条通知通道）
  python scripts/indexnow_submit.py --all-endpoints --ping-bing

  # 只验证 key 可校验性，不提交
  python scripts/indexnow_submit.py --check-key

  # 只打印 payload，不发网络请求
  python scripts/indexnow_submit.py --dry-run

退出码
------
  0  全部端点提交成功
  2  配置错误（找不到 IndexNow key）
  3  key 不可校验（搜索引擎会拒收，先修 api/server.py 的校验路由）
  4  所有端点提交失败
  5  网络不可达 —— 无法验证结果，不算成功

依赖：仅标准库。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
HOST = "aishield.tools"
SITE = f"https://{HOST}"
DEFAULT_SITEMAP = REPO_ROOT / "api" / "static" / "sitemap.xml"
KEY_FILE = REPO_ROOT / "api" / "static" / "indexnow-key.txt"

# api.indexnow.org 是规范里的规范端点（由它扇出到各搜索引擎）。
# 另外两个是 Bing / Yandex 自己的入口，`--all-endpoints` 时一并投递。
ENDPOINT_PRIMARY = "https://api.indexnow.org/indexnow"
ENDPOINTS_EXTRA = [
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]

# Bing 的 sitemap ping 是独立于 IndexNow 的另一条通知通道：只需 GET 一次
# /ping?sitemap=<url>，不要求域名 key 校验，因此即使 IndexNow key 出问题也能
# 至少通知到 Bing。两者都投，覆盖面更全。
BING_PING = "https://www.bing.com/ping"

EXIT_OK = 0
EXIT_CONFIG = 2
EXIT_KEY_UNVERIFIABLE = 3
EXIT_ALL_FAILED = 4
EXIT_NETWORK_UNREACHABLE = 5

# 可重试的状态码：与 .github/workflows/ci.yml 的 withRetry 判据保持一致。
RETRYABLE = {403, 429, 500, 502, 503, 504}


def resolve_key(env_key: Optional[str] = None, key_file: Path = KEY_FILE) -> str:
    """按 env → 仓库 key 文件的顺序解析 IndexNow key。找不到就抛错。"""
    candidate = (env_key or os.environ.get("INDEXNOW_KEY") or "").strip()
    if candidate:
        return candidate
    if key_file.exists():
        value = key_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    raise RuntimeError(
        "找不到 IndexNow key：设置 INDEXNOW_KEY 环境变量，或写入 "
        f"{os.path.relpath(key_file, REPO_ROOT)}（key 原文，无前后空白）"
    )


def urls_from_sitemap(path: Path) -> List[str]:
    """从 sitemap.xml 抽取 <loc>。纯文本解析，不依赖 lxml。"""
    if not path.exists():
        raise RuntimeError(f"sitemap 不存在: {path}")
    text = path.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"<loc>([^<]+)</loc>", text)))


def _open(url: str, method: str, body: Optional[bytes], headers: Dict[str, str],
          timeout: int, insecure: bool):
    """带重试的 HTTP 调用。返回 (status, body_text)。"""
    ctx = ssl._create_unverified_context() if insecure else None
    last_status, last_err = None, None
    for attempt in range(1, 5):
        try:
            req = urllib.request.Request(url, data=body, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last_status, last_err = e.code, str(e)
            payload = e.read().decode("utf-8", "replace") if e.fp else ""
            if e.code in RETRYABLE and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            return e.code, payload
        except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as e:
            last_err = str(e)
            if attempt < 4:
                time.sleep(2 ** attempt)
                continue
            return None, last_err
    return last_status, last_err or "重试耗尽"


def check_key(key: str, timeout: int, insecure: bool) -> Dict[str, object]:
    """验证 https://<host>/<key>.txt 是否返回 key 原文。"""
    url = f"{SITE}/{key}.txt"
    status, body = _open(url, "GET", None, {"User-Agent": "AIShield/IndexNow"},
                         timeout, insecure)
    return {
        "url": url,
        "status": status,
        "verifiable": status == 200 and body.strip() == key,
        "body": (body or "")[:120],
    }


def ping_bing(sitemap_url: str, timeout: int, insecure: bool,
              dry_run: bool) -> Dict[str, object]:
    """通知 Bing 有新 sitemap。GET 一次，不需要域名 key 校验。

    与 IndexNow 的区别：IndexNow 校验 key 归属、失败会静默拒收；Bing ping 只做
    通知。所以 ping 成功不代表收录，但 ping 至少多一条独立通道。
    """
    url = f"{BING_PING}?sitemap={urllib.parse.quote(sitemap_url, safe='')}"
    if dry_run:
        return {"dry_run": True, "url": url}
    status, resp = _open(url, "GET", None, {"User-Agent": "AIShield/IndexNow"},
                         timeout, insecure)
    ok = status in (200, 202)
    return {
        "dry_run": False,
        "url": url,
        "status": status,
        "ok": ok,
        "response": (resp or "")[:200],
    }


def submit(urls: List[str], key: str, endpoints: List[str], timeout: int,
           insecure: bool, dry_run: bool) -> Dict[str, object]:
    """POST 到各 IndexNow 端点，返回逐端点结果。"""
    payload = {"host": HOST, "key": key, "urlList": urls}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    results = []
    if dry_run:
        return {"dry_run": True, "payload": payload, "endpoints": endpoints}

    for endpoint in endpoints:
        status, resp = _open(endpoint, "POST", body, {
            "Content-Type": "application/json",
            "User-Agent": "AIShield/IndexNow",
        }, timeout, insecure)
        ok = status in (200, 202)
        results.append({
            "endpoint": endpoint,
            "status": status,
            "ok": ok,
            "response": (resp or "")[:300],
        })
    return {"dry_run": False, "submitted": len(urls), "results": results}


def main(argv: Optional[List[str]] = None, key_file: Optional[Path] = None) -> int:
    """CLI 入口。

    :param argv: 命令行参数（测试用）
    :param key_file: key 文件路径（测试用）；默认取模块级 KEY_FILE。
                     注意必须显式传入 —— Python 默认参数在 def 时就已绑定，
                     patch 模块级 KEY_FILE 不会生效。
    """
    parser = argparse.ArgumentParser(description="AIShield IndexNow 提交器")
    parser.add_argument("--url", action="append", default=[],
                        help="要提交的 URL，可重复。给了就不再读 sitemap。")
    parser.add_argument("--sitemap", default=str(DEFAULT_SITEMAP),
                        help="sitemap.xml 路径（默认 api/static/sitemap.xml）")
    parser.add_argument("--key", default=None, help="IndexNow key（默认从 env/文件读）")
    parser.add_argument("--max-urls", type=int, default=100, help="最多提交多少个 URL")
    parser.add_argument("--all-endpoints", action="store_true",
                        help="除 api.indexnow.org 外也投 Bing / Yandex 入口")
    parser.add_argument("--check-key", action="store_true", help="只校验 key 可校验性")
    parser.add_argument("--ping-bing", action="store_true",
                        help="额外用 Bing sitemap ping 通知一次（独立于 IndexNow 的通道）")
    parser.add_argument("--dry-run", action="store_true", help="只打印 payload")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--insecure", action="store_true",
                        help="跳过 TLS 校验（本地 TLS 拦截代理环境兜用）")
    args = parser.parse_args(argv)

    try:
        key = resolve_key(args.key, key_file=key_file or KEY_FILE)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        return EXIT_CONFIG

    if args.check_key:
        info = check_key(key, args.timeout, args.insecure)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        if info["status"] is None:
            return EXIT_NETWORK_UNREACHABLE
        return EXIT_OK if info["verifiable"] else EXIT_KEY_UNVERIFIABLE

    urls = list(args.url) if args.url else urls_from_sitemap(Path(args.sitemap))
    urls = urls[: args.max_urls]
    if not urls:
        print(json.dumps({"error": "没有可提交的 URL"}, ensure_ascii=False, indent=2))
        return EXIT_CONFIG

    endpoints = [ENDPOINT_PRIMARY]
    if args.all_endpoints:
        endpoints += ENDPOINTS_EXTRA

    result = submit(urls, key, endpoints, args.timeout, args.insecure, args.dry_run)

    if args.ping_bing:
        # ping 指向线上 sitemap，而不是本地文件路径 —— 搜索引擎读不到本地文件。
        sitemap_url = f"{SITE}/sitemap.xml"
        result["bing_ping"] = ping_bing(sitemap_url, args.timeout, args.insecure,
                                        args.dry_run)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.dry_run:
        return EXIT_OK

    statuses = [r["status"] for r in result["results"]]
    if all(s is None for s in statuses):
        return EXIT_NETWORK_UNREACHABLE
    if not any(r["ok"] for r in result["results"]):
        # IndexNow 全挂但 Bing ping 成功时仍算链路可用，不判 ALL_FAILED ——
        # 两条通道里至少一条通，收录通知就发出了。
        ping = result.get("bing_ping") or {}
        if ping.get("ok"):
            return EXIT_OK
        return EXIT_ALL_FAILED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
