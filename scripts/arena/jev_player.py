#!/usr/bin/env python3
"""Jev-driven NetMind Arena player.

ARCHITECTURE
------------
Jev is a System One model: it answers one typed question about a state. It cannot
maintain a map, a turn history, or a plan — and the arena games explicitly require
all three (fog-maze: "You MUST maintain your own position estimate"; machine-room:
"the full history of resolved turns"). So the split is:

    code holds structure  ->  enumerate legal actions and candidate ids from state
    Jev makes the call    ->  pick the action, pick the target, set the magnitude

That is the decomposition the TypeSafe docs prescribe ("atomic questions,
composed in code"), and it is the only way a stateless decision model can play.

HONESTY NOTE
------------
`selftest` exercises the real decision path against the live Jev API, but feeds it
a SYNTHETIC state (constructed from each game's documented field names) because no
live match was open when this was written. It validates the plumbing and the
question design — NOT win rate. Do not read it as a performance claim.

USAGE
-----
  python scripts/arena/jev_player.py selftest
  python scripts/arena/jev_player.py play <competition_id> [--max-turns 30]
  python scripts/arena/jev_player.py tick [--max-joins 3]
"""
import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "typesafe"))

import arena_client as arena  # noqa: E402
import jev_client as jev  # noqa: E402

# Legal actions per game type, transcribed from `arena rules <type>`.
# `ids` names the pattern used to harvest candidate arguments from the state.
CATALOG = {
    "echo": {
        "actions": {
            "set_valve": {"desc": "Set your own valve. Lower = less output now, less fatigue later.", "ids": "valve", "numeric": True},
            "inspect": {"desc": "Spend this turn reading that pipe's fatigue and its limit.", "ids": "pipe"},
            "reinforce": {"desc": "Raise a pipe's capacity. Cheap, does NOT clear existing fatigue.", "ids": "pipe"},
            "repair": {"desc": "Mend a pipe. Takes several turns, carries nothing meanwhile, clears fatigue.", "ids": "pipe"},
            "pass": {"desc": "Do nothing this turn.", "ids": None},
        },
        "numeric": {"field": "setting", "low": "valve fully closed, zero output", "high": "valve fully open, maximum output and maximum fatigue risk"},
    },
    "point-of-no-return": {
        "actions": {
            "move": {"desc": "Move one cell.", "ids": None, "dirs": True},
            "inspect": {"desc": "Learn an object's kind and which structures it belongs to. Costs a turn.", "ids": "object"},
            "pick": {"desc": "Carry an object. One at a time.", "ids": "object"},
            "drop": {"desc": "Put down what you are carrying.", "ids": None},
            "assemble": {"desc": "Complete a structure and take its reward. Pays much more than salvage.", "ids": "structure"},
            "salvage": {"desc": "Break an object down for an immediate but small payout. MAY be permanent.", "ids": "object"},
            "smelt": {"desc": "Break an object down for an immediate payout. MAY be permanent.", "ids": "object"},
            "sell": {"desc": "Break an object down for an immediate payout. MAY be permanent.", "ids": "object"},
        },
        "kill_warning": "Several of these are irreversible: destroying a load-bearing object makes its structure uncompletable for everyone for the rest of the match.",
    },
    "machine-room": {
        "actions": {
            "operate": {"desc": "Operate a control and observe what the gauges do.", "ids": "control"},
            "pass": {"desc": "Do nothing. Five missed turns in a row forfeits the match.", "ids": None},
        },
        "numeric": None,
    },
    "fog-maze": {
        "actions": {"move": {"desc": "Move one cell in a direction. A failed move wastes the turn and does not change your position.", "ids": None, "dirs": True}},
    },
}

ID_PATTERNS = {
    "pipe": r"\bP\d+\b",
    "valve": r"\bV\d+\b",
    "control": r"\bC\d+\b",
    "object": r"\bO\d+\b",
    "structure": r"\bS\d+\b",
    "participant": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
}

DIRECTIONS = ["up", "down", "left", "right"]


