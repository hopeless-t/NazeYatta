const $=id=>document.getElementById(id);
const views={home:$('homeView'),new:$('newView'),history:$('historyView')};
const titles={home:'今日は何を確認しますか？',new:'新しく確認',history:'これまでの確認'};
const history=[
 {time:'今日 18:42',title:'Webサイトを公開する',state:'準備OK',cls:'ready'},
 {time:'今日 15:16',title:'報告書を送る',state:'確認が必要',cls:'attention'},
 {time:'昨日 22:03',title:'バックアップを作る',state:'完了',cls:'done'},
 {time:'昨日 12:28',title:'アプリを更新する',state:'完了',cls:'done'},
];
function showView(name){
 Object.values(views).forEach(v=>v.classList.remove('active-view'));views[name].classList.add('active-view');
 document.querySelectorAll('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
 $('pageTitle').textContent=titles[name];
 if(name==='history') renderHistory('');
}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>showView(b.dataset.view));
document.querySelectorAll('[data-view-jump]').forEach(b=>b.onclick=()=>showView(b.dataset.viewJump));
$('heroStart').onclick=()=>showView('new');
$('helpButton').onclick=()=>$('helpDialog').showModal();$('closeHelp').onclick=()=>$('helpDialog').close();
document.querySelectorAll('.quick-chip').forEach(b=>b.onclick=()=>$('taskInput').value=b.dataset.task);
function setStep(n){
 document.querySelectorAll('.workflow-step').forEach(x=>x.classList.remove('active-step'));
 $('step'+['One','Two','Three'][n-1]).classList.add('active-step');
 document.querySelectorAll('.step').forEach((s,i)=>s.classList.toggle('active',i===n-1));
}
function makeResult(){
 const task=$('taskInput').value.trim(),target=$('targetInput').value.trim();
 if(!task){$('taskInput').focus();return;}
 const needsTarget=/送|公開|削除|更新/.test(task)&&!target;
 const panel=$('resultPanel');panel.className='result-panel '+(needsTarget?'attention-panel':'ready-panel');
 $('resultTitle').textContent=needsTarget?'確認が必要':'準備OK';
 $('resultMessage').textContent=needsTarget?'対象を確認すると、より安心して進められます。':'このまま進められます。';
 $('checkList').innerHTML=[
  ['やること',task,false],
  ['対象',target||'まだ指定されていません',needsTarget],
  ['次の操作',needsTarget?'対象を確認してから進む':'そのまま作業を進める',false]
 ].map(([a,b,w])=>`<div class="check-item ${w?'warn':''}"><span class="check-symbol">${w?'!':'✓'}</span><div><b>${a}</b><div>${escapeHtml(b)}</div></div></div>`).join('');
 $('continueButton').textContent=needsTarget?'内容を確認して進む':'進める';setStep(2);
}
$('checkButton').onclick=makeResult;$('backButton').onclick=()=>setStep(1);$('continueButton').onclick=()=>setStep(3);
document.querySelectorAll('.outcome-card').forEach(b=>b.onclick=()=>{
 const map={done:['完了として記録しました。','期待した結果になったことを確認しました。'],issue:['確認が必要です。','気になる点を残して、もう一度確認できます。'],unknown:['まだ完了にはしません。','結果が分かったら、あとから確認できます。']};
 const [h,p]=map[b.dataset.outcome];$('finalMessage').innerHTML=`<b>${h}</b><div>${p}</div>`;$('finalMessage').classList.remove('hidden');
});
function renderHistory(q){$('historyList').innerHTML=history.filter(x=>x.title.includes(q)).map(x=>`<div class="history-row"><time>${x.time}</time><b>${x.title}</b><span class="state ${x.cls}">${x.state}</span></div>`).join('')||'<p>該当する履歴はありません。</p>'}
$('historySearch').oninput=e=>renderHistory(e.target.value.trim());
function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))}
renderHistory('');
