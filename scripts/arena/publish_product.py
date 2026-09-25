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
  python scripts/arena/publish_product.py --status    # review status of our submission(s)
  python scripts/arena/publish_product.py --submit    # publish (refuses if already submitted)
  python scripts/arena/publish_product.py --tagline "..." --kind tool

STATUS MODE prints a machine-readable last line, so an automation can watch the
review without a human reading the output:

  STATUS=<published|pending|rejected|absent>

`--submit` is intentionally NOT idempotent-safe: Arena allows one product per
domain, so a second submission would create a duplicate entry. The script refuses
to submit while a record for our slug already exists.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arena_client as ac  # noqa: E402

NAME = "AIShield"
TAGLINE = "Agent-native security scanner for MCP servers and Agent Skills. Never executes what it scans."
SITE_URL = "https://aishield.tools"
KIND = "tool"  # tool | demo | game  -- the web form pre-selects "demo"; that is wrong for us
SLUG = "aishield"  # what our listing is expected to be called; used for the duplicate guard
COVER = "https://cdn.jsdelivr.net/gh/lm203688/aishield@main/docs/assets/aishield-cover.png"
# COVER is optional in the API. It is only sent when the URL is actually reachable,
# so a broken image never blocks the listing. Regenerate with scripts/arena/make_cover.py.


def opt(args, name, default):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def cover_reachable(url, timeout=30):
    """Check a cover URL. Returns True / False / None.

    True  -- HTTP 200 and an image/* content type: safe to publish.
    False -- a REAL negative verdict (HTTP error, or not an image).
    None  -- INCONCLUSIVE: the request never completed at the transport layer.

    The three-way result matters. This machine sits behind a TLS-intercepting
    proxy: `curl --ssl-no-revoke --tlsv1.3` reaches jsDelivr, but python-urllib's
    handshake times out (verified: URLError handshake timeout, while curl returned
    200 image/png for the same URL). Treating that timeout as "cover is broken"
    would silently drop a perfectly good image -- i.e. the check would be measuring
    this laptop, not the URL.
    """
    cmd = ["curl", "-sSL", "--ssl-no-revoke", "--tlsv1.3",
           "-o", os.devnull, "-w", "%{http_code} %{content_type}", url]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:  # noqa: BLE001
        return None
    parts = (p.stdout or "").strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or parts[0] == "000":
        return None                      # transport-level, not a verdict
    code, ctype = int(parts[0]), parts[1]
    if code != 200:
        return False
    return ctype.startswith("image/")


def product_status(token):
    """Report the review state of our product. Returns the STATUS string.

    Reads GET /api/creators/me, which returns BOTH the creator profile and a
    `products` array -- including items that are still `pending` and therefore
    absent from the public catalog. The public catalog is checked too, because a
    `status` field can lag behind actual publication.
    """
    code, cr = ac.req("GET", "/api/creators/me", token=token)
    if code != 200:
        print("[status] GET /api/creators/me -> HTTP %s" % code)
        print("        ", json.dumps(cr, ensure_ascii=False)[:300])
        print("STATUS=absent")
        return "absent"

    creator = cr.get("creator") or {}
    products = cr.get("products") or []
    print("[status] creator @%s (%s)" % (creator.get("handle"), creator.get("displayName")))
    print("[status] own submissions: %d" % len(products))
    mine = []
    for p in products:
        if p.get("slug") == SLUG or "aishield" in json.dumps(p, ensure_ascii=False).lower():
            mine.append(p)
    for p in mine:
        print("         - id=%s slug=%s kind=%s source=%s"
              % (p.get("id"), p.get("slug"), p.get("kind"), p.get("source")))
        print("           status=%s reviewNote=%r" % (p.get("status"), p.get("reviewNote")))
        print("           createdAt=%s publishedAt=%s"
              % (p.get("createdAt"), p.get("publishedAt")))
        print("           siteUrl=%s" % p.get("siteUrl"))
        if "cover" not in p:
            print("           cover: not echoed by this endpoint (cannot confirm from the API)")
    if not mine:
        print("         (no AIShield submission found)")

    # Cross-check the public catalog: does the listing actually resolve for visitors?
    c2, cat = ac.req("GET", "/api/products")
    live = [x for x in ((cat.get("products") or []) if c2 == 200 else [])
            if x.get("slug") == SLUG]
    print("[status] public catalog: HTTP %s, %d products, aishield present=%s"
          % (c2, len(cat.get("products") or []) if c2 == 200 else 0, bool(live)))
    if live:
        print("         live entry: %s" % json.dumps(live[0], ensure_ascii=False)[:300])

    if live:
        status = "published"
    elif mine:
        status = "rejected" if any(p.get("status") == "rejected" for p in mine) else "pending"
    else:
        status = "absent"
    print("STATUS=%s" % status)
    return status


def main():
    args = sys.argv[1:]
    do_submit = "--submit" in args
    name = opt(args, "--name", NAME)
    tagline = opt(args, "--tagline", TAGLINE)
    site_url = opt(args, "--url", SITE_URL)
    kind = opt(args, "--kind", KIND)
    cover = opt(args, "--cover", COVER)

    creds = ac.load_creds()
    token = creds["api_key"]

    if "--status" in args:
        return 0 if product_status(token) != "absent" else 1

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

    # 3. duplicate guard -- one product per domain, so never submit twice.
    existing = [p for p in (cr.get("products") or []) if p.get("slug") == SLUG]
    if existing:
        p = existing[0]
        print("[2b] already submitted: slug=%s status=%s id=%s"
              % (p.get("slug"), p.get("status"), p.get("id")))
        print("     REFUSING to submit again -- Arena allows one product per domain and a")
        print("     second submission would create a duplicate entry. Use --status to watch it.")
        return 1

    payload = {"name": name, "tagline": tagline, "siteUrl": site_url, "kind": kind}
    if cover:
        # The cover is optional; the listing is not. Never let it block publication.
        verdict = cover_reachable(cover)
        if verdict is True:
            payload["cover"] = cover
            print("[3a] cover verified: HTTP 200 image/*")
        elif verdict is False:
            print("[3a] WARN cover returned a real negative verdict -- omitting it.")
            print("     ", cover)
        else:
            # Inconclusive on this machine (TLS-intercepting proxy): keep the cover,
            # but say so instead of pretending it was verified.
            payload["cover"] = cover
            print("[3a] WARN cover reachability INCONCLUSIVE from here (transport error).")
            print("      Including it anyway; verify in a browser:", cover)
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
