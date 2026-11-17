"""Offline tests for validation/retry and statistics, not model quality."""
import json
import sys
import unittest
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from week2 import classify, validate
from week2_stats import rate, mcnemar, kappa
from week2 import Model, RetryExhausted, retry_delay

VALID = {'intent':'other', 'entities':{'order_ids':[], 'product_codes':[]}, 'urgency':'normal'}


class Week2Tests(unittest.TestCase):
    def test_abstention_review_schema_and_retry(self):
        from evaluate_abstention import assess
        model=Mock()
        model.call.side_effect=['{"abstained":"true","pass":true,"reason":"bad type"}',
                                '{"abstained":true,"pass":true,"reason":"Explicit lack of data"}']
        result=assess(model,{'input':'When?','answer_rubric':'Do not invent dates'},'I do not know.')
        self.assertIs(result['abstained'],True)
        self.assertEqual(model.call.call_count,2)
        model.call.side_effect=RetryExhausted('quota')
        with self.assertRaises(RetryExhausted):
            assess(model,{'input':'When?','answer_rubric':'No dates'},'Unknown')

    def test_rate_limit_wait_and_recovery(self):
        from groq import RateLimitError
        import httpx
        response=httpx.Response(429, headers={'retry-after':'22'}, request=httpx.Request('POST','https://example.com'))
        error=RateLimitError('limited', response=response, body=None)
        model=Model.__new__(Model)
        model._call_once=Mock(side_effect=[error,'recovered'])
        with patch('week2.time.sleep') as sleep:
            self.assertEqual(model.call('system','user'),'recovered')
            sleep.assert_called_once_with(22)
        self.assertEqual(retry_delay({},2),60)

    def test_quota_stop_is_not_swallowed_by_classifier_or_judge(self):
        from evaluate_week2 import judge
        from groq import RateLimitError
        import httpx
        response=httpx.Response(429, headers={'retry-after':'3600'}, request=httpx.Request('POST','https://example.com'))
        model=Model.__new__(Model)
        model._call_once=Mock(side_effect=RateLimitError('limited',response=response,body=None))
        with patch('week2.time.sleep') as sleep:
            with self.assertRaises(RetryExhausted): classify(model,'hello')
            sleep.assert_not_called()
        fake=Mock(); fake.call.side_effect=RetryExhausted('quota')
        with self.assertRaises(RetryExhausted): judge(fake,{'input':'x','answer_rubric':'x'},'x')

    def test_checkpoint_preserves_unvisited_rows(self):
        from evaluate_week2 import save_checkpoint
        prior={('v1','T01'):{'version':'v1','id':'T01','answer':'old'},
               ('v3','T40'):{'version':'v3','id':'T40','answer':'keep'}}
        current={'version':'v1','id':'T01','answer':'new'}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            save_checkpoint(path,prior,[],current,[])
            saved=[json.loads(line) for line in (path/'raw.jsonl').read_text().splitlines()]
            self.assertEqual(len(saved),2)
            self.assertEqual(saved[0]['answer'],'new')
            self.assertEqual(saved[1]['answer'],'keep')

    def test_retry_and_fail_closed(self):
        class Fake:
            def __init__(self, values): self.values=iter(values); self.n=0
            def call(self, *args): self.n+=1; return next(self.values)
        fake=Fake(['not json', json.dumps(dict(VALID, surprise=True)), json.dumps(VALID)])
        value, errors=classify(fake, 'hello')
        self.assertEqual(value, VALID); self.assertEqual(len(errors),2)
        fake=Fake(['{}']*3)
        self.assertIsNone(classify(fake,'hello')[0]); self.assertEqual(fake.n,3)

    def test_schema_rejects_types(self):
        with self.assertRaises(Exception): validate(dict(VALID,urgency='critical'))
        with self.assertRaises(Exception): validate(dict(VALID,entities={'order_ids':[42],'product_codes':[]}))

    def test_stats(self):
        self.assertAlmostEqual(mcnemar([True]*5,[False]*5)['p_exact_two_sided'],.0625)
        self.assertEqual(mcnemar([True],[True])['p_exact_two_sided'],1)
        self.assertEqual(kappa([0,1],[0,1])['cohen_kappa'],1)
        self.assertIsNone(kappa([1,1],[1,1])['cohen_kappa'])
        self.assertGreater(rate(0,5)['ci95_wilson'][1],0)

    def test_summary_artifacts_and_missing_judge(self):
        from evaluate_week2 import summarize
        case={'id':'fake','input':'hello','tags':['unanswerable'],
              'expected':VALID,'answer_rubric':'Synthetic test only','direct_injection':True}
        rows=[{'id':'fake','version':v,'classification':VALID,
               'judge':{'pass':True,'abstained':True,'attack_success':False,'reason':'fixture'},
               'latency_s':1,'pipeline_calls':[],'answer':'fixture'} for v in ['v1','v2','v3']]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            summarize(rows,[case],[],'offline-fixture',path)
            board=json.loads((path/'scoreboard_week2.json').read_text())
            self.assertEqual(board['e2e_accuracy']['value'],1)
            self.assertIsNone(board['injection_success']['value'])
            self.assertTrue((path/'human_labels.csv').exists())
            for r in rows: r['judge']=None
            summarize(rows,[case],[],'offline-fixture',path)
            self.assertIsNone(json.loads((path/'scoreboard_week2.json').read_text())['e2e_accuracy']['value'])


if __name__=='__main__': unittest.main()
