"""Tests for Demo #3 (no network: the Gemini call is replaced by a fake).

    python3 -m unittest discover tests
"""
import http.cookiejar
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['DEMO3_RUNTIME'] = tempfile.mkdtemp(prefix='demo3-test-')
os.environ['GEMINI_API_KEY'] = 'test-key'

import agents  # noqa: E402
import core  # noqa: E402
import protocol  # noqa: E402

CTX = {'index': agents.load('drawing_index.json'), 'revisions': agents.load('revisions.json'), 'issued_through': 6}
CASES = {c['case_id']: c for c in agents.load('rough_rfis.json')}


def fake_gemini(cfg, prompt, user, schema):
    """Stands in for Gemini. The draft answer deliberately invents a room number to test the guard."""
    raw = {'modelVersion': 'fake-model', 'usageMetadata': {'totalTokenCount': 1}}
    if 'rough message from the job site' in prompt:
        msg = user['message']
        return ({'title': 'Floor finish conflict', 'question': 'Which floor finish applies: terrazzo or VCT?', 'trade': 'Flooring',
                 'location': {'found_in_message': True, 'quote': '2nd floor bathroom', 'value': 'Room 221, Level 2'},
                 'needed_by': {'found_in_message': 'asap' in msg, 'quote': 'asap' if 'asap' in msg else '', 'value': 'asap'},
                 'impact': {'found_in_message': False, 'quote': '', 'value': ''},
                 'separate_questions': ['Single or double tier lockers?', 'What base goes under the lockers?'] if 'lockers' in msg else ['Which floor finish applies?'],
                 'questions_for_sub': [{'field': 'impact', 'ask': 'What is held up?'}],
                 'changes': [{'what': 'Rewrote the question', 'why': 'clarity'}]}, raw)
    if "site manager review an RFI" in prompt:
        cost = 'whether' in user['rfi']['question'].lower()
        return ({'location_specific': {'value': 'yes', 'reason': 'room given'}, 'impact_specific': {'value': 'yes', 'reason': 'ok'},
                 'route': {'value': 'design_team', 'reason': 'conflicting drawings'},
                 'possible_cost_or_scope': {'value': 'yes' if cost else 'no', 'reason': 'test'}, 'separate_questions': 1}, raw)
    return ({'sheets': [], 'issues': []}, raw)


agents.gemini_json = fake_gemini
core.gemini_json = fake_gemini


class Protocol(unittest.TestCase):
    def test_permissions(self):
        foreman = {'id': 'x', 'name': 'F', 'role': 'foreman'}
        with self.assertRaises(protocol.Denied): protocol.require(foreman, 'forward')
        protocol.require({'id': 'y', 'name': 'P', 'role': 'project_manager'}, 'ack_cost')
        with self.assertRaises(protocol.Denied): protocol.require({'id': 'z', 'name': 'A', 'role': 'architect'}, 'return')

    def test_agents_cannot_decide(self):
        sender = protocol.actor_of(agent='check_agent')
        with self.assertRaises(protocol.Denied): protocol.envelope('forwarded_to_design', 'RFI-1', sender, 'design', {})
        protocol.envelope('check_result', 'RFI-1', sender, 'gc', {})

    def test_transitions(self):
        self.assertEqual(protocol.next_status('forward', 'submitted'), 'forwarded')
        with self.assertRaises(protocol.Denied): protocol.next_status('respond', 'submitted')

    def test_audit_chain_detects_tampering(self):
        log = protocol.AuditLog(Path(tempfile.mkdtemp()) / 'a.jsonl')
        u = {'id': 'u', 'name': 'U', 'role': 'foreman'}
        for i in range(3): log.append(protocol.envelope('rfi_created', f'R{i}', protocol.actor_of(u), 'sub', {'i': i}))
        self.assertTrue(log.verify()['ok'])
        lines = log.path.read_text().splitlines(); lines[1] = lines[1].replace('"i": 1', '"i": 9')
        log.path.write_text('\n'.join(lines) + '\n')
        self.assertEqual(log.verify(), {'ok': False, 'broken_at_record': 2})


