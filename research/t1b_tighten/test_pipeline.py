import unittest
from fractions import Fraction as F
from prepare import cell_number,table_facts
from run_audit import build_model
from exact_solver import solve_range,verify_result

class PipelineTests(unittest.TestCase):
    def test_certificate_survives_variable_order_change(self):
        bounds={'z':(F(10),F(12)),'a':(F(3),F(4))}
        steps=[('divide','z','a')];band=(F(3),F(4))
        result=solve_range(bounds,[],steps,band)
        self.assertTrue(verify_result(dict(reversed(list(bounds.items()))),[],steps,band,result))

    def test_financial_negative_and_point_unit(self):
        self.assertEqual(cell_number('$(1,874)'),(F(-1874),F(1,2)))
        self.assertEqual(cell_number('4 pt'),(F(4),F(1,2)))
        self.assertEqual(cell_number('3.0%',allow_percent=True),(F(3),F(1,20)))
        self.assertIsNone(cell_number('—'))

    def test_data_first_row_and_header_year(self):
        d={'table_ori':[['Opening balance','5.5'],['Addition','0.5']]}
        self.assertIn('table_0:1',table_facts(d))
        self.assertNotIn('table_0:1',table_facts({'table_ori':[['','2018'],['Total','123']]}))

    def test_signed_duplicate_ties_table_fact(self):
        packet={'id':'synthetic','document':{'table_ori':[['','2018'],['Loss','(1,201)']]},
         'audit':{'input_intervals':{'x0':{'lo':{'exact':'23/20'},'hi':{'exact':'5/4'}}},
          'input_provenance':{'x0':{'location':'text_0:0','value':'6/5','half':'1/20'}}}}
        review={'duplicates':[{'variable':'x0','lo':'2401/2000','hi':'2403/2000','location':'table_1:1','scale':'-1/1000','reason':'loss magnitude'}],
                'equations':[],'extra_bounds':{}}
        bounds,eq,_=build_model(packet,review,2)
        self.assertEqual(bounds['x0'],(F(2401,2000),F(2403,2000)))
        self.assertIn({'x0':F(1),'table_1:1':F(1,1000)},eq)

if __name__=='__main__':unittest.main()
