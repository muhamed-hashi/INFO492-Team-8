"""Tests for the Demo #2 reference check: generated cases, code lookup, and the code + AI review.
AI calls are mocked; these tests check the software, not model quality."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import core  # noqa: E402
import generate_reference_cases as gen  # noqa: E402

CFG = {'key': 'TEST-NOT-A-REAL-KEY', 'model': 'test-model', 'provider': 'gemini'}


class GeneratedCases(unittest.TestCase):
    def setUp(self):
        self.cases, self.key = gen.build()
        self.index = core.load_json('drawing_index.json')

    def test_deterministic_and_matches_files(self):
        self.assertEqual(gen.build(), (self.cases, self.key))
        self.assertEqual(core.load_json('reference_cases.json'), self.cases)
        self.assertEqual(core.load_json('reference_answer_key.json'), self.key)

    def test_balanced_labels(self):
        self.assertEqual(len(self.cases), 24)
        kinds = [k['variant'] for k in self.key if k['reference_problem']]
        self.assertEqual(sorted(set(kinds)), ['nonexistent', 'typo', 'unrelated', 'vague'])
        self.assertEqual(len(kinds), 12)

    def test_defects_are_what_the_labels_say(self):
        key = {k['case_id']: k for k in self.key}
        for c in self.cases:
            k, refs = key[c['case_id']], core.reference_check(c['initial'], self.index)
            missing = [r for r in refs if r['status'] != 'observed_in_partial_index']
            if k['variant'] in ('clean', 'typo', 'unrelated'):
                self.assertFalse(missing, c['case_id'])          # every recognized sheet exists
                self.assertTrue(refs, c['case_id'])
            if k['variant'] == 'nonexistent':
                self.assertTrue(missing, c['case_id'])
            if k['variant'] == 'vague':
                self.assertFalse(refs, c['case_id'])
            if k['variant'] == 'typo':
                self.assertIn('O', c['initial']['references'])

    def test_brief_gives_correct_references(self):
        key = {k['case_id']: k for k in self.key}
        for c in self.cases:
            if not key[c['case_id']]['reference_problem']:
                self.assertEqual(c['brief']['known_details']['references'], c['initial']['references'])


class ReferenceReview(unittest.TestCase):
    def setUp(self):
        self.index = core.load_json('drawing_index.json')
        self.rfi = {'title': 'T', 'location': 'Room 101', 'trade': 'Flooring', 'question': 'Terrazzo or VCT in this room?',
                    'needed_by': '2026-10-23', 'impact': 'Ordering is on hold.', 'references': 'A-502, FP-200, Q-999'}

    def test_ai_verdicts_only_on_sheets_code_found(self):
        seen = {}

        def fake(cfg, prompt, user, schema):
            seen['user'] = user
            return ({'sheets': [{'sheet': 'A-502', 'fits_question': 'yes', 'reason': 'finish schedule'},
                                {'sheet': 'FP-200', 'fits_question': 'no', 'reason': 'fire protection sheet'},
                                {'sheet': 'Z-123', 'fits_question': 'no', 'reason': 'invented'}],
                     'issues': []}, {'modelVersion': 'test-model'})
        with patch('core.gemini_json', side_effect=fake):
            out = core.ai_reference_review(self.rfi, self.index, cfg=CFG)
        self.assertEqual([s['sheet'] for s in out['sheets']], ['A-502', 'FP-200'])   # Z-123 dropped
        self.assertTrue(out['flag'])
        self.assertIn('FP-200', out['findings'][0]['message'])
        lookup = {l['sheet']: l for l in seen['user']['code_lookup']}
        self.assertFalse(lookup['Q-999']['in_drawing_index'])
        self.assertTrue(lookup['FP-200']['title'])
        self.assertNotIn('reference_problem', json.dumps(seen['user']))

    def test_v2_check_combines_code_and_ai_and_drops_ai_reference_claims(self):
        replies = iter([
            ({'summary': 'ok', 'findings': [
                {'field': 'references', 'message': 'A-502 is not in the index', 'follow_up': 'x', 'evidence': 'x'},
                {'field': 'location', 'message': 'Which room?', 'follow_up': 'x', 'evidence': 'Room 101'}]}, {}),
            ({'sheets': [{'sheet': 'A-502', 'fits_question': 'yes', 'reason': 'ok'},
                         {'sheet': 'FP-200', 'fits_question': 'yes', 'reason': 'ok'}], 'issues': []}, {})])
        with patch('core.settings', return_value=CFG), patch('core.gemini_json', side_effect=lambda *a: next(replies)):
            out = core.ai_check_v2(self.rfi, self.index)
        fields = [(f['field'], f['source']) for f in out['findings']]
        self.assertIn(('location', 'AI'), fields)
        self.assertIn(('references', 'drawing index lookup (code)'), fields)     # Q-999 not in index
        self.assertFalse(any(f['source'] == 'AI' and f['field'] == 'references' for f in out['findings']))
        self.assertTrue(any('ai_note' in r for r in out['references']))
        self.assertEqual(out['pipeline'], 'v2')

    def test_no_sheet_cited_is_flagged_by_code(self):
        self.assertTrue(core.code_reference_findings([]))


if __name__ == '__main__':
    unittest.main()
