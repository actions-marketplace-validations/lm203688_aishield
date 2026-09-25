# Foresight AI for Science & Safety Nodes — Personal Info Fill

> 📘 **Read [`PLAYBOOK.md`](PLAYBOOK.md) first.** It holds the verified mechanics: the exact Airtable
> form fields, the **350-character "zero jargon"** pitch limit, the **January 2027** decision date, and
> the grantee comparison (including the 2026 project that already occupies our current framing).

**Purpose**: Every placeholder in the main `APPLICATION.md` is captured here. Fill this out first, then copy-paste into `APPLICATION.md`.

**Deadline**: 2026-10-31 23:59 PDT — **38 days from 2026-09-23**
**Apply at (Airtable form, no login)**: https://airtable.com/appyVXc5SMPAvIKpP/pagp7takV26cG6JY1/form
**RFP page**: https://foresight.org/grants/ai-science-safety-nodes-rfp/
**Grant size**: $30K–$100K (our focus area gets the **smaller** end)
**Decisions**: **January 2027**

> ⚠️ **Price this in before committing effort:** Foresight states it awards *"smaller amounts to the Human Empowerment and AI Insurance & Open Governance focus areas, and higher amounts to the rest."* AIShield's natural home is **AI Insurance & Open Governance** — i.e. the **lower end** of the range.
>
> ⚠️ **Second thing to price in:** Foresight already funded a 2026 project — Yue Zhao (USC FORTIS Lab),
> *Audit-to-Patch Pipelines for Secure LLM Agent Systems* — that *"detects and audits security risks in
> LLM agent code and configuration"*. Our current pitch is nearly the same sentence. The application has
> to lead with the **attestation / independent-assessment layer**, not the scanner. Details in
> `PLAYBOOK.md §3` and `§5.2`.

---

## 0. Eligibility — verified on the live RFP page, 2026-09-23

This section exists because "must attend in person" was previously assumed to be a deal-breaker. It is not.

- ✅ *"We accept applications from **individuals, teams, and organizations**. Both non-profit and for-profit organizations are welcome to apply."*
- ✅ **No country or nationality restriction is stated anywhere on the RFP.** Tax handling is pushed to the applicant: *"Tax obligations vary by country and organization type. Applicants are responsible for understanding and complying with any applicable tax requirements."*
- ✅ Travel is **Foresight-paid**, not applicant-paid: selected projects receive *"workspace in our San Francisco or Berlin AI Nodes, along with **travel-paid** field-building events"*. So the travel option is not a $5-10K outlay.
- ⚠️ *"We **strongly prioritize** applicants who want to be active, in-person contributors to the research ecosystem at the Nodes."* Remote-only is **allowed but is the weaker position** — this is the entire basis for the 15-25% (remote) vs 40-60% (travel) estimate.
- 📌 **Hard requirement: the work product must be open-sourced** (*"We require the work product (code, data, and outputs) of the funding to be open-sourced"*). AIShield is MIT — **satisfied**.
- 📌 Review takes **~3 months** after the deadline. One-shot form; no individual feedback for rejections.

### The three calls (corrected 2026-09-23)

Earlier versions of this file used "Track 1/2/3" labels that do not match the current RFP. The live RFP spans:

| Call | Scope | Fit for AIShield |
|---|---|---|
| **I. Local compute** | Compute that individuals/communities physically own and control | ✗ (AIShield is CPU-only, zero-dependency, needs no GPU) |
| **II. Coordination and accountability** | Supercollaboration, decentralized alignment, human empowerment, **AI insurance and open governance** | ✅ **This is us** — *"Build ways for people outside a lab to assess risks"* / *"Independent technical assessment"* |
| **III. AI-first science: Bio, Neuro, Nano** | Automated nanotech, whole-brain emulation, frontier bio | ✗ |

**Recommended: Call II**, focus area *AI insurance and open governance*. Track III would only fit by stretching `scripts/benchmark.py` as an evaluation standard — a weaker case.

---

## 1. Applicant identity — ⚠️ needs your decision

### Path A — Individual (simpler, no legal entity)

| Field | Value | Status |
|---|---|---|
| Full name | `_______________` | **your call** — placing your legal name in a foreign grant application is a disclosure decision |
| Affiliation | `Independent researcher / open-source maintainer` | suggested |
| Location | `Hangzhou, China` | **confirm you want this stated** |
| Prior work | see bio draft below | draft ready, edit freely |
| GitHub handle | `lm203688` | ✅ filled |
| Contact email | `_______________` | your call — any address you actively monitor |
| Time zone | `Asia/Shanghai (UTC+8)` | ✅ filled |
| Travel budget | `$0 — remote-only applicant` | ✅ filled, consistent with Travel Option A |

