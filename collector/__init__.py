"""AIShield Collector -- local-first continuous security observation for agents.

Public surface::

    from collector import collect_once, collect_from_configs, manifest, summarize

The collector turns AIShield from "run a scan" into "keep watching": it
discovers local MCP client configurations, re-scans them on an interval and
emits canonical security events (JSONL), plus a compact trust digest an agent
can cache on.
"""

from .aishield_collector import (  # noqa: F401
    COLLECTOR_NAME,
    SCHEMA_VERSION,
    EVENT_TYPES,
    append_jsonl,
    canonical_event,
    collect_from_configs,
    collect_once,
    events_from_result,
    fingerprint,
    main,
    manifest,
    read_jsonl,
    run_watch,
    summarize,
)

__all__ = [
    "COLLECTOR_NAME",
    "SCHEMA_VERSION",
    "EVENT_TYPES",
    "append_jsonl",
    "canonical_event",
    "collect_from_configs",
    "collect_once",
    "events_from_result",
    "fingerprint",
    "main",
    "manifest",
    "read_jsonl",
    "run_watch",
    "summarize",
]