def harvest_ids(state, kind):
    """Code holds structure: pull candidate argument ids out of the state."""
    if not kind:
        return []
    blob = json.dumps(state, ensure_ascii=False)
    return sorted(set(re.findall(ID_PATTERNS[kind], blob)))


def build_questions(game_type, state, history):
    """Two atomic questions: which action, and against which target."""
    spec = CATALOG[game_type]
    action_criteria = {}
    for name, meta in spec["actions"].items():
        action_criteria[name] = meta["desc"]

    stem = "You are playing the '%s' competition. Current state: %s" % (
        game_type, json.dumps(state, ensure_ascii=False))
    if spec.get("kill_warning"):
        stem += " Important: " + spec["kill_warning"]
    if history:
        stem += " Your recent turns: " + " | ".join(history[-6:])

    qs = {
        "action": {
            "type": "choice",
            "instructions": "Given the state and your recent turns, which single action should you take THIS turn to maximise your final score?",
            "criteria": action_criteria,
        }
    }
    return stem, qs, action_criteria


def build_target_question(game_type, action, state, history):
    ids = harvest_ids(state, CATALOG[game_type]["actions"].get(action, {}).get("ids"))
    if not ids:
        return None, []
    return {
        "type": "choice",
        "instructions": "Which one of these should the action '%s' be applied to this turn?" % action,
        "criteria": {i: "candidate id " + i for i in ids},
    }, ids


def _score_to_pct(value, levels):
    """Map a Score position back into 0-100.

    NOTE: Jev's Score primitive accepts AT MOST 10 levels (HTTP 400
    "Too many score levels. Must have at most 10 levels." on 11). Numeric
    magnitudes therefore go through Choice, not Score — see decide().
    """
    if value is None:
        return 50
    return int(max(0, min(100, round(value * 100.0 / max(1, len(levels) - 1)))))


def decide(game_type, state, history=None):
    """Return (action_name, parameters, rationale_dict). Raises on API failure."""
    history = history or []
    key = jev.load_key()
    stem, qs, _ = build_questions(game_type, state, history)
    code, body, _ = jev.call(stem, qs, key=key)
    if code != 200:
        raise RuntimeError("Jev action call failed HTTP %s: %s" % (
            code, json.dumps(body, ensure_ascii=False)[:300]))
    ans = (body.get("answers") or {}).get("action") or {}
    action = ans.get("choice")
    if action not in CATALOG[game_type]["actions"]:
        action = "pass" if "pass" in CATALOG[game_type]["actions"] else \
            list(CATALOG[game_type]["actions"])[0]
    trace = {"action": action, "action_confidence": ans.get("confidence"),
             "action_probs": ans.get("probabilities")}

    params = {}
    meta = CATALOG[game_type]["actions"][action]

    # target id — fail-closed: a dropped parameter yields an invalid payload,
    # so never swallow an error here.
    tq, ids = build_target_question(game_type, action, state, history)
    if tq:
        code, body, _ = jev.call(stem, {"target": tq}, key=key)
        if code != 200:
            raise RuntimeError("Jev target call failed HTTP %s: %s" % (
                code, json.dumps(body, ensure_ascii=False)[:300]))
        t = (body.get("answers") or {}).get("target") or {}
        if t.get("choice") not in ids:
            raise RuntimeError("Jev target answer %r not among %s" % (t.get("choice"), ids))
        params["target_choice"] = t["choice"]
        trace["target_confidence"] = t.get("confidence")

    # direction
    if meta.get("dirs"):
        dq = {"dir": {"type": "choice", "instructions": "Which direction should you move this turn?",
                      "criteria": {d: "move " + d for d in DIRECTIONS}}}
        code, body, _ = jev.call(stem, dq, key=key)
        if code != 200:
            raise RuntimeError("Jev direction call failed HTTP %s: %s" % (
                code, json.dumps(body, ensure_ascii=False)[:300]))
        d = (body.get("answers") or {}).get("dir") or {}
        if d.get("choice") not in DIRECTIONS:
            raise RuntimeError("Jev direction answer %r not in %s" % (d.get("choice"), DIRECTIONS))
        params["dir"] = d["choice"]
        trace["dir_confidence"] = d.get("confidence")

    # numeric magnitude
    # Why Choice and not Score: /v1/systemone rejects Score rubrics longer than
    # 10 levels ("Too many score levels. Must have at most 10 levels."), and a
    # 0-100 valve setting needs 11 discrete stops. Choice allows up to 255
    # options, so we let the model pick the setting directly and read the label
    # back as the number — no interpolation, no silent parameter loss.
    num = CATALOG[game_type].get("numeric")
    if meta.get("numeric") and num:
        stops = [str(i) for i in range(0, 101, 10)]  # 11 stops, 0..100
        nq = {"value": {"type": "choice",
                        "instructions": "Choose the %s for this turn. %s = %s; %s = %s. Weigh immediate output against fatigue that will arrive many turns later." % (
                            num["field"], stops[0], num["low"], stops[-1], num["high"]),
                        "criteria": {s: "%s = %s" % (num["field"], s) for s in stops}}}
        code, body, _ = jev.call(stem, nq, key=key)
        if code != 200:
            raise RuntimeError("Jev numeric call failed HTTP %s: %s" % (
                code, json.dumps(body, ensure_ascii=False)[:300]))
        v = (body.get("answers") or {}).get("value") or {}
        chosen = v.get("choice")
        if chosen in stops:
            params[num["field"]] = int(chosen)
            trace["value_raw"] = chosen
            trace["value_confidence"] = v.get("confidence")
        else:
            raise RuntimeError("Jev numeric answer %r not in %s" % (chosen, stops))

    return action, params, trace


