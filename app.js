const $=id=>document.getElementById(id);
const STORAGE_KEY='nazeyatta.public.history.v1';
const THEME_KEY='nazeyatta.public.theme.v1';
const views={home:$('homeView'),new:$('newView'),history:$('historyView')};
const titles={home:'今日は何を確認しますか？',new:'新しく確認',history:'これまでの確認'};
let activeTask=null;
let toastTimer=null;

function safeReadHistory(){
  try{return JSON.parse(localStorage.getItem(STORAGE_KEY)||'[]').filter(x=>x&&x.title).slice(0,100)}catch{return []}
}
function writeHistory(items){localStorage.setItem(STORAGE_KEY,JSON.stringify(items.slice(0,100)))}
function nowLabel(){return new Intl.DateTimeFormat('ja-JP',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date())}
function escapeHtml(s=''){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))}

function showView(name){
  Object.values(views).forEach(v=>v.classList.remove('active-view'));
  views[name].classList.add('active-view');
  document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
  $('pageTitle').textContent=titles[name];
  if(name==='home')renderHome();
  if(name==='history')renderHistory($('historySearch').value.trim());
  if(name==='new'&&!$('taskInput').value) setStep(1);
  window.scrollTo({top:0,behavior:'smooth'});
}

document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>showView(b.dataset.view));
document.querySelectorAll('[data-view-jump]').forEach(b=>b.onclick=()=>showView(b.dataset.viewJump));
$('heroStart').onclick=()=>{resetWorkflow();showView('new')};
$('workflowClose').onclick=()=>showView('home');
$('finishButton').onclick=()=>{resetWorkflow();showView('home')};

function applyTheme(theme){
  document.documentElement.dataset.theme=theme;
  document.body.classList.toggle('theme-dark',theme==='dark');
  localStorage.setItem(THEME_KEY,theme);
}
const preferred=localStorage.getItem(THEME_KEY)||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
applyTheme(preferred);
$('themeButton').onclick=()=>applyTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');

$('helpButton').onclick=()=>$('helpDialog').showModal();
$('closeHelp').onclick=()=>$('helpDialog').close();
$('helpStart').onclick=()=>{$('helpDialog').close();resetWorkflow();showView('new')};

function setStep(n){
  document.querySelectorAll('.workflow-step').forEach(x=>x.classList.remove('active-step'));
  $('step'+['One','Two','Three'][n-1]).classList.add('active-step');
  const steps=[...document.querySelectorAll('.step')];
  const lines=[...document.querySelectorAll('.step-line')];
  steps.forEach((s,i)=>{s.classList.toggle('active',i===n-1);s.classList.toggle('done',i<n-1)});
  lines.forEach((l,i)=>l.classList.toggle('done',i<n-1));
}

function resetWorkflow(){
  activeTask=null;
  $('taskInput').value='';$('targetInput').value='';$('taskCount').textContent='0 / 180';
  $('finalMessage').classList.add('hidden');$('finishButton').classList.add('hidden');
  setStep(1);
}

document.querySelectorAll('.quick-chip').forEach(b=>b.onclick=()=>{
  $('taskInput').value=b.dataset.task;updateCount();$('taskInput').focus();
});
function updateCount(){$('taskCount').textContent=`${$('taskInput').value.length} / 180`}
$('taskInput').addEventListener('input',updateCount);

$('demoButton').onclick=()=>{
  resetWorkflow();
  $('taskInput').value='お客様へ作業報告書を送る';
  $('targetInput').value='ガヤ・コーポレーション';
  updateCount();showView('new');
  setTimeout(()=>makeResult(),180);
};

function makeResult(){
  const task=$('taskInput').value.trim(),target=$('targetInput').value.trim();
  if(!task){shake($('taskInput'));$('taskInput').focus();showToast('やることをひとこと書いてみて');return}
  const needsTarget=/送|公開|削除|更新|共有|提出/.test(task)&&!target;
  activeTask={task,target,startedAt:new Date().toISOString(),needsTarget};
  const panel=$('resultPanel');
  panel.className='result-panel '+(needsTarget?'attention-panel':'ready-panel');
  $('resultSymbol').textContent=needsTarget?'!':'✓';
  $('resultTitle').textContent=needsTarget?'ここだけ確認。':'よし、いけそう。';
  $('resultMessage').textContent=needsTarget?'対象が分かると、安心して進められます。':'今の内容なら、そのまま進められます。';
  $('checkList').innerHTML=[
    ['やること',task,false],
    ['対象',target||'まだ指定されていません',needsTarget],
    ['次にすること',needsTarget?'対象を入れるか、内容を見直す':'そのまま作業を進める',false]
  ].map(([a,b,w])=>`<div class="check-item ${w?'warn':''}"><span class="check-symbol">${w?'!':'✓'}</span><div><b>${escapeHtml(a)}</b><div>${escapeHtml(b)}</div></div></div>`).join('');
  $('resultTip').innerHTML=needsTarget?'<span>◎</span><p>対象がなくても進められる作業なら、そのままでも大丈夫。</p>':'<span>◎</span><p>いま直すところはありません。終わったら結果だけ残しましょう。</p>';
  $('continueButton').textContent=needsTarget?'このまま進む':'進める';
  setStep(2);
  if(!needsTarget)spark($('resultPanel'));
}
$('checkButton').onclick=makeResult;
$('backButton').onclick=()=>setStep(1);
$('continueButton').onclick=()=>setStep(3);

