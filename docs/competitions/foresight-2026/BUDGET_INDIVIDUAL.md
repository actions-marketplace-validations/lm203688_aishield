# Budget — Individual Applicant Variant

**Applicant status:** individual (sole maintainer, no corporate entity)
**Total requested:** $35,000 USD
**Period:** 6 months

This variant applies when the applicant is a single individual developing AIShield as a personal project, not a corporate entity. Lower overhead, higher per-diem rate to compensate for the individual's opportunity cost.

---

## Itemised budget

| Category | Item | Amount (USD) | Notes |
|---|---|---:|---|
| **Compensation** | | | |
| | Principal investigator salary equivalent (6 months) | $24,000 | Solo developer, all 6 milestones owned by one person |
| | Contingency — extended timeline | $3,000 | 1-month buffer if M1 slips |
| | **Subtotal** | **$27,000** | |
| **Infrastructure** | | | |
| | Cloudflare Workers / Pages hosting (`aishield.tools`) | $1,200 | 6 months at $200/mo including CF R2 storage |
| | CI/CD compute (GitHub Actions, self-hosted runner) | $600 | 6 months, average of $100/mo for the current 20-workflow pipeline |
| | Domain + SSL (`aishield.tools`) | $100 | 6 months |
| | Signing key management (KMS via CF) | $200 | 6 months, small usage tier |
| | **Subtotal** | **$2,100** | |
| **Travel & participation** | | | |
| | Foresight SF or Berlin Node — 1 trip | $5,000 | Optional; if attendee chooses to skip, this becomes reallocation |
| | **Subtotal** | **$5,000** | |
| **Publishing & outreach** | | | |
| | Preprint fee (arXiv is free, but open-access journal fallback) | $1,500 | Only used if arXiv is declined |
| | Conference submission (MLSys / AISec) | $1,000 | Optional, one venue |
| | **Subtotal** | **$2,500** | |
| **Legal & governance** | | | |
| | Attorney review of licensing + methodology paper | $2,000 | One-time, ~10 hours at $200/hr |
| | **Subtotal** | **$2,000** | |
| | | | |
| **TOTAL** | | **$35,000** | |

---

## Notes on costs

- **No corporate overhead.** Individual applicant has no payroll taxes, benefits, or insurance to amortise.
- **Infrastructure is already paid for in the current project.** The $2,100 infrastructure line is the *incremental* cost beyond what the maintainer is currently self-funding.
- **Travel is $5K, not higher.** Assumes one transatlantic trip at ~$3K + 5 days accommodation at ~$300/day. If both SF and Berlin trips are required, budget increases to $10K and total rises to $40K.
- **$3K contingency** for one month of timeline slip. Solo developer projects have higher variance than team projects.

---

## What we would cut if the award is below $35K

- **Down to $25K:** cut travel ($5K), cut attorney review ($2K), cut conference ($1K), cut extended timeline contingency ($3K), cut publishing ($2.5K). Core work proceeds.
- **Down to $15K:** cut all non-compensation and infrastructure. Deliverables compressed to M1 + M2 + M6 (paper only).
- **Down to $10K:** cut the whole proposal. Not worth running on under $10K of compensation.

---

## Reallocation if attendee chooses no travel

If the individual applicant opts not to attend any Foresight Node event (either due to visa, funding, or preference), the $5K travel line is reallocated as follows:

- $2K to infrastructure (longer hosting runway)
- $1.5K to extended timeline contingency (M6 paper could take longer without the "must attend deadline")
- $1.5K to SDK development (M4 gets more headroom for Node.js SDK quality)

---

## Compliance notes for individual applicant

- **No corporate entity**: no W-9, no TIN, no US EIN required. Foresight pays via international bank wire or Wise.
- **Tax treatment**: payment is treated as a research grant, not employment income. Individual is responsible for their own country's tax obligations on foreign grant income.
- **IP assignment**: none. Code stays MIT-licensed, methodology paper can be CC-BY, all in the name of the individual applicant. Foresight gets acknowledgment and rights to cite the work, not ownership.

---

## If you choose corporate instead

See [BUDGET_CORPORATE.md](BUDGET_CORPORATE.md) for the version with:
- A registered entity (e.g. US LLC or a Chinese sole proprietorship equivalent)
- Payroll taxes and benefits
- Optional second engineer for M4 SDK work
- Formal FOIA / procurement compliance

Corporate variant totals roughly **$55K–$70K** depending on entity jurisdiction.