def to_api_params(game_type, action, params, state):
    """Translate harvested ids into the concrete parameter names the game expects."""
    spec = CATALOG[game_type]["actions"][action]
    out = {}
    target = params.get("target_choice")
    kind = spec.get("ids")
    named = {"pipe": "pipeId", "valve": "valveId", "control": "controlId",
             "object": "objectId", "structure": "structureId"}
    if target and kind in named:
        out[named[kind]] = target
    if "dir" in params:
        out["dir"] = params["dir"]
    for k in ("setting",):
        if k in params:
            out[k] = params[k]
    return out


# --- synthetic states for selftest, shaped from each game's documented fields ---
SYNTHETIC = {
    "echo": {"turn": 12, "yourValve": "V1", "valves": {"V1": {"setting": 70}}, "pipes": [
        {"id": "P3", "capacity": 40, "pressure": 33}, {"id": "P7", "capacity": 20, "pressure": 19},
        {"id": "P9", "capacity": 60, "pressure": 12}],
        "output": 31, "note": "P7 is at 95% of capacity and has been rising for four turns."},
    "point-of-no-return": {"turn": 22, "carrying": None, "you": {"x": 3, "y": 4},
                           "visible": [{"id": "O7", "kind": "pipe"}, {"id": "O11", "kind": "plate"}],
                           "structures": [{"id": "S2", "needs": ["O7", "O11"], "reward": 300}],
                           "note": "You looked up S2 last turn; O7 and O11 are both within reach."},
    "machine-room": {"turn": 9, "gauges": {"G1": {"value": 42, "min": 0, "max": 100, "target": 60}},
                     "controls": [{"id": "C3", "name": "Auxiliary Boost", "cooldown": 0, "jammed": False},
                                  {"id": "C5", "name": "Coolant Dump", "cooldown": 2, "jammed": False}],
                     "history": [{"turn": 8, "operated": "C3", "G1": 38}]},
    "fog-maze": {"turn": 30, "turnLimit": 120, "surroundings": [
        {"dx": -1, "dy": 0, "terrain": "floor"}, {"dx": 0, "dy": -1, "terrain": "wall"},
        {"dx": 1, "dy": 0, "terrain": "door", "mark": "red"}, {"dx": 0, "dy": 1, "terrain": "floor"}],
        "keysHeld": ["red"], "doorsOpen": 2, "doorsTotal": 9},
}


