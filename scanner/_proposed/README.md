# scanner/_proposed/ -- auto-drafted rule candidates

This directory holds **rule stubs auto-generated** by `scripts/tech_radar.py`
when it detects a high-severity signal matching a known attack pattern.

## Lifecycle

1. **Generated** by tech_radar.py (daily 02:00 cron).
   Each file contains:
   - Original signal metadata (source, URL, attack category, severity)
   - A `TODO(operator)` block in `check()` for you to implement detection
   - A "draft" id that won't conflict with active rule ids

2. **Reviewed by you** (the operator):
   - Open the source signal URL (in the file header)
   - Read the relevant attack class in OWASP MCP/Agentic Top 10
   - Implement the `check()` method using available manifest fields
   - Test against at least 1 known positive + 1 known negative sample

3. **Promoted or discarded**:
   - **Promote**: run the candidate through `scripts/adversarial_review.py`
     first (evasion-variant families + benign negative controls + hit-set
     redundancy against the static baseline). Only promote when the gate
     reports `pass`; on `fail` record the reasons and move the file to
     `rejected/` instead of editing it into compliance silently.
     Then copy the implementation into `scanner/rules.py` under a permanent
     id (e.g. `MCPxx-yy`), assign to ASI/MCP category, register in
     `RULE_REGISTRY`, then DELETE this stub.
   - **Discard**: set `"status": "rejected"`, add a `reject_reason` short code
     plus `reject_detail` evidence, and move the file into `rejected/`. Do not
     delete outright — the rejection record is the negative control that proves
     the gate can actually say no.

## Why a separate directory?

- Active rules in `scanner/rules.py` are loaded by every scan; we must not
  load stubs that return `fired=False` (they would silently degrade trust).
- Keeping them in `_proposed/` lets `git status` clearly show what's pending
  review (vs noise from routine updates).
- Each stub carries provenance: the signal that triggered its creation.
  This makes audit/trust decisions explicit.

## File naming

`PROPOSED_YYYYMMDD_<slug>_<id6>.py` -- date ensures chronological ordering,
slug is derived from the signal title.