"""Finite synthetic accounting world, with explicitly distinct stance/direction.

Integer currency units avoid floating point accounting discrepancies. Integer
time is a quarter index relative to cutoff 0, not a historical SEC timestamp.
Only the generator reads latent truth; learner inputs are text and labels.
"""
import hashlib
import json
import random


def encode(rows):
    return json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def generate(seed=20261115, companies=30, quarters=20, contamination=0):
    if companies <= 0 or quarters < 2:
        raise ValueError('positive companies and at least two quarters required')
    rng = random.Random(seed)
    verbs = ('opposes', 'is undecided about', 'supports')
    templates = (
        '{holder} {verb} {target} after reviewing the report . Revenue is {revenue} USD .',
        'On {target} , {holder} {verb} the outlook . Reported revenue : {revenue} USD .',
        '{target} reported revenue of {revenue} USD ; {holder} {verb} its prospects .',
    )
    rows = []
    prior = {c: 10000 for c in range(companies)}
    prices = {c: 100.0 for c in range(companies)}
    for q in range(quarters):
        for c in range(companies):
            assets = rng.randint(10000, 100000)
            debt = rng.randint(0, assets)
            revenue = rng.randint(5000, 20000)
            cost = rng.randint(1000, 22000)
            stance = rng.randrange(3)
            direction = (revenue > prior[c]) - (revenue < prior[c]) + 1
            shock = rng.gauss(0, 0.01)
            announcement_effect = 0.005 * (revenue / prior[c] - 1)
            prices[c] *= max(0.1, 1 + shock + announcement_effect)
            holder, target = f'analyst{c % 5}', f'firm{c}'
            template = templates[rng.randrange(len(templates))]
            def render(label):
                return template.format(holder=holder, verb=verbs[label], target=target, revenue=revenue)
            text = render(stance)
            changed = (stance + 1) % 3
            # UP is a metric-axis intervention; it is never a stance constraint.
            higher_revenue = max(revenue, prior[c]) + 100
            edits = [
                dict(permission='INV', text=text + ' The filing has a reference identifier .', stance=stance, axis='stance'),
                dict(permission='LBL', text=text + f' {holder} reiterates that assessment .', stance=stance, axis='stance'),
                dict(permission='REL', text=render(changed), stance=changed, axis='stance'),
                dict(permission='UP', text=text.replace(str(revenue), str(higher_revenue)), stance=stance, metric=2, axis='metric'),
                dict(permission='FREE', text=f'No attributed view of {target} is supplied .', stance=None, axis='stance'),
            ]
            t = q - quarters // 2
            rows.append(dict(id=f'c{c:03d}q{q:03d}', family=f'c{c:03d}q{q:03d}', company=c,
                             quarter=q, available_time=t, recorded_time=t, holder=holder, target=target,
                             text=text, stance=stance, metric=direction, revenue=revenue,
                             prior_revenue=prior[c], cost=cost, profit=revenue-cost,
                             assets=assets, liabilities=debt, equity=assets-debt,
                             unit='USD', scale=1, price=round(prices[c], 10), shock=shock,
                             announcement_effect=announcement_effect, edits=edits, contaminated=False))
            prior[c] = revenue
    candidates = [i for i, d in enumerate(rows) if d['available_time'] > 0]
    if not isinstance(contamination, int) or isinstance(contamination, bool) or not 0 <= contamination <= len(candidates):
        raise ValueError('contamination must be a feasible nonnegative integer')
    for i in rng.sample(candidates, contamination):
        rows[i]['recorded_time'] = 0
        rows[i]['contaminated'] = True
    return rows


def digest(rows):
    return hashlib.sha256(encode(rows)).hexdigest()
