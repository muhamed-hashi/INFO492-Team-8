"""RFI review logic and the Gemini and OpenAI adapters. No third-party packages."""
import hashlib
import json
import os
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ('title','location','trade','question','needed_by','impact','references')
CHECK_FIELDS = FIELDS[1:]
MODEL_DEFAULT = 'gpt-4.1-mini-2025-04-14'
GEMINI_MODEL_DEFAULT = 'gemini-3.5-flash-lite'


def load_json(name):
    return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))


def settings():
    config = {}
    path = ROOT/'config.local.json'
    if path.exists():
        try:
            config = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            raise ValueError('config.local.json is not valid JSON. Check the setup guide.')
        if not isinstance(config,dict): raise ValueError('config.local.json must contain an object.')
    gemini_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or str(config.get('GEMINI_API_KEY',''))
    openai_key=os.getenv('OPENAI_API_KEY') or str(config.get('OPENAI_API_KEY',''))
    provider=(os.getenv('AI_PROVIDER') or config.get('AI_PROVIDER') or
              ('gemini' if gemini_key or not openai_key else 'openai'))
    if provider not in ('gemini','openai'): raise ValueError('AI_PROVIDER must be gemini or openai.')
    if provider=='gemini':
        return {'provider':provider,'key':gemini_key,
                'model':os.getenv('GEMINI_MODEL') or str(config.get('GEMINI_MODEL',GEMINI_MODEL_DEFAULT))}
    return {'provider':provider,'key':openai_key,
            'model':os.getenv('OPENAI_MODEL') or str(config.get('OPENAI_MODEL',MODEL_DEFAULT))}


def clean_rfi(value):
    if not isinstance(value,dict): raise ValueError('RFI must be an object.')
    result = {}
    for field in FIELDS:
        s = value.get(field,'')
        if not isinstance(s,str): raise ValueError(f'{field} must be text.')
        if len(s)>4000: raise ValueError(f'{field} is too long (maximum 4,000 characters).')
        result[field]=s.strip()
    if not result['question']: raise ValueError('Write an RFI question first.')
    return result


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()


def normalize_sheet(value):
    return re.sub(r'[\s-]','',value.upper())


def reference_check(rfi,index):
    # Deliberately limited to letter-prefix sheet identifiers, not specification numbers.
    texts = rfi['references']+' '+rfi['question']
    identifiers = re.findall(r'\b[A-Za-z]{1,4}-?\d{3}[A-Za-z]?\b', texts)
    known = {normalize_sheet(k):(k,v) for k,v in index.items()}
    output=[];seen=set()
    for raw in identifiers:
        normal=normalize_sheet(raw)
        if normal in seen: continue
        seen.add(normal)
        if normal in known:
            name,source=known[normal]
            output.append({'reference':name,'status':'observed_in_partial_index',
               'message':'Identifier observed in the inspected addenda. Content, detail and current revision still need human verification.',**source})
        else:
            output.append({'reference':raw.upper(),'status':'not_found_in_partial_index',
               'message':'Not found in this partial index. This does not establish that the reference is invalid.',
               'source_label':'Team 8 partial index','url':'','page':None})
    return output


def rule_check(rfi,index):
    findings=[]
    for field in CHECK_FIELDS:
        if not rfi[field] or rfi[field].lower() in ('tbd','unknown','n/a','asap'):
            # This is an intentionally simple development aid, not an AI condition.
            if field=='impact' and rfi[field].lower()=='unknown': continue
            findings.append({'field':field,'message':f'Check the {field.replace("_"," ")} field.',
              'follow_up':'Supply a specific value, or confirm that the question already contains it.',
              'evidence':rfi[field] or 'Not supplied in this field'})
    if len(rfi['question'].split())<6:
        findings.append({'field':'question','message':'The question may be too brief.',
           'follow_up':'What specific clarification do you need?', 'evidence':rfi['question']})
    return {'summary':'Rule checklist only. Review the whole RFI because another field may already provide the information.',
            'findings':findings,'references':reference_check(rfi,index),
            'engine':'rules','model':None,'prompt_sha256':None}


def validate_ai_result(result):
    if not isinstance(result,dict) or not isinstance(result.get('summary'),str):
        raise ValueError('The AI returned an invalid review. Try again; no result was accepted.')
    if len(result['summary'])>3000: raise ValueError('AI summary exceeded the allowed length.')
    items=result.get('findings')
    if not isinstance(items,list) or len(items)>8: raise ValueError('Invalid AI findings.')
    for item in items:
        if not isinstance(item,dict) or item.get('field') not in CHECK_FIELDS:
            raise ValueError('Invalid AI finding field.')
        for name in ('message','follow_up','evidence'):
            if not isinstance(item.get(name),str) or len(item[name])>2000:
                raise ValueError('Invalid AI finding text.')
    return {'summary':result['summary'],'findings':items}


