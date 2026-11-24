import json
import unittest

from research.local.world import generate, encode


class WorldTests(unittest.TestCase):
    def test_accounting_contamination_and_seed(self):
        a = generate(seed=7, companies=8, quarters=5, contamination=9)
        self.assertEqual(encode(a), encode(generate(seed=7, companies=8, quarters=5, contamination=9)))
        self.assertNotEqual(encode(a), encode(generate(seed=8, companies=8, quarters=5, contamination=9)))
        self.assertEqual(sum(d['contaminated'] for d in a), 9)
        for d in a:
            self.assertEqual(d['assets'], d['liabilities'] + d['equity'])
            self.assertEqual(d['revenue'], d['cost'] + d['profit'])
            if d['contaminated']:
                self.assertLessEqual(d['recorded_time'], 0)
                self.assertGreater(d['available_time'], 0)
            else:
                self.assertEqual(d['recorded_time'], d['available_time'])
            edits = {x['permission']: x for x in d['edits']}
            self.assertEqual(set(edits), {'INV', 'LBL', 'REL', 'UP', 'FREE'})
            self.assertEqual(edits['INV']['stance'], d['stance'])
            self.assertEqual(edits['LBL']['stance'], d['stance'])
            self.assertNotEqual(edits['REL']['stance'], d['stance'])
            self.assertGreaterEqual(edits['UP']['metric'], d['metric'])
            self.assertEqual(edits['UP']['axis'], 'metric')

    def test_invalid_contamination(self):
        for k in (-1, 100):
            with self.assertRaises(ValueError):
                generate(companies=2, quarters=2, contamination=k)


if __name__ == '__main__':
    unittest.main()
