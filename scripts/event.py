"""Run one 歌合 (an "event") stage by stage. Every stage is a set of files under
data/events/NN/, so an interrupted event can be resumed and is never published half-done.

  event.py new            -> create next event, write the 題-suggestion prompt
  event.py schedule NN    -> pick 16 題 from the judges' suggestions, draw matchups, write poet prompts
  event.py sheet NN       -> validate poems, write the blind judge prompt
  event.py finish NN      -> validate judgments, mark complete, rebuild data/utaawase.json
  event.py status         -> stage and missing files of every event
  event.py build          -> rebuild data/utaawase.json from complete events only

Each command prints the agent jobs still to run as: model <TAB> prompt file <TAB> output file.
It never prints poems, authors' results or verdicts.
"""
import json, os, random, sys, glob, datetime

ROOT = os.path.join(os.path.dirname(__file__), "..")
EV = os.path.join(ROOT, "data", "events")
MODELS = ["fable", "opus", "sonnet", "haiku"]
JUDGES = ["fable", "opus", "sonnet"]
SIDES = [("left", "左方"), ("right", "右方")]
BU = ["春", "夏", "秋", "冬", "恋", "雑"]
BU_CAP = {"春": 3, "夏": 3, "秋": 3, "冬": 3, "恋": 4, "雑": 3}
BASE_SEED = 20261125
N = 16

def d(ev, *p): return os.path.join(EV, ev, *p)
def load(path): return json.load(open(path, encoding="utf-8"))
def dump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def write(text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)
def events(): return sorted(os.path.basename(p) for p in glob.glob(os.path.join(EV, "[0-9][0-9]")))
def status(ev): return load(d(ev, "status.json"))
def set_stage(ev, stage, **kw):
    s = status(ev) if os.path.exists(d(ev, "status.json")) else dict(id=int(ev))
    s.update(stage=stage, **kw); dump(s, d(ev, "status.json"))
def rel(p): return os.path.relpath(p, ROOT)
def jobs(ev, items):
    todo = [(m, pr, out) for m, pr, out in items if not os.path.exists(out)]
    for m, pr, out in todo: print(f"{m}\t{os.path.abspath(pr)}\t{os.path.abspath(out)}")
    if not todo: print("(no jobs pending)")

def used_dai(before):
    return [r["dai"] for ev in events() if ev != before and os.path.exists(d(ev, "schedule.json"))
            for r in load(d(ev, "schedule.json"))["rounds"]]

# ---------- stage 1: 題 ----------
def dai_jobs(ev): return [(j, d(ev, "prompts", "dai.txt"), d(ev, f"dai_{j}.json")) for j in JUDGES]
def new():
    ev = f"{(int(events()[-1]) + 1) if events() else 1:02d}"
    used = used_dai(ev)
    write("あなたは歌合の判者の一人です。主催者から、今度の十六番歌合のための題の案を求められました。"
          "四季・恋・雑をとりまぜ、伝統的な題も、やや新味のある結題も含めて、題を八つ提案してください。"
          + (f"\nこれまでの歌合で既に出た次の題は避けてください：{'、'.join(used)}" if used else "")
          + '\n\n次のJSONだけを指定のファイルに書いてください:\n'
          '{"dai":[{"dai":"題","yomi":"よみ","bu":"春|夏|秋|冬|恋|雑","note":"一言の趣意"}]}\n',
          d(ev, "prompts", "dai.txt"))
    set_stage(ev, "dai", started=datetime.date.today().isoformat(), seed=BASE_SEED + int(ev))
    print("event", ev); jobs(ev, dai_jobs(ev))

# ---------- stage 2: schedule + poet prompts ----------
def poet_jobs(ev):
    return [(m, d(ev, "prompts", f"poet_{s}_{m}.txt"), d(ev, f"poems_{s}_{m}.json")) for s, _ in SIDES for m in MODELS]
def schedule(ev):
    rng = random.Random(status(ev)["seed"])
    used, cands = set(used_dai(ev)), []
    for j in JUDGES:
        xs = load(d(ev, f"dai_{j}.json"))["dai"]
        assert len(xs) >= 6, f"{j}: too few 題"
        cands += [dict(x, by=j) for x in xs if x.get("bu") in BU and x.get("dai")]
    rng.shuffle(cands)
    picked, seen = [], set(used)
    for strict in (True, False):  # first pass keeps per-judge and per-部 balance, second pass fills up
        for c in cands:
            if len(picked) == N or c["dai"] in seen: continue
            if strict and (sum(p["by"] == c["by"] for p in picked) >= 6 or sum(p["bu"] == c["bu"] for p in picked) >= BU_CAP[c["bu"]]): continue
            picked.append(c); seen.add(c["dai"])
    assert len(picked) == N, "not enough distinct 題"
    picked.sort(key=lambda c: BU.index(c["bu"]))
    # Latin square: every left poet meets every right poet once; each poet appears once per block of 4
    perm = MODELS[:]; rng.shuffle(perm)
    shifts = [0, 1, 2, 3]; rng.shuffle(shifts)
    pairs = []
    for s in shifts:
        block = [(MODELS[i], perm[(i + s) % 4]) for i in range(4)]; rng.shuffle(block); pairs += block
    rounds = [dict(ban=n + 1, dai=c["dai"], yomi=c.get("yomi", ""), bu=c["bu"], dai_by=c["by"], dai_note=c.get("note", ""),
                   left=l, right=r) for n, (c, (l, r)) in enumerate(zip(picked, pairs))]
    dump(dict(seed=status(ev)["seed"], rounds=rounds), d(ev, "schedule.json"))
    for side, name in SIDES:
        for m in MODELS:
            mine = [r for r in rounds if r[side] == m]
            write(f"あなたは十六番歌合の{name}の歌人です。歌は左右それぞれ事前に独立して詠み、相手方の歌は見られません。"
                  "判は作者を伏せて行われます。次の四つの題それぞれに和歌（五七五七七）を一首ずつ詠んでください。\n"
                  + "\n".join(f'第{r["ban"]}番「{r["dai"]}」（{r["yomi"]}・{r["bu"]}）' for r in mine)
                  + '\n\n次のJSONだけを指定のファイルに書いてください。kuは漢字仮名交じりの五句、yomiはその読みをひらがなで五句:\n'
                  '{"poems":[{"ban":番号,"ku":["初句","二句","三句","四句","結句"],"yomi":["","","","",""]}]}\n',
                  d(ev, "prompts", f"poet_{side}_{m}.txt"))
    set_stage(ev, "poems"); jobs(ev, poet_jobs(ev))

