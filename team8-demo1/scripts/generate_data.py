"""Reproducible, deterministic transformations of documented bid-stage questions.
No LLM is used in data generation. All construction-stage details are simulated.
Run from any working directory: python3 scripts/generate_data.py
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBC = 'https://pbcchicago.com/wp-content/uploads/2023/06/'
URL5 = PBC + 'AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo5_20230609_Final.pdf'
URL6 = PBC + 'AD_PBC_PXM_RNDettESAnnexandRenoC1604_AddendumNo6_20230615_Final.pdf'


def generate():
    # Short paraphrases, not copied questions. Historical answers remain evaluator-only.
    seeds = [
        ('D01',5,2,2,'Camera specification','Electrical','Camera installation areas',
         'Please clarify the camera type for the added camera locations.',
         'E-202, E-203, E-204','Referenced electrical sheets were revised.',
         ['location','needed_by']),
        ('D02',5,3,2,'Countertop information','Casework','Hallway 101; Rooms 105 and 107',
         'Please clarify the conflicting countertop material notes.',
         'A-210, A-703','A-210 and A-221 were revised.', ['references']),
        ('D03',5,7,3,'Plumbing scope','Plumbing','Toilet rooms 140 and 143',
         'Please clarify the conflicting existing and new plumbing scope.',
         'P-100A, P-201, P-202','P-201 and P-202 were revised.', ['impact']),
        ('D04',6,2,2,'PV conduit information','Electrical','PV equipment feeder',
         'Please clarify the conduit size where the electrical and PV sheets disagree.',
         'E-600, PV-600','The electrical and PV sheets were updated.', ['needed_by']),
        ('D05',6,3,2,'Metering detail','Electrical','Circuit metering installation',
         'Please provide the metering wiring detail and equipment specification.',
         'E-702','Scope was clarified on E-702.', ['trade']),
        ('D06',6,4,2,'Item beside sink','Casework','Care Room 101E',
         'Please clarify whether the item beside the sink is casework or furniture.',
         'A-210','The response identifies owner furniture.', []),
    ]
    cases, keys = [], []
    for cid,add,no,page,title,trade,loc,q,refs,answer,missing in seeds:
        source = {'id':f'Dett-A{add}-RFI{no}', 'addendum':add, 'rfi':no,
                  'pdf_page':page, 'url':URL5 if add==5 else URL6,
                  'type':'public bid-stage question; paraphrased'}
        complete = {'title':title,'location':loc,'trade':trade,'question':q,
                    'needed_by':'2026-10-23','impact':'Work planning is waiting for clarification.',
                    'references':refs}
        initial = copy.deepcopy(complete)
        for field in missing: initial[field]=''
        cases.append({'case_id':cid,'is_simulated':True,'source':source,
          'initial':initial,
          'brief':{'known_details':complete,
             'simulation_note':'Construction setting, trade assignment, needed-by date and impact are invented for this exercise. Some location wording is generalized. Historical design answers are not supplied to the agent.'}})
        keys.append({'case_id':cid,'expected_missing_fields':missing,
                     'historical_response_summary':answer,'source':source,
                     'scoring_note':'Pilot annotation only. Review against the full source and chosen field rubric before an experiment. A blank field can be satisfied elsewhere in the text.'})
    index={}
    # Partial index: observed citations and revision lists, NOT a complete drawing register.
    for sheets,add,page in [(['A-210','A-221','A-703','E-010','E-202','E-203','E-204','P-201','P-202'],5,1),
                            (['P-100A'],5,3),
                            (['E-600','PV-600','E-702'],6,1)]:
        for sheet in sheets:
            index[sheet]={'source_label':f'Dett Addendum {add}, PDF page {page}',
                          'url':URL5 if add==5 else URL6,'page':page}
    for name,data in [('cases.json',cases),('answer_key.json',keys),('drawing_index.json',index)]:
        (ROOT/'data'/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Generated {len(cases)} simulated cases and {len(index)} partial-index entries.')


if __name__=='__main__': generate()
