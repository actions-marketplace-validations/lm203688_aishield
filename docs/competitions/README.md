# AIShield Competitions & Grants Tracker

Master index of all competitions, grants, and awards AIShield is targeting. All entries are real opportunities with verified deadlines (2026-09-22 scan).

**Current strategic stance (2026-09-22):** Focus on **remote + monetised** opportunities. In-person-required events and visibility-only programmes are deprioritised. See §"Strategic filter" below.

> **执行手册 →** [`TOMORROW.md`](./TOMORROW.md) 是下一步动作的完整清单（AI 已经把所有能做的做完，剩下的都需要你亲自出手）。

---

## GO / NO-GO verdict — Foresight (2026-09-23)

**Trigger:** the user asked directly — *"获奖可能性大吗？不大就别浪费时间"*. Answered with first-party verification of the live RFP text, not estimates.

**Verdict: NO-GO as a main line. P ≈ 1-3% (centre ~2%).** The blockers are **structural** — set by the programme, not by the quality of our materials. Better writing does not move them.

| Factor | Evidence (verified 2026-09-23) | Sign |
|---|---|:--:|
| **In-person is the default; remote is the exception** | RFP: *"We prioritize projects that want to be active, **in-person** members of one of our hubs in San Francisco or Berlin."* FAQ: *"we **strongly prioritize** applicants who want to be active, in-person contributors… such as regularly working out of the Node or spending dedicated time at either Nodes for sprints."* Programme description: *"**funding-only applications are considered only in exceptional cases**."* | **−−** |
| **An almost identical project is already funded** | Yue Zhao, USC FORTIS Lab, **2026 cohort**: *"Audit-to-Patch Pipelines for Secure LLM Agent Systems"* — *"detects and audits security risks in **LLM agent code and configuration**"*. We would be read as a weaker version of a funded project with an institutional backer. | **−−** |
| **"Capability to execute"** | Criterion reads *"Strong teams with **proven expertise** in the field **will be prioritized**."* We are a solo applicant, no affiliation, no publications, GitHub **2 stars / 0 forks**. | **−−** |
| **"AI-first work" is a weighted criterion** | AIShield's scan engine is deterministic static analysis; AI only generates radar rules. This is the weaker end of the criterion. | **−** |
| **Our focus area is the explicitly under-funded one** | *"smaller amounts being awarded to the Human Empowerment and **AI Insurance & Open Governance** focus areas"* ⇒ price at **$30-50K**, not the $62K draft. | **−** |
| **No prior relationship with Foresight** | The review's short-call stage structurally favours applicants already inside the network. | **−** |
| Working, deployed, MIT-licensed artifact | 235 MCP + 262 Skill rules, live endpoint, 22 real harnesses scanned | **+** (table stakes, not differentiating) |

**The arithmetic.** Foresight awards ≈**$3M/year**; the 2026 cohort is **33 grantees** ⇒ ≈33 awards/year. Against a globally-publicised open call that is a low-single-digit base rate *before* applying the remote-only penalty. Take **P = 2%**, grant **$40K** ⇒ **EV ≈ $800**.

**The cost.** Cash $0; your time ≈1-2 h (the form is short). But it also costs **one named recommender** (a real social cost, and a required field) and your name on Foresight's **public grantee list**.

**Therefore:**
- **Do not invest engineering** — no narrative rewrite, no star-chasing, no distribution push. Those cannot fix the three big negatives.
- **If you still want the lottery ticket:** submit *only what already exists*, cap effort at `PERSONAL_FILL.md` + the Airtable form, expect nothing. EV $800 for ~2 h is not insane; it is just not a plan.

**Structural note, and the part that matters beyond Foresight.** For this applicant's exact position — **mainland-China individual, no legal entity, cannot attend in person** — the "global award with real cash" category is close to *systematically* closed, and not for lack of ability:

