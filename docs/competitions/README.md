# AIShield Competitions & Grants Tracker

Master index of all competitions, grants, and awards AIShield is targeting. All entries are real opportunities with verified deadlines (2026-09-22 scan).

**Current strategic stance (2026-09-22):** Focus on **remote + monetised** opportunities. In-person-required events and visibility-only programmes are deprioritised. See §"Strategic filter" below.

> **执行手册 →** [`TOMORROW.md`](./TOMORROW.md) 是下一步动作的完整清单（AI 已经把所有能做的做完，剩下的都需要你亲自出手）。

---

## Active applications

| Priority | Competition | Type | Amount | Deadline | Win prob. | Status | Dir |
|---|---|---|---:|---|---|---|---|
| **P0** | [NetMind Agent Arena](netmind-arena/) | Agent arena | ~$200-300/yr USDC | Perpetual | 40-60% | Wrapper ready, awaiting registration | `netmind-arena/` |
| **P0** | [OWASP Red Teaming Solutions Landscape 2027](owasp-landscape-2027/) | Curated directory | — | 2027-03 (est) | 60-80% (inclusion) | Template + verification checklist ready | `owasp-landscape-2027/` |

**Combined expected value:** ~$200-300/yr direct cash + brand/procurement signal from OWASP inclusion.

## On hold (requires user decision)

| Priority | Competition | Type | Amount | Deadline | Win prob. | Status | Dir |
|---|---|---|---:|---|---|---|---|
| **P2** | [Foresight AI for Science & Safety Nodes](foresight-2026/) | Grant | $30K–$100K | 2026-10-31 | 15-25% (no SF/Berlin) | Drafted, awaiting user decision on travel | `foresight-2026/` |

Foresight remains drafted in case the user decides to attend SF or Berlin. Without in-person attendance, the win probability drops from 40-60% to 15-25%, which materially changes the expected value calculation.

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

**Without in-person travel:** ~$1.3-3.25K expected value over the next 12 months (mostly brand signal).
**With SF + Berlin travel for Foresight:** ~$15-80K expected value (mostly Foresight grant).

The delta (~$15-80K) is the "in-person premium." If the user wants that upside, Foresight should be re-promoted to P0.

---

## Monitoring automation

A recurring automation scans for competition window changes every 30 days (25th of each month at 10:00 UTC+8).

- **Name:** `aishield-competition-window-scan`
- **Schedule:** `FREQ=MONTHLY;BYMONTHDAY=25;BYHOUR=10;BYMINUTE=0`
- **Action:** Append findings to the "Monitoring log" section below
- **Escalation:** If any deadline is within 14 days, prepend a `⚠️ URGENT` marker

### Monitoring log

*Entries are appended here by the automated scan.*

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

- **2026-10-15:** Is Foresight worth re-promoting to P0? (Need user decision on travel)
- **2026-11-01:** Has OWASP 2027 CFS been published? Start final submission drafting
- **2027-01-31:** GitLab AI Hackathon 2027 opens — decide if P2 → P1
- **2027-02-28:** Final OWASP submission due

---

*This file is the single source of truth for AIShield's competition/grant activity. Any change to active applications must be reflected here first.*
