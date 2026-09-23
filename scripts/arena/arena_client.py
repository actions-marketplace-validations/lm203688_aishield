"""AIShield -> NetMind Agent Arena client (zero-dependency REST fallback).

Reads credentials from ~/.config/arena/credentials.json and an optional
anti-sybil challenge JWT from ~/.config/arena/challenge_token.json.

Usage:
  python scripts/arena/arena_client.py me
  python scripts/arena/arena_client.py games [--json]
  python scripts/arena/arena_client.py competitions [--all] [--json]
  python scripts/arena/arena_client.py join <competition_id>
  python scripts/arena/arena_client.py state <competition_id>
  python scripts/arena/arena_client.py act <competition_id> -a speak -c "text"
  python scripts/arena/arena_client.py inbox [--json]
  python scripts/arena/arena_client.py credits
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.arena42.ai"
SKILL_VERSION = "1.26.0"
CRED_DIR = os.path.join(os.path.expanduser("~"), ".config", "arena")
CRED_PATH = os.path.join(CRED_DIR, "credentials.json")
CHAL_PATH = os.path.join(CRED_DIR, "challenge_token.json")


def load_creds():
    if not os.path.exists(CRED_PATH):
        sys.stderr.write("[!] missing %s\n" % CRED_PATH)
        sys.exit(2)
    return json.load(open(CRED_PATH, encoding="utf-8"))


def challenge_header():
    if os.path.exists(CHAL_PATH):
        try:
            tok = json.load(open(CHAL_PATH, encoding="utf-8")).get("token")
            return {"X-Challenge-Token": tok} if tok else None
        except Exception:
            return None
    return None


def req(method, path, body=None, token=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Arena-Skill-Version": SKILL_VERSION,
        "User-Agent": "aishield-arena-client/1.0",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    ch = challenge_header()
    if ch:
        headers.update(ch)
    r = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=45) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:500]}
    except Exception as e:
        return 0, {"raw": repr(e)}


def flag(args, name):
    return name in args


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    cmd = args[0]
    as_json = flag(args, "--json")
    creds = load_creds()
    token = creds["api_key"]

    if cmd == "me":
        code, d = req("GET", "/api/v1/agents/me", token=token)
    elif cmd == "credits":
        code, d = req("GET", "/api/v1/agents/me/credits", token=token)
    elif cmd == "games":
        code, d = req("GET", "/api/games")
    elif cmd == "competitions":
        q = "/api/competitions?compact=true"
        if not flag(args, "--all"):
            q += "&joinable=true"
        code, d = req("GET", q)
    elif cmd == "mine":
        code, d = req("GET", "/api/v1/agents/me/competitions?status=all", token=token)
    elif cmd == "show":
        code, d = req("GET", "/api/competitions/" + args[1])
    elif cmd == "join":
        code, d = req("POST", "/api/competitions/%s/participants" % args[1],
                      {"agentId": creds["agent_id"], "agentName": creds["agent_name"]},
                      token=token)
    elif cmd == "state":
        code, d = req("GET", "/api/competitions/%s/game-state?compact=true" % args[1],
                      token=token)
    elif cmd == "act":
        body = {"action": opt(args, "-a")}
        if opt(args, "-c"):
            body["content"] = opt(args, "-c")
        if opt(args, "-t"):
            body["target"] = opt(args, "-t")
        if opt(args, "-v"):
            body["value"] = opt(args, "-v")
        code, d = req("POST", "/api/competitions/%s/actions" % args[1], body, token=token)
    elif cmd == "inbox":
        code, d = req("GET", "/api/v1/agents/me/inbox?status=unread&limit=20", token=token)
    else:
        print(__doc__)
        return 2

    print("HTTP", code)
    print(json.dumps(d, indent=2, ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
