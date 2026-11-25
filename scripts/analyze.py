"""Significance tests over all published 番. Writes data/analysis.json (contains spoilers)."""
import json, math, random, itertools
import numpy as np
from scipy import stats, optimize
D = json.load(open("data/utaawase.json"))
M = ["fable", "opus", "sonnet", "haiku"]; J = [j["id"] for j in D["judges"]]
R = [dict(r, ev=e["id"]) for e in D["events"] for r in e["rounds"]]
out = dict(events=len(D["events"]), ban=len(R), poems=2 * len(R), judgments=3 * len(R))

# 1. side: does 左 or 右 win more often than chance?
lw = sum(r["winner"] == "left" for r in R)
out["side"] = dict(left_wins=lw, right_wins=len(R) - lw, p=stats.binomtest(lw, len(R), .5).pvalue)

# 2. model strength: Bradley-Terry with a side term, likelihood-ratio test against "all models equal"
y = np.array([r["winner"] == "left" for r in R], float)
X = np.zeros((len(R), 4)); X[:, 0] = 1
for i, r in enumerate(R):
    for k, m in enumerate(M[1:], 1):
        X[i, k] += (r["left"]["model"] == m) - (r["right"]["model"] == m)
def nll(b, X): z = X @ b; return float(np.sum(np.log1p(np.exp(z)) - y * z))
full = optimize.minimize(nll, np.zeros(4), args=(X,), method="BFGS")
null = optimize.minimize(nll, np.zeros(1), args=(X[:, :1],), method="BFGS")
lr = 2 * (null.fun - full.fun)
nm = [r for r in R if r["left"]["model"] != r["right"]["model"]]
rate = {m: [sum(r[r["winner"]]["model"] == m for r in nm), sum(m in (r["left"]["model"], r["right"]["model"]) for r in nm)] for m in M}
out["model"] = dict(lr_chi2=lr, df=3, p=float(stats.chi2.sf(lr, 3)), non_mirror_ban=len(nm), wins_of_appearances=rate,
                    bt_strength_vs_fable=dict(zip(M[1:], map(float, full.x[1:]))), side_logit=float(full.x[0]))
# pairwise head-to-head (binomial, Holm-corrected)
pw = []
for a, b in itertools.combinations(M, 2):
    rs = [r for r in nm if {r["left"]["model"], r["right"]["model"]} == {a, b}]
    wa = sum(r[r["winner"]]["model"] == a for r in rs)
    pw.append([a, b, wa, len(rs) - wa, stats.binomtest(wa, len(rs), .5).pvalue])
order = sorted(range(6), key=lambda i: pw[i][4]); adj = 0
for rank, i in enumerate(order): adj = max(adj, min(1, pw[i][4] * (6 - rank))); pw[i].append(adj)
out["pairwise"] = [dict(a=a, b=b, a_wins=x, b_wins=z, p=p, p_holm=q) for a, b, x, z, p, q in pw]

# 3. judges: agreement, and do they favour poems by their own model?
votes = {j: np.array([next(x["pick"] for x in r["judgments"] if x["judge"] == j) == "left" for r in R], float) for j in J}
n = sum(votes.values()); pe = (n.sum() / (3 * len(R))) ** 2 + (1 - n.sum() / (3 * len(R))) ** 2
pbar = np.mean((n * (n - 1) + (3 - n) * (2 - n)) / 6)
out["judges"] = dict(unanimous=int(np.sum((n == 0) | (n == 3))), fleiss_kappa=float((pbar - pe) / (1 - pe)),
                     left_rate={j: float(votes[j].mean()) for j in J},
                     with_majority={j: float(np.mean(votes[j] == (n >= 2))) for j in J})
self_ = {}
for j in J:
    d = []
    for i, r in enumerate(R):
        l, rt = r["left"]["model"] == j, r["right"]["model"] == j
        if l == rt: continue
        own = votes[j][i] if l else 1 - votes[j][i]
        oth = np.mean([votes[k][i] if l else 1 - votes[k][i] for k in J if k != j])
        d.append(own - oth)
    d = np.array(d); rng = np.random.default_rng(1)
    perm = np.abs((rng.choice([-1, 1], (20000, len(d))) * d).mean(1))
    self_[j] = dict(n=len(d), own_minus_others=float(d.mean()), p=float((np.sum(perm >= abs(d.mean())) + 1) / 20001))
out["self_preference"] = self_
json.dump(out, open("data/analysis.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
