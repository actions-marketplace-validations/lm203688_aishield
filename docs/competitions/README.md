# AIShield Competitions & Grants Tracker

Master index of all competitions, grants, and awards AIShield is targeting. All entries are real opportunities with verified deadlines (2026-09-22 scan).

---

## Active applications

| Priority | Competition | Type | Amount | Deadline | Status | Dir |
|---|---|---|---:|---|---|---|
| **P0** | [Foresight AI for Science & Safety Nodes](foresight-2026/) | Grant | $30K–$100K | 2026-10-31 | Drafting | `foresight-2026/` |
| **P0** | [NetMind Agent Arena](netmind-arena/) | Agent arena | USDC | Perpetual | Ready to register | `netmind-arena/` |

## Prep work (later deadlines)

| Priority | Competition | Type | Amount | Deadline | Status | Dir |
|---|---|---|---:|---|---|---|
| **P1** | [OWASP Red Teaming Solutions Landscape 2027](owasp-landscape-2027/) | Curated directory | — | 2027-03 (est) | Template ready | `owasp-landscape-2027/` |
| **P1** | AIxCC @ NeurIPS 2026 | AI security CTF | ~$1M pool | ~2026-10 (est) | Watching | *(not yet drafted)* |

## Waiting for next cycle

| Competition | Type | Amount | Next cycle | Status |
|---|---|---:|---|---|
| HK AI x Cybersecurity Challenge | CTF | HK$180K | 2027 spring | 1st cycle closed 2026-08-23 |
| 火山引擎 Skill 安全攻防挑战赛 | Skill competition | ¥200K | 2027 spring | 1st cycle closed 2026-06-15 |
| GitLab AI Hackathon 2027 | Hackathon | $65K | 2027-02-09 ~ 03-25 | 2026 cycle closed |

## Not pursuing (documented why)

- CrowdStrike AgentWorks — requires CrowdStrike customer account
- Google.org AI for Science — non-profit only
- Humanity AI $10M — US-only non-profit
- CAAI-蚂蚁 AGI 专项 — only current university faculty
- CISPA Hackathon — only EU university students
- Gray Swan Arena — direction is jailbreak (frontend models), not defense scanning
- Prototype Fund Switzerland — requires Swiss work permit
- MLSys / NeurIPS papers — engineering product, not research paper
- Anthropic Claude Code Plugin Marketplace — see `../distribution/aishield-plugins/SUBMISSION.md`

---

## Monitoring automation

A recurring automation scans for competition window changes every 30 days. See `scripts/competition_watch.py` (planned; currently tracked manually in this README).

## Timeline summary

```
2026
  Q3 (now)
    ├── 2026-10-31  Foresight AI for Science & Safety Nodes
  Q4
    ├── ~2026-10    AIxCC @ NeurIPS 2026 (likely October)
  Q1 (2027)
    ├── 2027-02-09  GitLab AI Hackathon 2027 opens
    ├── 2027-03-20  OWASP Red Teaming Landscape 2027 (est)
  Q2 (2027)
    ├── Spring 2027 HK AI x Cybersecurity Challenge 2nd cycle
    ├── Spring 2027 火山引擎 Skill 安全攻防 2nd cycle
```

## File structure

```
docs/competitions/
├── README.md                    # This file
├── foresight-2026/
│   ├── APPLICATION.md           # Main application
│   ├── PROJECT_PLAN.md          # 6-month milestones
│   ├── BUDGET_INDIVIDUAL.md     # $35K individual variant
│   ├── BUDGET_CORPORATE.md      # $62K corporate variant
│   └── SUBMISSION_CHECKLIST.md  # 39-day checklist
├── owasp-landscape-2027/
│   └── SUBMISSION.md            # Template for 2027-03 submission
└── netmind-arena/
    └── INTEGRATION.md           # Registration + integration guide
```

---

## Next review

Revisit this README every 30 days. Automated scan (planned) will surface new opportunities and expired deadlines.
