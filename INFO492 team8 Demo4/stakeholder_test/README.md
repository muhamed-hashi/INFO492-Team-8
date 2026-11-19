# Stakeholder test, Demo #4 (Nov 18, 2026)

Recorded video call (16 minutes). A teammate shared the GC side of the live system; our stakeholder Kevin Chen
(assistant PM at a general contractor) judged each check result. He agreed to the recording and its use in our class.

- `rfi-demo4-transcript.txt`: transcript as spoken (Chinese with English terms).
- `Kevin_Chen_Demo4_system_test.md.pdf`: English translation by the team (filler words lightly cleaned up).
- The video recording is kept in the team's shared drive.

## What was tested

The **GC check on incoming RFIs** (Inbox → "Run check agent"), Site Manager role, on rough sub messages F01–F07
from `data/rough_rfis.json`. These are our simulated foreman messages built from real Dett RFIs (not the GWA log),
submitted from the sub side the day before, some with deliberately messy dates. He reviewed 7 of 8; the
close-out agent, the answer check and the review workbook (`data/kevin_review_demo4.xlsx`) were not part of
this session. (During the call the RFIs were described as coming from the public project he had sent; they are
the Dett-based rough messages above.)

## What he said

| RFI | Tool said | His call |
|---|---|---|
| F01 gym office fixture | return: date not read, impact vague | Impact vague is real; "2024/6/23" is a normal date our parser failed to read. Nothing invented. |
| F02 conduits IDF→MDF | return: impact, date missing; location vague | Impact and date real. Location is half a false alarm: a route has no room number; ask *which* IDF. |
| F03 terrazzo vs VCT | return: impact vague, date | Impact vague is real (price, lead time, maybe a change order). It missed: which bathroom (room number), which sheet the finish schedule is on. Inconsistent with F02. |
| F04 caisson concrete | no issues, forward to architect | Agrees: well written, can go straight through. |
| F05 lockers | A-102 not current (shown twice); split into 3 questions | Duplicate finding should be merged. Splitting is a false alarm (same item, same spec section). It missed: the size was scaled from a "do not scale" drawing; the GC may answer from spec 10 51 13 itself. |
| F06 countertop, Hallway 101 | location missing | False alarm: the location is in the title and question; the AI only checked the empty field. It missed: the floor-plan sheet with keynotes A.18/A.19 is not cited. He would call the sub, fill in, and forward. |
| F07 fire pump feeder | location missing; return | Location is a false alarm (feeder S4-8 on E-600 pins it down). It missed the real issue: #8 wire is undersized for a 40 hp, 480 V pump; "FP-2O0" is a typo and that sheet is not cited. Life safety on the critical path: forward now, call the sub for the date. |

Summary in his words (translated): "after looking at seven, I think the AI never once made anything up", and a
well-written one "lets it go straight through, so as a format checker it's reliable." But "it only checks whether
fields are filled in and doesn't read the body text", "it sent back 6 out of 7", and "it misses the things that
really matter, like whether there's a suggested solution, what the proposed method is, and how urgent it is."
