"""Tests for Demo #4 close-out (no network: the Gemini call is replaced by a fake).

    python3 -m unittest discover tests
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DEMO3_RUNTIME', tempfile.mkdtemp(prefix='demo4-test-'))
os.environ['GEMINI_API_KEY'] = 'test-key'

import agents  # noqa: E402
import closeout  # noqa: E402
import core  # noqa: E402
import protocol  # noqa: E402

LISTS_DATA = agents.load('addendum_drawing_lists.json')
LISTS = closeout.DrawingLists(LISTS_DATA)
_previous = agents.gemini_json


def fake_answer_check(user):
    """Stands in for Gemini on the answer-check prompt, steered by marker words in the test text."""
    raw = {'modelVersion': 'fake-model', 'usageMetadata': {'totalTokenCount': 1}}
    q, a = user['rfi_question'], user['answer']
    no = {'value': False, 'quote': ''}
    if 'TESTINVENT' in q:
        return ({'questions': [{'asks': 'a question nobody asked', 'status': 'answered', 'answer_quote': ''}],
                 'scope_change': {'value': True, 'quote': 'words that are not in the answer'},
                 'refers_to_missing': no, 'reason': 'test'}, raw)
    if 'TESTDEFER' in q:
        return ({'questions': [{'asks': 'Please provide the budget', 'status': 'deferred',
                                'answer_quote': 'will be announced at bid opening'}],
                 'scope_change': no, 'refers_to_missing': no, 'reason': 'test'}, raw)
    if 'TESTSCOPE' in q:
        return ({'questions': [{'asks': 'Provide size of wire', 'status': 'answered', 'answer_quote': ''}],
                 'scope_change': {'value': True, 'quote': 'Delete this scope of work'},
                 'refers_to_missing': no, 'reason': 'test'}, raw)
    return ({'questions': [{'asks': q[:30], 'status': 'answered', 'answer_quote': ''}],
             'scope_change': no, 'refers_to_missing': no, 'reason': 'test'}, raw)


def fake_gemini(cfg, prompt, user, schema):
    """Stands in for Gemini on the close-out prompt; other prompts go to the Demo #3 fake if it is loaded."""
    if 'another round of questions' in prompt:
        return fake_answer_check(user)
    if 'close out RFIs' not in prompt:
        return _previous(cfg, prompt, user, schema)
    raw = {'modelVersion': 'fake-model', 'usageMetadata': {'totalTokenCount': 1}}
    text = user['architect_answer']
    if 'TESTPARTIAL' in text:
        return ({'commitment': 'revised_drawings', 'revised_sheets': [
                    {'sheet': 'E-304', 'quote': 'Refer to revised Drawing E-304 included in this addendum'},
                    {'sheet': 'E-304', 'quote': 'invented quote'}],
                 'referenced_only': [], 'later_action': {'needed': False, 'quote': ''}, 'reason': 'test'}, raw)
    if 'TESTSERIES' in text:     # the model writes the bare numbers it saw
        return ({'commitment': 'revised_drawings', 'revised_sheets': [
                    {'sheet': '010', 'quote': 'ID sheets 010, 011 have been revised'},
                    {'sheet': '011', 'quote': 'ID sheets 010, 011 have been revised'}],
                 'referenced_only': [], 'later_action': {'needed': False, 'quote': ''}, 'reason': 'test'}, raw)
    if 'TESTGUARD' in text:      # invent a sheet and a quote: the guard must drop both claims
        return ({'commitment': 'revised_drawings', 'revised_sheets': [{'sheet': 'Z-999', 'quote': 'Z-999 was revised'},
                                                                     {'sheet': 'E-304', 'quote': 'a quote that is not there'}],
                 'referenced_only': [], 'later_action': {'needed': True, 'quote': 'not in the answer'}, 'reason': 'test'}, raw)
    sentences = [s.strip() for s in re.split(r'(?<=\.)\s+', text) if s.strip()]
    later = next((s for s in sentences if re.search(r'\bwill\b|pending|not yet|to be provided', s, re.I)), '')
    revised, referenced = [], []
    for sheet in user['sheet_numbers_in_answer']:
        plain = sheet.replace('-', '')
        hit = next((s for s in sentences if plain in s.upper().replace('-', '') and re.search(r'revis', s, re.I)
                    and s != later and not re.search(r'\b(?:see|refer to)\b(?!\s+revised)', s, re.I)), None)
        (revised if hit else referenced).append({'sheet': sheet, 'quote': hit} if hit else sheet)
    commitment = 'change_to_be_issued_later' if later else 'revised_drawings' if revised else 'no_change'
    return ({'commitment': commitment, 'revised_sheets': revised, 'referenced_only': referenced,
             'later_action': {'needed': bool(later), 'quote': later}, 'reason': 'fake'}, raw)


