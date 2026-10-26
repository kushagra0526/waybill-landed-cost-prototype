"""Four ways to pick a quote. Each sees only what a quote document shows: price, price break, MOQ, incoterm, lead time, channel, stated freight and the HS code the supplier wrote."""
import numpy as np

from . import model

METHODS = ["lowest unit price", "lowest price + stated freight among quotes that meet the date", "landed cost (as quoted)", "landed cost + HS check + channel risk"]
PRIOR_FAKE = 0.08


def estimate(method, need, q):
    n, cat = need["n"], need["cat"]
    if method == METHODS[0]:
        return model.parts_cost(q, n)
    if method == METHODS[1]:
        late = max(0, q["lead"] + model.TRANSIT_DAYS - need["need_in"])
        return model.parts_cost(q, n) + q["stated_freight"] + (1e9 if late else 0.0) + 1e6 * late
    qty = max(n, q["moq"])
    parts = model.parts_cost(q, qty)
    freight = model.AIR_PER_KG * qty * model.WEIGHT_G[cat] / 1000.0 + 60.0
    buyer_freight = freight if q["incoterm"] in ("EXW", "FOB") else (max(0.0, freight - q["stated_freight"]) if q["incoterm"] == "DAP" else 0.0)
    stated_rate = model.CATS[cat] * (0.5 if q["hs_wrong"] else 1.0)           # the HS code on the quote implies this rate
    av = parts + buyer_freight + (q["stated_freight"] if q["incoterm"] == "DAP" else 0.0)
    if method == METHODS[2]:
        d = 0.0 if q["incoterm"] == "DDP" else model.duty(av, stated_rate)
        late = max(0, q["lead"] + model.TRANSIT_DAYS - need["need_in"])
        return parts + buyer_freight + d + model.LATE_DAY * late
    d = 0.0 if q["incoterm"] == "DDP" else model.duty(av, model.CATS[cat])
    delay = 0
    if q["hs_wrong"] and q["incoterm"] != "DDP":
        d *= 1.10
        delay = 5
    p_fake = PRIOR_FAKE if q["kind"] == "broker" else 0.003
    late = max(0, q["lead"] + model.TRANSIT_DAYS + delay - need["need_in"])
    return parts + buyer_freight + d + p_fake * (parts + 21 * model.LATE_DAY) + model.LATE_DAY * late
