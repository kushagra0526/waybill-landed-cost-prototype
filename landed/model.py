"""Quotes for one part need from several sources, with a known true all-in cost.

Duty rates, freight rates, counterfeit rates and the cost of a late day are invented for the simulation; they are not current customs law or anyone's prices."""
import zlib

import numpy as np

CATS = {"ic": 0.0, "sensor": 0.05, "passive": 0.10, "motor": 0.10, "connector": 0.15, "mechanical": 0.20}      # illustrative basic duty
BASE = {"ic": 4.0, "sensor": 6.0, "passive": 0.08, "motor": 22.0, "connector": 0.9, "mechanical": 3.5}
WEIGHT_G = {"ic": 2, "sensor": 8, "passive": 0.4, "motor": 250, "connector": 6, "mechanical": 60}
AIR_PER_KG = 9.0
LATE_DAY = 120.0
SWS, IGST = 0.10, 0.18
TRANSIT_DAYS = 5


def duty(av, bcd):
    bcd_amt = av * bcd
    sws = bcd_amt * SWS
    return bcd_amt + sws + (av + bcd_amt + sws) * IGST


def make_need(rng, cfg):
    cat = str(rng.choice(list(CATS)))
    n = int(rng.choice([50, 200, 500, 1500, 5000]) if cat in ("passive", "connector", "ic") else rng.choice([5, 20, 60, 200]))
    quotes = []
    for _ in range(int(cfg["n_quotes"])):
        kind = str(rng.choice(["authorized", "broker", "maker"], p=cfg["mix"]))
        price = BASE[cat] * float(rng.uniform(0.9, 1.2)) * {"authorized": 1.0, "broker": float(rng.uniform(0.65, 0.95)), "maker": float(rng.uniform(0.5, 0.8))}[kind]
        moq = int(rng.choice([1, 1, 10, 100])) if kind != "maker" else int(rng.choice([n, 2 * n, 5 * n, 10 * n]))
        lead = {"authorized": rng.integers(3, 25), "broker": rng.integers(2, 10), "maker": rng.integers(20, 50)}[kind]
        incoterm = str(rng.choice(["EXW", "FOB", "DAP", "DDP"], p=cfg["inco"]))
        hs_wrong = bool(kind == "broker" and rng.random() < cfg["hs_wrong"]) or bool(kind == "maker" and rng.random() < 0.1)
        quotes.append({"kind": kind, "price": float(price), "break": (int(max(moq * 4, 4 * n)), float(price * rng.uniform(0.8, 0.95))), "moq": moq, "lead": int(lead),
                       "incoterm": incoterm, "hs_wrong": hs_wrong, "stated_freight": float(rng.uniform(40, 200)) if incoterm == "DAP" else 0.0})
    return {"cat": cat, "n": n, "need_in": int(rng.integers(8, 45)), "quotes": quotes}


def parts_cost(q, qty):
    p = q["break"][1] if qty >= q["break"][0] else q["price"]
    return p * qty


def true_cost(need, q, cfg, rng=None, draws=300):
    """Expected all-in cost over random outcomes: actual lead time (+-25%), freight (+-20%), whether customs catches a wrong HS code (70%), counterfeit parts (broker rate from cfg)."""
    rng = rng or np.random.default_rng(zlib.crc32(repr((need["cat"], need["n"], q["price"], q["lead"])).encode()))
    qty = max(need["n"], q["moq"])
    parts = parts_cost(q, qty)
    kg = qty * WEIGHT_G[need["cat"]] / 1000.0
    freight = (AIR_PER_KG * kg + 60.0) * rng.lognormal(0, 0.2, draws)
    buyer_freight = freight if q["incoterm"] in ("EXW", "FOB") else (np.maximum(0.0, freight - q["stated_freight"]) if q["incoterm"] == "DAP" else np.zeros(draws))
    av = parts + buyer_freight + (q["stated_freight"] if q["incoterm"] == "DAP" else 0.0)
    d = np.zeros(draws) if q["incoterm"] == "DDP" else duty(av, CATS[need["cat"]])
    caught = (rng.random(draws) < 0.7) & q["hs_wrong"] & (q["incoterm"] != "DDP")
    d = np.where(caught, d * 1.10, d)
    delay = np.where(caught, 5, 0)
    p_fake = cfg["fake"] if q["kind"] == "broker" else 0.003
    fake = rng.random(draws) < p_fake
    lead = q["lead"] * rng.lognormal(0, 0.25, draws)
    late = np.maximum(0.0, lead + TRANSIT_DAYS + delay - need["need_in"]) + fake * 21
    cost = parts + buyer_freight + d + fake * parts + LATE_DAY * late
    return float(cost.mean()), float((late > 0.5).mean())