agents.gemini_json = fake_gemini
core.gemini_json = fake_gemini


class DrawingListData(unittest.TestCase):
    def test_lists_complete(self):
        counts = {a['addendum']: len(a['drawings']) for a in LISTS_DATA['addenda']}
        self.assertEqual(counts, {1: 90, 2: 130, 3: 159, 4: 0, 5: 19, 6: 14})
        for a in LISTS_DATA['addenda']:
            self.assertEqual([d['no'] for d in a['drawings']], list(range(1, len(a['drawings']) + 1)))

    def test_evidence_points_to_pdf_page(self):
        e = LISTS.evidence(2, 'E304')
        self.assertEqual((e['sheet'], e['item'], e['pdf_page']), ('E-304', 106, 10))
        self.assertTrue(e['url'].endswith('#page=10'))

    def test_near_matches(self):
        self.assertEqual(LISTS.near(2, 'E-340'), ['E-304'])          # swapped digits
        self.assertEqual(LISTS.near(3, 'SD-300'), ['S-300'])          # SD is not a discipline in this project
        self.assertNotIn('E-304', LISTS.near(2, 'ED-304'))           # ED is a real one (electrical demolition)
        self.assertIn('A-301B', LISTS.near(5, 'A-301'))               # missing suffix letter
        self.assertEqual(LISTS.near(1, 'A-102B'), [])                 # a different sheet is not a typo


class CodeBaseline(unittest.TestCase):
    def rfi(self, response, addendum=2):
        return {'source_id': 'T', 'addendum': addendum, 'question': 'q', 'response': response}

    def test_verified_revision(self):
        out = closeout.code_closeout(self.rfi('Refer to revised Drawing E-304 included in this addendum.'), LISTS)
        self.assertEqual(out['recommendation'], 'ok_to_close')
        self.assertEqual(out['evidence'][0]['item'], 106)

    def test_explicit_earlier_addendum(self):
        r = self.rfi('Refer to Drawings A-421, A-422 which were revised and issued in Addendum No. 3.', addendum=5)
        self.assertEqual(closeout.code_closeout(r, LISTS)['target_addendum'], 3)
        self.assertEqual(closeout.code_closeout(r, LISTS)['recommendation'], 'ok_to_close')

    def test_baseline_cannot_tell_reference_from_revision(self):
        r = self.rfi('Refer to revised Drawing E-304 included in this addendum. Also see Drawing S-104.')
        self.assertEqual(closeout.code_closeout(r, LISTS)['recommendation'], 'hold')

    def test_missing_and_typo(self):
        planted = closeout.DrawingLists(LISTS_DATA, remove=[(2, 'E-304')])
        r = self.rfi('Refer to revised Drawing E-304 included in this addendum.')
        self.assertEqual(closeout.code_closeout(r, planted)['recommendation'], 'hold')
        self.assertEqual(closeout.code_closeout(self.rfi('Refer to revised Drawing E-340 included in this addendum.'), LISTS)
                         ['recommendation'], 'check')

    def test_spaced_and_lower_case_sheets(self):
        self.assertEqual(closeout.sheets_in("refer to sht P- 500, 2/m- 600 and e304"), ['E-304', 'P-500', 'M-600'])

    def test_sheet_series(self):
        self.assertEqual(closeout.sheets_in('ID sheets 010, 011 and 016 have been revised')[:3], ['ID-010', 'ID-011', 'ID-016'])


