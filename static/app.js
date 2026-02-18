function addMsg(role, text){
  const log = document.getElementById('log');
  const d = document.createElement('div');
  d.className = 'msg ' + (role==='user' ? 'user' : 'bot');
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

function renderStages(stages){
  document.getElementById('panel-normalize').textContent = stages.normalize.normalized + ' (' + stages.normalize.ms.toFixed(1) + ' ms)';
  // sentence
  const viewSentence = document.getElementById('view-sentence');
  if(viewSentence){
    viewSentence.textContent = stages.sentence.corrected + ' (' + stages.sentence.ms.toFixed(1) + ' ms)';
  }
  // spell
  const spell = stages.tokenize_spell;
  let s = '';
  s += 'Corrected: ' + spell.corrected_text + ' (' + spell.ms.toFixed(1) + ' ms)' + '\n';
  spell.corrections.forEach(c => {
    if(c.candidates && c.candidates.length){
      s += c.token + ' → ' + c.candidates.join(', ') + '\n';
    }
  });
  document.getElementById('panel-spell').textContent = s;
  // intent
  document.getElementById('panel-intent').textContent = stages.intent.intent + ' (' + stages.intent.ms.toFixed(1) + ' ms)';
  // retrieval
  document.getElementById('panel-retrieval').textContent = (stages.retrieval.docs.length ? stages.retrieval.docs.join(', ') : '-') + ' (' + stages.retrieval.ms.toFixed(1) + ' ms)';
  // timings summary
  document.getElementById('timings').textContent = `norm ${stages.normalize.ms.toFixed(1)}ms | spell ${stages.tokenize_spell.ms.toFixed(1)}ms | intent ${stages.intent.ms.toFixed(1)}ms | ret ${stages.retrieval.ms.toFixed(1)}ms`;
}

async function callAPI(text){
  const spell = document.getElementById('spellToggle').checked;
  const retrieve = document.getElementById('retrieveToggle').checked;
  const res = await fetch('/api/process', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text, opts:{spell, retrieve}})
  });
  const j = await res.json();
  return j;
}

window.addEventListener('DOMContentLoaded', ()=>{
  const inp = document.getElementById('inp');
  const send = document.getElementById('send');
  send.addEventListener('click', async ()=>{
    const v = inp.value.trim(); if(!v) return; inp.value=''; addMsg('user', v);
    const r = await callAPI(v);
    addMsg('bot', r.reply);
    renderStages(r.stages);
  });
  inp.addEventListener('keydown', async (e)=>{
    if(e.key === 'Enter'){ e.preventDefault(); send.click(); }
  });
  document.getElementById('clearMemory').addEventListener('click', ()=>{
    // purely UI: clears the chat and panels
    document.getElementById('log').innerHTML='';
    document.getElementById('panel-normalize').textContent='-';
    document.getElementById('panel-spell').textContent='-';
    document.getElementById('panel-intent').textContent='-';
    document.getElementById('panel-retrieval').textContent='-';
    document.getElementById('timings').textContent='No runs yet';
  });
});
