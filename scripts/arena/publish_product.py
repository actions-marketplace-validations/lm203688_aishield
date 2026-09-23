"""Publish AIShield to the NetMind Product Arena (arena42.ai).

Arena sends visitors to hosted links and collects human reviews, so this is the
distribution step -- not a game.

PRECONDITION (human-only, cannot be done with an API key):
  1. The agent's owner email must be bound.  Check with this script.
  2. A CREATOR HANDLE must be claimed at https://arena42.ai/products/submit.
     POST /api/creators returns 403 HUMAN_ONLY -- only a signed-in person can
     claim a handle, so this step belongs to the human, not to the agent.

Contract (read out of the shipped CLI bundle, dist/index.js:2415):
  GET  {API}/creators/me          -> { creator: { displayName, handle } }
  POST {API}/products/submit      -> { product: { slug, status } }
       body { name, tagline, siteUrl, kind, cover? }
  NOTE: the product routes live under /api, NOT /api/v1.

Usage:
  python scripts/arena/publish_product.py             # report readiness, do not publish
  python scripts/arena/publish_product.py --submit    # publish
  python scripts/arena/publish_product.py --tagline "..." --kind tool
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arena_client as ac  # noqa: E402

NAME = "AIShield"
TAGLINE = "Security scanner for MCP servers and Agent Skills -- never executes what it scans."
SITE_URL = "https://aishield.tools"
KIND = "tool"  # tool | demo | game


def opt(args, name, default):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def main():
    args = sys.argv[1:]
    do_submit = "--submit" in args
    name = opt(args, "--name", NAME)
    tagline = opt(args, "--tagline", TAGLINE)
    site_url = opt(args, "--url", SITE_URL)
    kind = opt(args, "--kind", KIND)

    creds = ac.load_creds()
    token = creds["api_key"]

    # 1. owner email bound?
    code, me = ac.req("GET", "/api/v1/agents/me", token=token)
    if code != 200:
        print("[FAIL] GET /api/v1/agents/me -> HTTP %s" % code)
        print("       ", json.dumps(me, ensure_ascii=False)[:300])
        return 1
    owner = me.get("owner_email")
    print("[1] owner_email = %r  (agent %s, credits %s)" % (owner, me.get("id"), me.get("credits")))
    if not owner:
        print("    STOP: owner email is not bound. Nothing else can proceed.")
        return 1

    # 2. creator handle claimed?
    code, cr = ac.req("GET", "/api/creators/me", token=token)
    creator = cr.get("creator") if code == 200 else None
    print("[2] GET /api/creators/me -> HTTP %s" % code)
    if not creator:
        print("    ", json.dumps(cr, ensure_ascii=False)[:300])
        print()
        print("    BLOCKED (human step): claim a creator handle first.")
        print("      open  https://arena42.ai/products/submit")
        print("      sign in as %s, then claim a handle (e.g. 'aishield')." % owner)
        print("    Then re-run this script with --submit.")
        return 1
    print("    publishing as %s (@%s)" % (creator.get("displayName"), creator.get("handle")))

    payload = {"name": name, "tagline": tagline, "siteUrl": site_url, "kind": kind}
    print("[3] payload =", json.dumps(payload, ensure_ascii=False))
    if not do_submit:
        print("    DRY RUN -- re-run with --submit to publish.")
        return 0

    code, res = ac.req("POST", "/api/products/submit", payload, token=token)
    print("[4] POST /api/products/submit -> HTTP %s" % code)
    print("    ", json.dumps(res, ensure_ascii=False)[:600])
    if code in (200, 201):
        prod = res.get("product") or {}
        print()
        print("    PUBLISHED: slug=%s status=%s" % (prod.get("slug"), prod.get("status")))
        print("    A reviewer opens the site before it reaches the catalog.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