class Agent(unittest.TestCase):
    def rfi(self, response, addendum=2):
        return {'source_id': 'T', 'addendum': addendum, 'question': 'q', 'response': response}

    def test_reference_is_not_a_revision(self):
        out = closeout.closeout_agent(self.rfi('Refer to revised Drawing E-304 included in this addendum. Also see Drawing S-104.'), LISTS)
        self.assertEqual(out['recommendation'], 'ok_to_close')
        self.assertEqual(out['revised_sheets'], ['E-304'])
        self.assertIn('S-104', out['referenced_only'])

    def test_deferred_change_stays_open(self):
        out = closeout.closeout_agent(self.rfi('Use type C12. Drawing E-304 will be revised for the permit set.'), LISTS)
        self.assertEqual(out['recommendation'], 'keep_open')

    def test_guard_drops_invented_claims(self):
        out = closeout.closeout_agent(self.rfi('TESTGUARD. Refer to revised Drawing E-304 included in this addendum.'), LISTS)
        self.assertEqual(out['revised_sheets'], [])
        self.assertEqual(len(out['guard']), 3)
        self.assertEqual(out['recommendation'], 'check')            # says "revised" but no claim survived

    def test_guard_drop_never_closes_silently(self):
        # one revised sheet is quoted correctly, the other claim is invented: the agent must ask for a person
        r = self.rfi('TESTPARTIAL Refer to revised Drawing E-304 included in this addendum.')
        out = closeout.closeout_agent(r, LISTS)
        self.assertEqual(out['revised_sheets'], ['E-304'])
        self.assertEqual(out['recommendation'], 'check')

    def test_sheet_number_without_letters(self):
        r = self.rfi('TESTSERIES The Finish Schedule and ID sheets 010, 011 have been revised and are included in this addendum.', addendum=3)
        out = closeout.closeout_agent(r, LISTS)
        self.assertEqual(out['revised_sheets'], ['ID-010', 'ID-011'])
        self.assertEqual(out['recommendation'], 'ok_to_close')

    def test_agent_cannot_close(self):
        sender = protocol.actor_of(agent='closeout_agent')
        with self.assertRaises(protocol.Denied): protocol.envelope('closeout_decision', 'X', sender, 'gc', {})
        protocol.envelope('closeout_check', 'X', sender, 'gc', {})


class TestCases(unittest.TestCase):
    def test_cases_file(self):
        cases = agents.load('closeout_cases.json')['cases']
        kinds = {k: sum(c['kind'] == k for c in cases) for k in ('clean', 'see_also', 'missing', 'deferred', 'typo')}
        self.assertEqual(kinds, {'clean': 12, 'see_also': 6, 'missing': 8, 'deferred': 8, 'typo': 6})
        before = (ROOT / 'data' / 'closeout_cases.json').read_text(encoding='utf-8')
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'make_closeout_cases.py')], check=True, capture_output=True)
        self.assertEqual((ROOT / 'data' / 'closeout_cases.json').read_text(encoding='utf-8'), before)   # deterministic


