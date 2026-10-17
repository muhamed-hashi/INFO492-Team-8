'use strict';
const $=id=>document.getElementById(id);
const fieldNames=['title','location','trade','question','needed_by','impact','references'];
let config,preparation=null,finalized=false;
const text=(tag,value,cls)=>{const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;return el;};
function message(value,error=true){$('message').replaceChildren();if(value)$('message').append(text('div',value,'notice'+(error?'':' success')));}
async function api(path,body){const res=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json','X-RFI-App':'1'},body:JSON.stringify(body)}:{});const data=await res.json();if(!res.ok)throw new Error(data.error||'Request failed');return data;}
function link(label,url){const a=text('a',label);a.href=url;a.target='_blank';a.rel='noopener';return a;}
function rfi(){return Object.fromEntries(fieldNames.map(k=>[k,$(k).value]));}
function currentCase(){return config.cases.find(c=>c.case_id===$('case').value);}
function showBrief(){const c=currentCase();$('brief').replaceChildren();if(!c){$('brief').append(text('p','Use only material your team is authorized to share. The built-in sheet index covers selected Dett addenda only.'));return;}
 $('brief').append(text('p',c.brief.simulation_note,'small'));
 $('brief').append(link(c.source.id+' · PDF page '+c.source.pdf_page,c.source.url+'#page='+c.source.pdf_page));
 const dl=document.createElement('dl');for(const [k,v] of Object.entries(c.brief.known_details)){dl.append(text('dt',k.replaceAll('_',' ')),text('dd',v));}$('brief').append(dl);
}
async function start(){if(preparation&&!finalized&&!confirm('Start a new preparation? Unsaved edits in the current form will be replaced.'))return;
 try{const out=await api('/api/preparations',{case_id:$('case').value,condition:$('condition').value});preparation=out.preparation_id;finalized=false;
 const c=currentCase();fieldNames.forEach(k=>$(k).value=c?c.initial[k]:'');$('fields').disabled=false;$('approved').checked=false;$('handoff-result').hidden=true;
 const mode=$('condition').value;$('check').disabled=mode==='manual';$('check').textContent=mode==='rules'?'Run rule checklist':'Run AI check';
 $('method-note').textContent=mode==='manual'?'Control condition: complete the form without automated suggestions.':mode==='rules'?'Practice only. These results are not evidence of an AI effect.':'The AI checks the wording. Drawing numbers are looked up in the drawing index by code, and the AI judges whether each sheet fits the question. You verify every suggestion.';
 $('suggestions').replaceChildren(text('div',mode==='manual'?'No automated suggestions in the control condition.':'Run a check to see suggestions.','empty'));
 $('review-state').textContent='No check yet.';$('prep-state').textContent='Preparation timer is running';showBrief();message('Session started. Preparation time includes reading, checking and editing.',false);
 $('case').disabled=true;$('condition').disabled=true;$('start').textContent='Choose a new session';$('start').onclick=choose;
 }catch(e){message(e.message);}}
function choose(){if(preparation&&!finalized&&!confirm('Leave this preparation? It will not enter the results unless saved for GC review.'))return;preparation=null;$('fields').disabled=true;$('case').disabled=false;$('condition').disabled=false;$('start').textContent='Start preparation';$('start').onclick=start;$('prep-state').textContent='Choose a case and method';}
async function check(){const b=$('check');b.disabled=true;b.textContent='Checking…';message('');const snapshot=rfi();try{const result=await api('/api/check',{preparation_id:preparation,rfi:snapshot});renderSuggestions(result);message('Check complete. Review the suggestions and edit the form yourself.',false);}catch(e){message(e.message);}finally{b.disabled=false;b.textContent=$('condition').value==='rules'?'Run rule checklist':'Run AI check';}}
function renderSuggestions(result){const box=$('suggestions');box.replaceChildren(text('p',result.summary));$('review-state').textContent=result.engine==='ai'?'AI review · '+result.model:'Rule checklist · no AI was used';
 if(!result.findings.length)box.append(text('p','No further omissions flagged. This is not a guarantee of correctness.','small'));
 for(const f of result.findings){const div=text('div','','finding');div.append(text('span',f.field.replaceAll('_',' ')+(f.source?' · '+f.source:''),'field'),text('p',f.message),text('p',f.follow_up),text('small','Basis in supplied form: '+f.evidence));box.append(div);}
 renderReferences(box,result);
}
const FIT={yes:['fits the question','fit-yes'],no:['may not fit the question','fit-no'],unclear:['unclear','fit-unclear']};
function chip(label,cls){return text('span',label,'chip '+cls);}
function renderReferences(box,result){
 const head=text('div','','ref-head');head.append(text('h3','Drawing reference check'),text('p',result.engine==='ai'?'Code looks every sheet number up in the drawing index. AI reads each sheet title and judges whether it fits the question.':'Code lookup only. No AI was used.','small'));box.append(head);
 if(!result.references.length){const div=text('div','','ref-card missing');div.append(text('strong','No sheet number found'),chip('Code: nothing to look up','bad'),text('p','Add the sheet(s) that show this condition.','small'));box.append(div);return;}
 for(const ref of result.references){const ok=ref.status==='observed_in_partial_index';const div=text('div','','ref-card'+(ok?'':' missing')+(ref.ai_fit==='no'?' misfit':''));
  const top=text('div','','ref-top');top.append(text('strong',ref.reference),chip(ok?'Code: in drawing index':'Code: not in drawing index',ok?'good':'bad'));div.append(top);
  if(ref.title)div.append(text('p',ref.title,'ref-title'));
  if(ref.ai_fit){const [label,cls]=FIT[ref.ai_fit]||FIT.unclear;const v=text('p','','ref-ai');v.append(chip('AI: '+label,cls),document.createTextNode(' '+(ref.ai_reason||'')));div.append(v);}
  else if(!ok)div.append(text('p','Check the sheet number against the drawing list before sending.','small'));
  if(ref.url)div.append(link(ref.source_label,ref.url+'#page='+ref.page));box.append(div);}
}
const KINDS=[['nonexistent','Sheet number not in the index'],['typo','Typo (letter O for zero)'],['unrelated','Real sheet, unrelated to the question'],['vague','No sheet number at all']];
const METHODS=[['code','Code lookup only','Looks every sheet number up in the 206-sheet index. No AI.'],['ai_only','AI only','Demo 1 design: the AI sees the RFI and the list of sheet numbers and judges everything itself.'],['code_ai','Code + AI','Demo 2 design: code does the lookup; the AI gets the result and each sheet title, and judges fit and typos.']];
async function demo2(){const box=$('demo2-body');box.replaceChildren();try{const d=await api('/api/demo2');
 if(!d.available){box.append(text('div','No Demo 2 results yet. In the terminal run: python3 scripts/run_reference_eval.py','notice'));return;}
 const first=(c,m)=>m==='code'?c.code:c[m][0];const probs=d.cases.filter(c=>c.kind!=='clean'),clean=d.cases.filter(c=>c.kind==='clean');
 box.append(text('p','Run '+(d.run_at||'')+' · model '+(d.model||'none')+' · cards show run 1 of '+d.runs+'.','small'));
 const grid=text('div','','stat-grid');
 for(const [m,name,desc] of METHODS){const caught=probs.filter(c=>first(c,m)).length,wrong=clean.filter(c=>first(c,m)).length;
  const card=text('div','','stat'+(m==='code_ai'?' best':''));card.append(text('p',name,'eyebrow'),text('strong',caught+'/'+probs.length),text('p','reference problems caught'),text('p',wrong+'/'+clean.length+' correct references wrongly flagged',wrong?'warn':'good-text'));
  if(m!=='code'&&d.runs>1){const per=[...Array(d.runs).keys()].map(r=>probs.filter(c=>c[m][r]).length+'/'+probs.length+' caught, '+clean.filter(c=>c[m][r]).length+' wrong');card.append(text('p','All runs: '+per.join(' · '),'small'));}
  card.append(text('p',desc,'small'));grid.append(card);}
 box.append(grid);
 const kt=text('table','','metric-table'),kh=document.createElement('tr');['Kind of problem','Cases','Code only','AI only','Code + AI'].forEach(v=>cell(kh,v,true));kt.append(kh);
 for(const [k,label] of KINDS){const cs=probs.filter(c=>c.kind===k);const row=document.createElement('tr');[label,cs.length,...METHODS.map(([m])=>cs.filter(c=>first(c,m)).length+'/'+cs.length)].forEach(v=>cell(row,v));kt.append(row);}
 const kr=document.createElement('tr');['Correct references wrongly flagged',clean.length,...METHODS.map(([m])=>clean.filter(c=>first(c,m)).length+'/'+clean.length)].forEach(v=>cell(kr,v));kt.append(kr);
 const ks=text('div','','table-scroll');ks.append(kt);box.append(text('h3','By kind of problem (run 1)'),ks);
 const mark=(v,problem)=>v==null?'failed':v?(problem?'✓ flagged':'✗ flagged (wrong)'):(problem?'✗ missed':'✓ ok');
 const pt=text('table','','metric-table'),ph=document.createElement('tr');['Case','Problem','References as written','Code only','AI only','Code + AI'].forEach(v=>cell(ph,v,true));pt.append(ph);
 for(const c of d.cases){const p=c.kind!=='clean';const row=document.createElement('tr');[c.case_id,p?c.kind:'correct',c.references,...METHODS.map(([m])=>mark(first(c,m),p))].forEach(v=>cell(row,v));
  [...row.children].slice(3).forEach(td=>td.className=td.textContent.startsWith('✓')?'cell-good':td.textContent.startsWith('✗')?'cell-bad':'');pt.append(row);}
 const ps=text('div','','table-scroll');ps.append(pt);box.append(text('h3','Every case (run 1)'),ps);
 box.append(text('h3','What each method said (run 1)'));
 for(const c of d.cases){if(!c.ai_only_said.length&&!c.code_ai_said.length)continue;const det=document.createElement('details');det.className='said';det.append(text('summary',c.case_id+' · '+(c.kind==='clean'?'correct references':c.kind)+(c.change?' · '+c.change:'')));
  det.append(text('p','Question: '+c.question,'small'));
  for(const [label,list] of [['AI only',c.ai_only_said],['Code + AI',c.code_ai_said]]){det.append(text('p',label,'said-label'));if(!list.length)det.append(text('p','Nothing flagged.','small'));for(const m of list)det.append(text('p','“'+m+'”','said-msg'));}
  box.append(det);}
 }catch(e){message(e.message);}}
async function handoff(){const button=$('handoff');button.disabled=true;try{const out=await api('/api/handoff',{preparation_id:preparation,rfi:rfi(),human_approved:$('approved').checked});finalized=true;$('fields').disabled=true;$('prep-state').textContent='Preparation saved';const box=$('handoff-result');box.hidden=false;box.replaceChildren(text('h3','Ready for a timed first review'),text('p','Preparation: '+out.preparation_seconds+' seconds.'),link('Open the GC review screen',out.review_url),text('p','Use this screen on the same computer with a separate reviewer. The localhost link will not work on a teammate’s other computer.','small'));message('Saved. Your GC reviewer should open the review page without viewing these suggestions.',false);}catch(e){message(e.message);}finally{button.disabled=false;}}
function cell(row,value,head=false){row.append(text(head?'th':'td',String(value??'—')));}
async function results(){try{const data=await api('/api/results');const box=$('summary');box.replaceChildren();const table=text('table','','metric-table'),head=document.createElement('tr');['Condition','Completed','Median GC time','Median preparation','Needs clarification','Errors scored','Mean errors'].forEach(v=>cell(head,v,true));table.append(head);
 for(const [k,g] of Object.entries(data.summary.groups)){const row=document.createElement('tr');[k==='rules'?'Rules (practice)':k,g.n,g.median_review_seconds==null?'—':g.median_review_seconds.toFixed(1)+' s',g.median_preparation_seconds==null?'—':g.median_preparation_seconds.toFixed(1)+' s',g.needs_clarification,g.scored_count+'/'+g.n,g.mean_errors==null?'Not assessed':g.mean_errors.toFixed(2)].forEach(v=>cell(row,v));table.append(row);}
 const sc=text('div','','table-scroll');sc.append(table);box.append(sc);
 const reduction=data.summary.observed_reduction_percent;box.append(text('p',reduction==null?'Complete both manual and AI reviews to calculate an observed time difference.':'Observed median time reduction: '+reduction+'%. This pilot comparison alone does not establish the thesis.','small'));box.append(text('p',data.summary.interpretation,'small'));
 $('trials').replaceChildren();if(!data.trials.length)$('trials').append(text('p','No trials yet. Prepare and save an RFI to begin.'));
 for(const trial of data.trials){const d=document.createElement('details');d.className='trial';d.append(text('summary',trial.case_id+' · '+trial.condition+' · '+(trial.decision||'Awaiting GC review')+' · '+trial.trial_id.slice(0,8)));
 const div=text('div','','panel');div.append(text('p',trial.rfi.question));if(trial.review_seconds==null)div.append(link('Open GC review','/review#'+trial.trial_id));else{div.append(text('p','GC time: '+trial.review_seconds+' s'+(trial.interrupted?' · interrupted, excluded from medians':'')));
 const label=text('label','Information errors (human assessment)'),input=document.createElement('input');input.type='number';input.min='0';input.max='100';input.placeholder='Leave unscored until checked';input.value=trial.error_count??'';label.append(input);const notes=document.createElement('textarea');notes.placeholder='What was wrong? Compare with the approved scenario and source. Missing context is tracked through clarification decisions.';notes.value=trial.error_notes||'';notes.rows=2;const save=text('button','Save error assessment');save.onclick=async()=>{try{if(input.value==='')throw Error('Enter an assessed error count; an empty value is not zero.');await api('/api/score',{trial_id:trial.trial_id,error_count:Number(input.value),notes:notes.value});message('Assessment saved.',false);await results();}catch(e){message(e.message);}};div.append(label,notes,save);}
 d.append(div);$('trials').append(d);}
 }catch(e){message(e.message);}}
function tab(name){for(const n of ['prepare','demo2','results']){$(n+'-page').hidden=n!==name;$(n+'-tab').classList.toggle('active',n===name);}message('');if(name==='results')results();if(name==='demo2')demo2();}
async function init(){try{config=await api('/api/config');const groups=[['R','Demo 2 · check references (R01–R24)'],['D','Demo 2 first run · all fields (D01–D24)']];for(const [prefix,label] of groups){const g=document.createElement('optgroup');g.label=label;for(const c of config.cases.filter(c=>c.case_id.startsWith(prefix))){const o=text('option',c.case_id+' · '+c.initial.title);o.value=c.case_id;g.append(o);}if(g.children.length)$('case').append(g);}const custom=text('option','Custom RFI');custom.value='CUSTOM';$('case').append(custom);
 $('ai-status').textContent=config.ai_configured?'AI key configured · '+config.provider+' · model: '+config.model+'. A successful check is still needed to verify access.':'AI not connected yet. In the terminal run: python3 setup_ai.py, then restart the app.';
 for(const [sheet,src] of Object.entries(config.drawing_index)){$('index').append(link(sheet,src.url+'#page='+src.page),document.createTextNode('  '));}
 showBrief();$('case').onchange=showBrief;$('start').onclick=start;$('check').onclick=check;$('handoff').onclick=handoff;$('refresh').onclick=results;$('prepare-tab').onclick=()=>tab('prepare');$('demo2-tab').onclick=()=>tab('demo2');$('results-tab').onclick=()=>tab('results');$('demo2-refresh').onclick=demo2;
 $('rfi-form').onsubmit=e=>e.preventDefault();for(const name of fieldNames)$(name).addEventListener('input',()=>{$('approved').checked=false;});
 }catch(e){message('Unable to start: '+e.message);}}
init();
