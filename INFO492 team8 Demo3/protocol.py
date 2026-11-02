"""Demo #3 protocol: who may do what, the message format every party uses, and the audit trail.

Three parties exchange one RFI: the subcontractor, the general contractor (GC) and the design team.
Each party has human roles and its own agent. Agents only SUGGEST or FLAG; every decision that changes
an RFI's status is made by a signed-in human whose role allows it. The code below enforces that.
"""
import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- roles and permissions
PARTIES = {'sub': 'Subcontractor', 'gc': 'General contractor', 'design': 'Design team'}

ROLES = {
    'foreman': {'party': 'sub', 'title': 'Foreman (subcontractor)',
                'can': {'create', 'request_draft', 'approve_draft', 'revise', 'view_own'}},
    'site_manager': {'party': 'gc', 'title': 'Site Manager / Assistant PM (GC)',
                     'can': {'run_check', 'return', 'answer', 'forward', 'view_all', 'handle_alert'}},
    'project_manager': {'party': 'gc', 'title': 'Project Manager (GC)',
                        'can': {'run_check', 'return', 'answer', 'forward', 'ack_cost', 'view_all', 'handle_alert',
                                'metrics', 'run_watcher', 'export'}},
    'architect': {'party': 'design', 'title': 'Architect (design team)',
                  'can': {'view_forwarded', 'respond', 'run_triage'}},
}

# Agents act for one party. They may only produce these message types, never a decision.
AGENTS = {
    'draft_agent': {'party': 'sub', 'acts_for': 'foreman', 'may_send': {'draft_suggestion'},
                    'does': 'Turns a rough field message into a clearer RFI draft, cites where each part came from, '
                            'and asks the foreman for anything missing. Never invents locations, dates or sheet numbers.'},
    'check_agent': {'party': 'gc', 'acts_for': 'site_manager', 'may_send': {'check_result'},
                    'does': 'Checks a submitted RFI for missing information, sheet numbers that are not in the current '
                            'drawing index or were revised later, and possible cost/scope items. Recommends; the GC decides.'},
    'triage_agent': {'party': 'design', 'acts_for': 'architect', 'may_send': {'triage_note'},
                     'does': 'Orders the architect\'s queue by deadline and stated impact. Code only; it never drafts a design answer.'},
    'watch_agent': {'party': 'gc', 'acts_for': 'site_manager', 'may_send': {'revision_alert', 'escalation'},
                    'does': 'Runs on each new addendum (or on a timer), finds open RFIs that cite a sheet revised after the '
                            'drawing set the writer used, and escalates RFIs close to their response date. Code only.'},
}

# Which status each human action moves an RFI to, and from which statuses it is allowed.
TRANSITIONS = {
    'request_draft': ({'rough', 'drafted', 'returned'}, 'drafted'),
    'approve_draft': ({'rough', 'drafted', 'returned'}, 'submitted'),
    'return':        ({'submitted'}, 'returned'),
    'answer':        ({'submitted'}, 'answered_by_gc'),
    'forward':       ({'submitted', 'cost_review'}, 'forwarded'),
    'ack_cost':      ({'cost_review'}, 'forwarded'),
    'respond':       ({'forwarded'}, 'answered'),
}
OPEN_STATUSES = {'rough', 'drafted', 'submitted', 'returned', 'cost_review', 'forwarded'}

MESSAGE_TYPES = {'rfi_created', 'draft_suggestion', 'draft_approved', 'check_result', 'returned_to_sub',
                 'gc_answer', 'forwarded_to_design', 'cost_review_requested', 'cost_acknowledged', 'triage_note',
                 'design_response', 'revision_alert', 'alert_handled', 'escalation', 'session'}


class Denied(Exception):
    """A role or agent tried to do something it is not allowed to do."""


def can(role, action):
    return role in ROLES and action in ROLES[role]['can']


def require(user, action):
    if not user or not can(user['role'], action):
        who = ROLES.get(user['role'], {}).get('title', 'This role') if user else 'Nobody signed in'
        raise Denied(f'{who} is not allowed to {action.replace("_", " ")}.')


def can_view(user, rfi):
    if can(user['role'], 'view_all'): return True
    if user['role'] == 'foreman': return rfi['created_by'] == user['id']
    if user['role'] == 'architect': return rfi['status'] in ('forwarded', 'answered')
    return False


def next_status(action, current):
    allowed, target = TRANSITIONS[action]
    if current not in allowed:
        raise Denied(f'Cannot {action.replace("_", " ")} an RFI whose status is "{current}".')
    return target


# --------------------------------------------------------------------------- messages and audit trail
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def actor_of(user=None, agent=None):
    if agent:
        a = AGENTS[agent]
        return {'kind': 'agent', 'id': agent, 'party': a['party'], 'acts_for': a['acts_for']}
    return {'kind': 'human', 'id': user['id'], 'name': user['name'], 'role': user['role'], 'party': ROLES[user['role']]['party']}


def envelope(msg_type, rfi_id, sender, to_party, body):
    """The one message format all parties use. Every message is also an audit record."""
    if msg_type not in MESSAGE_TYPES: raise ValueError(f'Unknown message type {msg_type}.')
    if sender['kind'] == 'agent' and msg_type not in AGENTS[sender['id']]['may_send']:
        raise Denied(f"{sender['id']} may not send {msg_type}; agents can only suggest or flag.")
    return {'msg_id': 'M-' + uuid.uuid4().hex[:10], 'type': msg_type, 'rfi_id': rfi_id, 'from': sender,
            'to_party': to_party, 'at': now_iso(), 'body': body}


class AuditLog:
    """Append-only JSON Lines file. Each record stores the SHA-256 of the previous one, so editing or
    deleting an old record breaks the chain and verify() reports where."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def _last_hash(self):
        if not self.path.exists(): return '0' * 64
        last = None
        with open(self.path, encoding='utf-8') as f:
            for line in f:
                if line.strip(): last = line
        return json.loads(last)['hash'] if last else '0' * 64

    @staticmethod
    def _hash(record):
        body = {k: v for k, v in record.items() if k != 'hash'}
        return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def append(self, message):
        with self.lock:
            record = dict(message, prev_hash=self._last_hash())
            record['hash'] = self._hash(record)
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            return record

    def records(self, rfi_id=None):
        if not self.path.exists(): return []
        with open(self.path, encoding='utf-8') as f:
            out = [json.loads(line) for line in f if line.strip()]
        return [r for r in out if rfi_id is None or r.get('rfi_id') == rfi_id]

    def verify(self):
        prev = '0' * 64
        for i, r in enumerate(self.records(), 1):
            if r.get('prev_hash') != prev or self._hash(r) != r.get('hash'):
                return {'ok': False, 'broken_at_record': i}
            prev = r['hash']
        return {'ok': True, 'records': len(self.records())}