class MessyCases(unittest.TestCase):
    def test_messy_cases_file(self):
        cases = agents.load('closeout_cases_messy.json')['cases']
        self.assertEqual(len(cases), 40)
        self.assertEqual(len({c['source_id'] for c in cases}), 40)
        self.assertEqual(sum('+' in c['kind'] for c in cases), 10)          # 10 cases with two problems
        before = (ROOT / 'data' / 'closeout_cases_messy.json').read_text(encoding='utf-8')
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'make_messy_cases.py')], check=True, capture_output=True)
        self.assertEqual((ROOT / 'data' / 'closeout_cases_messy.json').read_text(encoding='utf-8'), before)

    def test_every_planted_sheet_is_visible_to_code(self):
        for c in agents.load('closeout_cases_messy.json')['cases']:
            for _, s in c['remove_from_list']:
                self.assertIn(s, closeout.sheets_in(c['response']), c['case_id'])

    def test_stakeholder_cases_use_their_own_sheet_list(self):
        c = {'case_id': 'K', 'addendum': 1, 'response': "see rev'd A-201 attached", 'issued_sheets': ['A-201']}
        lists = closeout.case_lists(c, LISTS_DATA)
        self.assertTrue(lists.item(1, 'A-201'))
        self.assertIsNone(lists.item(1, 'E-304'))


class CloseoutFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading
        import app
        cls.srv = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.base = f'http://127.0.0.1:{cls.srv.server_address[1]}'
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def client(self, user, pin):
        import http.cookiejar
        import urllib.error
        import urllib.request
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

        def call(path, body=None):
            req = urllib.request.Request(self.base + path, data=None if body is None else json.dumps(body).encode(),
                                         headers={'Content-Type': 'application/json'}, method='GET' if body is None else 'POST')
            try:
                with op.open(req) as r: return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        self.assertEqual(call('/api/login', {'user_id': user, 'pin': pin})[0], 200)
        return call

    def test_close_out_flow(self):
        pm = self.client('u-pm', '3333'); site = self.client('u-site', '2222'); arch = self.client('u-arch', '4444')
        log = pm('/api/closeout')[1]
        self.assertEqual(len(log), 108)
        flagged = 'Dett-A3-RFI57'          # answer refers to A-432 and says A-434 was revised
        self.assertEqual(next(x for x in log if x['id'] == flagged)['code'], 'check')
        self.assertEqual(arch(f'/api/closeout/{flagged}')[0], 403)                  # not sent to the design team
        self.assertEqual(site(f'/api/closeout/{flagged}/agent', {})[0], 200)        # site manager may run the agent
        self.assertEqual(site(f'/api/closeout/{flagged}/decide', {'decision': 'close'})[0], 403)   # only the PM closes
        code, c = pm(f'/api/closeout/{flagged}/agent', {}); self.assertEqual(code, 200)
        self.assertEqual(c['agent']['recommendation'], 'ok_to_close')               # A-432 is only referred to
        plain = 'Dett-A3-RFI21'           # "Sd300 revised": no such sheet in the Addendum 3 list
        pm(f'/api/closeout/{plain}/agent', {})
        self.assertEqual(pm(f'/api/closeout/{plain}/decide', {'decision': 'close'})[0], 400)       # against advice: note needed
        self.assertEqual(pm(f'/api/closeout/{plain}/decide', {'decision': 'ask_architect',
                                                              'note': 'Which sheet is 12/Sd300? It is not in the Addendum 3 list.'})[0], 200)
        self.assertEqual([x['id'] for x in arch('/api/closeout')[1]], [plain])
        self.assertEqual(arch(f'/api/closeout/{plain}/reply', {'answer': 'Typo: detail 12 on S-300.'})[1]['status'], 'architect_replied')
        code, c = pm(f'/api/closeout/{plain}/decide', {'decision': 'close', 'note': 'Architect confirmed S-300.'})
        self.assertEqual((code, c['status'], c['decision']['override']), (200, 'closed', True))
        panel = pm('/api/panel')[1]
        self.assertEqual((panel['closeout']['closed'], panel['closeout']['overrides']), (1, 1))
        self.assertTrue(panel['audit']['ok'])


