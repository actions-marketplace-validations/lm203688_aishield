# Foresight AI for Science & Safety Nodes — Application Playbook

**Verified 2026-09-23 against primary sources** (RFP page, three Call pages, the live Airtable form,
the grantee sitemap, and the Secure AI focus-area page).

Sources are quoted verbatim where it matters. Where a claim could not be verified, it is marked
`[UNVERIFIED]` — do not repeat such claims to Foresight or in the application.

---

## 1. The shape of this grant — read this before anything else

This is **not** a PDF-submission grant. The entire formal submission is **one short web form**:

> **https://airtable.com/appyVXc5SMPAvIKpP/pagp7takV26cG6JY1/form**

The form is titled *"AI for Safety & Science Nodes RFP 2026"* and states, verbatim:

> "Application deadline is on **31st October 23:59 PDT**, with **decisions expected to be made in January 2027**."

Three consequences that change how we prepare:

1. **It has hard character limits.** The core pitch field is *"What are you trying to do? Explain it
   in as few words as possible with **zero jargon**. (max 350 characters)"*. The RFP-fit field is
   *"(max 500 characters)"*. Our 14 KB `APPLICATION.md` cannot be pasted into these fields — it has to be
   **compressed**, and the long document becomes an *attachment-by-link* at best.
2. **The reviewer's first impression is ~850 characters.** Everything in the long document is
   supporting material for a decision that is largely made in the first screen.
3. **Decisions land in January 2027.** Not "~3 months from application"; the form names the month.

### Deadline arithmetic (verified)

| Definition | Value |
|---|---|
| RFP deadline | 2026-10-31 23:59 PDT |
| = UTC | 2026-11-01 06:59 UTC |
| = Beijing time | **2026-11-01 14:59 CST** |
| Days remaining from 2026-09-23 | **38** |
| Decision expected | **January 2027** |

> ⚠️ **Conflicting deadline signal.** The RFP page and the Airtable form both say a single
> 31 Oct 2026 deadline. But `foresight.org/focus-areas/secure-ai` still says *"AI for Science &
> Safety Nodes — Application deadlines at the end of each month"*, and several third-party grant
> aggregators describe rolling monthly review. That is **stale content from the pre-RFP structure**;
> Foresight's own `/grants/grants-ai-for-science-safety/` page says *"we are moving from open,
> general applications to targeted calls… Until the RFPs are published we are not accepting further
> submissions."* Treat **31 Oct 2026 as the only real deadline**, and treat the "monthly" text as a
> leftover. Do not rely on it.

---

## 2. What the form actually asks (field-by-field, transcribed)

This is the complete field list. Nothing else is required to submit.

### Section: About you

| Field | Notes |
|---|---|
| Full name | |
| Email | |
| Website, CV, or LinkedIn profile link | **This is where the track record lives.** |
| Affiliated organization(s) or project(s) | *"Leave this blank if this isn't applicable to you."* |
| Applying as an | dropdown |
| What is your / your team's track record? | free text |
| Project participant(s) (roles + LinkedIn/website links) | |
| Primary region | |
| Primary country | |
| Full name and email of a primary reference | *"References will only be contacted if their input is relevant to the final decision."* |
| What type of org? | dropdown — includes **`Individual - World`**, `Individual - US`, `Individual - EU`, plus Non-profit / University / For-profit variants |

> **`Individual - World` exists in the dropdown.** This is first-party confirmation that a
> China-based individual with no legal entity is an accepted applicant type.

### Section: About your project

| Field | Constraint |
|---|---|
| What are you applying for? (select all) | funding / physical space / compute |
| RFP focus area you are applying for | 7 options, listed in §3 below |
| Project title | |
| What are you trying to do? | **max 350 characters**, *"zero jargon"* |
| How does your project address the RFP area you selected? | **max 500 characters** |
| How is today's approach limited? What is new in your approach, what does success look like? | free text |
| If there are risks, is it possible to differentially advance safety-enhancing aspects first? | free text |
| Outline start/end time and key project milestones | free text |
| If this project goes well, how do you plan to scale it for impact in 3 years? | free text |
| This program requires open-source work product. Do you commit to this? | yes/no |
| Share any additional information and links | free text |

> The prompt *"we prioritise projects wanting to be an active part of our physical spaces"* is
> repeated as **help text directly on the "What are you applying for?" field**.

### Section: About your request

**Physical Node** — *"To create community among mission-aligned projects, we strongly prioritize projects
wanting to be an active part of our physical spaces in the Bay Area (USA) or in Berlin (Germany). The
space is **free of charge** for our grantees."*