| Programme | Why closed |
|---|---|
| CrowdStrike × AWS *Agents of Chaos* ($100K, fully remote) | Official Rules exclude residents of **China** and **Macau** |
| AIxCC @ NeurIPS (~$1M pool) | In-person finals |
| HK AI × Cybersecurity Challenge (HK$180K) | In-person HK finals |
| 火山引擎 Skill 安全攻防 (¥200K) | In-person Beijing finals |
| Foresight ($30-100K) | Remote = *"exceptional cases"* only |
| OWASP Landscape 2027 | Pays nothing |

⇒ Continuing to hunt this specific category in the AIShield lane has a **low ceiling**. Redirect competitive effort to where the constraints actually fit (the SwarmLabs line — compute and prize programmes that do not require attendance), rather than to more searching here.

---

## Active applications

| Priority | Competition | Type | Amount | Deadline | Win prob. | Status | Dir |
|---|---|---|---:|---|---|---|---|
| **P0** | [OWASP Red Teaming Solutions Landscape 2027](owasp-landscape-2027/) | Curated directory | — | 2027-03 (est) | 60-80% (inclusion) | Template + verification checklist ready | `owasp-landscape-2027/` |
| **P2** | [Foresight AI for Science & Safety Nodes](foresight-2026/) | Grant | $30K–$100K (**focus area 4 → lower end**) | 2026-10-31 (decisions Jan 2027) | **≈2%** (NO-GO — see verdict above) | Materials complete; optional lottery-ticket submission only | `foresight-2026/` |
| **P1** | [NetMind Agent Arena](netmind-arena/) | Agent arena | **~$0 realistic cash** (measured — see note) | Perpetual | n/a | Registered; product listed (pending review) | `netmind-arena/` |

**Why Foresight was promoted to P0 (2026-09-23).** The standing filter is *"monetised **and** fully remote"*. Foresight satisfies both, and eligibility was re-verified on the live RFP page: *"We accept applications from individuals, teams, and organizations"* — **no country or nationality restriction** — and travel for field-building events is listed as **Foresight-paid**, not applicant-paid. Being remote-only lowers the odds (Foresight "strongly prioritises" in-person contributors) but does not disqualify anyone. One real caveat to price in: grants for the **AI Insurance & Open Governance** focus area are explicitly the *smaller* ones ("$30,000 to $100,000, with smaller amounts being awarded to the Human Empowerment and AI Insurance & Open Governance focus areas"). Submission is an Airtable form; review takes ~3 months; **open-sourcing the output is a hard requirement** (AIShield is MIT — satisfied).

**Why NetMind dropped to P1 (2026-09-23).** The earlier "~$200-300/yr USDC" figure did not survive contact with the API. Measured live: `/agents/me/rewards` returns `{rewards:[], total:0}`, every cash-out verb (`withdraw`/`payout`/`redeem`/`exchange`/`earnings`) returns 404, and the only USDC anywhere on the platform is ~10 parimutuel pools of exactly `1.00000000` each — which additionally require a **bound wallet** we do not have. Realistic cash: **$0**. What NetMind genuinely provides is distribution (a listed product page) and a public, third-party-verifiable track record. Full evidence: `netmind-arena/REGISTRATION.json` → `credit_economy.roi_probe_2026-09-23`.

## On hold (requires user decision)

*None.* Foresight was the only entry parked here; it was promoted to P0 on 2026-09-23 and **demoted to P2 the same day** after the GO/NO-GO verdict above. No entry now blocks on a user decision.

## Prep work (later deadlines)

| Priority | Competition | Type | Amount | Deadline | Win prob. | Status |
|---|---|---|---:|---|---|---|
| P2 | GitLab AI Hackathon 2027 | Hackathon | $65K pool | 2027-02-09 ~ 03-25 | 2-5% | Watching; requires Duo Agent Platform account |
| P2 | AIxCC @ NeurIPS 2026 | AI security CTF | ~$1M pool | ~2026-10 | Depends on attendance | Watching (in-person required) |

