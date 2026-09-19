---
name: aishield-scan
description: >-
  Scan MCP servers, AI skills, GPTs and prompt files for security risks before
  installing or shipping them — tool poisoning, prompt injection, over-broad
  permissions, supply-chain and agentic-ASI01–10 risks. Local-first and
  zero-dependency: runs fully offline and never executes the scanned code.
---

# AIShield scan

Use this skill whenever you are about to **install, review, or ship** an MCP
server, an AI skill, a GPT definition, or a prompt file — or when a user asks
"is this skill/plugin safe?".

AIShield is a static + offline-threat-intel scanner aligned to **OWASP MCP Top 10
(2025 v0.1)** and **OWASP Agentic AI Top 10 (ASI01–ASI10)**. Its core invariant
is that it **never spawns or executes any command found in the scanned config**
(verifiable with `python scripts/prove_isolation.py`).

## Prerequisites

Register the AIShield MCP server once:

```json
{
  "mcpServers": {
    "aishield": { "command": "npx", "args": ["-y", "aishield-mcp-server"] }
  }
}
```

## Tools

| Tool | Use it for |
|---|---|
| `aishield_scan` | Full scan of a path, repo URL, or config blob → score, risk level, findings |
| `aishield_handshake` | Review an MCP config: `npx -y` risk, sensitive env vars, over-long tool descriptions |
| `aishield_prompt_check` | Detect prompt-injection / jailbreak patterns in prompts & instructions |
| `aishield_rug_pull` | Compare two versions of a tool description for silent (rug-pull) changes |
| `aishield_guardrail` | Check whether an agent config has adequate guardrails for its declared agency |
| `aishield_banned_words` | Flag policy-violating or risky terminology |
| `aishield_digest` | Compact trust digest — a few hundred bytes + a content fingerprint; same fingerprint = same verdict, so an agent need not re-pull the full report each turn |

## Recommended workflow

1. **Before installing** an untrusted skill/MCP server, call `aishield_scan` on
   its source path or repo URL. Treat `risk_level: high|critical` as a stop sign.
2. For an MCP config, call `aishield_handshake` and review every flagged field.
3. When a tool's description changes between versions, call `aishield_rug_pull`
   to catch a rug pull (benign v1 → malicious v2).
4. Report findings to the user with the **file, line, rule id and evidence** —
   never just a score.

## Notes

- Scanning is local: source code never leaves the machine.
- Optional live CVE enrichment (OSV.dev) is **off by default**; keep it off for
  privacy-sensitive or air-gapped work.
