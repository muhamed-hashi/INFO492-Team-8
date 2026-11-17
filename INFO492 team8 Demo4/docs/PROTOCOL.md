# Multi-party protocol (Demo #4)

Demo #4 keeps the Demo #3 exchange unchanged and adds **close-out**: the step before the GC closes an RFI the
architect has answered. Additions are marked **(Demo #4)**.

One RFI moves between three parties. Each party has human roles and its own agent. The rules below are
enforced in code (`protocol.py`), not just described.

## Roles and what they may do

| Role | Party | May |
|---|---|---|
| Foreman | Subcontractor | create an RFI, ask the draft agent, approve and send, revise after a return; sees only their own RFIs |
| Site Manager / Assistant PM | GC | run the check agent, return to the sub, answer as GC, forward to the architect, handle revision alerts; **(Demo #4)** run the close-out agent |
| Project Manager | GC | everything the site manager may, plus sign off cost/scope items, see the control panel, issue addenda (project clock), export the RFI log; **(Demo #4)** close an RFI, keep it open, or ask the architect a close-out question |
| Architect | Design team | see forwarded RFIs, see the triage queue, respond; **(Demo #4)** see and reply to close-out questions sent to the design team (nothing else in the close-out log) |

Sign-in: each demo user has a PIN (README). This shows role-based access; it is not production authentication.

## Agents

| Agent | Works for | May send | Uses AI? |
|---|---|---|---|
| `draft_agent` | Foreman | `draft_suggestion` | Yes, for wording and spotting what is missing. Code looks up sheets and dates; a guard removes any location, date or impact the AI filled in that the foreman's message does not contain. |
| `check_agent` | Site manager | `check_result` | Code checks blanks, dates, sheet numbers and revisions; AI judges whether location and impact are specific, the route (GC or design team), and possible cost/scope. |
| `triage_agent` | Architect | `triage_note` | No. Orders the queue by days left and stated impact. Never drafts a design answer. |
| `watch_agent` | Site manager | `revision_alert`, `escalation` | No. Runs when an addendum is issued (button, or `--watch-every N` seconds). |
| `closeout_agent` **(Demo #4)** | Project manager | `closeout_check` | Yes, only to read what the architect's answer committed to (which sheets it says were revised, anything still to be issued). Every claim needs a quote from the answer; a guard drops claims whose quote or sheet number is not in the answer. Code checks each revised sheet against the drawing list attached to the addendum and makes the recommendation. |

**Authority to respond:** agents can only send the message types above. Any attempt by an agent to send a
decision (`returned_to_sub`, `forwarded_to_design`, `gc_answer`, `design_response`, `cost_acknowledged`,
`closeout_decision`) raises
an error. Every status change needs a signed-in human whose role allows it.

## RFI life cycle

```
rough --draft agent--> drafted --foreman approves--> submitted --GC--> returned --foreman--> submitted ...
                                                         |--GC answers--> answered_by_gc
                                                         |--GC forwards--> forwarded --architect--> answered
                                                         '--forward + cost/scope flag--> cost_review --PM signs off--> forwarded
```

## Close-out (Demo #4)

```
answered --close-out agent recommends (ok to close / keep open / hold / check)--> PM decides:
    close             -> closed          (closing against the advice needs a written reason, recorded as an override)
    keep open         -> kept_open       (the change goes into the Issue for Construction set)
    ask the architect -> asked_architect --architect replies--> architect_replied --PM decides again
```

Why this step: every Dett addendum says "Drawings/specifications corresponding to inquiry responses will be
issued with the Issue for Construction Documents". An RFI answer that promises a revised sheet is a commitment;
if the RFI is closed before the sheet is issued, the field can build from the old drawing.

## Escalation

- **Cost or scope:** if the check agent flags a possible cost/scope change, a site manager's "forward" stops
  at `cost_review` until the project manager signs off. (From our interview: some RFIs set up a later change order.)
- **Deadline:** an open RFI within 5 days of its response date is escalated to the project manager once.
- **New drawings:** when an addendum is issued, the watch agent alerts on open RFIs that cite a sheet revised
  after the drawing set the RFI was written from. People mark each alert useful or wrong (so false alarms are counted).

## Message format

Demo #4 adds four message types: `closeout_check` (agent → GC), `closeout_decision` (PM → GC record),
`closeout_query` (PM → design team) and `closeout_reply` (architect → GC).

Every exchange is one JSON envelope, and every envelope is written to the audit trail:

```json
{
  "msg_id": "M-3f9c1a2b7d",
  "type": "draft_suggestion",
  "rfi_id": "RFI-004",
  "from": {"kind": "agent", "id": "draft_agent", "party": "sub", "acts_for": "foreman"},
  "to_party": "sub",
  "at": "2026-11-02T18:04:11+00:00",
  "body": {"to_role": "foreman", "draft": {"question": "...", "questions_for_sub": ["..."]}},
  "prev_hash": "a41c…",
  "hash": "9be0…"
}
```

## Audit trail

`runtime/audit.jsonl` is append-only. Each record stores the SHA-256 of the record before it, so editing or
deleting any earlier record breaks the chain. The control panel shows whether the chain is intact
(`AuditLog.verify()`), and every RFI page shows its own messages.

## Integration (sandbox)

The project manager can export the RFI log as a CSV with Procore-style columns (Number, Subject, Status,
Received From, Responsible Contractor, Due Date, Drawing Number, …). Nothing is written to any outside system.