## Waiting for next cycle

| Competition | Type | Amount | Next cycle | In-person |
|---|---|---:|---|---|
| HK AI x Cybersecurity Challenge | CTF | HK$180K | 2027 spring | Yes (HK finals) |
| 火山引擎 Skill 安全攻防挑战赛 | Skill competition | ¥200K | 2027 spring | Yes (Beijing finals) |
| GitLab Transcend Hackathon | Hackathon | Variable | 2027 spring | Remote |

## Not pursuing (documented why)

**Direction mismatch:**
- Gray Swan Arena — direction is jailbreak (frontend models), not defense scanning
- Google OSS VRP — bug bounty on Google's code, not for scanners
- MLSys / NeurIPS papers — engineering product, not research paper

**Eligibility mismatch:**
- CrowdStrike × AWS "AI Unlocked: Agents of Chaos" — **$100,000 prize pool, fully remote** (`play virtually from anywhere in the world`), three acts ending 2026-09-29. Rejected on eligibility, not on fit: the Official Rules state a participant "must not be a resident of any of the following countries: Afghanistan, Belarus, Brazil, Burma, ... **China**, Cuba, ... **Macau**, ..." and "Contest is void in ... **China**, ... **Macau**, ...". Verified 2026-09-23 at `crowdstrike.com/en-us/legal/ai-unlocked-agents-of-chaos-contest/`. This is a *separate* programme from the AgentWorks entry below and was newly found during the 2026-09-23 sweep — recorded here so it is not re-investigated.
- CrowdStrike AgentWorks — requires CrowdStrike customer account
- Google.org AI for Science — non-profit only
- Humanity AI $10M — US-only non-profit
- CAAI-蚂蚁 AGI 专项 — only current university faculty
- CISPA Hackathon — only EU university students
- Prototype Fund Switzerland — requires Swiss work permit

**Deadline passed (as of 2026-09-22):**
- Schmidt Sciences Scaling AI Safety — deadline Aug 09, 2026
- AI Alignment Foundation Fellowship — deadline Aug 17, 2026
- OpenAI Safety Fellowship — deadline May 3, 2026
- The Hacker News Cybersecurity Stars Awards 2026 — deadline May 15, 2026
- GitLab Hackathon July 2026 — already closed (Oct 6 next)
- GitLab Transcend Hackathon 2026 — closed June 24, 2026

**Other:**
- Anthropic Claude Code Plugin Marketplace — see `../distribution/aishield-plugins/SUBMISSION.md`
- Thinking Machines Safety Research Grants — direction mismatch (requires fine-tuning research), deadline was 3 days away

---

## Strategic filter

Applied to all P0/P1 opportunities. An opportunity must satisfy **both** conditions to be active:

1. **Monetised** — has a monetary award (cash, credits, USDC)
2. **Fully remote** — no in-person attendance required at any stage

Rationale: the user's preference is to avoid in-person commitments and prefer direct monetisation over pure visibility plays.

**Consequences of the filter:**

| Filtered out | Would have been |
|---|---|
| Foresight AI for Science & Safety Nodes ($30-100K) | Highest single-prize value |
| AIxCC @ NeurIPS 2026 (~$1M pool) | Highest prize pool |
| HK AI x Cybersecurity Challenge (HK$180K) | Large regional prize |
| 火山引擎 Skill 安全攻防 (¥200K) | Directly AIShield-relevant |
| OWASP Landscape 2027 (visibility-only) | **Actually kept** — inclusion is worth the brand signal |

**Note:** OWASP Landscape was originally excluded by the "monetised" filter but re-included because:
- Inclusion in OWASP's curated directory drives procurement adoption
- Enterprise procurement teams use OWASP landscapes as a short-list
- The brand signal is worth more than the "no direct cash" penalty

If the user wants a stricter "cash-only" filter, OWASP Landscape can be moved to P2.

