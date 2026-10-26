import json

import numpy as np

from . import model, rank

CONFIG = {"dev": dict(n_quotes=6, mix=[0.4, 0.35, 0.25], inco=[0.3, 0.3, 0.2, 0.2], hs_wrong=0.2, fake=0.08),
          "held": dict(n_quotes=8, mix=[0.25, 0.55, 0.2], inco=[0.2, 0.2, 0.2, 0.4], hs_wrong=0.4, fake=0.14)}


def score(seeds, cfg):
    acc = {m: {"regret": [], "best": 0, "late": 0, "n": 0} for m in rank.METHODS}
    for s in seeds:
        rng = np.random.default_rng(s)
        need = model.make_need(rng, cfg)
        truth = [model.true_cost(need, q, cfg) for q in need["quotes"]]
        best = min(t[0] for t in truth)
        for m in rank.METHODS:
            pick = int(np.argmin([rank.estimate(m, need, q) for q in need["quotes"]]))
            a = acc[m]
            a["regret"].append(truth[pick][0] / best - 1)
            a["best"] += truth[pick][0] <= best + 1e-9
            a["late"] += truth[pick][1] > 0.5
            a["n"] += 1
    return {m: {"picked_true_best_pct": round(100 * a["best"] / a["n"]), "mean_extra_cost_pct": round(100 * float(np.mean(a["regret"])), 1),
                "median_extra_cost_pct": round(100 * float(np.median(a["regret"])), 1), "late_pct": round(100 * a["late"] / a["n"])} for m, a in acc.items()}


def main():
    res = {"dev": score(range(0, 1000), CONFIG["dev"]), "held_out": score(range(1000000, 1001000), CONFIG["held"])}
    json.dump(res, open("out/result.json", "w"), indent=1)
    for k, v in res.items():
        print(k)
        for m, d in v.items():
            print("  ", m, d)


if __name__ == "__main__":
    main()
