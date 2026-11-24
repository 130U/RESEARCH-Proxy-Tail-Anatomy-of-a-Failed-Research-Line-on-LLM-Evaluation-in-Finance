"""Regression cases for source precision; run with unittest discover."""
import unittest
from fractions import Fraction as F

from analyze import bind, tokens, analyze_one


def record(table, original, program, gold, question="What is the amount?", answer="10", exe_ans=10):
    return dict(id="fixture", table=table, table_ori=original, pre_text=[],post_text=[],
                qa=dict(question=question,program=program,gold_inds=gold,answer=answer,exe_ans=exe_ans))


class SourceBindingTests(unittest.TestCase):
    def test_original_negative_and_trailing_zero(self):
        v=tokens("$(1,234.50)","cell","money",table=True)[0]
        self.assertEqual(v["value"], F(-2469,2))
        self.assertEqual(v["half"],F(1,200))
        self.assertEqual(v["sig"],6)

    def test_dash_is_not_2014(self):
        self.assertEqual(tokens("—","cell","money",table=True),[])

    def test_leading_decimal_and_normalized_percentage_duplicate(self):
        v=tokens(".635","answer","answer",table=True)[0]
        self.assertEqual(v["half"],F(1,2000))
        v=tokens("hedged 60% ( 60 % ) of purchases", "text", "text")
        self.assertEqual([x["value"] for x in v],[F(60)])

    def test_multi_header_matches_label_not_physical_row(self):
        r=record([["metric","2018"],["revenue","12.0"]],
                 [["","year"],["metric","2018"],["Revenue","12.0"]],
                 "multiply(12.0, const_2)",{"table_1":"revenue 12.0"})
        _,_,p,_=bind(r)
        self.assertEqual(p["x0"]["location"],"table_2:1")
        self.assertFalse(p["x0"]["fallback"])
        self.assertEqual(p["x0"]["half"],"1/20")

    def test_same_numeric_value_two_years_does_not_collapse(self):
        r=record([["metric","2014","2013"],["investment","2.6","2.6"]],
                 [["metric","2014","2013"],["investment","2.6","2.6"]],
                 "subtract(2.6, 2.6)",{"table_1":"investment 2.6 2.6"})
        with self.assertRaisesRegex(ValueError,"same_literal_distinct_roles_possible"):
            bind(r)

    def test_const_vocabulary_can_contain_a_source_value(self):
        r=record([["metric","volume","transactions"],["amex","637","5.0"]],
                 [["metric","volume","transactions"],["amex","637","5.0"]],
                 "divide(637, const_5)",{"table_1":"amex 637 5.0"})
        with self.assertRaisesRegex(ValueError,"constant_source_role_ambiguous"):
            bind(r)

    def test_integer_store_count_is_not_continuous_rounding(self):
        r=record([["region","retail"],["europe","22"],["total","158"]],
                 [["region","retail"],["europe","22"],["total","158"]],
                 "divide(22, 158)",{"table_1":"europe 22","table_2":"total 158"},
                 question="What percentage of retail stores are in Europe?")
        with self.assertRaisesRegex(ValueError,"possibly_exact_count"):
            bind(r)

    def test_declared_dividend_is_not_assumed_rounded(self):
        r=record([["metric","2017"],["dividends declared per common share","2.90"]],
                 [["metric","2017"],["dividends declared per common share","2.90"]],
                 "multiply(2.90, const_2)",{"table_1":"dividends declared per common share 2.90"})
        with self.assertRaisesRegex(ValueError,"possibly_exact_or_semantic_quantity"):
            bind(r)


if __name__=="__main__":
    unittest.main()
