import numpy as np

from landed import model, rank

CFG = dict(n_quotes=6, mix=[0.4, 0.35, 0.25], inco=[0.3, 0.3, 0.2, 0.2], hs_wrong=0.2, fake=0.08)
NEED = {"cat": "connector", "n": 500, "need_in": 20, "quotes": []}


def quote(**kw):
    q = {"kind": "authorized", "price": 1.0, "break": (10 ** 9, 1.0), "moq": 1, "lead": 10, "incoterm": "DDP", "hs_wrong": False, "stated_freight": 0.0}
    q.update(kw)
    return q


def test_duty_formula_stacks_surcharge_and_igst():
    assert abs(model.duty(1000.0, 0.10) - (100 + 10 + (1000 + 110) * 0.18)) < 1e-9
    assert model.duty(1000.0, 0.0) == 1000 * 0.18


def test_moq_forces_buying_more_than_needed():
    q = quote(moq=5000)
    assert model.parts_cost(q, max(NEED["n"], q["moq"])) == 5000.0
    assert rank.estimate(rank.METHODS[2], NEED, q) > rank.estimate(rank.METHODS[0], NEED, q)


def test_ddp_quote_carries_no_extra_duty_but_exw_does():
    ddp, exw = quote(incoterm="DDP"), quote(incoterm="EXW")
    assert model.true_cost(NEED, exw, CFG)[0] > model.true_cost(NEED, ddp, CFG)[0]


def test_wrong_hs_costs_more_than_a_right_one_under_exw():
    ok, bad = quote(incoterm="EXW"), quote(incoterm="EXW", hs_wrong=True)
    assert model.true_cost(NEED, bad, CFG)[0] > model.true_cost(NEED, ok, CFG)[0]
    assert rank.estimate(rank.METHODS[3], NEED, bad) > rank.estimate(rank.METHODS[2], NEED, bad)


def test_late_quotes_are_filtered_by_the_on_time_baseline():
    need = dict(NEED, quotes=[quote(lead=40, price=0.1), quote(lead=5, price=2.0)])
    pick = int(np.argmin([rank.estimate(rank.METHODS[1], need, q) for q in need["quotes"]]))
    assert pick == 1


def test_true_cost_is_reproducible():
    q = quote(kind="broker", incoterm="EXW")
    assert model.true_cost(NEED, q, CFG) == model.true_cost(NEED, q, CFG)
