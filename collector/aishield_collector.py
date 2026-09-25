#!/usr/bin/env python3
"""AIShield Collector -- local-first continuous security observation for agents.

Architecture borrowed from ``microsoft/project-telescope`` (a ``Collector``
manifest + an interval ``collect()`` loop + a canonical, internally-tagged
event schema), with one deliberate difference: telescope records *what an
agent did*, AIShield's collector records *whether what the agent is configured
with should be believed*. Behavior observability and content trust are
complementary planes; this module is the trust side.

Design invariants (asserted by ``tests/test_collector.py``):
  * never spawns or executes a command found in a scanned configuration
  * never makes a network call
  * standard library only (zero third-party dependencies)
  * finding evidence is passed through exactly as the scanner emitted it
    (the scanner already redacts credential values to ``<redacted:kind>``)

Usage::

    python -m collector.aishield_collector --manifest
    python -m collector.aishield_collector --once --digest
    python -m collector.aishield_collector --once --out events.jsonl
    python -m collector.aishield_collector --watch --interval 60 --out events.jsonl
    python -m collector.aishield_collector --scan-file ./mcp.json --digest
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import time

# Repo root on sys.path so `python -m collector.aishield_collector` works from anywhere.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

COLLECTOR_NAME = "aishield-collector"
SCHEMA_VERSION = "aishield-collector/v1"

EVENT_TYPES = (
    "CollectorStarted",
    "ConfigDiscovered",
    "FindingRaised",
    "ScanCompleted",
    "CollectorHeartbeat",
)

# Highest first -- used to sort findings so the digest surfaces the worst items.
_SEVERITY_ORDER = ("critical", "high", "medium", "low", "info")


def _tool_version():
    """Single source of truth: the scanner's own shipped version."""
    try:
        from scanner.sbom import TOOL_VERSION

        return TOOL_VERSION
    except Exception:
        return "0.0.0"


def _now_iso():
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def manifest():
    """Collector manifest -- declares what this collector is and is not."""
    return {
        "name": COLLECTOR_NAME,
        "version": _tool_version(),
        "schema_version": SCHEMA_VERSION,
        "description": (
            "Local-first content-trust collector: discovers local MCP client "
            "configurations, re-scans them on change and emits canonical "
            "security events. Never executes a scanned command."
        ),
        "event_types": list(EVENT_TYPES),
        "transport": "jsonl",
        "local_first": True,
        "network": False,
        "spawns_scanned_configs": False,
    }


def canonical_event(etype, **payload):
    """Build one internally-tagged canonical event (telescope-style)."""
    if etype not in EVENT_TYPES:
        raise ValueError(
            "unknown event type %r; expected one of %s" % (etype, ", ".join(EVENT_TYPES))
        )
    event = {
        "schema_version": SCHEMA_VERSION,
        "type": etype,
        "ts": _now_iso(),
        "collector": COLLECTOR_NAME,
    }
    event.update(payload)
    return event


def _sorted_findings(findings):
    def key(f):
        try:
            return _SEVERITY_ORDER.index(str(f.get("severity", "info")).lower())
        except ValueError:
            return len(_SEVERITY_ORDER)

    return sorted(findings, key=key)


def _normalized_findings(findings):
    """Security-relevant projection used for the content fingerprint."""
    out = []
    for f in _sorted_findings(findings):
        out.append(
            {
                "type": f.get("type"),
                "severity": f.get("severity"),
                "server": f.get("server"),
                "file": f.get("file"),
                "owasp_category": f.get("owasp_category"),
                "evidence": f.get("evidence"),
            }
        )
    return out


