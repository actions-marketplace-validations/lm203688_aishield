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

*This document is a template. Update the exact field values when the OWASP 2027 call for submissions is published (expected 2026-11). The 2027 form may ask different questions; adapt as needed.*