---

## Expected value analysis

Assumed win probabilities for active opportunities:

| Competition | Prize pool | Win prob. | Expected value |
|---|---:|---:|---:|
| NetMind Arena | $200-300/yr | 40-60% | $80-180/yr |
| OWASP Landscape 2027 | $0 direct | 60-80% | $0 direct + brand signal |
| Foresight (if attended) | $30-100K | 40-60% | $12-60K |
| Foresight (no attend) | $30-100K | 15-25% | $4.5-25K |
| GitLab AI Hackathon 2027 | $65K | 2-5% | $1.3-3.25K |
| AIxCC 2026 (if attended) | $1M | Depends on ranking | $20-100K |

**Without in-person travel — corrected 2026-09-23.** The previous one-line summary ("~$1.3-3.25K") implicitly dropped the Foresight row while the table directly above it listed "Foresight (no attend) … $4.5-25K". Both cannot be true. Recomputing, and netting NetMind's USDC to the measured $0:

| Competition | Prize pool | Win prob. | Expected value |
|---|---:|---:|---:|
| **Foresight (remote-only)** | $30-100K | **≈2%** (re-derived 2026-09-23 — see verdict) | **≈$800** |
| GitLab AI Hackathon 2027 | $65K | 2-5% | $1.3-3.25K |
| NetMind Arena | $0 cash (measured) | — | $0 |
| OWASP Landscape 2027 | $0 direct | 60-80% | $0 + brand/procurement signal |

⇒ **~$800 expected value while staying home**, not the ~$6-28K previously recorded. The earlier 15-25% figure was an un-derived estimate; it did not survive the in-person-is-the-default clause, the already-funded look-alike, or the 33-grant cohort arithmetic. **The remote path in this lane is not a plan — it is a lottery ticket.**

---

## Monitoring automation

A recurring automation scans for competition window changes every 30 days (25th of each month at 10:00 UTC+8).

- **Name:** `aishield-competition-window-scan`
- **Schedule:** `FREQ=MONTHLY;BYMONTHDAY=25;BYHOUR=10;BYMINUTE=0`
- **Action:** Append findings to the "Monitoring log" section below
- **Escalation:** If any deadline is within 14 days, prepend a `⚠️ URGENT` marker

### Monitoring log

### 2026-09-23 manual sweep (not the automated scan)

Full re-verification of this file against live sources, prompted by the user's question about which AI competitions award cash or compute without requiring attendance.

**Corrections made:**

0. **2026-09-23 — full RFP mechanics verified, plus a competitor finding.** Added
   [`foresight-2026/PLAYBOOK.md`](foresight-2026/PLAYBOOK.md): the submission is a **single short
   Airtable form** (350-character zero-jargon pitch), not a PDF; decisions land **January 2027**;
   correct home is **Call II → focus area 4**; and — the finding that matters — Foresight's **2026**
   cohort already includes a project (Yue Zhao, USC FORTIS Lab, *Audit-to-Patch Pipelines for Secure
   LLM Agent Systems*) that occupies almost exactly our current framing. Our application must lead with
   the **independent attestation layer**, not the scanner. Also corrected four false claims in our own
   materials (2 stars ≠ ~100; the 19 radar rules were double-counted; 1295 tests ≠ 1283; "Track 1"
   is not a real label). **The 15-25% remote estimate above now carries an overlap discount and has not
   been re-derived** — treat it as an upper bound until the pitch is reframed.
