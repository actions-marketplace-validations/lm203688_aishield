"""
AIShield Arena Agent — standalone FastAPI server (local dev / alternative deploys).

The production deployment uses api/server.py's http.server-based routes
(/api/v1/arena/health + /api/v1/arena/scan) which live under
https://aishield.tools/api/v1/arena/*.

This file exists for:
  * Local dev / smoke testing without going through the main server
  * Users who want to deploy the arena agent on their own infrastructure
    (Docker, cloud function, etc.) via FastAPI + uvicorn
  * CLI selftest

All scan logic lives in api/arena_core.py — this file is only the FastAPI
wrapper. Do NOT duplicate scan logic here.

Usage:
    python scripts/arena/arena_agent.py serve --port 8080
    python scripts/arena/arena_agent.py selftest
    python scripts/arena/arena_agent.py version
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path so `api.arena_core` is importable
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from api.arena_core import (  # noqa: E402
    SCANNER_AVAILABLE,
    SCANNER_VERSION,
    PAYLOAD_LIMIT_BYTES,
    RateLimiter,
    arena_envelope_to_payload,
    report_to_dict,
    run_scan,
    selftest as _core_selftest,
    _get_rule_count,
)


# ---------------------------------------------------------------------------
# FastAPI dependency (optional)
# ---------------------------------------------------------------------------

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    FASTAPI_AVAILABLE = False
    FastAPI = None  # type: ignore[assignment]
    Request = None  # type: ignore[assignment]
    HTTPException = Exception  # type: ignore[assignment,misc]
    JSONResponse = None  # type: ignore[assignment]


def create_app(limiter: RateLimiter | None = None) -> Any:
    """Build the FastAPI app exposing /arena/scan + /arena/health."""
    if not FASTAPI_AVAILABLE:  # pragma: no cover
        raise RuntimeError(
            "FastAPI is not installed. Install with: pip install fastapi uvicorn"
        )
    limiter = limiter or RateLimiter()
    app = FastAPI(
        title="AIShield Arena Agent",
        version="1.0.0",
        description=(
            "Security scanner for AI agent tool configurations. "
            "Aligned to OWASP MCP Top 10 + Agentic AI Top 10. "
            "Production endpoint: https://aishield.tools/api/v1/arena/scan"
        ),
    )

    @app.get("/arena/health")
    async def health() -> dict[str, Any]:
        return {
            "ok": True,
            "version": SCANNER_VERSION,
            "scanner_available": SCANNER_AVAILABLE,
            "mcp_rules": _get_rule_count("mcp") if _get_rule_count else None,
            "skill_rules": _get_rule_count("skill") if _get_rule_count else None,
        }

    @app.post("/arena/scan")
    async def scan(request: Request) -> Any:
        ip = request.client.host if request.client else "unknown"
        if not limiter.allow(ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        body_bytes = await request.body()
        if len(body_bytes) > PAYLOAD_LIMIT_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Payload too large (limit {PAYLOAD_LIMIT_BYTES} bytes)",
            )

        import json
        try:
            envelope = json.loads(body_bytes)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}")

        if isinstance(envelope, dict) and ("config" in envelope or "payload" in envelope):
            payload = arena_envelope_to_payload(envelope)
        else:
            payload = envelope if isinstance(envelope, dict) else {"config": envelope}

        report = run_scan(payload)
        return JSONResponse(report_to_dict(report))

    return app


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AIShield Arena Agent (FastAPI wrapper)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="Run the arena agent HTTP server")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8080)
    serve.add_argument("--rate-limit", type=int, default=60,
                       help="Max requests per hour per IP (default: 60)")

    sub.add_parser("selftest", help="Smoke test the scanner adapter")
    sub.add_parser("version", help="Print version and exit")

    args = parser.parse_args(argv)

    if args.cmd == "version":
        print(f"wrapper={SCANNER_VERSION}")
        print(f"scanner_available={SCANNER_AVAILABLE}")
        print(f"fastapi_available={FASTAPI_AVAILABLE}")
        return 0

    if args.cmd == "selftest":
        return _core_selftest()

    if args.cmd == "serve":
        if not FASTAPI_AVAILABLE:
            print("FastAPI not installed. Install with: pip install fastapi uvicorn")
            return 2
        import uvicorn  # type: ignore
        app = create_app(RateLimiter(max_per_hour=args.rate_limit))
        print(f"Starting AIShield Arena Agent on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
