"""Local-only RFI demo. Start: python3 app.py. Open http://127.0.0.1:8765."""
import argparse
import csv
import io
import json
import os
import sqlite3
import statistics
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from core import ROOT, ai_check, clean_rfi, digest, load_json, rule_check, settings

DB = Path(os.getenv('RFI_DB_PATH',str(ROOT/'runtime'/'demo.sqlite3')))
CONDITIONS=('manual','ai','rules')


def now_iso(): return datetime.now(timezone.utc).isoformat()


def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB,timeout=15)
    db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS preparations (id TEXT PRIMARY KEY, case_id TEXT, condition TEXT, started REAL, checks TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS trials (id TEXT PRIMARY KEY, preparation_id TEXT UNIQUE, payload TEXT)')
    return db


def fetch_trial(db,tid):
    row=db.execute('SELECT payload FROM trials WHERE id=?',(tid,)).fetchone()
    if not row: raise ValueError('Trial was not found on this computer.')
    return json.loads(row['payload'])


def save_trial(db,trial):
    db.execute('UPDATE trials SET payload=? WHERE id=?',(json.dumps(trial),trial['trial_id']))


def rows(db):
    return [json.loads(r['payload']) for r in db.execute('SELECT payload FROM trials ORDER BY rowid')]


def summarize(trials):
    groups={}
    for condition in CONDITIONS:
        done=[x for x in trials if x['condition']==condition and x.get('review_seconds') is not None]
        usable=[x for x in done if not x.get('interrupted')]
        scored=[x for x in usable if x.get('error_count') is not None]
        groups[condition]={'n':len(usable),'interrupted_excluded':len(done)-len(usable),
            'median_review_seconds':statistics.median(x['review_seconds'] for x in usable) if usable else None,
            'median_preparation_seconds':statistics.median(x['preparation_seconds'] for x in usable) if usable else None,
            'needs_clarification':sum(x['decision']=='needs_clarification' for x in usable),
            'ready_count':sum(x['decision']=='ready' for x in usable),
            'scored_count':len(scored),
            'mean_errors':statistics.mean(x['error_count'] for x in scored) if scored else None}
    baseline=groups['manual']['median_review_seconds']; ai=groups['ai']['median_review_seconds']
    reduction=round((baseline-ai)/baseline*100,1) if baseline and ai is not None else None
    return {'groups':groups,'observed_reduction_percent':reduction,
            'interpretation':'Descriptive pilot results only. Check case mix, decisions, errors, preparation effort and reviewer familiarity. Rule practice is excluded from the AI comparison.'}


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # Do not log RFI contents or secrets.

    def local_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')

    def send(self,status,value,ctype='application/json; charset=utf-8'):
        if ctype.startswith('application/json'): value=json.dumps(value,ensure_ascii=False).encode()
        elif isinstance(value,str): value=value.encode()
        self.send_response(status)
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(value)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers();self.wfile.write(value)

    def do_GET(self):
        if not self.local_host(): return self.send(403,{'error':'Use the local application address.'})
        path=urlparse(self.path).path
        assets={'/':'index.html','/review':'review.html','/app.js':'app.js',
                '/review.js':'review.js','/style.css':'style.css'}
        try:
            if path in assets:
                file=ROOT/'static'/assets[path]
                ctype={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[file.suffix]
                return self.send(200,file.read_bytes(),ctype)
            if path=='/api/config':
                cfg=settings()
                return self.send(200,{'ai_configured':bool(cfg['key']),'model':cfg['model'],'provider':cfg['provider'],
                    'cases':load_json('cases.json'),'drawing_index':load_json('drawing_index.json')})
            if path in ('/api/results','/api/export.json','/api/export.csv'):
                with connect() as db: trials=rows(db)
                if path=='/api/results': return self.send(200,{'trials':trials,'summary':summarize(trials)})
                if path=='/api/export.json': return self.send(200,{'schema_version':1,'exported_at':now_iso(),'trials':trials,'summary':summarize(trials)})
                keys=['trial_id','case_id','condition','reviewer','preparation_seconds','review_seconds','decision','interrupted','error_count','error_notes','review_notes','created_at']
                buf=io.StringIO(); writer=csv.DictWriter(buf,fieldnames=keys);writer.writeheader()
                for trial in trials:
                    row={k:trial.get(k,'') for k in keys}
                    # Prevent spreadsheet formulas when user-supplied notes are opened in Excel.
                    row={k:("'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v) for k,v in row.items()}
                    writer.writerow(row)
                return self.send(200,buf.getvalue(),'text/csv; charset=utf-8')
            self.send(404,{'error':'Not found'})
        except (ValueError,OSError) as exc: self.send(400,{'error':str(exc)})

    def do_POST(self):
        if not self.local_host(): return self.send(403,{'error':'Use the local application address.'})
        # Only the local UI can initiate AI calls or write trial records.
        allowed=f'http://{self.headers.get("Host","")}'
        if self.headers.get('Origin') not in (None,allowed):
            return self.send(403,{'error':'Cross-origin requests are not allowed.'})
        if self.headers.get('X-RFI-App')!='1': return self.send(403,{'error':'Open the local application to perform this action.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=80000: raise ValueError('Request is empty or too large.')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise ValueError('Expected a JSON object.')
            path=urlparse(self.path).path
            if path=='/api/preparations':
                condition=data.get('condition');cid=data.get('case_id')
                if condition not in CONDITIONS: raise ValueError('Choose a preparation condition.')
                if cid not in [x['case_id'] for x in load_json('cases.json')]+['CUSTOM']: raise ValueError('Choose a case.')
                pid=uuid.uuid4().hex
                with connect() as db: db.execute('INSERT INTO preparations VALUES (?,?,?,?,?)',(pid,cid,condition,time.time(),'[]'))
                return self.send(200,{'preparation_id':pid})
            if path in ('/api/check','/api/handoff'):
                rfi=clean_rfi(data.get('rfi'))
                with connect() as db:
                    p=db.execute('SELECT * FROM preparations WHERE id=?',(data.get('preparation_id'),)).fetchone()
                if not p: raise ValueError('Start a preparation session first.')
                with connect() as db:
                    if db.execute('SELECT id FROM trials WHERE preparation_id=?',(p['id'],)).fetchone():
                        raise ValueError('This preparation is already finalized. Start a new preparation.')
                checks=json.loads(p['checks'])
                if path=='/api/check':
                    if p['condition']=='manual': raise ValueError('Manual control sessions do not allow automated checks.')
                    start=time.time()
                    result=ai_check(rfi,load_json('drawing_index.json')) if p['condition']=='ai' else rule_check(rfi,load_json('drawing_index.json'))
                    checks.append({'at':now_iso(),'seconds':round(time.time()-start,3),'input':rfi,'input_sha256':digest(rfi),'output':result})
                    with connect() as db: db.execute('UPDATE preparations SET checks=? WHERE id=?',(json.dumps(checks),p['id']))
                    return self.send(200,result)
                if data.get('human_approved') is not True: raise ValueError('A human must review and confirm the final RFI.')
                if p['condition'] in ('ai','rules') and not checks:
                    raise ValueError('Run the selected check before exporting this condition. AI failures never count as AI checks.')
                tid=uuid.uuid4().hex
                trial={'trial_id':tid,'case_id':p['case_id'],'condition':p['condition'],'rfi':rfi,
                    'created_at':now_iso(),'preparation_seconds':round(time.time()-p['started'],2),
                    'checks':checks,'human_approved':True,'review_started':None,'review_seconds':None,
                    'reviewer':'','decision':None,'error_count':None,'interrupted':False}
                with connect() as db: db.execute('INSERT INTO trials VALUES (?,?,?)',(tid,p['id'],json.dumps(trial)))
                return self.send(200,{'trial_id':tid,'review_url':'/review#'+tid,'preparation_seconds':trial['preparation_seconds']})
            if path=='/api/start-review':
                reviewer=str(data.get('reviewer','')).strip()
                if not reviewer or len(reviewer)>60: raise ValueError('Enter a short reviewer alias, such as GC01.')
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    trial=fetch_trial(db,data.get('trial_id'))
                    if trial['review_seconds'] is not None: raise ValueError('This RFI has already been reviewed.')
                    if trial['review_started'] is None:
                        trial.update({'review_started':time.time(),'reviewer':reviewer});save_trial(db,trial)
                    elif trial['reviewer']!=reviewer: raise ValueError('Another reviewer started this trial.')
                return self.send(200,{'rfi':trial['rfi'],'elapsed':time.time()-trial['review_started']})
            if path=='/api/finish-review':
                decision=data.get('decision')
                if decision not in ('ready','needs_clarification'): raise ValueError('Choose a review decision.')
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    trial=fetch_trial(db,data.get('trial_id'))
                    if trial['review_started'] is None or trial['review_seconds'] is not None: raise ValueError('Review is not active.')
                    trial.update({'decision':decision,'review_seconds':round(time.time()-trial['review_started'],2),
                         'interrupted':data.get('interrupted') is True,'review_notes':str(data.get('notes',''))[:3000]})
                    save_trial(db,trial)
                return self.send(200,{'review_seconds':trial['review_seconds']})
            if path=='/api/score':
                n=data.get('error_count')
                if type(n) is not int or not 0<=n<=100: raise ValueError('Error count must be a whole number between 0 and 100.')
                with connect() as db:
                    trial=fetch_trial(db,data.get('trial_id'))
                    if trial['review_seconds'] is None: raise ValueError('Complete the review before scoring errors.')
                    trial.update({'error_count':n,'error_notes':str(data.get('notes',''))[:3000]})
                    save_trial(db,trial)
                return self.send(200,{'saved':True})
            self.send(404,{'error':'Not found'})
        except (ValueError,TypeError,KeyError) as exc: self.send(400,{'error':str(exc)})
        except sqlite3.IntegrityError: self.send(409,{'error':'This preparation is already finalized.'})
        except Exception:
            self.send(500,{'error':'The local operation failed. Check the setup guide and try again.'})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    if not (ROOT/'data'/'cases.json').exists():
        from scripts.generate_data import generate
        generate()
    with connect(): pass
    print(f'Team 8 RFI Review: http://127.0.0.1:{args.port}',flush=True)
    print('Keep this window open. Press Ctrl+C to stop. Local classroom prototype.',flush=True)
    try: ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
    except KeyboardInterrupt: print('\nStopped.')


if __name__=='__main__': main()
