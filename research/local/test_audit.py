from fractions import Fraction
from itertools import product
from math import comb
import unittest

from research.local.audit import audit_upper, reachable, statistic_interval


class AuditTests(unittest.TestCase):
    def test_outward_rounding_keeps_small_score_terms(self):
        result = statistic_interval([[1],[1],[1]], [[1.0],[1e-16],[1e-16]],0)
        exact = (Fraction(1.0)+2*Fraction(1e-16))/3
        self.assertLessEqual(Fraction(result['lower']),exact)
        self.assertGreaterEqual(Fraction(result['upper']),exact)
        self.assertEqual(Fraction(result['lower_exact']),exact)
        with self.assertRaises(ValueError):
            statistic_interval([[1]],[[float('nan')]],0)

    def test_exact_coverage_all_small_populations(self):
        alpha = Fraction(1, 20)
        for N in range(1, 13):
            for n in range(N+1):
                for K in range(N+1):
                    bad = 0
                    for x in range(max(0,n-N+K), min(n,K)+1):
                        if audit_upper(N,n,x) < K:
                            bad += comb(K,x)*comb(N-K,n-x)
                    self.assertLessEqual(Fraction(bad,comb(N,n)),alpha)

    def test_full_census_and_zero_sample(self):
        self.assertEqual(audit_upper(100,0,0),100)
        for x in range(11):
            self.assertEqual(audit_upper(10,10,x),x)
        for args in [(10,11,0),(10,3,4),(10,-1,0),(True,0,0)]:
            with self.assertRaises(ValueError):
                audit_upper(*args)

    def test_reachable_against_exhaustive_vote_replacements(self):
        for m in range(1,7):
            for a in range(m+1):
                for b in range(m-a+1):
                    counts = [a,b,m-a-b]
                    original = [0]*a+[1]*b+[2]*(m-a-b)
                    for k in range(m+1):
                        truth = set()
                        for changed in product(range(3), repeat=m):
                            if sum(a!=b for a,b in zip(original,changed)) <= k:
                                totals = [changed.count(c) for c in range(3)]
                                truth.add(max(range(3),key=lambda c:(totals[c],-c)))
                        self.assertEqual(set(reachable(counts,k)),truth)


if __name__ == '__main__':
    unittest.main()