class Code(unittest.TestCase):
    def test_lookup_revisions_and_nonexistent(self):
        rows = {r['sheet']: r['status'] for r in agents.lookup('E301, E-801, A-102', 1, CTX)}
        self.assertEqual(rows, {'E-301': 'revised_since_your_set', 'E-801': 'current', 'A-102': 'not_in_index'})

    def test_dates(self):
        self.assertEqual(agents.parse_date('need it by 9/20'), '2023-09-20')
        self.assertIsNone(agents.parse_date('3-1/2" conduit'))
        self.assertIsNone(agents.parse_date('asap'))

    def test_guard_blocks_invented_values(self):
        c = CASES['F03']
        d = agents.draft_agent(c['message'], c['sheets_as_written'], c['drawing_set'], CTX, {'key': 'k', 'model': 'm', 'provider': 'gemini'})
        self.assertEqual(d['location']['value'], '')                       # "Room 221" is not in the message
        self.assertIn('location', [g['field'] for g in d['guard_blocked']])
        self.assertIn('location', [q['field'] for q in d['questions_for_sub']])

    def test_asap_is_not_a_date(self):
        c = CASES['F02']
        d = agents.draft_agent(c['message'], c['sheets_as_written'], c['drawing_set'], CTX, {'key': 'k', 'model': 'm', 'provider': 'gemini'})
        self.assertEqual(d['needed_by']['value'], '')
        self.assertIn('needed_by', [q['field'] for q in d['questions_for_sub']])

    def test_split_multi_question_rfi(self):
        """Added after stakeholder testing: one RFI per question."""
        cfg = {'key': 'k', 'model': 'm', 'provider': 'gemini'}
        c = CASES['F05']
        d = agents.draft_agent(c['message'], c['sheets_as_written'], c['drawing_set'], CTX, cfg)
        self.assertEqual(len(d['split_suggestion']), 2)
        self.assertTrue(any('its own RFI' in q['ask'] for q in d['questions_for_sub']))
        c = CASES['F03']
        d = agents.draft_agent(c['message'], c['sheets_as_written'], c['drawing_set'], CTX, cfg)
        self.assertEqual(d['split_suggestion'], [])

    def test_watch_agent_remembers(self):
        rfis = [{'id': c['case_id'], 'status': 'submitted', 'drawing_set': c['drawing_set'], 'final': None,
                 'rough': {'message': c['message'], 'sheets_as_written': c['sheets_as_written']}} for c in CASES.values()]
        seen = set()
        first = [a for n in range(1, 7) for a in agents.watch_agent(rfis, n, CTX, seen)]
        self.assertEqual(sorted({(a['rfi_id'], a['sheet']) for a in first}), [('F01', 'E-301'), ('F07', 'E-600')])
        again = [a for n in range(1, 7) for a in agents.watch_agent(rfis, n, CTX, seen)]
        self.assertEqual(again, [])