# ---------- stage 3: blind sheet ----------
def poems(ev):
    rounds = load(d(ev, "schedule.json"))["rounds"]
    for r in rounds:
        for side, _ in SIDES:
            m = r[side]
            ps = load(d(ev, f"poems_{side}_{m}.json"))["poems"]
            p = next((x for x in ps if int(x["ban"]) == r["ban"]), None)
            assert p and len(p["ku"]) == 5 and all(p["ku"]), f"bad poem: {side} {m} ban {r['ban']}"
            clean = lambda xs: [str(k).replace(" ", "").replace("　", "") for k in xs]
            r[side] = dict(model=m, ku=clean(p["ku"]), yomi=clean(p.get("yomi", [])))
    return rounds
def judge_jobs(ev): return [(j, d(ev, "prompts", "judge.txt"), d(ev, f"judg_{j}.json")) for j in JUDGES]
def sheet(ev):
    rounds = poems(ev)
    body = "\n".join(f'第{r["ban"]}番「{r["dai"]}」（{r["yomi"]}・{r["bu"]}）\n 左：{"".join(r["left"]["ku"])}\n 右：{"".join(r["right"]["ku"])}' for r in rounds)
    write("あなたは十六番歌合の判者です。歌は兼題で、左右の歌人が事前に独立して詠んだものです。作者はすべて伏せられています。"
          "各番について左右いずれかを勝と定め（持は不可、必ず一方を選ぶ）、短い判詞（一〜二文）を添えてください。"
          "題の本意にかなうか、詞・姿・心を見て判じてください。\n\n" + body
          + '\n\n次のJSONだけを指定のファイルに書いてください（全十六番）:\n'
          '{"judgments":[{"ban":1,"pick":"left または right","comment":"判詞"}]}\n', d(ev, "prompts", "judge.txt"))
    set_stage(ev, "judging"); jobs(ev, judge_jobs(ev))

# ---------- stage 4: finish + build ----------
def judged_rounds(ev):
    rounds = poems(ev)
    for j in JUDGES:
        js = {int(x["ban"]): x for x in load(d(ev, f"judg_{j}.json"))["judgments"]}
        for r in rounds:
            x = js.get(r["ban"])
            assert x and x["pick"] in ("left", "right") and x["comment"].strip(), f"bad judgment: {j} ban {r['ban']}"
            r.setdefault("judgments", []).append(dict(judge=j, pick=x["pick"], comment=x["comment"].strip()))
    for r in rounds:
        r["winner"] = "left" if sum(x["pick"] == "left" for x in r["judgments"]) * 2 > len(JUDGES) else "right"
    return rounds
def finish(ev):
    judged_rounds(ev); set_stage(ev, "complete", finished=datetime.date.today().isoformat()); build()
def build():
    evs = [dict(id=int(ev), date=status(ev).get("finished", ""), seed=status(ev).get("seed"), rounds=judged_rounds(ev))
           for ev in events() if status(ev)["stage"] == "complete"]
    dump(dict(meta=dict(title="AI歌合", effort="medium",
                        rules=["兼題。左右とも事前に独立して詠み、相手方の歌は見ない", "判は作者を伏せて行う（判者が知るのは題と左右のみ）", "持なし・三判者の多数決"]),
              judges=[dict(id=j, model=j) for j in JUDGES], teams={s: MODELS for s, _ in SIDES}, events=evs),
         os.path.join(ROOT, "data", "utaawase.json"))
    print("published events:", [e["id"] for e in evs])
def show():
    for ev in events():
        st = status(ev)["stage"]; print("event", ev, st)
        if st == "dai": jobs(ev, dai_jobs(ev))
        if st == "poems": jobs(ev, poet_jobs(ev))
        if st == "judging": jobs(ev, judge_jobs(ev))

if __name__ == "__main__":
    cmd, arg = sys.argv[1], (f"{int(sys.argv[2]):02d}" if len(sys.argv) > 2 else None)
    {"new": new, "status": show, "build": build}.get(cmd, lambda: globals()[cmd](arg))()
