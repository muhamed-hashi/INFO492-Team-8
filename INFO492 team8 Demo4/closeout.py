"""Demo #4 close-out agent (GC): check what an answered RFI committed to before the project manager closes it.

An architect's RFI answer often says "refer to revised Drawing E-304 included in this addendum". That is a
commitment. If the revised sheet never appears in the addendum's drawing list, or the change was pushed to
the Issue for Construction (IFC) set, closing the RFI now means the site may build from an old drawing.

Split of work, same rule as Demo #3:
    code   finds sheet numbers, looks them up in the drawing list attached to each addendum, finds near
           matches (possible typos) and points to the PDF page that proves it. Code never guesses.
    AI     reads the answer and says what it committed to: which sheets it says were REVISED (not just
           referred to) and whether anything is still to be issued later. Every claim needs a quote from the
           answer; a guard drops claims whose quote or sheet number is not in the answer.
    person the project manager closes the RFI, keeps it open, or asks the architect. The agent only recommends.

Recommendations: ok_to_close, keep_open (carry to the IFC set), hold (revised sheet not issued), check (a person
must look: possible wrong sheet number, or the answer is unclear).
"""
import re

import agents
from core import normalize_sheet

LABELS = {'ok_to_close': 'OK to close', 'keep_open': 'Keep open: carry to IFC set',
          'hold': 'Hold: revised sheet not issued', 'check': 'Check: a person should look'}
REVISED_WORDS = re.compile(r'\brevis\w*|\bupdated\b|\bhas been (?:added|changed)|\bhave been (?:added|changed)', re.I)
DEFER_WORDS = re.compile(r'issue[ds]? for construction|\bIFC\b|will be (?:issued|revised|updated|shown|reflected|provided)'
                         r'|future (?:addend\w+|revision|bulletin)|to follow\b|forthcoming|after (?:the )?permit', re.I)
ADDENDUM_REF = re.compile(r'(?:issued|included|provided)\s+(?:in|with)\s+Addend(?:um|a)\s+(?:No\.?\s*)?(\d)', re.I)


def norm(sheet):
    """'A102B', 'a-102b' -> 'A-102B' so lists and answers compare equal."""
    m = re.match(r'^([A-Z]{1,3})-?(\d{1,3}[A-Z]?)$', normalize_sheet(sheet))
    return f'{m.group(1)}-{m.group(2)}' if m else normalize_sheet(sheet)


class DrawingLists:
    """The drawings attached to each addendum. `remove` drops (addendum, sheet) pairs; the evaluation uses it
    to plant a missing revision. The real data is never changed on disk."""

    def __init__(self, data, remove=()):
        self.url = {a['addendum']: a.get('url', '') for a in data['addenda']}
        self.items = {a['addendum']: {norm(d['sheet']): d for d in a['drawings']} for a in data['addenda']}
        self.prefixes = {x.split('-')[0] for v in self.items.values() for x in v}    # discipline letters in use
        for n, s in remove:
            self.items.get(n, {}).pop(norm(s), None)

    def item(self, addendum, sheet):
        return self.items.get(addendum, {}).get(norm(sheet))

    def where(self, sheet):
        return [n for n in sorted(self.items) if norm(sheet) in self.items[n]]

    def near(self, addendum, sheet):
        """Sheets in that addendum's list that look like a typo of `sheet`: same discipline and number but a
        different or missing suffix letter (A-301 / A-301B), two neighbouring digits swapped (E-340 / E-304), or
        the same number with one letter more or less in the discipline (SD-300 / S-300), but only when the written
        discipline does not exist in the project (ED-304 is a real electrical demolition sheet, not a typo of E-304)."""
        s = norm(sheet)
        m = re.match(r'^([A-Z]{1,3})-(\d+)([A-Z]?)$', s)
        if not m: return []
        out = []
        for x in self.items.get(addendum, {}):
            k = re.match(r'^([A-Z]{1,3})-(\d+)([A-Z]?)$', x)
            if not k or x == s: continue
            a, b = m.group(2), k.group(2)
            p, q = m.group(1), k.group(1)
            if p != q:
                if p not in self.prefixes and a == b and m.group(3) == k.group(3) and abs(len(p) - len(q)) == 1 and (p.startswith(q) or q.startswith(p)):
                    out.append(x)
                continue
            swapped = len(a) == len(b) and sum(i != j for i, j in zip(a, b)) == 2 and sorted(a) == sorted(b) and \
                any(a[i] == b[i + 1] and a[i + 1] == b[i] for i in range(len(a) - 1))
            if (a == b and m.group(3) != k.group(3)) or (swapped and m.group(3) == k.group(3)):
                out.append(x)
        return sorted(out)[:3]

    def evidence(self, addendum, sheet):
        d = self.item(addendum, sheet)
        return {'sheet': norm(sheet), 'addendum': addendum, 'item': d['no'], 'pdf_page': d['pdf_page'], 'dated': d['dated'],
                'title': d['title'], 'url': f"{self.url.get(addendum, '')}#page={d['pdf_page']}",
                'text': f"{norm(sheet)} is item {d['no']} in the drawing list attached to Addendum {addendum} "
                        f"(PDF page {d['pdf_page']}{', dated ' + d['dated'] if d['dated'] else ''})."}


