import unittest
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from lab import (load_customers,load_usage,clean_customers,split_task,
                 preprocessor,NUM_CLASS)

class DataContractTests(unittest.TestCase):
    def test_data_contracts_and_target(self):
        customers,usage = load_customers(),load_usage()
        self.assertEqual(customers.shape,(600,8))
        self.assertEqual(usage.shape,(600,7))
        self.assertTrue(customers['customer_id'].is_unique)
        self.assertEqual(set(customers['churn'].unique()),{0,1})

    def test_fixed_constraints_preserve_input_and_rare_value(self):
        raw = load_customers()
        result = clean_customers(raw)
        self.assertEqual(raw.loc[0,'monthly_fee'],-10)
        self.assertTrue(np.isnan(result.loc[0,'monthly_fee']))
        self.assertTrue(np.isnan(result.loc[1,'last_usage']))
        self.assertEqual(result.loc[2,'monthly_fee'],10000)

    def test_split_disjoint_and_aligned(self):
        for task in ('classification','regression'):
            a,b,c,ya,yb,yc = split_task(task)
            self.assertEqual([len(a),len(b),len(c)],[360,120,120])
            self.assertTrue(a.index.equals(ya.index) and b.index.equals(yb.index) and c.index.equals(yc.index))
            self.assertTrue(set(a.index).isdisjoint(b.index))
            self.assertTrue(set(a.index).isdisjoint(c.index))
            self.assertTrue(set(b.index).isdisjoint(c.index))
            self.assertNotIn('churn',a.columns)
            self.assertNotIn('usage_hours',a.columns)

    def test_imputer_state_is_training_only(self):
        a,b,c,ya,yb,yc = split_task()
        p = preprocessor().fit(a)
        stats = p.named_transformers_['num'].named_steps['imputer'].statistics_.copy()
        b = b.copy()
        b.loc[:,'monthly_fee'] = 1e7
        p.transform(b)
        np.testing.assert_allclose(stats,p.named_transformers_['num'].named_steps['imputer'].statistics_)
        np.testing.assert_allclose(stats,a[NUM_CLASS].median().to_numpy())

    def test_unknown_category_keeps_shape_and_finite_values(self):
        a,b,c,ya,yb,yc = split_task()
        p = preprocessor().fit(a)
        known = p.transform(b)
        changed = b.copy()
        changed.loc[:,'contract_type'] = 'new-contract'
        transformed = p.transform(changed)
        self.assertEqual(transformed.shape,known.shape)
        self.assertTrue(np.isfinite(transformed).all())

    def test_missing_required_column_is_not_silently_filled(self):
        a,b,c,ya,yb,yc = split_task()
        p = preprocessor().fit(a)
        with self.assertRaises(ValueError):
            p.transform(b.drop(columns=['monthly_fee']))

    def test_predictions_keep_sample_count(self):
        a,b,c,ya,yb,yc = split_task()
        model = Pipeline([('prep',preprocessor()),('clf',LogisticRegression(max_iter=1000))]).fit(a,ya)
        pred = model.predict(b)
        self.assertEqual(pred.shape,(120,))
        self.assertTrue(set(pred).issubset({0,1}))

    def test_unknown_task_is_rejected(self):
        with self.assertRaises(ValueError):
            split_task('not-a-task')

if __name__ == '__main__':
    unittest.main()