def fingerprint(result):
    """Stable content hash of the verdict.

    Two scans of an unchanged configuration produce the same fingerprint, so a
    collector loop can cheaply decide "nothing changed" instead of re-emitting
    and re-alerting. This is what makes the collector idempotent.
    """
    payload = json.dumps(
        {
            "summary": result.get("summary", {}),
            "findings": _normalized_findings(result.get("findings", [])),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def summarize(result, max_findings=3):
    """Compact trust digest for agent consumption.

    Inspired by Cache-to-Cache's observation that a rich-but-compact semantic
    carrier beats re-transmitting an entire report: an agent that only needs
    "should I trust this?" can read a few hundred bytes and cache on the
    fingerprint instead of pulling the full findings list every turn.
    """
    summary = result.get("summary", {}) or {}
    findings = _sorted_findings(result.get("findings", []) or [])
    top = []
    for f in findings[: max(0, int(max_findings))]:
        top.append(
            {
                "severity": f.get("severity"),
                "type": f.get("type"),
                "server": f.get("server"),
                "owasp": f.get("owasp_category"),
            }
        )
    return {
        "collector": COLLECTOR_NAME,
        "version": _tool_version(),
        "config_score": summary.get("config_score"),
        "servers_found": summary.get("servers_found"),
        "findings_total": summary.get("findings_total"),
        "severity_counts": summary.get("severity_counts", {}),
        "top_findings": top,
        "fingerprint": fingerprint(result),
    }


def events_from_result(result, previous_fingerprint=None, max_findings=None):
    """Project a scan result into canonical events.

    Returns ``(events, fingerprint)``. ``changed`` on the ScanCompleted event
    tells a consumer whether anything actually moved since the last collection.
    """
    fp = fingerprint(result)
    changed = fp != previous_fingerprint
    summary = result.get("summary", {}) or {}
    events = [
        canonical_event(
            "ScanCompleted",
            config_score=summary.get("config_score"),
            servers_found=summary.get("servers_found"),
            findings_total=summary.get("findings_total"),
            severity_counts=summary.get("severity_counts", {}),
            fingerprint=fp,
            changed=changed,
        )
    ]

    findings = _sorted_findings(result.get("findings", []) or [])
    if max_findings is not None:
        findings = findings[: max(0, int(max_findings))]
    for f in findings:
        events.append(
            canonical_event(
                "FindingRaised",
                severity=f.get("severity"),
                finding_type=f.get("type"),
                server=f.get("server"),
                file=f.get("file"),
                owasp_category=f.get("owasp_category"),
                description=f.get("description"),
                evidence=f.get("evidence"),
                remediation=f.get("remediation"),
            )
        )
    return events, fp


def _discovery_events(discovered):
    events = []
    for d in discovered or []:
        events.append(
            canonical_event(
                "ConfigDiscovered",
                path=d.get("path"),
                client=d.get("client"),
                scope=d.get("scope"),
                exists=bool(d.get("exists")),
            )
        )
    return events


def _collect_result(result, discovered=None, previous_fingerprint=None, max_findings=None):
    events, fp = events_from_result(
        result, previous_fingerprint=previous_fingerprint, max_findings=max_findings
    )
    events = _discovery_events(discovered) + events
    digest = summarize(result)
    return {
        "result": result,
        "events": events,
        "fingerprint": fp,
        "digest": digest,
        "changed": fp != previous_fingerprint,
    }


def collect_from_configs(configs, previous_fingerprint=None, max_findings=None):
    """Scan an explicit ``{path: content}`` mapping. Pure, no discovery, no FS.

    This is the injection point used by tests and by callers that already have
    configuration text in hand (e.g. a CI harness).
    """
    from scanner.client_discovery import scan_client_configs

    result = scan_client_configs(configs)
    return _collect_result(
        result, previous_fingerprint=previous_fingerprint, max_findings=max_findings
    )


def collect_once(home=None, project_root=None, platform_name=None, read=None,
                 previous_fingerprint=None, max_findings=None):
    """Discover local MCP configurations, scan them, and return events + digest."""
    from scanner.client_discovery import discover_and_scan

    result = discover_and_scan(
        home=home, project_root=project_root, platform_name=platform_name, read=read
    )
    return _collect_result(
        result,
        discovered=result.get("discovered"),
        previous_fingerprint=previous_fingerprint,
        max_findings=max_findings,
    )


def append_jsonl(records, out_path):
    """Append canonical events to a JSONL file. Returns the number written."""
    if not records:
        return 0
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    written = 0
    with open(out_path, "a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            written += 1
    return written


def read_jsonl(path):
    """Read a JSONL event log back into a list (skips blank / corrupt lines)."""
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def run_watch(interval=60, out_path=None, iterations=None, home=None,
              project_root=None, platform_name=None, read=None,
              max_findings=None, emit_heartbeat=True, on_cycle=None):
    """Collect on an interval, emitting events only when the verdict changes.

    ``iterations=None`` runs until interrupted. ``on_cycle`` is a test hook
    called with the cycle result after each pass.
    """
    interval = max(1, int(interval))
    previous = None
    cycle = 0
    started = canonical_event("CollectorStarted", interval=interval, manifest=manifest())
    if out_path:
        append_jsonl([started], out_path)

    while iterations is None or cycle < iterations:
        cycle += 1
        outcome = collect_once(
            home=home,
            project_root=project_root,
            platform_name=platform_name,
            read=read,
            previous_fingerprint=previous,
            max_findings=max_findings,
        )
        previous = outcome["fingerprint"]

        to_write = outcome["events"]
        if not outcome["changed"] and emit_heartbeat:
            to_write = [
                canonical_event(
                    "CollectorHeartbeat",
                    cycle=cycle,
                    fingerprint=previous,
                    config_score=outcome["digest"].get("config_score"),
                )
            ]
        if out_path:
            append_jsonl(to_write, out_path)
        if on_cycle is not None:
            on_cycle(outcome)
        if iterations is None or cycle < iterations:
            time.sleep(interval)
    return previous


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="aishield-collector",
        description="Local-first content-trust collector for MCP/agent configurations.",
    )
    parser.add_argument("--manifest", action="store_true", help="print the collector manifest and exit")
    parser.add_argument("--once", action="store_true", help="run a single discovery + scan pass")
    parser.add_argument("--watch", action="store_true", help="run continuously on an interval")
    parser.add_argument("--interval", type=int, default=60, help="seconds between watch cycles (default 60)")
    parser.add_argument("--iterations", type=int, default=None, help="stop after N watch cycles (test/CI use)")
    parser.add_argument("--scan-file", default=None, help="scan a single config file instead of discovering")
    parser.add_argument("--out", default=None, help="append canonical events to this JSONL file")
    parser.add_argument("--digest", action="store_true", help="print the compact trust digest")
    parser.add_argument("--max-findings", type=int, default=None, help="cap FindingRaised events per pass")
    parser.add_argument("--home", default=None, help="override home directory for discovery")
    parser.add_argument("--project-root", default=None, help="override project root for discovery")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    args = parser.parse_args(argv)

    indent = 2 if args.pretty else None

    if args.manifest:
        print(json.dumps(manifest(), ensure_ascii=False, indent=indent))
        return 0

    if args.scan_file:
        with open(args.scan_file, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        outcome = collect_from_configs(
            {args.scan_file: content}, max_findings=args.max_findings
        )
        if args.out:
            append_jsonl(outcome["events"], args.out)
        print(json.dumps(outcome["digest"] if args.digest else outcome["result"],
                         ensure_ascii=False, indent=indent))
        return 0

    if args.watch:
        run_watch(
            interval=args.interval,
            out_path=args.out,
            iterations=args.iterations,
            home=args.home,
            project_root=args.project_root,
            max_findings=args.max_findings,
        )
        return 0

    # --once is the default action
    outcome = collect_once(
        home=args.home,
        project_root=args.project_root,
        max_findings=args.max_findings,
    )
    if args.out:
        append_jsonl(outcome["events"], args.out)
    print(json.dumps(outcome["digest"] if args.digest else outcome["events"],
                     ensure_ascii=False, indent=indent))
    return 0


def create_audit_chain(secret_key: str = None, key_id: str = "default") -> "AuditChain":
    """Create an HMAC audit chain for tamper-evident event logging.

    Inspired by CyberGuard's hash-bound approvals and HMAC audit chain design.
    Each event is signed with HMAC-SHA256, creating a tamper-evident chain
    where any modification breaks the chain.

    Args:
        secret_key: HMAC secret key (generates random if None).
        key_id: Key identifier for rotation tracking.

    Returns:
        AuditChain instance.

    Usage:
        chain = create_audit_chain(secret_key="your-key")
        chain.append(chain.sign(event_payload))
    """
    from .audit_chain import AuditChain
    return AuditChain(secret_key=secret_key, key_id=key_id)


def emit_with_audit(events: list, audit_chain: "AuditChain") -> list:
    """Sign and append events to an audit chain.

    Args:
        events: List of event dicts to sign.
        audit_chain: AuditChain instance.

    Returns:
        List of signed events.
    """
    signed_events = []
    for event in events:
        signed = audit_chain.sign(event)
        audit_chain.append(signed)
        signed_events.append(signed)
    return signed_events


if __name__ == "__main__":
    raise SystemExit(main())