def case_lists(case, data):
    """Drawing lists for one test case. Dett cases use the real addendum lists (minus any planted removal).
    Cases from another project (our stakeholder's) carry their own `issued_sheets`: the sheets actually issued
    with or after that answer (from the bulletin, ASI or sketch log), treated as one addendum."""
    if case.get('issued_sheets') is not None:
        own = {'addenda': [{'addendum': int(case.get('addendum') or 1), 'url': '',
                            'drawings': [{'no': i + 1, 'sheet': s, 'title': '', 'dated': '', 'pdf_page': ''}
                                         for i, s in enumerate(case['issued_sheets'])]}]}
        return DrawingLists(own)
    return DrawingLists(data, remove=[tuple(x) for x in case.get('remove_from_list', [])])


# --------------------------------------------------------------------------- code facts and the code-only baseline
SPACED_SHEET = re.compile(r'\b([A-Z]{1,3})-\s+(\d{3}[A-Z]?)\b', re.I)    # "P- 500" (a line break in the PDF)
SHEET_SERIES = re.compile(r'\b([A-Z]{1,3})\s+(?:sheets|drawings)\s+((?:\d{3}[A-Z]?(?:\s*,\s*(?:and\s+)?|\s+and\s+)?)+)')


def sheets_in(text):
    """Every sheet number in the text, including series such as 'ID sheets 010, 011 and 012'."""
    out = [norm(s) for s in agents.find_sheets(text)]
    for prefix, num in SPACED_SHEET.findall(text or ''):
        s = norm(f'{prefix.upper()}-{num.upper()}')
        if s not in out: out.append(s)
    for prefix, nums in SHEET_SERIES.findall(text or ''):
        for n in re.findall(r'\d{3}[A-Z]?', nums):
            s = norm(f'{prefix}-{n}')
            if s not in out: out.append(s)
    return out


def facts(rfi):
    """What code can read from the answer without understanding it."""
    text = rfi['response']
    m = ADDENDUM_REF.search(text)
    return {'sheets': sheets_in(text),
            'target_addendum': int(m.group(1)) if m else int(rfi['addendum']),
            'revision_words': bool(REVISED_WORDS.search(text)),
            'defer_words': [x.group(0) for x in DEFER_WORDS.finditer(text)]}


def verify(sheets, target, lists):
    """Look each sheet up in the target addendum's drawing list. Returns found evidence, missing sheets, near matches."""
    found, missing, near = [], [], {}
    for s in sheets:
        if lists.item(target, s):
            found.append(lists.evidence(target, s))
        else:
            missing.append(s)
            close = lists.near(target, s)
            if close: near[s] = close
    return found, missing, near


def decide(target, revised, later, lists, unclear=False):
    """Shared rules that turn (revised sheets, later work) into a recommendation with reasons and evidence."""
    found, missing, near = verify(revised, target, lists)
    reasons = []
    if later:
        reasons.append(f'The answer says something is still to come: "{later}". Keep the RFI open until it is issued '
                       f'(the addenda say changes from RFI answers go into the Issue for Construction set).')
    for s in missing:
        elsewhere = [n for n in lists.where(s) if n != target]
        if s in near:
            reasons.append(f'{s} is not in the drawing list attached to Addendum {target}. Did the answer mean '
                           f'{" or ".join(near[s])}? A person should confirm the sheet number.')
        else:
            reasons.append(f'The answer says {s} was revised, but {s} is not in the drawing list attached to Addendum '
                           f'{target}' + (f' (it appears in Addendum {", ".join(map(str, elsewhere))}).' if elsewhere else '.')
                           + ' Ask the architect to issue it or confirm where it was issued.')
    for e in found:
        reasons.append(e['text'])
    if unclear and not reasons:
        reasons.append('The answer is not clear about what changed. A person should read it.')
    if later:
        rec = 'keep_open'
    elif missing:
        rec = 'check' if all(s in near for s in missing) else 'hold'
    elif unclear:
        rec = 'check'
    else:
        rec = 'ok_to_close'
    if rec == 'ok_to_close' and not found:
        reasons.append('The answer clarifies the documents and does not say any drawing was revised.')
    return {'recommendation': rec, 'label': LABELS[rec], 'reasons': reasons, 'evidence': found,
            'missing': missing, 'near_matches': near, 'target_addendum': target}