class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app
        cls.app = app
        cls.srv = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.base = f'http://127.0.0.1:{cls.srv.server_address[1]}'
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def client(self, user, pin):
        jar = http.cookiejar.CookieJar()
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

        def call(path, body=None):
            req = urllib.request.Request(self.base + path, data=None if body is None else json.dumps(body).encode(),
                                         headers={'Content-Type': 'application/json'}, method='GET' if body is None else 'POST')
            try:
                with op.open(req) as r:
                    data = r.read(); return r.status, (json.loads(data) if r.headers.get_content_type() == 'application/json' else data.decode())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        self.assertEqual(call('/api/login', {'user_id': user, 'pin': pin})[0], 200)
        return call

    def test_full_exchange(self):
        sam = self.client('u-foreman', '1111'); jordan = self.client('u-site', '2222')
        priya = self.client('u-pm', '3333'); morgan = self.client('u-arch', '4444')
        code, r = sam('/api/rfis', {'case_id': 'F03'}); self.assertEqual(code, 200); rid = r['id']
        self.assertEqual(jordan(f'/api/rfis/{rid}/forward', {})[0], 403)            # not submitted yet: move not allowed
        self.assertEqual(sam(f'/api/rfis/{rid}/forward', {})[0], 403)               # foreman cannot forward
        self.assertEqual(sam(f'/api/rfis/{rid}/draft', {'use_ai': True})[0], 200)
        final = {'title': 'Floor finish', 'question': 'Terrazzo or VCT in Room 221?', 'location': 'Room 221, Level 2',
                 'needed_by': '2023-11-10', 'impact': 'Floor prep on hold', 'references': 'A-502, ID-015', 'trade': 'Flooring'}
        self.assertEqual(sam(f'/api/rfis/{rid}/approve', final)[0], 200)
        self.assertEqual(morgan(f'/api/rfis/{rid}')[0], 403)                        # architect cannot see it yet
        code, out = jordan(f'/api/rfis/{rid}/check', {'use_ai': True}); self.assertEqual(code, 200)
        self.assertEqual(out['rfi']['check']['recommendation'], 'forward_to_design')
        self.assertEqual(jordan(f'/api/rfis/{rid}/return', {'note': 'Add the photo'})[0], 200)
        final['question'] = 'Please confirm whether terrazzo or VCT is required in Room 221.'
        self.assertEqual(sam(f'/api/rfis/{rid}/approve', final)[0], 200)
        jordan(f'/api/rfis/{rid}/check', {'use_ai': True})                          # now flags possible cost/scope
        code, out = jordan(f'/api/rfis/{rid}/forward', {'note': '', 'review_seconds': 42})
        self.assertEqual(out['rfi']['status'], 'cost_review')
        self.assertEqual(jordan(f'/api/rfis/{rid}/ack_cost', {})[0], 403)           # only the PM signs off
        self.assertEqual(priya(f'/api/rfis/{rid}/ack_cost', {})[1]['rfi']['status'], 'forwarded')
        q = morgan('/api/triage')[1]; self.assertEqual(q[0]['rfi_id'], rid)
        self.assertEqual(morgan(f'/api/rfis/{rid}/respond', {'answer': 'Provide VCT per ID-015.'})[1]['rfi']['status'], 'answered')
        panel = priya('/api/panel')[1]
        self.assertEqual(panel['round_trips']['returns'], 1)
        self.assertTrue(panel['audit']['ok'])
        self.assertEqual(panel['gc_first_review_seconds']['median'], 42)
        code, csv_text = priya('/api/export/rfi_log.csv'); self.assertIn(rid, csv_text)
        self.assertEqual(jordan('/api/panel')[0], 403)                              # metrics are PM-only

    def test_watcher_and_alerts(self):
        sam = self.client('u-foreman', '1111'); priya = self.client('u-pm', '3333')
        priya('/api/watch/reset', {'issued_through': 1})
        rid = sam('/api/rfis', {'case_id': 'F01'})[1]['id']
        out = priya('/api/watch/next', {})[1]
        self.assertEqual(out['addendum'], 2)
        self.assertIn(rid, [a['rfi_id'] for a in out['alerts']])
        key = next(a['key'] for a in out['alerts'] if a['rfi_id'] == rid)
        self.assertEqual(priya('/api/alerts/' + urllib.request.quote(key), {'verdict': 'useful'})[1]['status'], 'useful')
        self.assertEqual(sam('/api/watch/next', {})[0], 403)

    def test_wrong_pin(self):
        req = urllib.request.Request(self.base + '/api/login', data=json.dumps({'user_id': 'u-pm', 'pin': '0000'}).encode(),
                                     headers={'Content-Type': 'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as e: urllib.request.urlopen(req)
        self.assertEqual(e.exception.code, 401)


if __name__ == '__main__':
    unittest.main()
