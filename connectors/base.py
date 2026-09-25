"""
connectors/base.py — 跨平台 Connector 基础工具
================================================

复用能力（Muse / Grok Bot / 后续其他平台）：
  - OAuth 2.0 授权码 → access_token / refresh_token
  - token 存储（不落盘 client_secret）
  - fail-closed 自动续期
  - HTTPS_PROXY 透传（大陆需海外代理）
  - 敏感动词检测（8 种通用触发词）
  - prompt 金额粗估（¥/$ + 数字）
  - HMAC prompt 指纹（审计用）
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

HTTPPost = Optional[Callable[[str, Dict[str, Any]], Tuple[int, Dict[str, Any]]]]

# ============================================================
# Proxy 支持（大陆访问海外平台必需）
# ============================================================


def _opener(timeout: int) -> urllib.request.OpenerDirector:
    """构建支持 HTTPS_PROXY / HTTP_PROXY / SOCKS5 的 opener（读环境变量）"""
    handler = urllib.request.ProxyHandler()  # 默认读 env: HTTPS_PROXY, HTTP_PROXY, NO_PROXY
    return urllib.request.build_opener(handler)


def http_post(
    url: str,
    payload: Dict[str, Any],
    token: Optional[str] = None,
    timeout: int = 30,
    http_post_mock: HTTPPost = None,
) -> Tuple[int, Dict[str, Any]]:
    """统一 POST 封装。

    http_post_mock: 测试注入点，签名 (url, payload) → (status, json_dict)
    """
    if http_post_mock is not None:
        return http_post_mock(url, payload)

    headers = {"Content-Type": "application/json", "User-Agent": "AIShield/4.8.2"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers=headers, method="POST",
    )
    try:
        opener = _opener(timeout)
        with opener.open(req, timeout=timeout) as r:
            body = r.read().decode("utf-8")
            try:
                return r.status, json.loads(body)
            except Exception:
                return r.status, {"raw": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": str(e), "raw": body[:500]}
    except urllib.error.URLError as e:
        return 0, {"error": f"network error: {e.reason}", "url": url}
    except Exception as e:
        return 0, {"error": f"unexpected: {type(e).__name__}: {e}", "url": url}


def http_get(url: str, timeout: int = 15, headers: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    """HEAD/GET 通用封装（用于可达性探测）"""
    req = urllib.request.Request(url, headers=headers or {}, method="HEAD")
    try:
        opener = _opener(timeout)
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, url
    except Exception as e:
        return 0, f"error: {e}"


# ============================================================
# 存储
# ============================================================


def store_path(platform_slug: str) -> Path:
    """每平台独立状态文件"""
    base = Path(os.environ.get(
        f"AISHIELD_{platform_slug.upper()}_STORE",
        f"~/.aishield/{platform_slug}/state.json",
    ).replace("~", str(Path.home())))
    base.parent.mkdir(parents=True, exist_ok=True)
    return base


def load_state(platform_slug: str) -> Dict[str, Any]:
    p = store_path(platform_slug)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {"tokens": {}}


def save_state(platform_slug: str, data: Dict[str, Any]) -> None:
    p = store_path(platform_slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def secret_path(platform_slug: str) -> Path:
    return Path(os.environ.get(
        f"AISHIELD_{platform_slug.upper()}_SECRET",
        f"~/.aishield/{platform_slug}/client_secret.txt",
    ).replace("~", str(Path.home())))


def get_client_secret(platform_slug: str) -> Optional[str]:
    env_key = os.environ.get(f"AISHIELD_{platform_slug.upper()}_SECRET_KEY")
    if env_key:
        return env_key
    p = secret_path(platform_slug)
    if p.exists():
        s = p.read_text(encoding="utf-8").strip()
        if s:
            return s
    return None


# ============================================================
# OAuth 通用（授权码 + refresh）
# ============================================================


def build_authorize_url(
    authorize_endpoint: str,
    client_id: str,
    redirect_uri: str,
    scopes: List[str],
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """构造授权 URL（用户浏览器访问；授权后回跳 redirect_uri?code=...&state=...）"""
    import uuid as _uuid
    if not client_id:
        return {"ok": False, "error": "client_id required"}
    st = state or _uuid.uuid4().hex[:16]
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": st,
    }
    return {
        "ok": True,
        "authorize_url": authorize_endpoint + "?" + urllib.parse.urlencode(params),
        "state": st,
        "scopes": scopes,
        "redirect_uri": redirect_uri,
    }


def exchange_code_for_token(
    token_endpoint: str,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    http_post_mock: HTTPPost = None,
) -> Dict[str, Any]:
    """授权码换 token（OAuth 2.0 标准）"""
    if not (code and client_id and client_secret):
        return {"ok": False, "error": "code / client_id / client_secret required"}
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    status, resp = http_post(token_endpoint, body, http_post_mock=http_post_mock)
    data = resp.get("data") if isinstance(resp.get("data"), dict) else resp
    if status != 200 or "access_token" not in data:
        return {"ok": False, "error": "token exchange failed", "status": status, "detail": resp}
    return {
        "ok": True,
        "tokens": {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "expires_at": int(time.time()) + int(data.get("expires_in", 7200)),
            "refresh_expires_at": int(time.time()) + int(data.get("refresh_expires_in", 2592000)),
            "scope": data.get("scope", ""),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "token_type": data.get("token_type", "Bearer"),
        },
    }


def refresh_access_token(
    token_endpoint: str,
    refresh_token: str,
    client_id: str,
    client_secret: str,
    http_post_mock: HTTPPost = None,
) -> Dict[str, Any]:
    if not (refresh_token and client_id and client_secret):
        return {"ok": False, "error": "refresh_token / client_id / client_secret required"}
    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    status, resp = http_post(token_endpoint, body, http_post_mock=http_post_mock)
    data = resp.get("data") if isinstance(resp.get("data"), dict) else resp
    if status != 200 or "access_token" not in data:
        return {"ok": False, "error": "refresh failed", "status": status, "detail": resp}
    return {
        "ok": True,
        "tokens": {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", refresh_token),
            "expires_at": int(time.time()) + int(data.get("expires_in", 7200)),
            "refresh_expires_at": int(time.time()) + int(data.get("refresh_expires_in", 2592000)),
            "scope": data.get("scope", ""),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "token_type": data.get("token_type", "Bearer"),
        },
    }


def store_access_token(platform_slug: str, agent_instance_id: str, client_id: str, tokens: Dict[str, Any]) -> Dict[str, Any]:
    """持久化 token（client_secret 不落盘）"""
    if not (agent_instance_id and tokens.get("access_token")):
        return {"ok": False, "error": "agent_instance_id and tokens.access_token required"}
    state = load_state(platform_slug)
    state.setdefault("tokens", {})[agent_instance_id] = {
        "client_id": client_id,
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "expires_at": tokens.get("expires_at", int(time.time()) + 7200),
        "refresh_expires_at": tokens.get("refresh_expires_at", int(time.time()) + 2592000),
        "scope": tokens.get("scope", ""),
        "fetched_at": tokens.get("fetched_at", datetime.now(timezone.utc).isoformat()),
    }
    save_state(platform_slug, state)
    return {"ok": True, "agent_instance_id": agent_instance_id, "expires_at": tokens.get("expires_at")}


def get_access_token(platform_slug: str, agent_instance_id: str, http_post_mock: HTTPPost = None) -> Dict[str, Any]:
    """取 access_token；过期则 refresh；refresh 失败 → fail-closed（不静默继续）"""
    state = load_state(platform_slug)
    entry = state.get("tokens", {}).get(agent_instance_id)
    if not entry:
        return {"ok": False, "error": "no token stored", "agent_instance_id": agent_instance_id}

    now = int(time.time())
    if entry.get("expires_at", 0) - now > 60:  # 60s 提前刷新
        return {"ok": True, "access_token": entry["access_token"], "expires_at": entry["expires_at"]}

    if not entry.get("refresh_token") or entry.get("refresh_expires_at", 0) < now:
        return {"ok": False, "error": "token expired, refresh unavailable", "action": "re_authorize"}

    # 需要 token_endpoint — 平台侧提供
    token_endpoint = _TOKEN_ENDPOINTS.get(platform_slug)
    if not token_endpoint:
        return {"ok": False, "error": f"unknown platform: {platform_slug}"}

    secret = get_client_secret(platform_slug)
    if not secret:
        return {"ok": False, "error": "client_secret not configured", "action": "re_authorize"}

    result = refresh_access_token(
        token_endpoint, entry["refresh_token"], entry["client_id"], secret,
        http_post_mock=http_post_mock,
    )
    if not result.get("ok"):
        return {"ok": False, "error": "refresh failed", "action": "re_authorize", "detail": result}
    store_access_token(platform_slug, agent_instance_id, entry["client_id"], result["tokens"])
    return {"ok": True, "access_token": result["tokens"]["access_token"],
            "expires_at": result["tokens"].get("expires_at")}


# 各平台 token 端点注册表（platform_slug → token endpoint）
_TOKEN_ENDPOINTS: Dict[str, str] = {}


def register_token_endpoint(platform_slug: str, endpoint: str) -> None:
    _TOKEN_ENDPOINTS[platform_slug] = endpoint


# ============================================================
# 敏感词 + 金额 + 指纹（跨平台通用）
# ============================================================

SENSITIVE_KEYWORDS = [
    # 支付/资金
    "转账", "提现", "付款", "扣款", "charge my card", "withdraw", "transfer",
    # 破坏性
    "删除所有", "群发", "发布到全网", "对外发送", "delete all", "broadcast",
    # 越权
    "以我的名义", "代替我", "on my behalf", "as me",
]

_AMOUNT_PATTERNS = [
    r"[¥￥]\s*(\d+(?:[.,]\d+)?)(?:\s*(?:元|块|CNY|RMB))?",
    r"\$\s*(\d+(?:[.,]\d+)?)",
    r"(\d+(?:[.,]\d+)?)\s*(?:USD|dollars?)",
    r"(\d+(?:[.,]\d+)?)\s*(?:元|块|CNY|RMB)",
    r"€\s*(\d+(?:[.,]\d+)?)",
    r"£\s*(\d+(?:[.,]\d+)?)",
]


def detect_sensitive_triggers(prompt: Optional[str]) -> List[str]:
    if not prompt:
        return []
    p_lower = prompt.lower()
    return [k for k in SENSITIVE_KEYWORDS if k.lower() in p_lower]


def extract_amount(prompt: Optional[str]) -> float:
    best = 0.0
    for pat in _AMOUNT_PATTERNS:
        for m in re.finditer(pat, prompt or "", re.IGNORECASE):
            v = float(m.group(1).replace(",", ""))
            if v > best:
                best = v
    return best


def prompt_fingerprint(prompt: Optional[str]) -> str:
    return hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()[:16]


def proxy_env_summary() -> Dict[str, str]:
    """返回当前 proxy 环境变量（脱敏：只给 scheme/host 判断）"""
    keys = ["HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "SOCKS_PROXY"]
    return {k: (os.environ.get(k, "") or "")[:60] for k in keys if os.environ.get(k)}


__all__ = [
    "http_post", "http_get",
    "store_path", "load_state", "save_state",
    "secret_path", "get_client_secret",
    "build_authorize_url", "exchange_code_for_token", "refresh_access_token",
    "store_access_token", "get_access_token",
    "register_token_endpoint",
    "SENSITIVE_KEYWORDS", "detect_sensitive_triggers",
    "extract_amount", "prompt_fingerprint",
    "proxy_env_summary",
]