| Field | Notes |
|---|---|
| Which node are you interested in? | |
| For how long do you want to use the space? (start/end dates) | |
| Who in your team wants to use the space? | |
| How do you want to use the space? (office / co-working / events) | |
| Are you open to joining one workshop during your node use? | *"We expect grantees to join **one travel-paid workshop** on AI for Science and Safety either in the Bay or Berlin (whichever is closer)"* |

**Funding** — *"Grants typically range from $30,000 to $100,000 with smaller amounts being awarded to the
**Human Empowerment** and **AI Insurance & Open Governance** focus areas, and higher amounts to the rest.
**More cost-effective projects will be preferably considered.**"*

| Field | Notes |
|---|---|
| Are you requesting funding? | |
| If yes, will there be overhead? | dropdown: `0-10%`, `10%-20%`, etc. |

**Compute** — *"We will provide the opportunity to request local compute for projects contributing to open
source architectures and blueprints that build capacity for private local compute and for sensitive
projects requiring that type of compute."*

| Field | Notes |
|---|---|
| Are you requesting compute? | AIShield is CPU-only; requesting compute would hurt us, not help |

### Section: Sharing with Lightcone Commons (optional)

*"To broaden your chances of funding, we may share selected applications with Lightcone Commons, a
third-party grant-coordination platform operated by Lightcone Infrastructure… Your application will be
visible to funders, evaluators and direct grantors on the platform, who may be located **anywhere in the
world and some of whom may be pseudonymous or anonymous**."*

Opt-in is a genuine trade-off: it widens the funnel beyond Foresight, but it publishes the application
to unnamed third parties.

---

## 3. Where AIShield fits — and the two problems with our current framing

The RFP spans **three calls only**. Verified from `/grants/`:

| Call | Fit |
|---|---|
| **I. Local compute** | ✗ — AIShield is zero-dependency CPU; needs no cluster |
| **II. Coordination and accountability** | ✅ this is us |
| **III. AI-first science: Bio, Neuro, Nano** | ✗ |

Call II has four focus areas, and the form's dropdown numbers them:

| # | Focus area | Fit |
|---|---|---|
| 1 | Building and scaling local compute setups | ✗ |
| 2 | Supercollaboration and decentralized alignment | △ partial — "distributed oversight, agent monitoring, and verification projects" |
| 3 | Human Empowerment | ✗ |
| **4** | **AI Insurance & Open Governance** | ✅ **our home** |

> ⚠️ **There is no call named "AI for Security."** That phrase appears as a *category label on grantee
> pages* and as a focus area on the older, superseded general-grants page. Applicants must select from
> the 7 dropdown options above. An earlier draft of `APPLICATION.md` said *"Track 1 — AI Insurance and
> Open Governance"* — a label that appears nowhere in the RFP. **Corrected: Call II, focus area 4.**

### Problem 1: focus area 4 is explicitly the *lower-funded* area

Foresight states it plainly, twice: *"smaller amounts being awarded to the Human Empowerment and
AI Insurance & Open Governance focus areas."* So our natural home is the **small end of $30K–$100K**,
likely **$30–50K**, not the $62K the corporate budget variant asks for.

### Problem 2: the generic framing is already funded

The 2026 cohort contains a project that occupies very nearly the same ground as our current pitch.

| | Yue Zhao (USC FORTIS Lab), **funded 2026**, SF Node, AI for Security |
|---|---|
| Their title | *Audit-to-Patch Pipelines for Secure LLM Agent Systems* |
| Their description | *"building an audit-to-patch pipeline that **detects and audits security risks in LLM agent code and configuration**, then proposes safe, reviewable patches with automated checks"* |

That is AIShield's §1 executive summary, minus the attestation layer, with an elite affiliation
attached. If we submit *"we built a scanner that detects security risks in agent configs"*, a reviewer
who has already funded Yue Zhao reads it as a weaker restatement.