def code_closeout(rfi, lists):
    """Baseline with no AI: treat every sheet in an answer that mentions a revision as 'revised', and any
    deferral keyword as 'still to come'. Fast and transparent, but it cannot tell 'revised' from 'see also'."""
    f = facts(rfi)
    revised = f['sheets'] if f['revision_words'] else []
    later = f['defer_words'][0] if f['defer_words'] else ''
    unclear = f['revision_words'] and not f['sheets'] and not later
    out = decide(f['target_addendum'], revised, later, lists, unclear=unclear)
    return dict(out, source='code', facts=f)


# --------------------------------------------------------------------------- AI reading + code verification
CLOSEOUT_SCHEMA = {'type': 'object', 'additionalProperties': False,
    'required': ['commitment', 'revised_sheets', 'referenced_only', 'later_action', 'reason'],
    'properties': {
        'commitment': {'type': 'string', 'enum': ['no_change', 'revised_drawings', 'spec_or_document_change',
                                                  'change_to_be_issued_later', 'unclear']},
        'revised_sheets': {'type': 'array', 'maxItems': 12, 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['sheet', 'quote'], 'properties': {'sheet': {'type': 'string'}, 'quote': {'type': 'string'}}}},
        'referenced_only': {'type': 'array', 'maxItems': 12, 'items': {'type': 'string'}},
        'later_action': {'type': 'object', 'additionalProperties': False, 'required': ['needed', 'quote'],
                         'properties': {'needed': {'type': 'boolean'}, 'quote': {'type': 'string'}}},
        'reason': {'type': 'string'}}}


def _quoted(quote, text):
    return bool(quote) and agents._norm(quote) in agents._norm(text)


def closeout_agent(rfi, lists, cfg=None):
    """AI reads the commitment; a guard checks every claim against the answer; code verifies and decides."""
    cfg = cfg or agents.settings()
    f = facts(rfi)
    out, meta = agents._ai(cfg, 'closeout_agent.txt',
                           {'rfi_question': rfi.get('question', ''), 'architect_answer': rfi['response'],
                            'sheet_numbers_in_answer': f['sheets']}, CLOSEOUT_SCHEMA)
    guard = []
    revised = []
    for x in out.get('revised_sheets') or []:
        s = norm(str(x.get('sheet', '')))
        if s not in f['sheets']:                 # "010" for "ID sheets 010, 011": map if exactly one sheet matches
            same = [c for c in f['sheets'] if c.split('-')[-1] == s.split('-')[-1]]
            if len(same) == 1: s = same[0]
        if s not in f['sheets']:
            guard.append(f'Dropped "{s}": that sheet number is not in the answer.')
        elif not _quoted(str(x.get('quote', '')), rfi['response']):
            guard.append(f'Dropped "{s}": the quote given for it is not in the answer.')
        elif s not in revised:
            revised.append(s)
    la = out.get('later_action') or {}
    later = ''
    if la.get('needed'):
        if _quoted(str(la.get('quote', '')), rfi['response']):
            later = str(la['quote']).strip()
        else:
            guard.append('Dropped a "still to be issued" claim: its quote is not in the answer.')
    commitment = out.get('commitment', 'unclear')
    unclear = commitment == 'unclear' or (commitment == 'revised_drawings' and not revised and not later) or \
        (commitment == 'change_to_be_issued_later' and not later)
    res = decide(f['target_addendum'], revised, later, lists, unclear=unclear)
    if guard and res['recommendation'] == 'ok_to_close':
        # something the AI claimed could not be checked: never close silently on a partial reading
        res.update(recommendation='check', label=LABELS['check'])
        res['reasons'].insert(0, 'Part of the AI reading could not be checked against the answer (see Guard). '
                                 'A person should read the answer before closing.')
    if commitment == 'spec_or_document_change' and res['recommendation'] == 'ok_to_close':
        res['reasons'].append('The answer changes a specification or bid document. Code checks drawing lists only, '
                              'so the specification change itself was not verified.')
    return dict(res, source='AI + code', facts=f, commitment=commitment, revised_sheets=revised,
                referenced_only=[norm(s) for s in out.get('referenced_only') or [] if norm(s) in f['sheets']],
                ai_reason=str(out.get('reason', ''))[:600], guard=guard, meta=meta)