def ai_check(rfi,index):
    cfg=settings()
    if not cfg['key']: raise ValueError('AI is not connected. Run python3 setup_ai.py in the project folder to configure your key. Rule practice is available separately.')
    prompt=(ROOT/'prompts'/'review.txt').read_text(encoding='utf-8')
    props={k:{'type':'string'} for k in ('message','follow_up','evidence')}
    props['field']={'type':'string','enum':list(CHECK_FIELDS)}
    schema={'type':'object','additionalProperties':False,'properties':{
       'summary':{'type':'string'},'findings':{'type':'array','maxItems':8,'items':{
           'type':'object','additionalProperties':False,'properties':props,'required':list(props)}}},
       'required':['summary','findings']}
    if cfg.get('provider')=='gemini': return gemini_check(rfi,index,cfg,prompt,schema)
    payload={'model':cfg['model'],'store':False,'instructions':prompt,
       'input':json.dumps({'rfi':rfi,'partial_drawing_index':list(index)},ensure_ascii=False),
       'text':{'format':{'type':'json_schema','name':'rfi_review','strict':True,'schema':schema}},
       'max_output_tokens':2400}
    request=urllib.request.Request('https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+cfg['key'],
        'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=60) as response:
            raw=json.load(response)
    except urllib.error.HTTPError as exc:
        messages={401:'API key was rejected.',403:'This account cannot access the model.',
                  429:'API quota or rate limit reached. Check API billing or try later.'}
        raise ValueError(messages.get(exc.code,f'AI request failed (HTTP {exc.code}). Check model access and configuration.')) from None
    except (urllib.error.URLError,TimeoutError,OSError):
        raise ValueError('Could not reach the AI service. Check your internet connection and retry.') from None
    if raw.get('status')!='completed':
        raise ValueError('AI response did not complete. No result was accepted; try again.')
    texts=[]
    for item in raw.get('output',[]):
        for content in item.get('content',[]):
            if content.get('type')=='refusal': raise ValueError('The AI declined this request. Review the input.')
            if content.get('type')=='output_text': texts.append(content['text'])
    try: result=validate_ai_result(json.loads(''.join(texts)))
    except (json.JSONDecodeError,KeyError): raise ValueError('The AI returned unreadable output. No result was accepted.') from None
    result.update({'references':reference_check(rfi,index),'engine':'ai','provider':'openai','model':raw.get('model',cfg['model']),
                   'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                   'response_id':raw.get('id'),'usage':raw.get('usage',{})})
    return result


def gemini_check(rfi,index,cfg,prompt,schema):
    model=cfg['model'].removeprefix('models/')
    if not re.fullmatch(r'[A-Za-z0-9._-]+',model): raise ValueError('Use a valid Gemini model ID.')
    payload={
        'systemInstruction':{'parts':[{'text':prompt}]},
        'contents':[{'role':'user','parts':[{'text':json.dumps({'rfi':rfi,'partial_drawing_index':list(index)},ensure_ascii=False)}]}],
        'generationConfig':{'responseMimeType':'application/json','responseJsonSchema':schema,'maxOutputTokens':8192}
    }
    request=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',
        data=json.dumps(payload).encode(),headers={'x-goog-api-key':cfg['key'],'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=60) as response: raw=json.load(response)
    except urllib.error.HTTPError as exc:
        messages={400:'Gemini rejected the request. Check the key and model ID; no AI result was accepted.',
                  401:'Gemini API key was rejected.',
                  403:'Gemini access was denied. Check the key permissions, project and regional eligibility.',
                  404:'This Gemini model is unavailable to your project. Check models in AI Studio and configure GEMINI_MODEL.',
                  429:'Gemini quota or rate limit reached. Check your free-tier limits in AI Studio and retry later. The app will not switch providers or enable billing.'}
        raise ValueError(messages.get(exc.code,f'Gemini request failed (HTTP {exc.code}). No AI result was accepted; retry later.')) from None
    except urllib.error.URLError as exc:
        if isinstance(exc.reason,ssl.SSLCertVerificationError):
            raise ValueError('Python cannot verify HTTPS certificates. On macOS, run Install Certificates.command in Applications > Python, then restart the app. Do not disable certificate verification.') from None
        raise ValueError('Could not reach Gemini. Check your internet connection and retry.') from None
    except (TimeoutError,OSError):
        raise ValueError('The Gemini request timed out or could not connect. No AI result was accepted.') from None
    except ValueError:
        raise ValueError('Gemini returned an unreadable response. No AI result was accepted.') from None
    if not isinstance(raw,dict): raise ValueError('Gemini returned an invalid response.')
    if raw.get('promptFeedback',{}).get('blockReason'):
        raise ValueError('Gemini blocked this request. Review the input; no AI result was accepted.')
    candidates=raw.get('candidates',[])
    if not candidates or candidates[0].get('finishReason')!='STOP':
        raise ValueError('Gemini did not finish a usable response. No AI result was accepted; try again.')
    texts=[p['text'] for p in candidates[0].get('content',{}).get('parts',[])
           if isinstance(p.get('text'),str) and not p.get('thought')]
    try: result=validate_ai_result(json.loads(''.join(texts)))
    except (json.JSONDecodeError,KeyError):
        raise ValueError('Gemini returned unreadable review text. No AI result was accepted.') from None
    result.update({'references':reference_check(rfi,index),'engine':'ai','provider':'gemini',
        'model':raw.get('modelVersion',model),'requested_model':model,
        'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
        'response_id':raw.get('responseId'),'usage':raw.get('usageMetadata',{})})
    return result
