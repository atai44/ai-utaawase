"""Merge schedule + raw stage records into data/utaawase.json (what the site reads)."""
import json, os

def R(f):
    p = f"data/raw/{f}"
    return json.load(open(p)) if os.path.exists(p) else None

s = json.load(open("data/schedule.json"))
poems, judg = R("02_poems.json"), R("03_judgments.json")
for r in s["rounds"]:
    for side in ("left", "right"):
        src = (poems or {}).get(side, {}).get(r[side]["model"], [])
        p = next((x for x in src if x["ban"] == r["ban"]), None)
        r[side].update(waka=p["waka"] if p else "", yomi=p["yomi"] if p else "")
    r["judgments"] = [dict(judge=j, pick=x["pick"], comment=x["comment"])
                      for j, xs in (judg or {"judges": {}})["judges"].items() for x in xs if x["ban"] == r["ban"]]
    if r["judgments"]:
        l = sum(j["pick"] == "left" for j in r["judgments"])
        r["winner"] = "left" if l * 2 > len(r["judgments"]) else "right"
out = dict(
    meta=dict(title="AI歌合", date="2026-11-25", ban=len(s["rounds"]), seed=s["seed"], effort="medium",
              rules=["兼題。左右とも事前に独立して詠み、相手方の歌は見ない",
                     "判は作者を伏せて行う（判者が知るのは題と左右のみ）",
                     "持なし・三判者の多数決"]),
    judges=[dict(id=m, model=m) for m in ("fable", "opus", "sonnet")],
    teams={t: ["fable", "opus", "sonnet", "haiku"] for t in ("left", "right")},
    rounds=s["rounds"])
json.dump(out, open("data/utaawase.json", "w"), ensure_ascii=False, indent=1)
print("rounds", len(out["rounds"]), "judged", sum(bool(r["judgments"]) for r in out["rounds"]))
