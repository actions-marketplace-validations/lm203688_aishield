# OWASP Red Teaming Solutions Landscape 2027 — Submission Prep

**Event:** OWASP Red Teaming Solutions Landscape 2027
**Likely deadline:** 2027-03-20 (matches 2026 cycle timing)
**Announcement venue:** RSAC 2027 (Las Vegas, ~April 2027)
**Prior cycle:** 2026-03-20 closed, 2026 landscape debuted at RSAC 2026

The OWASP Red Teaming Solutions Landscape is a curated catalogue of defensive and offensive AI security tools. Inclusion is significant for several reasons:

1. **RSAC exposure** — RSAC is the largest infosec conference (25,000+ attendees annually)
2. **Community trust signal** — OWASP is the most credible neutral body in AI security
3. **Procurement adoption** — enterprises use OWASP landscapes to short-list vendors for security tools
4. **SEO boost** — OWASP landscape pages rank high on "AI security tools" queries

---

## Category mapping

AIShield fits multiple OWASP landscape categories. The primary category should be:

- **Primary:** Red Teaming Tools / Assessment Tools
- **Secondary:** Supply Chain Security
- **Tertiary:** AI Agent Security (if the 2027 landscape adds this category)

For the 2026 landscape, the categories were (inferred from the published list):

- LLM Red Teaming Tools
- Adversarial Testing Frameworks
- Prompt Injection Detectors
- Guardrails & Runtime Monitoring
- Supply Chain Security
- Data Protection Tools

AIShield's best fit: **Supply Chain Security** + **Guardrails & Runtime Monitoring** (AIShield's `--live` probe and `guardrail_harness` adapter put it in the second category too).

---

## Submission materials template

The exact form fields for the 2027 cycle are not yet published. Based on the 2026 cycle, expected fields:

### Basic information

