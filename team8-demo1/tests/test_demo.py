import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer

import app
import core


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.rfi=core.load_json('cases.json')[0]['initial']
        self.index=core.load_json('drawing_index.json')

    def test_reference_match_normalizes_without_claiming_correctness(self):
        rfi={**self.rfi,'references':'e202, PV600, A-999'}
        refs=core.reference_check(rfi,self.index)
        self.assertEqual(refs[0]['reference'],'E-202')
        self.assertEqual(refs[-1]['status'],'not_found_in_partial_index')
        self.assertIn('does not establish',refs[-1]['message'])

    def test_missing_fields_detected_in_practice(self):
        findings=core.rule_check(self.rfi,self.index)['findings']
        self.assertEqual({x['field'] for x in findings},{'location','needed_by'})

    def test_failed_ai_never_silently_falls_back(self):
        with patch('core.settings',return_value={'key':'','model':'example'}):
            with self.assertRaisesRegex(ValueError,'AI is not connected'):
                core.ai_check(self.rfi,self.index)

    def test_provider_payload_and_response_contract(self):
        response={'status':'completed','model':'test-model','output':[{'content':[{'type':'output_text',
            'text':json.dumps({'summary':'Please review missing details.','findings':[]})}]}]}
        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*a): self.close()
        def fake_open(request,timeout):
            payload=json.loads(request.data)
            self.assertFalse(payload['store'])
            self.assertTrue(payload['text']['format']['strict'])
            self.assertNotIn('historical_response_summary',payload['input'])
            self.assertNotIn('expected_missing_fields',payload['input'])
            return Reply(json.dumps(response).encode())
        with patch('core.settings',return_value={'key':'TEST-NOT-A-REAL-KEY','model':'test-model'}),patch('urllib.request.urlopen',side_effect=fake_open):
            out=core.ai_check(self.rfi,self.index)
            self.assertEqual(out['engine'],'ai')
            self.assertEqual(out['model'],'test-model')
            self.assertEqual(len(out['prompt_sha256']),64)

    def test_invalid_ai_fields_rejected(self):
        with self.assertRaises(ValueError):
            core.validate_ai_result({'summary':'x','findings':[{'field':'authorize_work'}]})


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.old_db=app.DB
        app.DB=Path(cls.temp.name)/'test.sqlite3'
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url='http://127.0.0.1:'+str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
        app.DB=cls.old_db;cls.temp.cleanup()

    def post(self,path,body):
        req=urllib.request.Request(self.url+path,data=json.dumps(body).encode(),
            headers={'Content-Type':'application/json','X-RFI-App':'1'})
        with urllib.request.urlopen(req) as r:return json.load(r)

    def test_manual_handoff_timing_scoring(self):
        pid=self.post('/api/preparations',{'condition':'manual','case_id':'D06'})['preparation_id']
        rfi=core.load_json('cases.json')[5]['initial']
        with self.assertRaises(urllib.error.HTTPError):
            self.post('/api/check',{'preparation_id':pid,'rfi':rfi})
        with self.assertRaises(urllib.error.HTTPError):
            self.post('/api/handoff',{'preparation_id':pid,'rfi':rfi,'human_approved':False})
        tid=self.post('/api/handoff',{'preparation_id':pid,'rfi':rfi,'human_approved':True})['trial_id']
        with self.assertRaises(urllib.error.HTTPError):
            self.post('/api/handoff',{'preparation_id':pid,'rfi':rfi,'human_approved':True})
        opened=self.post('/api/start-review',{'trial_id':tid,'reviewer':'test-gc'})
        self.assertEqual(set(opened),{'rfi','elapsed'})
        self.assertNotIn('condition',opened)
        result=self.post('/api/finish-review',{'trial_id':tid,'decision':'ready','interrupted':False})
        self.assertGreaterEqual(result['review_seconds'],0)
        with app.connect() as db: self.assertIsNone(app.fetch_trial(db,tid)['error_count'])
        self.post('/api/score',{'trial_id':tid,'error_count':0,'notes':'TEST ONLY'})
        with app.connect() as db: self.assertEqual(app.fetch_trial(db,tid)['error_count'],0)

    def test_ai_handoff_requires_actual_success(self):
        pid=self.post('/api/preparations',{'condition':'ai','case_id':'D01'})['preparation_id']
        with self.assertRaises(urllib.error.HTTPError):
            self.post('/api/handoff',{'preparation_id':pid,'rfi':core.load_json('cases.json')[0]['initial'],'human_approved':True})

    def test_rule_run_is_separate_condition(self):
        pid=self.post('/api/preparations',{'condition':'rules','case_id':'D01'})['preparation_id']
        rfi=core.load_json('cases.json')[0]['initial']
        out=self.post('/api/check',{'preparation_id':pid,'rfi':rfi})
        self.assertEqual(out['engine'],'rules')
        tid=self.post('/api/handoff',{'preparation_id':pid,'rfi':rfi,'human_approved':True})['trial_id']
        with app.connect() as db:self.assertEqual(app.fetch_trial(db,tid)['condition'],'rules')

    def test_secrets_not_served(self):
        for path in ['/config.local.json','/.env','/data/answer_key.json','/../app.py']:
            with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(self.url+path)

    def test_summary_excludes_interrupted_and_rule_practice(self):
        def trial(condition,seconds,interrupted=False):
            return {'condition':condition,'review_seconds':seconds,'interrupted':interrupted,
                'preparation_seconds':50,'decision':'ready','error_count':None}
        s=app.summarize([trial('manual',40),trial('manual',999,True),trial('ai',30),trial('rules',1)])
        self.assertEqual(s['observed_reduction_percent'],25)
        self.assertIsNone(s['groups']['ai']['mean_errors'])
        self.assertEqual(s['groups']['manual']['interrupted_excluded'],1)


if __name__=='__main__':unittest.main()
