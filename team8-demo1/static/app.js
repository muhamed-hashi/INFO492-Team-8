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
 $('method-note').textContent=mode==='manual'?'Control condition: complete the form without automated suggestions.':mode==='rules'?'Practice only. These results are not evidence of an AI effect.':'The AI receives this RFI and the partial drawing index. You verify every suggestion.';
 $('suggestions').replaceChildren(text('div',mode==='manual'?'No automated suggestions in the control condition.':'Run a check to see suggestions.','empty'));
 $('review-state').textContent='No check yet.';$('prep-state').textContent='Preparation timer is running';showBrief();message('Session started. Preparation time includes reading, checking and editing.',false);
 $('case').disabled=true;$('condition').disabled=true;$('start').textContent='Choose a new session';$('start').onclick=choose;
 }catch(e){message(e.message);}}
function choose(){if(preparation&&!finalized&&!confirm('Leave this preparation? It will not enter the results unless saved for GC review.'))return;preparation=null;$('fields').disabled=true;$('case').disabled=false;$('condition').disabled=false;$('start').textContent='Start preparation';$('start').onclick=start;$('prep-state').textContent='Choose a case and method';}
async function check(){const b=$('check');b.disabled=true;b.textContent='Checking…';message('');const snapshot=rfi();try{const result=await api('/api/check',{preparation_id:preparation,rfi:snapshot});renderSuggestions(result);message('Check complete. Review the suggestions and edit the form yourself.',false);}catch(e){message(e.message);}finally{b.disabled=false;b.textContent=$('condition').value==='rules'?'Run rule checklist':'Run AI check';}}
function renderSuggestions(result){const box=$('suggestions');box.replaceChildren(text('p',result.summary));$('review-state').textContent=result.engine==='ai'?'AI review · '+result.model:'Rule checklist · no AI was used';
 if(!result.findings.length)box.append(text('p','No further omissions flagged. This is not a guarantee of correctness.','small'));
 for(const f of result.findings){const div=text('div','','finding');div.append(text('span',f.field.replaceAll('_',' '),'field'),text('p',f.message),text('p',f.follow_up),text('small','Basis in supplied form: '+f.evidence));box.append(div);}
 if(result.references.length)box.append(text('h3','Drawing identifier checks'));
 for(const ref of result.references){const div=text('div','','reference');div.append(text('strong',ref.reference),text('p',ref.message));if(ref.url)div.append(link(ref.source_label,ref.url+'#page='+ref.page));box.append(div);}
}
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
function tab(showResults){$('prepare-page').hidden=showResults;$('results-page').hidden=!showResults;$('results-tab').classList.toggle('active',showResults);$('prepare-tab').classList.toggle('active',!showResults);message('');if(showResults)results();}
async function init(){try{config=await api('/api/config');for(const c of config.cases){const o=text('option',c.case_id+' · '+c.initial.title);o.value=c.case_id;$('case').append(o);}const custom=text('option','Custom RFI');custom.value='CUSTOM';$('case').append(custom);
 $('ai-status').textContent=config.ai_configured?'AI key configured · '+config.provider+' · model: '+config.model+'. A successful check is still needed to verify access.':'AI not connected yet. You can use manual preparation or rule practice now. See START_HERE_ZH.md to connect AI.';
 for(const [sheet,src] of Object.entries(config.drawing_index)){$('index').append(link(sheet,src.url+'#page='+src.page),document.createTextNode('  '));}
 showBrief();$('case').onchange=showBrief;$('start').onclick=start;$('check').onclick=check;$('handoff').onclick=handoff;$('refresh').onclick=results;$('prepare-tab').onclick=()=>tab(false);$('results-tab').onclick=()=>tab(true);
 $('rfi-form').onsubmit=e=>e.preventDefault();for(const name of fieldNames)$(name).addEventListener('input',()=>{$('approved').checked=false;});
 }catch(e){message('Unable to start: '+e.message);}}
init();
