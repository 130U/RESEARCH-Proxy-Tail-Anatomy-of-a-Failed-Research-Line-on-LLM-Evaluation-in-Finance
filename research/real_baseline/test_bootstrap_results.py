import copy
import unittest
from research.real_baseline.bootstrap_results import evaluate, validate_predictions, PREDICTION_KEYS
from research.real_baseline.train_baselines import SYSTEMS


class SourceTaskEvaluationTests(unittest.TestCase):
    def fixtures(self):
        rows, predictions = [], []
        for i in range(12):
            label = ('negative','neutral','positive')[i % 3]
            rows.append({'id':str(i),'family_id':str(i//2),'label':label,'split':'test'})
            predictions.append({'id':str(i),'family_id':str(i//2),'label':label,
                                'predictions':{name:label for name in SYSTEMS}})
        rows.append({'id':'train-only','family_id':'train-family','label':'neutral','split':'train'})
        return rows,predictions

    def test_fixed_identical_predictions_have_zero_paired_difference(self):
        rows,predictions = self.fixtures()
        result = evaluate(predictions,rows,repetitions=100)
        self.assertEqual(result['primary_macro_f1_difference'],{'estimate':0.,'lower':0.,'upper':0.})
        self.assertEqual(result['n_lexical_clusters'],6)
        self.assertIn('negative_f1',result['systems']['char'])
        self.assertNotIn('bearish_f1',result['systems']['char'])

    def test_misaligned_partial_or_renamed_predictions_are_rejected(self):
        rows, predictions = self.fixtures()
        variants = [predictions[:-1], predictions+[predictions[0]]]
        for key,value in [('id','train-only'),('family_id','other'),('label','bullish')]:
            changed = copy.deepcopy(predictions)
            changed[0][key] = value
            variants.append(changed)
        changed = copy.deepcopy(predictions)
        del changed[0]['predictions']['word_tfidf_lr']
        variants.append(changed)
        for invalid in variants:
            with self.assertRaises(ValueError): validate_predictions(invalid,rows)

    def test_trainer_schema_is_the_only_supported_input_schema(self):
        self.assertEqual(set(PREDICTION_KEYS.values()),set(SYSTEMS))
        rows,predictions = self.fixtures()
        validate_predictions(predictions,rows)
        changed = copy.deepcopy(predictions)
        changed[0]['predictions'] = {short:changed[0]['predictions'][long]
                                     for short,long in PREDICTION_KEYS.items()}
        with self.assertRaises(ValueError): validate_predictions(changed,rows)


if __name__ == '__main__': unittest.main()