**The differentiation has to move.** What nobody in the 2026 cohort is building is the **trust layer
above the scanner**: reproducible, third-party-verifiable attestations, and a machine-readable incident
record that an insurer, a procurement team, or a governance body can pin a policy to. That is exactly
what Call II area 4 asks for (*"Build ways for people outside a lab to assess risks… independent incident
reporting… frameworks for evaluating security practices without exposing proprietary information"*), and
it is a claim Yue Zhao's project does not make.

---

## 4. How selection actually works

Verbatim from the RFP:

> "The approximate review time is three months after the application deadline. Proposals are first
> reviewed **in-house for fit and quality**. Strong submissions are sent to **technical advisors** for
> further evaluation. If your proposal advances, we may follow up with **written questions or a short
> call**. If you choose to opt into Lightcone Commons sharing, Foresight may also share selected
> applications with Lightcone Commons for evaluation, and possible additional funding consideration.
> Unfortunately, due to the number of applications we receive, **we are unable to provide individual
> feedback to unsuccessful applicants**."

So: **4 gates** — in-house fit → technical advisors → clarification (short call possible) → optional
Lightcone Commons. No feedback on rejection. The "short call" gate is the point at which an applicant
who has never interacted with Foresight is at a disadvantage.

### The seven published evaluation criteria

1. **Alignment with the specific RFP focus area** — the degree to which the project addresses the
   selected focus area.
2. **Impact on reducing existential risks from AI** — significant advancements within short timelines.
3. **Feasibility within short AGI timelines** — concrete milestones and deliverables in **1–3 years**.
4. **AI-first work** — *"smart allocation of resources and compute to automate workflows"*, not large
   team budgets.
5. **Capability to execute** — *"quotations, experience, and resources… Strong teams with proven
   expertise in the field will be prioritized."*
6. **High-risk, high-reward potential** — *"We encourage speculative, high-risk projects."*
7. **Requirement for open source** — *"We require the work product (code, data, and outputs) of the
   funding to be open-sourced."*

Criterion 1, 4, 5 and 6 are where we are weakest, and they are stated in the most absolute language
("require", "strongly prioritize"). Criterion 7 is where we are strongest — AIShield is MIT.

### Funding terms (verbatim substance)

- Lump sum; tranches only for multi-year work, each tranche contingent on reporting.
- Overhead fundable **up to 10% of direct research costs**.
- Due diligence: *"confirming your connections to Foresight Institute, sharing any ongoing criminal
  proceedings, bankruptcy, tax documents etc., and sharing an itemized budget, project plan and
  organizational documents."*
- Grantees agree Foresight may *"list their project on our website and share the project title and
  project lead"* including social media.
- *"Basic reporting requirements… brief progress updates at regular intervals."*
- Tax: *"Applicants are responsible for understanding and complying with any applicable tax requirements."*

---

## 5. Comparison with previously funded projects

Data source: `foresight.org/grantee-sitemap.xml` — **33 grantee pages dated 2026**, plus the
"previously funded" roster on the Secure AI focus page.

### 5.1 Composition of the funded pool

Overwhelmingly one of two things:

**Elite academic labs** — MIT (Boyden), UC Berkeley (Dawn Song, Ariel Procaccia), USC (Yue Zhao,
Souti Chattopadhyay), Oxford (Fazl Barez, Christian Schroeder de Witt, Toby Pilditch, Abhinav Singh),
Cambridge (Herbie Bradley, Lovkush Agarwal, Zhonghao He), Harvard / Wyss (Michael Shadpour),
ETH Zurich (Florian Tramer), UNSW (Gernot Heiser, Rob Sison), Penn (Eva Dyer), Mila (Blake Richards),
NYU + Basel (Catalin Mitelut), CMU (Aran Nayebi), Georgia Tech (Shucong Li), WashU (Yevgeniy
Vorobeychik), King's College London (Chiara Herzog), Radboud (Samuel Nellessen), Surrey (Roman Bauer),
Cornell (Tom Burns), NC State (Patrick Seebold), Boston University (Mayank Varia), HES-SO (Simon Dürr),
Salk (Talmo Pereira), UMass Lowell (Sean Simonini), UCL (Bradley Love), Hasso Plattner (Georgios Kaissis).

**Established organisations** — FAR AI (Adam Gleave), Center for AI Safety (Dan Hendrycks),
Metaculus (Benjamin Wilson), PIBBSS (Nora Ammann), OpenMined, Agoric (Mark Miller),
Cooperative AI Foundation (Chandler Smith), Apart Research (Jaime Raldúa Veuthey), AE Studio,
Eon Systems, Mileva Security Labs (Harriet Farlow), Zeroth Research, MettaAi, Salesforce,
Center for AI Risk Management & Alignment (Richard Mallah), AI Digest (Adam Binksmith),
Ludlow Institute (Naomi Brockwell), Security Level 5 Task Force (Lisa Thiergart), The Society Library.

**And a small but real set of independents** — this is the important one for us:

| Grantee | Listed affiliation |
|---|---|
| Chris Lakin | **Independent** |
| Joel Pyykkö | **Independent** |
| Kathleen Finlinson | **Independent** |
| Richard Csaky | **Independent** |
| Roland Pihlakas | Simplify (Macrotec LLC) |

> **Conclusion on the "is there any chance?" question:** yes, but the median funded applicant is a
> named academic or an org with a track record. Independents do get funded — roughly 5 of ~130 names
> on the Secure AI roster, i.e. **low single-digit percent**. Applying as a solo independent is a real
> path, not a fiction, but it is the hardest path, and it is the path that makes the "capability to
> execute" criterion the decisive one.

### 5.2 The 2026 "AI for Security" cluster — our direct competition

Five 2026 grants sit in agent/AI security. Two of them are uncomfortably close to us.

| Grantee | Affiliation | Node | Project |
|---|---|---|---|
| **Yue Zhao** | USC FORTIS Lab | SF | **Audit-to-Patch Pipelines for Secure LLM Agent Systems** — *"detects and audits security risks in LLM agent code and configuration, then proposes safe, reviewable patches"* ← **direct overlap** |
| **Souti Chattopadhyay** | USC Viterbi (ACE Lab) | SF | Scalable Formally-Verified Code Generation — compiles protective constraints into formal automata so vulnerability classes become *"mathematically impossible"* |
| **Samuel Nellessen** | KachmanLab, Radboud University | Berlin | Slingshot: Automated Multi-Turn Jailbreaking for Agentic AI — RL discovers agent failure modes; *"companies might stop AIs from saying harmful things, they fail to stop them from doing harmful things"* |
| **Leo McKee-Reid** | Neolithic / Coordinal Research | SF | Automating AI safety research; platform for rapidly iterating dangerous-capability evals |
| **Mayank Varia** | RISCS, Boston University | — | (security / reliable information systems) |

Relevant non-grant signal: the Secure AI seminar roster includes *"**Never Trust An Agent:
Accountability For Agentic AI**"* (Daniel Benarroch, Sep 2026) — the accountability framing is
already in their air.

Also directly upstream: **Dawn Song (UC Berkeley)**, a Foresight grantee, for *"Benchmarking AI Agents
on Real-World Vulnerability Reproduction"* — the CyberGym / ExploitGym line of work. Foresight
**already funds agent-security benchmarking**.

### 5.3 The nearest small-applicant precedent

**Samuel Nellessen** is the closest thing to our profile that got funded in 2026: a researcher at a
small lab, not a famous professor, at the **Berlin** node. His application reads as a **single crisp
empirical claim** — *"safety locks on AIs are easy to break. I built a small AI that teaches itself to
trick bigger AIs into performing dangerous actions (not just writing text)."*

That is the template that works for a small applicant: **one falsifiable finding, stated as a finding,
not a tool description.** AIShield's equivalent would not be "235 rules" but something like
*"we scanned N real agent toolchains and found X% ship an install-time execution path that no
marketplace checks"* — a number nobody else has published.

---

## 6. What we must do besides filling the form

### Blocking, and only the user can do these

| # | Item | Why it blocks |
|---|---|---|
| 1 | **Real name, email, country/region** | The form requires them; `Individual - World` is the applicable org type |
| 2 | **Decide funding / space / compute** | Node-first is strongly preferred; funding-only is *"considered only in exceptional cases"* |
| 3 | **Node attendance + workshop willingness** | The form asks directly, and *"we expect grantees to join one travel-paid workshop"* |
| 4 | **Visa reality check** | Travel is paid, but a PRC passport still needs a **US B1/B2** or **Schengen** visa. Interview backlogs for B1/B2 in China are measured in months. If the honest answer is "cannot obtain a visa in the grant window", say so on the form rather than promising attendance — a promise we cannot keep is worse than a remote application. |
| 5 | **A named primary reference who has agreed** | The field is required. Never list someone who has not consented |
| 6 | **Lightcone Commons opt-in yes/no** | Publishing the application to pseudonymous third-party evaluators is a disclosure decision |

### Doable, and materially improves the odds

| # | Action | Rationale |
|---|---|---|
| A | **Fix the false claims in our own materials** (see §7) | Two of them are checkable in one click; a reviewer who checks and finds a fabricated number is done with us |
| B | **Compress the pitch to 350 characters, zero jargon** | The whole review starts with this field |
| C | **Reframe from "scanner" to "independent assessment + attestation infrastructure"** | Avoids reading as a weaker Yue Zhao |
| D | **Manufacture the missing evidence: a real distribution/usage number** | 2 stars is the weakest signal in the packet. Either earn a real number (npm/Glama/CI installs) before submitting, or **stop claiming community** |
| E | **Publish one falsifiable finding** (à la Nellessen) | A measured claim from real toolchains is worth more than a ruleset count |
| F | **Write the reference request** | Give the reference the 350-char pitch so their letter is about the same project |
| G | **Prepare the due-diligence pack now** | Itemized budget + project plan + org docs are requested of winners; having them ready shortens the gap between "funded" and "paid" |
| H | **Watch the free public recordings** | `foresight.org/resources/recordings/` is free and is the cheapest available read on their taste. The seminar *group* itself requires a **paid annual subscription** — not free |

### Things that do NOT help

- **Requesting compute.** AIShield is CPU-only and the compute line is aimed at private/local-compute
  blueprints. Asking for compute weakens the application.
- **Requesting overhead at 10%+.** The dropdown goes to 10-20%, but *"more cost-effective projects will
  be preferably considered"* and overhead is capped at 10% of direct costs. Ask for 0%.
- **Trying to be added to a Node without being there.** The Node fields assume physical presence.
- **Waiting for a monthly deadline.** See the deadline warning in §1.

---

## 7. Corrections made to our own materials (2026-09-23)

These were found while writing this playbook. All were self-inflicted, and two were checkable in one click.

| File | Claim | Reality | Action |
|---|---|---|---|
| `APPLICATION.md §7` | *"500+ GitHub stars (currently ~100)"* | **2 stars, 0 forks** (`api.github.com/repos/lm203688/aishield`) | **Removed as a target; corrected to the real number** |
| `APPLICATION.md §1, §8` | *"235 MCP rules + 262 Skill rules + 19 radar-generated daily"* | `235` already **includes** the 19 radar (208 static + 8 generated + 19 radar). Listing them separately double-counts | **Rewritten to show the breakdown** |
| `APPLICATION.md §1, §2.3` | *"1283 automated tests"* | `unittest` discovery finds **1295** | **Updated** |
| `APPLICATION.md` header, `SUBMISSION_CHECKLIST.md` | *"Track 1 — AI Insurance and Open Governance"* | No such label exists. Correct: **Call II, focus area 4** | **Corrigendum added** |
| `APPLICATION.md` header | *"Deadline 2026-10-31 (39 days from drafting)"* | 38 days from 2026-09-23 | **Updated** |
| `SUBMISSION_CHECKLIST.md` | *"Log in at foresight.org/grants/…"* | It is a **public Airtable form**. No login, no account | **Corrigendum added** |
| `SUBMISSION_CHECKLIST.md` | *"Foresight typically accepts up to 10MB per submission"* | `[UNVERIFIED]` — invented. There is no stated limit; the form has character limits instead | **Flagged** |
| `SUBMISSION_CHECKLIST.md` | *"Foresight processes applications in receipt order in a tie"* | `[UNVERIFIED]` — invented | **Flagged** |
| `SUBMISSION_CHECKLIST.md` | *"Foresight explicitly asks that applicants not run parallel applications to competing grants"* | `[UNVERIFIED]` — **nowhere in the RFP** | **Flagged; do not rely on this to withhold other applications** |
| `SUBMISSION_CHECKLIST.md` | *"Foresight reviews active community signals"* | `[UNVERIFIED]` though plausible given the *capability to execute* criterion | **Flagged** |
| `SUBMISSION_CHECKLIST.md` | *"Prepare a letter-of-intent… Foresight loves to see this"* | `[UNVERIFIED]` and the form has **no attachment field** | **Deprioritised** |
| `APPLICATION.md §5` | *"3+ years building open-source security tooling"*, *"Prior work on supply-chain scanning for Python, npm, and Go ecosystems"* | **`[UNVERIFIED]` — these are claims about the applicant, not about the codebase.** They came from a draft bio and must be confirmed, corrected, or deleted by the applicant before submission. A CV-style claim a reviewer cannot substantiate is worse than no claim | **Requires user confirmation** |

**Verified-correct claims kept as-is:** MIT licence; individuals eligible with **no nationality
restriction**; travel is Foresight-paid for the expected workshop; the 31 Oct 2026 deadline;
`Individual - World` as a valid applicant type; open-source as a hard requirement.

---

## 8. Decision log

| Date | Decision | Basis |
|---|---|---|
| 2026-09-23 | Foresight promoted to **P0** | Eligibility verified: individuals, no nationality bar, travel paid |
| 2026-09-23 | Correct home is **Call II / focus area 4** | Verified against the form's own dropdown |
| 2026-09-23 | Expect the **lower end** of $30K–$100K | RFP states area 4 receives smaller amounts |
| 2026-09-23 | Reframe from scanner → **independent assessment + attestation infrastructure** | Yue Zhao 2026 already funds the scanner framing |
| 2026-09-23 | Drop the star-count and community-size claims | 2 stars is the real number |
