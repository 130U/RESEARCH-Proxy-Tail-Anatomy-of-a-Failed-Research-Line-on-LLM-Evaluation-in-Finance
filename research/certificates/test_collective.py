from fractions import Fraction
from itertools import combinations, product
import random
import unittest

from research.certificates.collective import BudgetExceeded, certify, certify_from_audit


def brute(votes, labels, classes, budget):
    """Independent oracle enumerates replacement vote cells, not count states."""
    n, m = len(labels),len(votes[0])
    results=set()
    for size in range(min(m,budget)+1):
        for changed in combinations(range(m),size):
            for replacement in product(range(classes),repeat=n*size):
                predicted=[]
                for j,row in enumerate(votes):
                    edited=list(row)
                    for slot,head in enumerate(changed): edited[head]=replacement[j*size+slot]
                    predicted.append(max(range(classes),key=lambda c:(edited.count(c),-c)))
                accuracy=Fraction(sum(y==p for y,p in zip(labels,predicted)),n)
                terms=[]
                for c in range(classes):
                    denominator=labels.count(c)+predicted.count(c)
                    numerator=2*sum(y==p==c for y,p in zip(labels,predicted))
                    terms.append(Fraction(numerator,denominator) if denominator else Fraction(0))
                results.add((accuracy,sum(terms)/classes))
    return dict(accuracy=(min(x[0] for x in results),max(x[0] for x in results)),
                macro_f1=(min(x[1] for x in results),max(x[1] for x in results)))


class CollectiveTests(unittest.TestCase):
    def test_audit_chain_two_metrics_share_one_event(self):
        result=certify_from_audit([[0,1],[1,0],[0,1],[1,0]],[0,0,1,1],20,16,0,classes=2,method='exact')
        self.assertEqual(result['audit']['contamination_upper'],1)
        self.assertEqual(result['audit']['joint_coverage_at_least_exact'],'19/20')
        self.assertEqual(result['collective']['macro_f1']['lower_exact'],'1/5')
        contaminated=certify_from_audit([[0,1],[1,0],[0,1],[1,0]],[0,0,1,1],20,16,1,classes=2,method='exact')
        self.assertGreater(contaminated['audit']['contamination_upper'],1)
        self.assertEqual(contaminated['collective']['macro_f1']['lower_exact'],'0')
        with self.assertRaises(ValueError):
            certify_from_audit([[0]],[0],20,16,17)

    def assert_bounds(self, result, truth, equal=False):
        for metric,(lo,hi) in truth.items():
            got=result['collective'][metric]
            lower,upper=Fraction(got['lower_exact']),Fraction(got['upper_exact'])
            self.assertLessEqual(lower,lo)
            self.assertGreaterEqual(upper,hi)
            self.assertLessEqual(Fraction(got['lower']),lower)
            self.assertGreaterEqual(Fraction(got['upper']),upper)
            if equal: self.assertEqual((lower,upper),(lo,hi))
            point=result['independent'][metric]
            self.assertGreaterEqual(lower,Fraction(point['lower_exact']))
            self.assertLessEqual(upper,Fraction(point['upper_exact']))

    def test_exhaustive_binary_small_votes_against_cell_oracle(self):
        for values in product(range(2),repeat=4):
            votes=[list(values[:2]),list(values[2:])]
            for labels in product(range(2),repeat=2):
                for budget in range(4):
                    truth=brute(votes,list(labels),2,budget)
                    exact=certify(votes,labels,2,budget,'exact')
                    outer=certify(votes,labels,2,budget,'component')
                    self.assert_bounds(exact,truth,equal=True)
                    self.assert_bounds(outer,truth)

    def test_three_class_joint_counts_against_cell_oracle(self):
        rng=random.Random(20261115)
        for _ in range(12):
            votes=[[rng.randrange(3) for _ in range(3)] for _ in range(3)]
            labels=[0,1,2]
            for budget in (0,1,2):
                truth=brute(votes,labels,3,budget)
                self.assert_bounds(certify(votes,labels,3,budget,'exact'),truth,equal=True)
                self.assert_bounds(certify(votes,labels,3,budget,'component'),truth)

    def test_shared_budget_strictly_tightens_both_metrics(self):
        result=certify([[0,1],[1,0],[0,1],[1,0]],[0,0,1,1],2,1,'exact')
        self.assertEqual(result['independent']['macro_f1']['lower_exact'],'0')
        self.assertEqual(result['independent']['macro_f1']['upper_exact'],'1')
        self.assertEqual(result['collective']['macro_f1']['lower_exact'],'1/5')
        self.assertEqual(result['collective']['macro_f1']['upper_exact'],'11/15')
        self.assertEqual(result['collective']['accuracy']['lower_exact'],'1/4')
        self.assertEqual(result['collective']['accuracy']['upper_exact'],'3/4')

    def test_component_extrema_are_not_jointly_attainable(self):
        votes=[[1,1,1,2,2],[1,1,1,1,1],[2,2,2,2,2]]
        exact=certify(votes,[0,1,2],3,1,'exact')
        outer=certify(votes,[0,1,2],3,1,'component')
        self.assertEqual(exact['collective']['macro_f1']['lower_exact'],'5/9')
        self.assertEqual(exact['collective']['macro_f1']['upper_exact'],'5/9')
        self.assertEqual(outer['collective']['macro_f1']['lower_exact'],'4/9')
        self.assertEqual(outer['collective']['macro_f1']['upper_exact'],'2/3')

    def test_zero_budget_and_absent_class_convention(self):
        result=certify([[0],[0]],[0,0],3,0,'exact')
        self.assertEqual(result['collective']['accuracy']['lower_exact'],'1')
        self.assertEqual(result['collective']['macro_f1']['lower_exact'],'1/3')

    def test_invalid_inputs_and_search_limits_fail_closed(self):
        for votes,labels,k in [([[0],[0,1]],[0,1],0),([[True]],[0],0),([[0]],[-1],0),
                               ([[0]],[0],-1),([],[],0)]:
            with self.assertRaises(ValueError): certify(votes,labels,3,k)
        with self.assertRaises(BudgetExceeded):
            certify([[0,0,1,1]],[0],3,2,'component',max_subsets=5)
        with self.assertRaises(BudgetExceeded):
            certify([[0]],[0],3,1,'exact',max_states=1)


if __name__=='__main__': unittest.main()
