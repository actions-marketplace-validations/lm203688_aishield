# AIShield Project Plan — 6-Month Milestones

**Funding request:** $30K–100K (Foresight Track 1)
**Period:** 6 months from notification
**Assumed start:** 2027-02-01 (based on Foresight's 3-month review cycle)

---

## Milestone M1 — Verifier pipeline v1.0 (2027-02)

**Goal:** independent verifier replaces static ruleset as the promotion gate for new rules.

### Deliverables
1. `engine/promote_verifier.py` productionised (currently 350 LOC prototype in sibling project, porting)
2. Five rules promoted through the verifier: 3 attack patterns from recent arXiv, 2 defensive samples from existing corpus
3. `scripts/promote_rule.py --shadow` reports both candidate and verifier results side-by-side
4. CI gate: `run_all.py` refuses to merge rules that fail verifier

### Test coverage
- New: `tests/test_promote_verifier.py` (12 tests, ported)
- Modified: `tests/test_rules.py` to require `verifier_passed=True` on new rules
- Existing 1283 tests must remain green

### Acceptance criteria
- Verifier catches ≥80% of attacks that any single curated rule catches (from the 22-file harness corpus)
- Verifier rejects ≥95% of defensive samples that static rules reject
- Verifier adds <5s latency to a normal scan

---

## Milestone M2 — Radar ↔ Verifier integration (2027-03)

**Goal:** the existing 02:00 UTC daily radar that already generates candidate rules now flows through the verifier automatically.

### Deliverables
1. `scripts/radar.py` emits candidate rules into `_proposed/` directory
2. `scripts/verifier_worker.py` (new) runs each proposed rule against the harness corpus
3. Human approval: only rules passing verifier get moved from `_proposed/` → `scanner/rules.py`
4. Weekly digest of candidate rules + verifier outcomes sent to maintainer email

### Test coverage
- `tests/test_radar.py` + new `tests/test_verifier_worker.py` (8 tests)
- End-to-end test: mock a new malicious skill → radar discovers → verifier tests → promote (or reject)

### Acceptance criteria
- A manually-crafted malicious MCP config is discovered by the radar within 24h and rejected (or promoted) by the verifier within 48h without human intervention on the detection side
- Human approval remains a required gate — no autonomous promotion to production ruleset

---

## Milestone M3 — JWKS endpoint + signed attestation (2027-04)

**Goal:** anyone calling the API gets a signature they can verify independently.

### Deliverables
1. `.well-known/jwks.json` endpoint live at `aishield.tools/.well-known/jwks.json`
2. Ed25519 keypair: private key in CF Workers secret, public key in JWKS
3. `POST /api/v1/scan` returns `{ findings, signature, kid, timestamp }`
4. Public verification tool: `scripts/verify_report.py <report.json>` — one command, zero dependencies
5. Key rotation workflow: 90-day cycle, revocation list at `.well-known/jwks/revoked.json`

### Test coverage
- `tests/test_jwks.py` (10 tests, ported from SwarmLabs sibling project)
- Round-trip test: sign → verify → tamper → verify-fails

### Acceptance criteria
- Independent third party can call the API, download JWKS, verify signature, all within a single script without contacting aishield.tools again
- Signature covers canonical form (sorted keys, no whitespace, JSON-1 with UTF-8 byte preservation)
- Key rotation tested: old key still verifiable via `kid` for 30 days, revoked key fails verification

---

## Milestone M4 — SDKs + OpenAPI + rate limiting (2027-05)

**Goal:** the API becomes usable from any language, with documented behavior and governance-friendly rate limits.

### Deliverables
1. OpenAPI 3.1 schema published at `aishield.tools/openapi.json`
2. Python SDK (`pip install aishield-client`) — 400 LOC, mirrors core API
3. Node.js SDK (`npm install @aishield/client`) — 400 LOC, mirrors core API
4. Rate limits: 60 scans/hour unauthenticated, 500/hour with signed JWT
5. Documentation: `docs/api.md` with request/response examples

### Test coverage
- `tests/test_sdk_python.py` (10 tests)
- `tests/test_sdk_node.py` (10 tests, run via CI)
- OpenAPI schema validated by `spectral` in CI

### Acceptance criteria
- A governance body can write a 10-line script that scans a URL, gets a signed result, and stores it with a stable identifier
- Public endpoint handles 100 concurrent users without throttling on legitimate traffic

---

## Milestone M5 — Public incident feed (2027-06)

**Goal:** a machine-readable, append-only feed of AI tool supply-chain incidents discovered by the radar + verifier pipeline.

### Deliverables
1. `GET /api/v1/incidents` — returns JSON feed of incidents, paginated, filterable by date + category
2. `GET /api/v1/incidents/{id}` — single incident with rule reference, sample payload (redacted), timestamp
3. RSS/Atom mirror for human readers at `aishield.tools/feed.xml`
4. Historical backfill: seed the feed with the last 90 days of radar discoveries (projected ~40-80 entries)
5. `docs/incident-feed.md` — methodology for what counts as an "incident"

### Test coverage
- `tests/test_incident_feed.py` (15 tests)
- Backfill script tested against real historical radar output

### Acceptance criteria
- Feed is append-only: no edit/delete endpoints
- Every entry has a stable ID that survives radar rule updates
- Backfill covers at least 60% of the last 90 days

---

## Milestone M6 — Methodology paper + public beta (2027-07)

**Goal:** publish the methodology as a critiquable preprint + open the entire stack to external review.

### Deliverables
1. 8–12 page preprint: `docs/methodology-v1.pdf`
2. All four deliverables (A, B, C) marked public-beta in the changelog
3. Public issue template for methodology critiques: `docs/methodology-feedback.md`
4. Public Slack/Discord channel for adopters (optional; maintainer judgment)
5. Community report: list of all organizations/persons who called the API during the 6-month period

### Test coverage
- No new tests — this milestone is about the paper and outreach
- Existing test suite must remain green

### Acceptance criteria
- Paper is posted on arXiv or equivalent open preprint server
- At least 3 external parties (companies, researchers, or community members) confirm they have consumed the API
- Methodology is critiqued by at least one external reviewer before final publication

---

## Dependency graph

```
M1 (Verifier core)
    │
    ▼
M2 (Radar ↔ Verifier integration)
    │
    ├──▶ M3 (JWKS + attestation) ──▶ M4 (SDKs) ──▶ M6 (Paper + beta)
    │
    └──▶ M5 (Incident feed) ────────▶ M6 (Paper + beta)
```

M3 and M5 are independent of each other and can run in parallel. If M1 slips, the whole schedule shifts. If M3 slips, M4 still runs on the same API spec.

---

## Definition of done for the project

Six months after funding notification:

1. All 6 milestones merged to `main` on GitHub
2. All 1283+ existing tests still pass (regression gate)
3. New test count ≥ 65 additional tests (12 promote_verifier + 8 verifier_worker + 10 jwks + 10 sdk_python + 10 sdk_node + 15 incident_feed)
4. Public API has at least 3 external callers verified via `kid` audit log
5. Methodology paper is posted and has received at least 1 external critique
6. Full changelog updated at https://github.com/lm203688/aishield/releases

---

*Project plan is versioned alongside the code. Any scope change requires a Foresight notification email + a public commit to the changelog.*