def cmd_selftest(args):
    ok = True
    for gt, st in SYNTHETIC.items():
        print("=" * 72)
        print("%s  (SYNTHETIC state — plumbing test, not a win-rate claim)" % gt)
        try:
            action, params, trace = decide(gt, st)
            api = to_api_params(gt, action, params, st)
            print("  chosen action :", action)
            print("  params        :", json.dumps(params, ensure_ascii=False))
            print("  api payload   :", json.dumps({"action": action, "parameters": api}, ensure_ascii=False))
            print("  confidence    :", trace.get("action_confidence"),
                  "| probs:", json.dumps(trace.get("action_probs"), ensure_ascii=False))
        except Exception as e:
            ok = False
            print("  FAILED:", e)
    print("=" * 72)
    print("selftest:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def play_one(cid, state, history):
    gt = state.get("type") or state.get("game_type")
    if gt not in CATALOG:
        return None
    action, params, trace = decide(gt, state, history)
    api = to_api_params(gt, action, params, state)
    code, resp = arena.req("POST", "/api/competitions/%s/actions" % cid,
                           {"action": action, "parameters": api},
                           token=arena.load_creds()["api_key"])
    print("  -> %s %s HTTP %s %s" % (action, json.dumps(api, ensure_ascii=False), code,
                                     json.dumps(resp, ensure_ascii=False)[:160]))
    return {"action": action, "parameters": api, "http": code, "trace": trace}


def cmd_play(args):
    tok = arena.load_creds()["api_key"]
    history = []
    for turn in range(args.max_turns):
        code, st = arena.req("GET", "/api/competitions/%s/game-state?compact=true" % args.competition_id, token=tok)
        if code != 200:
            print("state HTTP", code, json.dumps(st, ensure_ascii=False)[:200]); return 1
        status = st.get("status")
        you = st.get("you") or {}
        print("[turn %d] status=%s round=%s can_act=%s score=%s" % (
            turn, status, st.get("round"), you.get("can_act"), you.get("score")))
        if status == "ended":
            print("match ended."); break
        if not you.get("can_act"):
            time.sleep(args.interval); continue
        # merge the game type into the state so the catalog can dispatch
        code2, detail = arena.req("GET", "/api/competitions/%s" % args.competition_id)
        st = dict(st); st["type"] = (detail or {}).get("type")
        r = play_one(args.competition_id, st, history)
        if r:
            history.append("%s %s" % (r["action"], r["parameters"]))
        time.sleep(args.interval)
    return 0


def cmd_tick(args):
    """Join fresh instances of supported games and take one action in each."""
    tok = arena.load_creds()["api_key"]
    code, d = arena.req("GET", "/api/competitions?joinable=true&compact=true")
    items = (d or {}).get("data") or []
    joined = 0
    for c in items:
        if joined >= args.max_joins:
            break
        if c.get("type") not in CATALOG:
            continue
        if c.get("entry_fee"):
            continue  # zero-cost policy
        cid = c["id"]
        code, join = arena.req("POST", "/api/competitions/%s/participants" % cid,
                               {"agentId": arena.load_creds()["agent_id"],
                                "agentName": arena.load_creds()["agent_name"]}, token=tok)
        print("%-18s %-34s join HTTP %s" % (c.get("type"), str(c.get("name"))[:34], code))
        if code not in (200, 201, 409):
            continue
        joined += 1
        code, st = arena.req("GET", "/api/competitions/%s/game-state?compact=true" % cid, token=tok)
        if code == 200 and (st.get("you") or {}).get("can_act"):
            st = dict(st); st["type"] = c.get("type")
            play_one(cid, st, [])
        time.sleep(0.5)
    print("tick done, acted in %d games" % joined)
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)
    sp = sub.add_parser("play"); sp.add_argument("competition_id")
    sp.add_argument("--max-turns", type=int, default=30); sp.add_argument("--interval", type=float, default=20.0)
    sp.set_defaults(fn=cmd_play)
    sp = sub.add_parser("tick"); sp.add_argument("--max-joins", type=int, default=3); sp.set_defaults(fn=cmd_tick)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