class AnswerCheck(unittest.TestCase):
    """Second real data set (data/gwa): did the answer actually answer?"""
    def item(self, q, a, date='6/30/26'):
        return {'no': 1, 'date': date, 'question': q, 'response': a}

    def test_answered_can_close(self):
        out = closeout.answer_check(self.item('Confirm the screen is 316L.', 'EOR Response: Yes, 316L.'))
        self.assertEqual(out['recommendation'], 'ok_to_close')

    def test_deferred_answer_is_not_closed(self):
        out = closeout.answer_check(self.item('TESTDEFER Please provide the budget.', 'The budget will be announced at bid opening.'))
        self.assertEqual(out['recommendation'], 'check')
        self.assertTrue(out['flags']['not_fully_answered'])

    def test_scope_change_needs_a_quote(self):
        out = closeout.answer_check(self.item('TESTSCOPE Provide size of wire and conduit.', 'EOR Response: Delete this scope of work.'))
        self.assertTrue(out['flags']['scope_change'])
        self.assertEqual(out['recommendation'], 'check')

    def test_guard_drops_invented_quotes_and_never_closes(self):
        out = closeout.answer_check(self.item('TESTINVENT Provide the pump model.', 'EOR Response: Pump P-1.', date=''))
        self.assertFalse(out['flags']['scope_change'])
        self.assertEqual(len(out['guard']), 2)
        self.assertEqual(out['recommendation'], 'check')
        self.assertTrue(out['flags']['no_date'])

    def test_picture_text_is_part_of_the_question(self):
        q, _ = closeout.answer_texts({'question': 'See above.', 'response': 'x', 'question_picture_text': 'Section 3.1'})
        self.assertIn('read by OCR', q); self.assertIn('Section 3.1', q)

    def test_copied_answer_found_across_items(self):
        items = [{'no': 1, 'question': 'Where is the drying bed?', 'response': 'EOR Response: Contractor may use one of the four beds at the plant.'},
                 {'no': 2, 'question': 'Where is the holding area?', 'response': 'EOR Response: Contractor may use one of the four beds at the plant. See spec.'},
                 {'no': 3, 'question': 'Other?', 'response': 'EOR Response: No.'}]
        self.assertEqual(closeout.copied_answers(items), {1: [2], 2: [1]})

    def test_gwa_data_and_answer_key(self):
        items = json.loads((ROOT / 'data' / 'gwa' / 'rfi1_items.json').read_text())
        self.assertEqual([i['no'] for i in items], list(range(1, 45)))
        sys.path.insert(0, str(ROOT / 'scripts'))
        import run_gwa_eval
        self.assertEqual(run_gwa_eval.item_numbers('#39–#40'), [39, 40])
        key, listed, _ = run_gwa_eval.answer_key()
        self.assertEqual(len(listed), 37)
        self.assertEqual(sorted(set(range(1, 45)) - listed), [12, 21, 24, 30, 31, 34, 41])
        self.assertIn('multiple_questions', key[42]); self.assertIn('scope_change', key[32])

    def test_blind_review_sample_is_fixed(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import csv, run_gwa_eval
        log = list(csv.DictReader(open(ROOT / 'results' / 'gwa' / 'gwa_log.csv', encoding='utf-8')))
        self.assertEqual(run_gwa_eval.review_sample(log), [1, 7, 13, 14, 20, 21, 28, 30, 34, 35, 39, 41])

    def test_kevin_scoring(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import run_gwa_eval
        log = [{'no': '1', 'x_rec': 'check', 'x_error': ''}, {'no': '2', 'x_rec': 'ok_to_close', 'x_error': ''},
               {'no': '3', 'x_rec': 'check', 'x_error': ''}]
        out = run_gwa_eval.score_kevin(log, 'x', {1: 'another_round', 2: 'scope_change', 3: 'ok_to_close'})
        self.assertEqual((out['stopped_of_those'], out['missed'], out['stopped_but_he_says_ok']), (1, [2], [3]))


if __name__ == '__main__':
    unittest.main()