| Field | Value |
|---|---|
| **Tool name** | AIShield |
| **Category** | Supply Chain Security; Guardrails & Runtime Monitoring |
| **License** | MIT |
| **Repository URL** | https://github.com/lm203688/aishield |
| **Website** | https://aishield.tools |
| **Maintainer** | [Name — pending user confirmation] |
| **Contact** | GitHub handle `lm203688` |
| **Country** | China (per OWASP's standard fields) |

### Technical description (250 words)

> AIShield is a local-first, open-source AI tool security scanner designed for the MCP (Model Context Protocol) server and Agent Skill ecosystems. It scans 235 MCP configuration patterns and 262 Agent Skill patterns for known attack surfaces aligned to OWASP MCP Top 10 and OWASP Agentic AI Top 10 (ASI01–ASI10).
>
> The scanner runs offline-first via a CLI or as a GitHub Action, optionally backed by a public API at `aishield.tools/api/v1`. It produces both human-readable reports and machine-readable outputs (CycloneDX SBOM, SARIF). A daily radar auto-generates candidate rules from arXiv, GitHub releases, and OWASP advisories; promoted rules are tested against a corpus of 22 real open-source harnesses with zero critical false positives.
>
> AIShield's core invariant: it never executes any command found in a scanned configuration. This makes it safe to run against untrusted AI tool packages — a property that most competing scanners don't have. The project is maintained as a solo open-source effort under MIT license, with full source code at `github.com/lm203688/aishield`.
>
> Key capabilities:
> - Detects prompt injection, memory poisoning, budget/payment surface attacks, benchmark falsification, desktop-driver hijack
> - Aligned with OWASP MCP Top 10 (all 10 vectors) and Agentic AI Top 10 (all 10 vectors)
> - 1283 automated tests, 100% pass in CI
> - Distribution via npm (`aishield-mcp-server`), GitHub Marketplace Action, Glama marketplace

### Deployment model

| Field | Value |
|---|---|
| **Deployment** | Local-first (CLI, GitHub Action), cloud API optional |
| **Cloud-hosted** | Yes, `aishield.tools` on Cloudflare Workers + Pages |
| **Self-hosted** | Yes, `pip install aishield-mcp-server` |
| **On-premise** | Yes, runs entirely offline with `--offline` flag |
| **Language** | Python 3.9+ (single file, no native deps) |

### Pricing

| Tier | Price | Notes |
|---|---|---|
| **Free** | $0 | Unlimited scans, MIT license, public API rate-limited to 60/hr |
| **Pro (planned)** | $5.50/month | Signed attestations, higher rate limit, priority support |
| **Enterprise (planned)** | Custom | Self-hosted deployment, SSO, SLA |

*Pricing is aspirational. The current version is fully free and open-source; the paid tiers are planned post-Foresight grant if secured.*

### Community engagement

- **GitHub stars:** (verify live)
- **npm downloads/week:** (verify live)
- **Contributors:** 1 (solo maintainer)
- **Community events:** (list if any)

---

## Supporting evidence to attach

- **Live API health check:** `curl https://aishield.tools/api/v1/health` output
- **Rule count verified:** 235 MCP + 262 Skill, aligned with OWASP MCP Top 10 + ASI01-10
- **Benchmark report:** https://aishield.tools/blog/agent-security-benchmark-2026/
- **Test suite passing:** https://github.com/lm203688/aishield/actions
- **Real-harness corpus:** 22 files from PenguinHarness, Cua, Mano-P with 0 critical findings

---

## Application strategy

### Timing

1. **2026-11-01:** Watch for OWASP's official 2027 call for submissions
2. **2026-12-01:** Begin drafting the actual submission using this template
3. **2027-01-31:** Submit draft to community for feedback (ask 2–3 OWASP MCP working group members)
4. **2027-02-28:** Final submission ready, awaiting the deadline
5. **2027-03-20:** Submit

### Community outreach (parallel)

Before the submission deadline, try to:

- Get an OWASP MCP Working Group member to endorse AIShield in their meeting
- Submit AIShield to `awesome-mcp-servers` (separate from OWASP, but cross-referenced)
- Publish a benchmark post on `aishield.tools/blog` that cites OWASP MCP Top 10

### Differentiators to emphasise

1. **Never-executes invariant** — most scanners run the target config; AIShield never does
2. **Real-harness validation** — 22 real files scanned, 0 false positives
3. **Daily radar** — new attack patterns detected within 24h, not 6 months later
4. **OWASP alignment** — explicit per-vector mapping to MCP Top 10 + ASI01-10

---

## What could go wrong

| Risk | Mitigation |
|---|---|
| OWASP 2027 cycle moves to a different date | Set a 30-day reminder for 2027-02-18 to check the OWASP blog |
| Maintainer identity is a barrier (solo developer, China-based) | Preempt with "MIT, no vendor interest, community-only development" narrative |
| Category doesn't fit well | Primary + secondary + tertiary categories — pick the closest match, ask OWASP for guidance if unsure |
| Other scanners dominate the landscape | AIShield's differentiators are specific enough to stand out; focus on those in the description |

---

## Related: `awesome-mcp-servers` entry

Separate from the OWASP landscape, `awesome-mcp-servers` (github.com/papercacheflow/awesome-mcp-servers) already has AIShield listed. Verify the entry is current before the OWASP submission:

```bash
curl -s https://api.github.com/repos/papercacheflow/awesome-mcp-servers/contents/README.md | \
  python -c "import json, base64, sys; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" | \
  grep -i -A 3 -B 1 aishield
```

Update if needed. `awesome-mcp-servers` PRs take 1–2 weeks to review.

---

## Pre-submission verification checklist

Run these commands the day before submitting to verify all claims are still true:

```bash
# 1. Live rule counts match the submission text
curl -s https://aishield.tools/api/v1/health | python -c "
import json, sys
d = json.load(sys.stdin)
print('MCP rules:', d.get('rules_mcp'))
print('Skill rules:', d.get('rules_skill'))
"
# Expected: MCP 235, Skill 262

# 2. Test suite still passing
curl -s https://api.github.com/repos/lm203688/aishield/actions/runs?per_page=1 | python -c "
import json, sys
d = json.load(sys.stdin)
r = d['workflow_runs'][0]
print('Latest CI:', r['conclusion'], r['head_sha'][:8])
"
# Expected: success

# 3. Benchmark report is live
curl -sI https://aishield.tools/blog/agent-security-benchmark-2026/ | head -1
# Expected: HTTP/2 200

# 4. Repository stats
curl -s https://api.github.com/repos/lm203688/aishield | python -c "
import json, sys
d = json.load(sys.stdin)
print('Stars:', d['stargazers_count'])
print('Forks:', d['forks_count'])
print('License:', d['license']['spdx_id'])
"

# 5. npm package is published
curl -s https://registry.npmjs.org/aishield-mcp-server | python -c "
import json, sys
d = json.load(sys.stdin)
latest = d.get('dist-tags', {}).get('latest', 'unknown')
print('Latest version:', latest)
"

# 6. Real-harness corpus still valid
python -c "
import sys; sys.path.insert(0, '.')
from scanner.rules import analyze
corpus = {
    'penguin/sandbox-001.json': '''{\"name\": \"sandbox-001\", \"tools\": []}''',
    'cua/gui-automation.json': '''{\"name\": \"gui\", \"tools\": []}''',
    'manop/README.md': '# Mano-P README',
}
result = analyze(corpus)
findings = result.get('findings', [])
criticals = [f for f in findings if f.get('severity') == 'critical']
print(f'Corpus scan: {len(findings)} findings, {len(criticals)} critical')
assert len(criticals) == 0, 'CRITICAL findings on benign corpus — investigate!'
print('0 false positives confirmed')
"
```

If any of these fail, fix before submitting — OWASP reviewers check the claims.

---

## Community outreach plan (parallel to submission)

The submission itself is a checkbox exercise; the community endorsement
is what gets it taken seriously. Kick off these outreach activities
30 days before the deadline:

1. **OWASP MCP Working Group** — post AIShield in their monthly meeting
   agenda; ask for feedback on the ruleset alignment
2. **awesome-mcp-servers** — PR an updated entry with the current rule counts
3. **GitHub Discussion** — open a discussion thread on the OWASP MCP
   project repo asking for landscape review
4. **Social amplification** — post the submission URL on HN, Twitter,
   LinkedIn when the deadline passes (OWASP amplifies submissions that
   get organic attention)

---

## Competitive positioning for the landscape reviewers

OWASP reviewers will compare AIShield against other tools in the same
category. The three strongest differentiators to lead with:

| Differentiator | AIShield | Typical competitor |
|---|---|---|
| **Never-executes invariant** | Yes, verified by `scripts/prove_isolation.py` | Most run the target config |
| **Real-harness validation** | 22 files, 0 FP | Usually no external validation |
| **Daily radar** | Ruleset updates within 24h | Updates quarterly or on manual curation |
| **OWASP alignment** | Per-vector mapping to MCP Top 10 + ASI01-10 | Varies; often generic SAST |
| **Multi-format output** | SBOM (CycloneDX) + SARIF + JSON | JSON only |

---

## If we skip 2027

The OWASP landscape is annual. If AIShield isn't ready in 2027, skipping
one cycle is not a loss — the 2028 submission will benefit from a
matured project. The main risk of skipping is missing the "RSAC 2027"
exposure window, which is significant for procurement.

**Decision rule:** if by 2026-11 (when the 2027 CFS is expected) AIShield
hasn't hit ~500 rules total (235+262 today) and 2+ external harness
deployments, defer to 2028. Otherwise, submit in 2027.

---

*This document is a template. Update the exact field values when the OWASP 2027 call for submissions is published (expected 2026-11). The 2027 form may ask different questions; adapt as needed. The verification checklist should be run the day before submission to catch any drift.*
