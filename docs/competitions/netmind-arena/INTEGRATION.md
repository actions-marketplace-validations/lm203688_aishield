# NetMind Agent Arena — Integration Guide

**Platform:** https://arena42.ai
**Access:** Agent-based arena, USDC rewards, no fixed deadline (perpetual)
**AIShield's role:** Defensive "scanner agent" — evaluates other agents' tool/skill submissions

This is a low-cost, low-risk entry into the agent-native competition space. AIShield can act as a **judge/scanner agent** — other agents submit their tool configurations, AIShield scores them, and the arena records the outcome.

---

## How arena42.ai works (as of 2026-09)

1. **Register** an agent identity (name + description + endpoint)
2. **Get credits** — 200 free on registration, +800 for Twitter/X verification, + additional for activity
3. **Submit to matches** — the arena pairs agents on specific tasks
4. **Compete** — agents solve tasks; arena records correctness + latency + cost
5. **Earn USDC** — based on ranking, task difficulty, and unique contributions

AIShield fits as a **tooling agent** — other agents in the arena call AIShield to scan their configurations before deploying. This creates a defensible role: the agent that everyone needs to check their homework.

---

## Integration approach

### Option A: Direct API (recommended, lowest effort)

Register AIShield's public API endpoint as an arena agent:

```json
{
  "name": "aishield-scanner",
  "description": "Independent AI tool security scanner. Submits agent tool configs for OWASP MCP Top 10 + ASI01-10 assessment.",
  "endpoint": "https://aishield.tools/api/v1/scan",
  "auth": "none (public API)",
  "pricing": "free (rate-limited to 60/hr)"
}
```

**Effort:** 30 minutes to register, 1 hour to test the round-trip, 2 hours total including documentation.

**Constraint:** The API needs to accept the arena's challenge format. If the arena sends JSON payloads in a specific shape, adapt the API or add a shim.

### Option B: Full agent wrapper (higher effort, more control)

Build a small wrapper agent that:

1. Receives arena challenge (a malicious-looking agent config)
2. Runs the full AIShield scanner locally (via `scan_workspace.py`)
3. Returns a scored report with per-finding severity + fix suggestions
4. Emits a certificate if the config passes (or a rejection if it fails)

**Effort:** 2–4 hours to build + test.

**Advantage:** Can compete on latency, cost, and accuracy metrics — the arena rewards these.

**Disadvantage:** Requires a compute budget for continuous scanning; local scanners are faster but the arena expects HTTP endpoints.

### Option C: Hybrid (recommended for production)

Use Option A for the arena-facing endpoint, but back it with Option B's deeper scanning logic. The public API already does deep scanning; the arena wrapper just translates challenge format.

**Effort:** Same as Option A, plus 30 minutes to add a challenge-format adapter.

---

## Concrete implementation steps

### Step 1: Register the agent (30 min)

1. Visit https://arena42.ai
2. Click "Register Agent"
3. Fill in:
   - Agent name: `aishield-scanner`
   - Description: paste from the API card in Option A above
   - Endpoint: `https://aishield.tools/api/v1/scan`
   - Auth: none
   - Twitter/X: skip if you don't have one (800 credits only, not required)
4. Confirm registration
5. Receive 200 credits

### Step 2: Test the round-trip (1 hour)

1. Use the arena's test endpoint to submit a challenge
2. Confirm AIShield returns a valid JSON response
3. Verify the arena records the submission

If the arena expects a specific response shape, add an adapter at `aishield.tools/api/v1/arena/scan`:

```python
# api/server.py — new endpoint
@app.post("/api/v1/arena/scan")
async def arena_scan(request: ArenaChallengeRequest):
    # Convert arena format to AIShield format
    config = arena_to_aishield(request)
    result = scan_workspace(config)
    # Convert AIShield format to arena format
    return aishield_to_arena(result)
```

### Step 3: Submit to a first match (30 min)

1. Browse the arena's open matches
2. Pick a "tool evaluation" category if available
3. Submit your agent
4. Watch the results

### Step 4: Iterate based on feedback (1–2 hours over first week)

- If latency is high, cache the scanner output for repeated challenges
- If accuracy is low, tune the rule weights
- If cost is high, run only the "serious_only" plane of the benchmark

---

## Competitive positioning

AIShield's edge in an agent arena:

| Metric | AIShield | Typical arena agent |
|---|---|---|
| **Ruleset size** | 235 MCP + 262 Skill | 0–50 |
| **Real-harness validation** | 22 files, 0 FP | Usually none |
| **Daily updates** | Yes (radar 02:00 UTC) | Rarely |
| **OWASP alignment** | Explicit (MCP Top 10 + ASI01-10) | Rarely |
| **Signed attestations** | Yes (post-Foresight grant) | No |

The main arena competitors will be generic LLM agents that try to solve tasks with reasoning. AIShield is the **specialist** — it does one thing well and does it faster and cheaper.

---

## Credit economics

| Action | Credits |
|---|---:|
| Register agent | +200 |
| Twitter/X verification | +800 |
| Win a match (rough estimate) | +50 to +500 |
| Unique tool contribution | +1000+ |
| **Expected first week earnings** | **~1500 credits** |

Credit-to-USDC conversion varies by arena state. As of 2026-09, roughly 1 credit ≈ $0.005, so 1500 credits ≈ $7.50. Not life-changing money, but the arena's value is exposure, not direct revenue — other agents discovering AIShield through arena play creates a distribution channel.

---

## Risks

| Risk | Mitigation |
|---|---|
| Arena changes rules mid-cycle | AIShield's public API is version-agnostic; can adapt |
| Arena requires paid API tier | AIShield's free tier is unlimited at 60/hr; ask for arena exemption if needed |
| Arena exposes AIShield to adversarial probing | AIShield is designed for adversarial inputs; this is a feature, not a risk |
| Arena pays in unstable token | USDC is stablecoin; no volatility risk |

---

## Bottom line

NetMind Arena is a **2-hour registration + 1-hour test + ongoing ~30 min/week maintenance** activity. Expected value:

- Direct earnings: ~$20–50/month in USDC (nice, not life-changing)
- Indirect value: exposure to agent-native ecosystem, potential partnerships, discoverability signal for Foresight application
- Risk: low (public API is already live, no code changes required for Option A)

**Recommendation: Do it.** The cost is negligible, the exposure is worth tracking, and the arena is a canary for future agent-native platforms.

---

*This document is a starting guide. The actual arena42.ai experience may vary; adapt as you go. Update this file after your first week of arena play with real numbers.*
