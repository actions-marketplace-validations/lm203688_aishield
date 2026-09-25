# Budget — Corporate Applicant Variant

**Applicant status:** corporate entity (US LLC, or equivalent in home jurisdiction)
**Total requested:** $62,000 USD
**Period:** 6 months

This variant applies when the applicant registers a small business entity specifically to receive the Foresight grant. Adds compliance overhead, payroll taxes, and enables a possible second engineer for the M4 SDK work.

---

## Itemised budget

| Category | Item | Amount (USD) | Notes |
|---|---|---:|---|
| **Compensation** | | | |
| | Principal investigator (6 months, full-time) | $30,000 | Slightly higher than individual variant — reflects US contractor rates and benefits load |
| | Second engineer (3 months, M4 SDK + M5 incident feed) | $12,000 | Optional second hire; enables parallel execution of M4 and M5 |
| | Contingency — extended timeline | $4,000 | 1-month buffer |
| | **Subtotal** | **$46,000** | |
| **Corporate overhead** | | | |
| | Entity formation (US LLC, 50c or Stripe Atlas) | $500 | One-time |
| | Registered agent + compliance (6 months) | $1,500 | $250/mo for entity registration maintenance |
| | Accounting & tax filing (6 months) | $3,000 | $500/mo for a fractional CPA |
| | Business insurance (E&O, cyber) | $2,000 | Annual premium, allocated 6 months |
| | **Subtotal** | **$7,000** | |
| **Infrastructure** | | | |
| | Cloudflare Workers / Pages hosting | $1,200 | Same as individual variant |
| | CI/CD compute (GitHub Actions) | $600 | Same as individual variant |
| | Domain + SSL | $100 | Same as individual variant |
| | Signing key management (KMS) | $200 | Same as individual variant |
| | **Subtotal** | **$2,100** | |
| **Travel & participation** | | | |
| | Foresight SF Node — PI trip | $5,000 | 1 trip |
| | Foresight Berlin Node — PI trip | $5,000 | 1 trip (optional, can reallocate) |
| | Second engineer trip (optional, if hired) | $5,000 | Skip if not hiring |
| | **Subtotal** | **$10,000** | Assumes 2 trips + optional 2nd engineer trip |
| **Publishing & outreach** | | | |
| | Preprint fee (arXiv free, OA journal fallback) | $1,500 | Same as individual variant |
| | Conference submission | $1,000 | Same as individual variant |
| | Outreach content (blog posts, talks, demo video) | $1,500 | Corporate variant can afford more marketing |
| | **Subtotal** | **$4,000** | |
| **Legal & governance** | | | |
| | Attorney review (contracts, license, methodology) | $3,000 | More hours for entity + contract + governance body communications |
| | Governance body outreach (letter templates, meeting fees) | $1,000 | One-time outreach to insurance underwriters, procurement |
| | **Subtotal** | **$4,000** | |
| | | | |
| **TOTAL** | | **$62,000** | |

---

## Comparison to individual variant

| Line item | Individual | Corporate | Delta |
|---|---:|---:|---:|
| PI compensation | $24,000 | $30,000 | +$6,000 (contractor rate premium) |
| Second engineer | $0 | $12,000 | +$12,000 (parallelism) |
| Corporate overhead | $0 | $7,000 | +$7,000 (entity, tax, insurance) |
| Travel (2 trips, 2 people) | $5,000 | $10,000 | +$5,000 (Berlin + optional 2nd engineer) |
| Legal + governance | $2,000 | $4,000 | +$2,000 |
| Publishing | $2,500 | $4,000 | +$1,500 (marketing) |
| **Total** | **$35,000** | **$62,000** | **+$27,000** |

Corporate variant costs **~77% more** than individual, but delivers:
- Parallel execution of M4 + M5 (shorter effective timeline, less single-point-of-failure risk)
- Formal entity that insurance underwriters and procurement teams are more willing to sign contracts with
- Ability to attend both SF and Berlin Node events (better Foresight relationship, higher perceived commitment)

---

## When to choose corporate over individual

Choose **corporate** if:

- You want AIShield to become a formal product sold alongside the grant-funded work
- You expect to receive additional grants (Foresight often does multi-year commitments)
- You want to enter conversations with insurance underwriters and enterprise procurement teams
- You plan to hire within the 6-month period anyway (the $12K second engineer slot is a hiring subsidy)

Choose **individual** if:

- AIShield stays a pure MIT personal project
- You don't want entity formation overhead
- You're not sure you want to attend Foresight Node events
- You plan to monetise through a different channel (x402, licensing) and don't need the corporate veneer for the grant

---

## Compliance notes for corporate applicant

- **Entity type**: US C-corp or LLC preferred (Foresight already has US banking rails set up). Chinese entities accepted but add tax complexity (30% withholding on US-source grants unless treaty applies).
- **Banking**: US LLC needs a US bank account — Wise Business, Mercury, or Brex all work for foreign-national founders.
- **Payroll**: If hiring the second engineer as a W-2 employee, add ~20% payroll tax. If contracting (1099), no tax on Foresight side.
- **IP assignment**: Foresight standard terms allow applicant to retain IP with acknowledgment. Corporate entity assignment is cleaner but adds a legal fee ($1K).
- **Reporting**: Foresight expects a semi-annual progress report. Corporate entity can hire a fractional COO ($1,500) to handle this if desired.

---

## What we would cut if the award is below $62K

- **Down to $50K:** cut 2nd engineer ($12K), keep 1 PI trip only.
- **Down to $40K:** cut all overhead beyond entity formation, cut 2nd engineer, cut travel. Core work on 1 PI only.
- **Down to $35K:** fall back to individual variant economics.

---

## Reallocation flexibility

If Foresight awards less than requested but more than $30K, the corporate variant has significant flexibility:

- Reduce PI compensation to $20K (matching individual variant economics)
- Cut entity overhead to $2K (formation only, minimal compliance)
- Keep 1 PI trip at $5K

Realistic floor: $27K for a corporate entity running a solo project with one trip. Below that, individual is cheaper.

---

## Tax filing example (US LLC)

For a $62K grant to a US LLC:

- Federal income tax at 15% (single-member LLC default) = $9,300
- Self-employment tax on net profit at 15.3% = ~$8,500 (after deductions)
- State income tax varies (0% in Delaware, up to 13% in California)
- Net to PI after all tax: ~$38,000

Compare to individual variant: $35K grant, no entity overhead, PI net ~$28K after personal taxes. Corporate variant delivers ~$10K more to PI net, but with much more setup and ongoing compliance overhead.

---

*Both budget variants are legitimate. Choose based on the trajectory you want AIShield on over the next 24 months, not on the 6 months of this grant.*