document.addEventListener('keydown',e=>{
  if((e.metaKey||e.ctrlKey)&&e.key==='Enter'){
    const newVisible=$('newView').classList.contains('active-view');
    if(!newVisible){resetWorkflow();showView('new');return}
    if($('stepOne').classList.contains('active-step'))makeResult();
    else if($('stepTwo').classList.contains('active-step'))setStep(3);
  }
});

function outcomeCopy(type){
  return {
    done:{state:'done',label:'完了',title:'できた！',text:'予定どおり終わったことを残しました。',accent:'#2fc58d'},
    issue:{state:'attention',label:'あとで確認',title:'ここだけ残しておこう。',text:'気になる点を残しました。あとから戻って確認できます。',accent:'#d18517'},
    unknown:{state:'unknown',label:'未確認',title:'まだ決めなくてOK。',text:'結果が見えてから、あとで確認できます。',accent:'#7b61e8'}
  }[type];
}
document.querySelectorAll('.outcome-card').forEach(b=>b.onclick=()=>{
  if(!activeTask)return;
  const copy=outcomeCopy(b.dataset.outcome);
  const item={id:crypto.randomUUID(),time:nowLabel(),iso:new Date().toISOString(),title:activeTask.task,target:activeTask.target,state:copy.state,label:copy.label,summary:copy.text};
  const items=safeReadHistory();items.unshift(item);writeHistory(items);
  $('finalMessage').innerHTML=`<b>${escapeHtml(copy.title)}</b><div>${escapeHtml(copy.text)}</div>`;
  $('finalMessage').classList.remove('hidden');$('finishButton').classList.remove('hidden');
  if(b.dataset.outcome==='done'){spark(b,22);showToast('できた！ 履歴に残しました')}
  else showToast('履歴に残しました');
  renderStats(items);
});

function renderHome(){
  const items=safeReadHistory();renderStats(items);
  const recent=items.slice(0,6);$('recentEmpty').classList.toggle('hidden',recent.length>0);$('recentGrid').classList.toggle('hidden',recent.length===0);
  $('recentGrid').innerHTML=recent.map(x=>recentCard(x)).join('');
}
function renderStats(items){
  const today=new Date().toDateString();
  $('todayCount').textContent=items.filter(x=>new Date(x.iso).toDateString()===today).length;
  $('doneCount').textContent=items.filter(x=>x.state==='done').length;
  $('openCount').textContent=items.filter(x=>x.state!=='done').length;
}
function recentCard(x){
  const cls=x.state==='attention'?'attention':x.state==='done'?'done':x.state==='unknown'?'unknown':'ready';
  const color=cls==='done'?'#7b61e8':cls==='attention'?'#d18517':cls==='unknown'?'#8893a1':'#2fc58d';
  return `<article class="recent-card" style="--accent:${color}"><div class="recent-top"><span class="state ${cls}">${escapeHtml(x.label)}</span><time>${escapeHtml(x.time)}</time></div><h3>${escapeHtml(x.title)}</h3><p>${escapeHtml(x.summary||'確認しました。')}</p><div class="recent-meta">${x.target?escapeHtml(x.target):'対象の指定なし'}</div></article>`;
}
function renderHistory(q=''){
  const items=safeReadHistory().filter(x=>(x.title+' '+(x.target||'')).toLowerCase().includes(q.toLowerCase()));
  $('historyEmpty').classList.toggle('hidden',items.length>0);$('historyList').classList.toggle('hidden',items.length===0);
  $('historyList').innerHTML=items.map(x=>{
    const cls=x.state==='attention'?'attention':x.state==='done'?'done':x.state==='unknown'?'unknown':'ready';
    return `<div class="history-row"><time>${escapeHtml(x.time)}</time><div><b>${escapeHtml(x.title)}</b>${x.target?`<div class="recent-meta">${escapeHtml(x.target)}</div>`:''}</div><span class="state ${cls}">${escapeHtml(x.label)}</span></div>`;
  }).join('');
}
$('historySearch').oninput=e=>renderHistory(e.target.value.trim());
$('clearHistory').onclick=()=>{
  if(!safeReadHistory().length)return;
  if(confirm('このブラウザに保存された履歴をすべて削除しますか？')){writeHistory([]);renderHistory('');renderHome();showToast('履歴を削除しました')}
};

function showToast(text){
  clearTimeout(toastTimer);$('toast').querySelector('p').textContent=text;$('toast').classList.add('show');
  toastTimer=setTimeout(()=>$('toast').classList.remove('show'),2200);
}
function shake(el){el.animate([{transform:'translateX(0)'},{transform:'translateX(-5px)'},{transform:'translateX(5px)'},{transform:'translateX(0)'}],{duration:220})}
function spark(origin,count=14){
  if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const r=origin.getBoundingClientRect();const ox=r.left+r.width/2,oy=r.top+r.height/2;
  const colors=['#3c6df0','#2fc58d','#7b61e8','#f0ad4f'];
  for(let i=0;i<count;i++){
    const s=document.createElement('i');s.className='spark';s.style.left=ox+'px';s.style.top=oy+'px';s.style.setProperty('--spark',colors[i%colors.length]);
    const a=(Math.PI*2*i/count)+(Math.random()-.5)*.25,d=44+Math.random()*70;s.style.setProperty('--x',Math.cos(a)*d+'px');s.style.setProperty('--y',Math.sin(a)*d+'px');
    $('sparkLayer').appendChild(s);s.onanimationend=()=>s.remove();
  }
}

renderHome();renderHistory('');
