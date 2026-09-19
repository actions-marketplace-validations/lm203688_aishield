# AIShield Collector

**Local-first continuous security observation for agent configurations.**

AIShield scans. The Collector keeps watching. It discovers the MCP client
configurations on a machine, re-scans them on an interval, and emits
**canonical security events** as JSONL — plus a compact **trust digest** an
agent can cache on.

```
discover local MCP configs ─► static scan (no spawn) ─► canonical events (JSONL)
                                                   └─► compact trust digest
```

## Why this design (and what it borrows)

The collector architecture — a declared **manifest**, an interval **collect
loop**, and a **canonical, internally-tagged event schema** — is borrowed from
[`microsoft/project-telescope`](https://github.com/microsoft/project-telescope)
("local-first observability for AI agents"). Telescope records *what an agent
did*; AIShield's collector records *whether what the agent is configured with
should be believed*. Behavior observability and content trust are complementary
planes.

The **compact digest** (score + severity counts + top findings + fingerprint)
follows the same principle behind
[Cache-to-Cache](https://arxiv.org/abs/2510.03215): a rich but small semantic
carrier beats re-transmitting a full report. An agent that only needs
"should I trust this?" reads a few hundred bytes and caches on the
fingerprint, instead of pulling the full findings list every turn.

## Invariants

| Invariant | Why |
|---|---|
| Never spawns a scanned configuration's `command` | Auditing a malicious config must not compromise the auditing machine |
| Never makes a network call | Content trust must work air-gapped and leak-free |
| Standard library only | `npx aishield-mcp-server` and `python -m collector` both stay dependency-free |
| Evidence passed through as emitted | The scanner already redacts credentials to `<redacted:kind>`; the collector must not become a new leak channel |
| Idempotent by fingerprint | An unchanged configuration produces an unchanged fingerprint, so a watch loop does not re-alert |

These are pinned by `tests/test_collector.py`, including a source-level
assertion that the module imports no `subprocess` / `socket` / `urllib`.

## Usage

```bash
# What is this collector, and what does it not do?
python -m collector.aishield_collector --manifest

# One pass over the local machine, print the compact trust digest
python -m collector.aishield_collector --once --digest

# One pass, append canonical events to a JSONL log
python -m collector.aishield_collector --once --out events.jsonl

# Continuous: re-scan every 60s, emit events only when the verdict changes
python -m collector.aishield_collector --watch --interval 60 --out events.jsonl

# Scan a single config file you already have
python -m collector.aishield_collector --scan-file ./mcp.json --digest
```

## Programmatic use

```python
from collector import collect_once, collect_from_configs, summarize

# Discover + scan the local machine (read-only, never executes anything)
outcome = collect_once()
print(outcome["digest"]["config_score"], outcome["fingerprint"])

# Or scan configuration text you already hold (pure, no filesystem discovery)
outcome = collect_from_configs({"mcp.json": open("mcp.json").read()})
for event in outcome["events"]:
    print(event["type"], event.get("severity", ""))
```

## Event schema (`aishield-collector/v1`)

Internally-tagged JSON, one object per line:

```json
{"schema_version": "aishield-collector/v1", "type": "ScanCompleted", "ts": "2026-09-19T07:00:00Z",
 "collector": "aishield-collector", "config_score": 55, "findings_total": 3,
 "severity_counts": {"critical": 1}, "fingerprint": "sha256:...", "changed": true}
```

| Event | Meaning |
|---|---|
| `CollectorStarted` | A watch loop began (carries the manifest + interval) |
| `ConfigDiscovered` | A client configuration file was found (path / client / scope / exists) |
| `FindingRaised` | One security finding (severity / type / server / OWASP category / redacted evidence) |
| `ScanCompleted` | The verdict for a pass (score / counts / fingerprint / `changed`) |
| `CollectorHeartbeat` | A cycle ran but the fingerprint was unchanged |

## Relationship to the rest of AIShield

- Reuses `scanner.client_discovery.discover_and_scan` / `scan_client_configs` — no second scanner.
- Complements `scanner/batch_scanner.py` (bulk ingestion into the local DB): the collector is the
  *continuous, event-emitting* front door; the batch scanner is the *bulk backfill*.
- Pairs with `eco/blackboard.py`'s append-only `security_events` stream: the collector writes
  canonical events to disk for any consumer (dashboard, SIEM, another agent).