**Suggested bio (edit freely):**
> Independent open-source maintainer. Author of AIShield, a local-first security scanner for AI agent tooling: 235 MCP rules and 262 Skill rules, aligned to the OWASP MCP Top 10 and the OWASP Agentic AI Top 10, with a hard invariant that it never executes anything found in a scanned configuration. Distributed as an MIT-licensed Python package and an MCP server, and deployed as a public API.

### Path B — For-profit LLC / Ltd (only if asking >$50K or hiring)

- **Company name**: `_______________`
- **Country of incorporation**: `_______________` (US LLC / DE GmbH / CN WFOE / other)
- **Federal tax ID / EIN / VAT**: `_______________` (only needed if requesting >$50K)
- **Legal representative**: `_______________` (name + role)
- **Company website**: `_______________`
- **Contact email**: `_______________`
- **Bank account for grant receipt**: `_______________`
- **Prior funding history**: `_______________` (any other grants, investors, revenue)

---

## 2. In-person participation decision

Foresight strongly prioritises applicants who commit to attending in person at the SF or Berlin Node. This is the single biggest score lever.

- **Which option?**
  - **[ ] A — No travel** (fastest, ~15-25% success rate) ← matches the "fully remote" filter
  - **[ ] B — Travel once during the project** (SF or Berlin, ~40-60%)
  - **[ ] C — Travel twice** (higher credibility, ~60-80%)

- **If B or C, which Node(s)?** `_______________` (SF / Berlin)
  - **Months available**: `_______________` (Nodes run on specific schedules — see https://foresight.org/nodes/)
  - **Travel budget**: `$0 out of pocket — Foresight covers field-building event travel`. Confirm with the RFP contact before relying on this for *all* trips.

- **Rationale** (1-2 sentences, useful in the cover letter):
  `_______________`

---

## 3. Focus area selection

- **[ ] Call I — Local compute** — not a fit
- **[x] Call II — Coordination and accountability → AI insurance and open governance** — **recommended**
- **[ ] Call III — AI-first science** — not a fit

---

## 4. Milestone commitments (6-month scope, appears in `PROJECT_PLAN.md`)

- **[ ] 235 → 500+ MCP rules** (aggressive, ~2 hrs/day)
- **[x] 235 → 350+ MCP rules** (moderate, ~1 hr/day) — **recommended**
- **[ ] 235 → 280+ MCP rules** (steady, ~30 min/day)

The middle option is ambitious enough to show momentum and realistic for a solo developer.

---

## 5. Budget scope

- **[x] $35K Individual (`BUDGET_INDIVIDUAL.md`)** — recommended if solo
  - PI $24K + Infrastructure $2.1K + Travel $5K + Compliance $2K + Misc $1.9K
  - ⚠️ If you pick Travel Option A, move the $5K travel line out — a remote-only applicant asking for travel budget invites questions.
- **[ ] $62K Corporate (`BUDGET_CORPORATE.md`)** — only if you will hire a second engineer within 6 months

Reduction rungs if Foresight counters:
- $25K: travel → $0, drop second engineer, PI → $18K
- $20K: 3-month milestones instead of 6-month

---

## 6. Contact references (optional but recommended)

- **Reference 1**: `_______________`
- **Reference 2**: `_______________`

Ask OWASP WG members or GitHub collaborators — **and tell them first**; never list someone who has not agreed.

---

## 7. Pre-submission checklist

- [ ] Fill every remaining `_______________` above
- [ ] Choose Path A or B
- [ ] Choose Travel Option A / B / C
- [ ] Confirm Call II + "AI insurance and open governance"
- [ ] Confirm milestone scope (350+ recommended)
- [ ] Choose budget variant, and drop the travel line if Travel Option A
- [ ] Fill reference list (if used)
- [ ] Sync `PROJECT_PLAN.md` timeline to the chosen milestone scope
- [ ] Sync the chosen budget file
- [ ] Copy the filled values into `APPLICATION.md`
- [ ] Peer-review `APPLICATION.md` (~15 min with any security engineer)
- [ ] Final typo + consistency pass on 2026-10-29
- [ ] **Submit via the Airtable form** by 2026-10-31 23:59 PDT

---

## 8. Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-23 | Promoted Foresight from "on hold" to **P0** | Eligibility verified: individuals welcome, no nationality restriction, travel is Foresight-paid. The "needs in-person to be worth it" premise that parked this entry did not hold up. |
| | Path A / B | |
| | Travel A / B / C | |
| | Call I / II / III | |
| | Milestone scope | |
| | Budget variant | |
| | References | |

---

*Working file — do not submit this file itself. Copy the filled values into `APPLICATION.md`, then submit the Airtable form.*
