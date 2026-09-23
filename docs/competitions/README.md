# AIShield Competitions & Grants Tracker

Master index of all competitions, grants, and awards AIShield is targeting. All entries are real opportunities with verified deadlines (2026-09-22 scan).

**Current strategic stance (2026-09-22):** Focus on **remote + monetised** opportunities. In-person-required events and visibility-only programmes are deprioritised. See §"Strategic filter" below.

> **执行手册 →** [`TOMORROW.md`](./TOMORROW.md) 是下一步动作的完整清单（AI 已经把所有能做的做完，剩下的都需要你亲自出手）。

---

## Active applications

| Priority | Competition | Type | Amount | Deadline | Win prob. | Status | Dir |
|---|---|---|---:|---|---|---|---|
| **P0** | [Foresight AI for Science & Safety Nodes](foresight-2026/) | Grant | $30K–$100K (**lower end for RFP II**) | 2026-10-31 | 15-25% (remote-only) | Fully drafted — only the personal-info blanks + the Airtable form remain | `foresight-2026/` |
| **P0** | [OWASP Red Teaming Solutions Landscape 2027](owasp-landscape-2027/) | Curated directory | — | 2027-03 (est) | 60-80% (inclusion) | Template + verification checklist ready | `owasp-landscape-2027/` |
| **P1** | [NetMind Agent Arena](netmind-arena/) | Agent arena | **~$0 realistic cash** (measured — see note) | Perpetual | n/a | Registered; product listed (pending review) | `netmind-arena/` |

**Why Foresight was promoted to P0 (2026-09-23).** The standing filter is *"monetised **and** fully remote"*. Foresight satisfies both, and eligibility was re-verified on the live RFP page: *"We accept applications from individuals, teams, and organizations"* — **no country or nationality restriction** — and travel for field-building events is listed as **Foresight-paid**, not applicant-paid. Being remote-only lowers the odds (Foresight "strongly prioritises" in-person contributors) but does not disqualify anyone. One real caveat to price in: grants for the **AI Insurance & Open Governance** focus area are explicitly the *smaller* ones ("$30,000 to $100,000, with smaller amounts being awarded to the Human Empowerment and AI Insurance & Open Governance focus areas"). Submission is an Airtable form; review takes ~3 months; **open-sourcing the output is a hard requirement** (AIShield is MIT — satisfied).

**Why NetMind dropped to P1 (2026-09-23).** The earlier "~$200-300/yr USDC" figure did not survive contact with the API. Measured live: `/agents/me/rewards` returns `{rewards:[], total:0}`, every cash-out verb (`withdraw`/`payout`/`redeem`/`exchange`/`earnings`) returns 404, and the only USDC anywhere on the platform is ~10 parimutuel pools of exactly `1.00000000` each — which additionally require a **bound wallet** we do not have. Realistic cash: **$0**. What NetMind genuinely provides is distribution (a listed product page) and a public, third-party-verifiable track record. Full evidence: `netmind-arena/REGISTRATION.json` → `credit_economy.roi_probe_2026-09-23`.

## On hold (requires user decision)

*None.* Foresight was the only entry parked here; it is now P0. The remaining decision is a set of choices **inside** `foresight-2026/PERSONAL_FILL.md` (identity path, travel option, focus area, milestone scope, budget variant) — not whether to apply at all.

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
| **Foresight (remote-only)** | $30-100K | 15-25% | **$4.5-25K** |
| GitLab AI Hackathon 2027 | $65K | 2-5% | $1.3-3.25K |
| NetMind Arena | $0 cash (measured) | — | $0 |
| OWASP Landscape 2027 | $0 direct | 60-80% | $0 + brand/procurement signal |

⇒ **~$6-28K expected value while staying home**, driven almost entirely by Foresight. So the real comparison is not "$1.3-3.25K vs $15-80K" — it is **"$6-28K remote" vs "~$15-80K with travel"**, i.e. the in-person premium is much smaller than the old summary implied. Since travel for field-building events is Foresight-paid, the true incremental cost of the travel option is mainly *time and visa logistics*, not cash.

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

- **2026-10-15:** Foresight submission checkpoint — is `PERSONAL_FILL.md` complete, and has the Airtable form been sent? (Hard deadline 2026-10-31, no extensions, ~3-month review)
- **2026-11-01:** Has OWASP 2027 CFS been published? Start final submission drafting
- **2027-01-31:** GitLab AI Hackathon 2027 opens — decide if P2 → P1
- **2027-02-28:** Final OWASP submission due

---

*This file is the single source of truth for AIShield's competition/grant activity. Any change to active applications must be reflected here first.*
