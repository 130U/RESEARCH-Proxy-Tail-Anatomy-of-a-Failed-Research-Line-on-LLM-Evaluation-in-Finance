"""Independent document-subset enumeration for fixed-size randomized audits."""
from fractions import Fraction
from itertools import combinations, product
import unittest

from research.planning.randomized_audit import (
    minimum_pooled_audits, minimum_randomized_audits, pooled_srs_risk,
    randomized_risk, sample_concentrated_audit,
)


def documents(N, d):
    return tuple((h, i) for h in range(d) for i in range(N))


def harmful_sets(N, d, r):
    return [frozenset(zip(layers, ids)) for layers in combinations(range(d), r)
            for ids in product(range(N), repeat=r)]


def enumerated_average_lower_bound(N, d, r, m):
    """Minimize average misses over every deterministic m-subset, no formula."""
    bad_sets = harmful_sets(N, d, r)
    averages = [Fraction(sum(not bad.intersection(audit) for bad in bad_sets), len(bad_sets))
                for audit in combinations(documents(N, d), m)]
    return min(averages)


def concentrated_support(N, d, m):
    """Enumerate the complete construction support with equal atom weights."""
    q, t = divmod(m, N)
    support = []
    for full in combinations(range(d), q):
        whole = frozenset((h, i) for h in full for i in range(N))
        if not t:
            support.append(whole)
        else:
            for partial in range(d):
                if partial not in full:
                    for ids in combinations(range(N), t):
                        support.append(whole | frozenset((partial, i) for i in ids))
    return support


class RandomizedAuditTests(unittest.TestCase):
    def test_all_audit_subsets_give_average_lower_bound_and_construction_attains_it(self):
        for N, d, r in ((2, 3, 2), (2, 4, 3), (3, 2, 2), (1, 5, 3), (2, 3, 1)):
            bad_sets = harmful_sets(N, d, r)
            for m in range(N*d+1):
                lower = enumerated_average_lower_bound(N, d, r, m)
                support = concentrated_support(N, d, m)
                per_bad = [Fraction(sum(not bad.intersection(audit) for audit in support), len(support))
                           for bad in bad_sets]
                # Each fixed bad set has the same risk, reaching the lower
                # bound for *every* audit law, not merely a support-average check.
                self.assertTrue(all(value == lower for value in per_bad))
                self.assertEqual(randomized_risk(N, d, r, m), lower)

    def test_pooled_srs_by_actual_sample_outcomes(self):
        for N, d, r in ((2, 3, 2), (3, 2, 2), (1, 5, 3)):
            fixed_bad = harmful_sets(N, d, r)[-1]
            for m in range(N*d+1):
                samples = list(combinations(documents(N, d), m))
                oracle = Fraction(sum(not fixed_bad.intersection(a) for a in samples), len(samples))
                self.assertEqual(pooled_srs_risk(N, d, r, m), oracle)

    def test_minimum_audits_against_independent_exhaustive_scan(self):
        for N, d, r in ((2, 3, 2), (2, 3, 3), (3, 2, 2)):
            for alpha in (Fraction(1, 2), Fraction(1, 5), Fraction(1, 20)):
                randomized_oracle = next(m for m in range(N*d+1)
                    if enumerated_average_lower_bound(N, d, r, m) <= alpha)
                fixed_bad = harmful_sets(N, d, r)[0]
                pooled_oracle = None
                for m in range(N*d+1):
                    draws = list(combinations(documents(N, d), m))
                    miss = Fraction(sum(not fixed_bad.intersection(a) for a in draws), len(draws))
                    if miss <= alpha:
                        pooled_oracle = m
                        break
                self.assertEqual(minimum_randomized_audits(N, d, r, alpha), randomized_oracle)
                self.assertEqual(minimum_pooled_audits(N, d, r, alpha), pooled_oracle)

    def test_known_strict_example_and_boundaries(self):
        self.assertEqual(minimum_randomized_audits(2, 3, 2), 4)
        self.assertEqual(minimum_pooled_audits(2, 3, 2), 5)
        self.assertEqual(minimum_randomized_audits(2, 3, 3), 2)
        self.assertEqual(minimum_pooled_audits(2, 3, 3), 3)
        for N, d, r in ((1, 1, 1), (2, 3, 1), (2, 3, 3), (3, 4, 2)):
            previous = Fraction(1)
            for m in range(N*d+1):
                risk = randomized_risk(N, d, r, m)
                self.assertLessEqual(risk, previous)
                self.assertLessEqual(risk, pooled_srs_risk(N, d, r, m))
                previous = risk
                if r == 1:
                    self.assertEqual(risk, Fraction(N*d-m, N*d))
            self.assertEqual(randomized_risk(N, d, r, 0), 1)
            self.assertEqual(randomized_risk(N, d, r, N*d), 0)
        for d in range(1, 6):
            for r in range(1, d+1):
                for m in range(d+1):
                    self.assertEqual(randomized_risk(1, d, r, m), pooled_srs_risk(1, d, r, m))

    def test_sampler_unique_size_concentration_and_replay(self):
        for N, d in ((1, 3), (2, 3), (3, 2)):
            for m in range(N*d+1):
                for seed in (0, 1, 130):
                    sample = sample_concentrated_audit(N, d, m, seed=seed)
                    self.assertEqual(sample, sample_concentrated_audit(N, d, m, seed=seed))
                    self.assertEqual(len(sample), m)
                    self.assertEqual(len(set(sample)), m)
                    self.assertEqual(tuple(sorted(sample)), sample)
                    self.assertTrue(set(sample).issubset(documents(N, d)))
                    counts = [sum(h == layer for h, i in sample) for layer in range(d)]
                    q, t = divmod(m, N)
                    self.assertEqual(sum(count == N for count in counts), q)
                    self.assertEqual(sorted(count for count in counts if 0 < count < N), [t] if t else [])

    def test_invalid_inputs_and_sampler_budget_fail_closed(self):
        for risk in (randomized_risk, pooled_srs_risk):
            for args in ((0, 2, 1, 0), (1, 0, 1, 0), (1, 2, 0, 0), (1, 2, 3, 0),
                         (True, 2, 1, 0), (1, 2.0, 1, 0), (1, 2, False, 0),
                         (1, 2, 1, 0.0), (1, 2, 1, True), (1, 2, 1, -1), (1, 2, 1, 3),
                         (1, 2, 1, None)):
                with self.assertRaises(ValueError):
                    risk(*args)
        for minimum in (minimum_randomized_audits, minimum_pooled_audits):
            for alpha in (True, 0.05, 0, 1, '1/0', '1e1000000000'):
                with self.assertRaises(ValueError):
                    minimum(2, 3, 2, alpha)
        for seed in (True, 0.0, -1):
            with self.assertRaises(ValueError):
                sample_concentrated_audit(2, 3, 3, seed=seed)
        with self.assertRaises(ValueError):
            sample_concentrated_audit(2, 3, 4, max_output=3)
        with self.assertRaises(ValueError):
            sample_concentrated_audit(2, 3, 0, max_output=True)


if __name__ == '__main__':
    unittest.main()
