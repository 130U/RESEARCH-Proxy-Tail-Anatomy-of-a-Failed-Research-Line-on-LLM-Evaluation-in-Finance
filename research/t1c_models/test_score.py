"""Tests of scoring semantics that could change the scientific conclusion."""
import importlib.util
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import score
import analyze
T1=ROOT.parents[2]/'proxy-tail/research/t1_rounding'
core=score.load_module('test_t1c_core',T1/'interval_core.py')

def item(steps,lo=1,hi=3):
    return {'steps':steps,'input_intervals':{'x0':{'lo':{'exact':str(lo)},'hi':{'exact':str(hi)}}}}

class ScoringTests(unittest.TestCase):
    def test_dependent_interval_hit_is_not_attainability(self):
        # The natural outer interval is [-2,2], but f(x)=x-x is identically zero.
        result=score.attainable(item([['subtract','x0','x0']]),F(1),core)
        self.assertTrue(result['outer_hit'])
        self.assertFalse(result['certified'])

    def test_bracketing_proves_real_interior_value(self):
        result=score.attainable(item([['divide','const_1','x0']]),F(2,3),core)
        self.assertTrue(result['certified'])
        self.assertEqual(result['certificate']['kind'],'continuous_segment_IVT')

    def test_boundary_not_falsely_called_strictly_interior(self):
        result=score.attainable(item([['add','x0','const_0']]),F(1),core)
        self.assertTrue(result['outer_hit'])
        self.assertFalse(result['certified'])

    def test_reject_pole(self):
        with self.assertRaises(core.IntervalDomainError):
            score.attainable(item([['divide','const_1','x0']],-1,1),F(0),core)

    def test_ast_does_not_execute_code(self):
        for s in ['__import__("os").getcwd()','(1).__class__','[x for x in [1]]','True','2**99999']:
            with self.assertRaises(ValueError):score.parse_expression(s)

    def test_exact_calculation_differs_from_printed_rounding(self):
        tree=score.parse_expression('(137-133)/133*100')
        y=score.run_tree(tree)/100
        self.assertEqual(y,F(4,133))
        self.assertNotEqual(round(float(y),5),round(.03,5))
        self.assertLess(abs(y-F(3,100)),abs(y)/100)

    def test_signed_expression_and_half_even_display(self):
        self.assertEqual(score.run_tree(score.parse_expression('(-3.5 - -5.3) / -5.3')),F(-18,53))
        self.assertEqual(score.round_places(F('1.25'),1),F('1.2'))
        self.assertEqual(score.round_places(F('-1.35'),1),F('-1.4'))

    def test_official_dsl_execution_matches_its_own_float_semantics(self):
        official=score.load_module('test_finqa_official',T1/'data/finqa/evaluate.py')
        for expression in ['223.82/195.02','(137-133)/133','(2.1+3.7+3.0)/3','-3.5','2**3']:
            tree=score.parse_expression(expression)
            invalid,result=official.eval_program(score.dsl_tokens(tree),[])
            self.assertFalse(invalid)
            self.assertEqual(result,round(score.run_tree(tree,float),5))

    def test_shared_page_bootstrap_keeps_cross_group_dependence(self):
        rows=[]
        for page,correct in [('p1',True),('p2',False),('p3',True)]:
            for group in ('witness','control'):
                rows.append({'page_id':page,'group':group,'parse_status':'ok','expression_scores':{'official':correct}})
        result=analyze.cluster_bootstrap(rows,'expression','official',draws=1000)
        self.assertEqual(result['ci95'],[0.0,0.0])
        self.assertEqual(result['error_difference'],0.0)

    def test_abstention_keeps_available_display_denominator(self):
        row={'call_id':'truncated','parse_status':'error','expression_scores':{'official':False,'relative_1pct':False,'display':False}}
        self.assertIs(analyze.accepted(row,'expression','display'),False)
        review={'truncated':{'primary_cause':'unresolved'}}
        self.assertEqual(analyze.cause(row,'expression','official',review),'unresolved')
        row['expression_scores']['display']=None
        self.assertIsNone(analyze.accepted(row,'expression','display'))

    def test_growth_budget_is_invariant_to_reporting_a_decline_magnitude(self):
        import math
        row={'input_provenance':{'a':{'value':'133','half':'1/2'},'b':{'value':'137','half':'1/2'}},
             'input_intervals':{'a':{},'b':{}}}
        budgets=[]
        for sign,operands in [(1,('b','a')),(-1,('a','b'))]:
            row['steps']=[['subtract',*operands],['divide','#0','a']]
            row['center']={'exact':str(sign*F(4,133))}
            row['relative_1pct']={'enclosure':{'lo':{'exact':'1/100' if sign==1 else '-1/20'},'hi':{'exact':'1/20' if sign==1 else '-1/100'}}}
            measured=score.precision(row,'3.0',core)
            budgets.append(measured['t1a_precision_budget'])
            self.assertAlmostEqual(measured['t1a_first_order_budget'],-math.log10(135/532))
            self.assertGreater(measured['t1a_first_order_budget'],measured['t1a_precision_budget'])
        self.assertAlmostEqual(budgets[0],-math.log10(135/530))
        self.assertEqual(budgets[0],budgets[1])

    def test_declared_currency_units_map_to_source_execution_units(self):
        overrides={'Q377':{'reference_money_magnitude':'1000000000','reason':'source operands explicitly billions'}}
        for unit,value in [('million dollars','1400'),('billion dollars','1.4'),('USD','1400000000')]:
            factor,_=score.scale_response({'call_id':'Q377'},unit,overrides)
            self.assertEqual(F(value)*factor,F('1.4'))
        with self.assertRaises(ValueError):score.scale_response({'call_id':'Q377'},'million shares',overrides)

if __name__=='__main__':unittest.main()