1. **Foresight promoted P2 → P0.** Eligibility verified on the live RFP page: individuals welcome, **no nationality restriction stated**, travel is Foresight-**paid**, and open-sourcing the output is required (AIShield is MIT — satisfied). The "only worth it with travel" premise that parked this entry did not hold up.
2. **Foresight's calls corrected.** The live RFP spans *I. Local compute / II. Coordination and accountability / III. AI-first science* — not the "Track 1/2/3" labels used previously. AIShield fits **Call II → AI insurance and open governance**. Caveat recorded: Foresight awards the **smaller** grants to that focus area.
3. **NetMind's USDC figure struck.** `~$200-300/yr USDC` was never measured. Live probe (2026-09-23): `/agents/me/rewards` = `{rewards:[], total:0}`; every cash-out verb 404s; the only USDC on the platform is ~10 parimutuel pools of exactly `1.00000000`, each additionally requiring a bound wallet we do not have. Realistic cash: $0. Demoted P0 → P1.
4. **Expected-value summary recomputed.** The old "~$1.3-3.25K without travel" contradicted the table directly above it (which listed Foresight no-attend at $4.5-25K). Correct remote figure: **~$6-28K**.
5. **New opportunity found, rejected on eligibility:** CrowdStrike × AWS "AI Unlocked: Agents of Chaos" ($100K, fully remote) — Official Rules exclude residents of **China and Macau**. Filed under "Not pursuing" so it is not re-investigated.
6. **Compute grants are not a fit for AIShield.** It is deliberately zero-dependency and CPU-only and needs no GPU; the major GPU-credit programmes (NVIDIA Inception, AWS Activate, Google for Startups) are also entity/VC-gated. Compute-hungry work belongs to the SwarmLabs line, not this one.

**Only remaining blocker:** filling `foresight-2026/PERSONAL_FILL.md` and submitting the Airtable form before 2026-10-31.

---

## Timeline summary

```
2026
  Q3 (now)
    ├── 2026-09-25  Thinking Machines Safety Grants (skipped — 3 days, direction mismatch)
    ├── 2026-10-06  GitLab Hackathon Oct (skipped — rewards are trees/swag, no cash)
    ├── 2026-10-31  Foresight AI for Science & Safety Nodes (on hold — travel decision needed)
    ├── ~2026-10    AIxCC @ NeurIPS 2026 (in-person required)
  Q4
    ├── 2026-11-01  OWASP 2027 CFS expected (start drafting submission)
  Q1 (2027)
    ├── 2027-02-09  GitLab AI Hackathon 2027 opens (P2 prep)
    ├── 2027-03-20  OWASP Red Teaming Landscape 2027 (P0 submit)
  Q2 (2027)
    ├── Spring 2027 HK AI x Cybersecurity Challenge 2nd cycle
    ├── Spring 2027 火山引擎 Skill 安全攻防 2nd cycle
    ├── Spring 2027 GitLab Transcend Hackathon (remote, watch)
```

---

## File structure

```
docs/competitions/
├── README.md                    # This file
├── foresight-2026/              # On hold (P2) — awaiting travel decision
│   ├── APPLICATION.md
│   ├── PROJECT_PLAN.md
│   ├── BUDGET_INDIVIDUAL.md     # $35K variant (no travel)
│   ├── BUDGET_CORPORATE.md      # $62K variant (with travel)
│   └── SUBMISSION_CHECKLIST.md
├── owasp-landscape-2027/        # P0 — active
│   └── SUBMISSION.md
└── netmind-arena/               # P0 — active
    └── INTEGRATION.md

scripts/arena/
└── arena_agent.py               # NetMind wrapper (deploy-ready)
```

---

## Next review

Revisit this README every 30 days (automated scan on the 25th). Key decision points:

- **~~2026-10-15: Foresight submission checkpoint~~** — **cancelled 2026-09-23.** Foresight is NO-GO as a main line (P2). Only revisit if the user explicitly asks for the lottery-ticket submission; deadline 2026-10-31 still stands if so.
- **2026-11-01:** Has OWASP 2027 CFS been published? Start final submission drafting
- **2027-01-31:** GitLab AI Hackathon 2027 opens — decide if P2 → P1
- **2027-02-28:** Final OWASP submission due

---

*This file is the single source of truth for AIShield's competition/grant activity. Any change to active applications must be reflected here first.*
