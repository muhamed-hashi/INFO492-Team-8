"""Provider contract tests use synthetic replies, never a real key or API call."""
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import core
import setup_ai


class GeminiTests(unittest.TestCase):
    def setUp(self):
        self.rfi=core.load_json('cases.json')[0]['initial']
        self.index=core.load_json('drawing_index.json')
        self.cfg={'provider':'gemini','key':'TEST-KEY-NOT-REAL','model':core.GEMINI_MODEL_DEFAULT}

    def test_gemini_contract_and_audit(self):
        output={'summary':'Check the missing date.','findings':[{'field':'needed_by','message':'No date supplied.',
            'follow_up':'When do you need an answer?','evidence':'Not supplied in the RFI'}]}
        raw={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(output)}]}}],
             'modelVersion':'test-gemini-version','responseId':'test-response','usageMetadata':{'totalTokenCount':42}}
        def fake_open(request,timeout):
            self.assertEqual(request.get_header('X-goog-api-key'),self.cfg['key'])
            self.assertNotIn(self.cfg['key'],request.full_url)
            payload=json.loads(request.data)
            self.assertEqual(payload['generationConfig']['responseMimeType'],'application/json')
            self.assertEqual(payload['generationConfig']['responseJsonSchema']['type'],'object')
            self.assertNotIn('expected_missing_fields',json.dumps(payload['contents']))
            self.assertNotIn('historical_response_summary',json.dumps(payload['contents']))
            return io.BytesIO(json.dumps(raw).encode())
        with patch('core.settings',return_value=self.cfg),patch('urllib.request.urlopen',side_effect=fake_open):
            out=core.ai_check(self.rfi,self.index)
        self.assertEqual(out['provider'],'gemini')
        self.assertEqual(out['model'],'test-gemini-version')
        self.assertEqual(out['findings'][0]['field'],'needed_by')
        self.assertEqual(len(out['prompt_sha256']),64)

    def test_quota_error_never_falls_back(self):
        failure=urllib.error.HTTPError('https://example.invalid',429,'quota',{},None)
        with patch('core.settings',return_value=self.cfg),patch('urllib.request.urlopen',side_effect=failure),patch('core.rule_check') as rules:
            with self.assertRaisesRegex(ValueError,'quota or rate limit'): core.ai_check(self.rfi,self.index)
            rules.assert_not_called()

    def test_unfinished_response_rejected(self):
        raw={'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'{"summary":'}]}}]}
        with patch('core.settings',return_value=self.cfg),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(raw).encode())):
            with self.assertRaisesRegex(ValueError,'did not finish'): core.ai_check(self.rfi,self.index)

    def test_configuration_prefers_selected_provider(self):
        with tempfile.TemporaryDirectory() as d,patch('core.ROOT',Path(d)),patch.dict(os.environ,{},clear=True):
            p=Path(d)/'config.local.json'
            p.write_text(json.dumps({'AI_PROVIDER':'gemini','GEMINI_API_KEY':'test-google','OPENAI_API_KEY':'test-openai'}))
            self.assertEqual(core.settings()['key'],'test-google')
            self.assertEqual(core.settings()['provider'],'gemini')

    def test_setup_saves_key_without_printing_it(self):
        with tempfile.TemporaryDirectory() as d,patch('setup_ai.__file__',str(Path(d)/'setup_ai.py')),patch('sys.argv',['setup_ai.py']),patch('getpass.getpass',return_value='TEST-NOT-REAL-GEMINI-KEY'),patch('sys.stdout',new_callable=io.StringIO) as stdout:
            setup_ai.main()
            data=json.loads((Path(d)/'config.local.json').read_text())
            self.assertEqual(data['AI_PROVIDER'],'gemini')
            self.assertNotIn(data['GEMINI_API_KEY'],stdout.getvalue())


if __name__=='__main__': unittest.main()
