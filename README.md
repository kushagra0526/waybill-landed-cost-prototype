# landed: which quote is really the cheapest for a hardware part?

Waybill builds "one comparison across every quote (true landed cost with freight and duties included, lead time against your date, minimum order quantity, proof the parts are genuine)" (https://www.waybill.to/). Each of those is a field a quote can get wrong or leave out. This prototype is a simulator with a known expected all-in cost per quote that scores four ways of picking one. It is not Waybill's system, and the duty rates, freight rates and prices are invented, not current customs law.

## The setup
`landed/model.py`: a part need (category, quantity, need-by day) and 6 (dev) or 8 (held-out) quotes from authorized sellers, brokers and makers: unit price and a price break, MOQ (makers often force 2-10x the need), Incoterm (EXW, FOB, DAP, DDP), lead time, the supplier's HS code (sometimes wrong, more often from brokers), a stated freight on DAP. True expected cost over random outcomes: parts at the quantity actually bought (MOQ, price break), freight by weight (+-20%), duty stack (basic duty + 10% surcharge + 18% IGST) unless DDP, 70% chance customs catches a wrong HS code (+10% of duty and 5 days), actual lead time +-25%, counterfeit parts (broker rate 8% dev, 14% held-out; 0.3% otherwise) which cost the parts again and 21 days, and 120 per day late.
`landed/rank.py`: four pickers that see only what a quote shows: lowest unit price; lowest price + stated freight among quotes that meet the date; landed cost as quoted (MOQ, price break, freight, duty at the HS code the quote implies, lateness); landed cost + HS check (own category rate, mismatch penalty) + a channel risk prior (8% for brokers).

## Results (1,000 needs each; held-out seeds 1,000,000+, more brokers and DDP, 40% wrong HS, 14% counterfeit; fixed in git before the first run)
| | dev: picked true best | dev: median extra cost | held-out: picked true best | held-out: median / mean extra cost | held-out: late |
|---|---|---|---|---|---|
| lowest unit price | 11% | 269% | 9% | 283% / 636% | 56% |
| lowest price + freight, on time only | 33% | 20% | 23% | 42% / 208% | 5% |
| landed cost (as quoted) | 64% | 0% | 44% | 4% / 97% | 6% |
| landed cost + HS check + channel risk | **84%** | 0% | **77%** | 0% / 6.6% | 7% |
- Lowest unit price is rarely the cheapest all-in: MOQ, duties, lateness and counterfeits dominate. Ranking only among on-time quotes helps a lot but still misses MOQ and duties.
- Computing landed cost from the quote's own fields gets about half the held-out picks right; the rest are lost to a supplier HS code that understates duty and to broker risk, which the quote does not show. The HS check and channel prior close most of that gap.
- The last method has the same cost structure as the simulation (with a different counterfeit rate and noisy outcomes), so its score is near-circular: it shows what each term is worth in this model, not that a real system gets 77%. The mean extra cost is dominated by a few late or counterfeit outcomes.

## Read this before believing the table
All rates, prices and the 120-per-day lateness cost are invented; duty is simplified to one stack. HS classification from the part description is assumed correct in the last method. Nothing says how Waybill ranks quotes.

## Run it (3 commands)
```
pip install numpy pytest
python -m pytest -q tests
python -m landed.run
```
numpy only. 6 tests; the run takes a few seconds.

Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Waybill.
