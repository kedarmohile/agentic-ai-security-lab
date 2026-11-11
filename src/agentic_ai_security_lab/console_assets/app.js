const state={catalog:{labs:[],hunts:[]},status:{},runs:[],findings:[],cases:[],view:"start",selectedEvidenceRun:null};
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]})}
async function api(path,options){const o=options||{};o.headers=Object.assign({"Content-Type":"application/json"},o.headers||{});const response=await fetch(path,o);const payload=await response.json();if(!response.ok)throw new Error(payload.error||("HTTP "+response.status));return payload}
function toast(message,kind){const el=document.createElement("div");el.className="toast "+(kind||"success");el.textContent=message;$("#toast-stack").appendChild(el);setTimeout(function(){el.remove()},3200)}
function labById(id){return state.catalog.labs.find(function(l){return l.lab_id===id})}
function setView(view){state.view=view;$$(".view").forEach(function(el){el.classList.toggle("active",el.id==="view-"+view)});$$(".nav-item").forEach(function(el){el.classList.toggle("active",el.dataset.view===view)});const active=$('.nav-item[data-view="'+view+'"]');$("#page-title").textContent=active?active.textContent.trim().replace(/\d+$/,"").trim():"Command Center";window.scrollTo({top:0,behavior:"smooth"});if(view==="evidence")renderEvidence()}
function fillLabSelect(select){select.innerHTML=state.catalog.labs.map(function(l){return '<option value="'+esc(l.lab_id)+'">LAB '+esc(l.number)+' · '+esc(l.name)+'</option>'}).join("")}
function fillModes(labSelect,modeSelect){const lab=labById(labSelect.value);if(!lab)return;modeSelect.innerHTML=lab.modes.map(function(m){return '<option value="'+esc(m)+'">'+esc(m)+'</option>'}).join("")}
function updateDrawerQuestion(){const lab=labById($("#drawer-lab").value);$("#drawer-lab-question").innerHTML=lab?'<b>'+esc(lab.domain)+' boundary</b><br>'+esc(lab.question):""}
function postureColor(score){if(score==null)return"#42505c";if(score>=85)return"#44d39a";if(score>=60)return"#f4b860";return"#ff6577"}
function renderStatus(){const s=state.status;const score=s.posture_score;$("#posture-score").textContent=score==null?"--":score;$("#assessed-count").textContent=s.assessed_labs||0;$("#assessment-fill").style.width=((s.assessed_labs||0)/(s.total_labs||5)*100)+"%";$("#metric-findings").textContent=s.findings||0;$("#metric-high").textContent=(s.high_findings||0)+" HIGH";$("#metric-medium").textContent=(s.medium_findings||0)+" MED";$("#metric-evidence").textContent=s.evidence_confidence==null?"--":s.evidence_confidence;$("#nav-findings").textContent=s.findings||0;const circumference=314.159;const ratio=score==null?0:score/100;const ring=$("#ring-value");ring.style.strokeDashoffset=String(circumference*(1-ratio));ring.style.stroke=postureColor(score);const badge=$("#posture-state");if(score==null){badge.className="tag neutral";badge.textContent="UNASSESSED";$("#posture-title").textContent="Run a lab to establish posture";$("#posture-detail").textContent="Scores are calculated only from executed lab evidence. No demo findings are pre-seeded."}else if(score>=85){badge.className="tag pass";badge.textContent="CONTROLLED";$("#posture-title").textContent="Controls holding across assessed labs";$("#posture-detail").textContent="Posture is based on the latest executed result for each assessed lab."}else{badge.className="tag fail";badge.textContent="ATTENTION";$("#posture-title").textContent="Security boundary failures need review";$("#posture-detail").textContent="Pivot into Findings or Attack Graph for evidence-backed investigation."}}
function renderPriorityHunts(){$("#priority-hunts").innerHTML=state.catalog.hunts.map(function(h){return '<div class="hunt-row" data-hunt="'+esc(h.hunt_id)+'"><div class="hunt-id">'+esc(h.hunt_id)+'</div><div><div class="hunt-title">'+esc(h.title)+'</div><div class="subtle-copy">'+esc(h.objective)+'</div></div><div class="hunt-meta difficulty">'+esc(h.difficulty)+'</div><div class="hunt-meta">'+esc(h.points)+' PTS</div></div>'}).join("");$$(".hunt-row").forEach(function(el){el.addEventListener("click",function(){setView("hunts");setTimeout(function(){const t=document.querySelector('[data-hunt-card="'+el.dataset.hunt+'"]');if(t)t.scrollIntoView({behavior:"smooth",block:"center"})},60)})})}
function renderHunts(){$("#hunts-grid").innerHTML=state.catalog.hunts.map(function(h){const steps=h.steps.map(function(step){return '<div class="step">'+esc(step)+'</div>'}).join("");return '<article class="hunt-card" data-hunt-card="'+esc(h.hunt_id)+'"><div class="hunt-card-top"><div><div class="hunt-id">'+esc(h.hunt_id)+'</div><h3>'+esc(h.title)+'</h3></div><div class="points">'+esc(h.points)+' PTS</div></div><p class="hypothesis"><b>Hypothesis:</b> '+esc(h.hypothesis)+'</p><p class="hypothesis"><b>Objective:</b> '+esc(h.objective)+'</p><div class="hunt-stats"><span>'+esc(h.difficulty).toUpperCase()+'</span><span>'+esc(h.controls)+' CONTROLS</span><span>LAB '+esc(labById(h.lab_id).number)+'</span></div><div class="steps">'+steps+'</div><div class="card-actions"><button class="button primary run-hunt" data-lab="'+esc(h.lab_id)+'" data-mode="'+esc(h.recommended_mode)+'">Run Hunt</button><button class="button subtle open-lab" data-lab="'+esc(h.lab_id)+'">Open Lab</button></div></article>'}).join("");$$(".run-hunt").forEach(function(btn){btn.addEventListener("click",function(){execute(btn.dataset.lab,btn.dataset.mode)})});$$(".open-lab").forEach(function(btn){btn.addEventListener("click",function(){openRunner(btn.dataset.lab)})})}
function renderLabs(){$("#labs-grid").innerHTML=state.catalog.labs.map(function(l){const modes=l.modes.map(function(m){return '<span class="mode-chip">'+esc(m)+'</span>'}).join("");return '<article class="lab-card"><div class="lab-card-top"><div><div class="lab-domain">'+esc(l.domain).toUpperCase()+' BOUNDARY</div><h3>'+esc(l.name)+'</h3></div><div class="lab-number">'+esc(l.number)+'</div></div><div class="lab-question">'+esc(l.question)+'</div><div class="mode-chips">'+modes+'</div><div class="card-actions"><button class="button primary open-runner-lab" data-lab="'+esc(l.lab_id)+'">Run Lab</button><button class="button subtle run-secure" data-lab="'+esc(l.lab_id)+'" data-mode="'+esc(l.secure_mode)+'">Secure Control</button></div></article>'}).join("");$$(".open-runner-lab").forEach(function(btn){btn.addEventListener("click",function(){openRunner(btn.dataset.lab)})});$$(".run-secure").forEach(function(btn){btn.addEventListener("click",function(){execute(btn.dataset.lab,btn.dataset.mode)})})}
function renderRecentRuns(){const runs=state.runs.slice(0,5);const root=$("#recent-runs");if(!runs.length){root.className="run-list empty-state";root.textContent="No runs yet. Execute a lab to create evidence.";return}root.className="run-list";root.innerHTML=runs.map(function(r){return '<div class="run-item" data-run="'+esc(r.run_id)+'"><div class="run-number">L'+esc(r.lab_number)+'</div><div><div class="run-name">'+esc(r.lab_name)+'</div><div class="run-mode">'+esc(r.mode)+'</div></div><div class="tag '+(r.result.finding?"fail":"pass")+'">'+esc(r.result.verdict).toUpperCase()+'</div><div class="score-mini">'+esc(r.scores.control)+'</div></div>'}).join("");$$(".run-item").forEach(function(el){el.addEventListener("click",function(){openRunDetail(el.dataset.run)})})}
function renderRuns(){const root=$("#runs-list");if(!state.runs.length){root.innerHTML='<div class="empty-state">No run history yet.</div>';return}let body='<div class="run-table-head"><span>LAB</span><span>RUN</span><span>MODE</span><span>CONTROL</span><span>EXPOSURE</span><span>VERDICT</span></div>';body+=state.runs.map(function(r){return '<div class="run-table-row" data-run="'+esc(r.run_id)+'"><span class="run-number">L'+esc(r.lab_number)+'</span><span>'+esc(r.lab_name)+'</span><span class="mono tiny">'+esc(r.mode)+'</span><span class="score-pill">'+esc(r.scores.control)+'/100</span><span class="score-pill">'+esc(r.scores.exposure)+'/100</span><span class="tag '+(r.result.finding?"fail":"pass")+'">'+esc(r.result.verdict).toUpperCase()+'</span></div>'}).join("");root.innerHTML=body;$$(".run-table-row").forEach(function(el){el.addEventListener("click",function(){openRunDetail(el.dataset.run)})})}
function renderFindings(){const root=$("#findings-list");if(!state.findings.length){root.innerHTML='<div class="empty-state">No confirmed findings. Run vulnerable scenarios to validate the investigation workflow.</div>';return}root.innerHTML=state.findings.map(function(f){return '<article class="finding-card"><div class="finding-head"><div><div class="finding-id">'+esc(f.finding_id)+'</div><h3>'+esc(f.title)+'</h3></div><span class="severity-badge '+esc(f.severity)+'">'+esc(f.severity)+'</span></div><div class="finding-summary">'+esc(f.summary)+'</div><div class="finding-meta"><span>STATUS '+esc(f.status).toUpperCase()+'</span><span>'+esc(f.lab_id).toUpperCase()+'</span><span>'+esc(f.evidence_keys.length)+' EVIDENCE FLAGS</span></div><div class="card-actions"><button class="button subtle view-finding" data-run="'+esc(f.run_id)+'">Open Evidence</button><button class="button primary create-case" data-finding="'+esc(f.finding_id)+'">Create Case</button></div></article>'}).join("");$$(".view-finding").forEach(function(btn){btn.addEventListener("click",function(){openRunDetail(btn.dataset.run)})});$$(".create-case").forEach(function(btn){btn.addEventListener("click",function(){createCase(btn.dataset.finding)})})}
function renderCases(){const root=$("#cases-list");if(!state.cases.length){root.innerHTML='<div class="empty-state">No cases. Create one from a confirmed finding.</div>';return}root.innerHTML=state.cases.map(function(c){return '<article class="case-card"><div class="finding-id">'+esc(c.case_id)+'</div><h3>'+esc(c.title)+'</h3><div class="finding-meta"><span>'+esc(c.status).toUpperCase()+'</span><span>'+esc(c.finding_id||"NO FINDING LINK")+'</span></div></article>'}).join("")}
function renderEvidence(){const root=$("#evidence-view");if(!state.runs.length){root.innerHTML='<div class="empty-state">Execute a lab to populate the evidence vault.</div>';return}const selected=state.runs.find(function(r){return r.run_id===state.selectedEvidenceRun})||state.runs[0];state.selectedEvidenceRun=selected.run_id;const index=state.runs.map(function(r){return '<div class="evidence-row" data-evidence-run="'+esc(r.run_id)+'"><span class="run-number">L'+esc(r.lab_number)+'</span> '+esc(r.lab_name)+'<div class="mono tiny muted">'+esc(r.mode)+' · '+esc(r.run_id.slice(-8))+'</div></div>'}).join("");root.innerHTML='<div class="evidence-index"><div class="label">RUN EVIDENCE</div><div class="subtle-copy">Select a deterministic run artifact</div><div style="margin-top:12px">'+index+'</div></div><div class="evidence-detail"><div class="panel-head"><div><div class="label">'+esc(selected.lab_name)+'</div><div class="subtle-copy">'+esc(selected.run_id)+'</div></div><span class="tag '+(selected.result.finding?"fail":"pass")+'">'+esc(selected.result.verdict).toUpperCase()+'</span></div>'+scoreMarkup(selected.scores)+'<h3 style="font-size:12px;margin-top:18px">STRUCTURED RESULT</h3><pre class="json-block">'+esc(JSON.stringify(selected.result,null,2))+'</pre></div>';$$("[data-evidence-run]").forEach(function(el){el.addEventListener("click",function(){state.selectedEvidenceRun=el.dataset.evidenceRun;renderEvidence()})})}
function scoreMarkup(scores){return '<div class="score-trio"><div class="score-box control"><span>CONTROL</span><b>'+esc(scores.control)+'</b></div><div class="score-box exposure"><span>EXPOSURE</span><b>'+esc(scores.exposure)+'</b></div><div class="score-box evidence"><span>EVIDENCE</span><b>'+esc(scores.evidence)+'</b></div></div>'}
function openRunner(labId){$("#run-drawer").classList.add("open");$("#drawer-backdrop").classList.add("open");if(labId)$("#drawer-lab").value=labId;fillModes($("#drawer-lab"),$("#drawer-mode"));updateDrawerQuestion()}
function closeDrawers(){$("#run-drawer").classList.remove("open");$("#detail-drawer").classList.remove("open");$("#drawer-backdrop").classList.remove("open")}
function openRunDetail(runId){const run=state.runs.find(function(r){return r.run_id===runId});if(!run)return;$("#detail-kicker").textContent="LAB "+run.lab_number+" · "+run.mode;$("#detail-title").textContent=run.lab_name;const timeline=run.timeline.map(function(e){return '<div class="timeline-event '+esc(e.status)+'"><div class="timeline-mark"></div><div class="timeline-phase">'+esc(e.phase)+'</div><div class="timeline-message">'+esc(e.message)+'</div></div>'}).join("");let findingButton="";if(run.finding)findingButton='<button class="button primary wide detail-create-case" data-finding="'+esc(run.finding.finding_id)+'">Create Investigation Case</button>';$("#detail-body").innerHTML=scoreMarkup(run.scores)+'<div><div class="label">VERDICT</div><div style="margin-top:6px"><span class="tag '+(run.result.finding?"fail":"pass")+'">'+esc(run.result.verdict).toUpperCase()+'</span></div></div><hr class="sep"><div><div class="label">INVESTIGATION TIMELINE</div><div class="timeline">'+timeline+'</div></div><hr class="sep"><div><div class="label">HUNT POINTS</div><div class="metric-value" style="font-size:22px">'+esc(run.points.earned)+' <small>/ '+esc(run.points.possible)+'</small></div></div><div><div class="label">EVIDENCE</div><pre class="json-block">'+esc(JSON.stringify(run.result,null,2))+'</pre></div>'+findingButton;const create=$(".detail-create-case");if(create)create.addEventListener("click",function(){createCase(create.dataset.finding)});$("#detail-drawer").classList.add("open");$("#drawer-backdrop").classList.add("open")}
async function execute(labId,mode){try{toast("Executing "+labId.toUpperCase()+" / "+mode+"…","success");const record=await api("/api/run",{method:"POST",body:JSON.stringify({lab_id:labId,mode:mode})});await refreshData();closeDrawers();openRunDetail(record.run_id);toast(record.finding?("Confirmed finding: "+record.finding.title):("Run completed: "+record.result.verdict),record.finding?"error":"success")}catch(err){toast(err.message,"error")}}
async function createCase(findingId){const finding=state.findings.find(function(f){return f.finding_id===findingId});const title=finding?("Investigation · "+finding.title):"Security Investigation";try{await api("/api/cases",{method:"POST",body:JSON.stringify({title:title,finding_id:findingId})});await refreshData();closeDrawers();setView("cases");toast("Investigation case created.")}catch(err){toast(err.message,"error")}}
async function runHuntPack(){if(!confirm("Run all five deterministic vulnerable hunt scenarios? This creates local simulated findings only."))return;for(const h of state.catalog.hunts){await execute(h.lab_id,h.recommended_mode);closeDrawers()}setView("findings")}
function paletteItems(){const nav=[["Start Here","view","start"],["Command Center","view","command"],["Hunts","view","hunts"],["Findings","view","findings"],["Runs","view","runs"],["Cases","view","cases"],["Labs","view","labs"],["Attack Graph","view","graph"],["Evidence","view","evidence"]];const labs=[];state.catalog.labs.forEach(function(l){labs.push(["Run "+l.name+" · secure","run",l.lab_id+"|"+l.secure_mode]);labs.push(["Run "+l.name+" · vulnerable","run",l.lab_id+"|"+l.vulnerable_mode])});return nav.concat(labs)}
function renderPalette(query){const q=(query||"").toLowerCase().trim();const items=paletteItems().filter(function(item){return item[0].toLowerCase().includes(q)}).slice(0,14);$("#palette-results").innerHTML=items.map(function(item,i){return '<button class="palette-item '+(i===0?"active":"")+'" data-type="'+esc(item[1])+'" data-value="'+esc(item[2])+'"><span>'+esc(item[0])+'</span><span>'+(item[1]==="run"?"EXECUTE":"OPEN")+'</span></button>'}).join("");$$(".palette-item").forEach(function(btn){btn.addEventListener("click",function(){activatePaletteItem(btn)})})}
function activatePaletteItem(btn){$("#command-palette").classList.remove("open");if(btn.dataset.type==="view")setView(btn.dataset.value);else{const parts=btn.dataset.value.split("|");execute(parts[0],parts[1])}}
function openPalette(){$("#command-palette").classList.add("open");$("#palette-input").value="";renderPalette("");setTimeout(function(){$("#palette-input").focus()},20)}
async function refreshData(){const values=await Promise.all([api("/api/status"),api("/api/runs"),api("/api/findings"),api("/api/cases")]);state.status=values[0];state.runs=values[1].runs;state.findings=values[2].findings;state.cases=values[3].cases;renderStatus();renderRecentRuns();renderRuns();renderFindings();renderCases();if(state.view==="evidence")renderEvidence()}
async function boot(){state.catalog=await api("/api/catalog");fillLabSelect($("#quick-lab"));fillLabSelect($("#drawer-lab"));fillModes($("#quick-lab"),$("#quick-mode"));fillModes($("#drawer-lab"),$("#drawer-mode"));updateDrawerQuestion();renderPriorityHunts();renderHunts();renderLabs();await refreshData();$("[data-scroll-target]").forEach(function(btn){btn.addEventListener("click",function(){const target=document.getElementById(btn.dataset.scrollTarget);if(target)target.scrollIntoView({behavior:"smooth",block:"start"})})});$("#nav").addEventListener("click",function(e){const btn=e.target.closest(".nav-item");if(btn)setView(btn.dataset.view)});$$("[data-jump]").forEach(function(btn){btn.addEventListener("click",function(){setView(btn.dataset.jump)})});$("#quick-lab").addEventListener("change",function(){fillModes($("#quick-lab"),$("#quick-mode"))});$("#drawer-lab").addEventListener("change",function(){fillModes($("#drawer-lab"),$("#drawer-mode"));updateDrawerQuestion()});$("#quick-run").addEventListener("click",function(){execute($("#quick-lab").value,$("#quick-mode").value)});$("#drawer-run").addEventListener("click",function(){execute($("#drawer-lab").value,$("#drawer-mode").value)});$("#open-runner").addEventListener("click",function(){openRunner()});$("#close-runner").addEventListener("click",closeDrawers);$("#close-detail").addEventListener("click",closeDrawers);$("#drawer-backdrop").addEventListener("click",closeDrawers);$("#run-pack").addEventListener("click",runHuntPack);$("#command-button").addEventListener("click",openPalette);$("#palette-input").addEventListener("input",function(e){renderPalette(e.target.value)});$("#command-palette").addEventListener("click",function(e){if(e.target.id==="command-palette")e.currentTarget.classList.remove("open")});document.addEventListener("keydown",function(e){if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openPalette()}if(e.key==="Escape"){$("#command-palette").classList.remove("open");closeDrawers()}if(e.key==="Enter"&&$("#command-palette").classList.contains("open")){const first=$(".palette-item.active");if(first)activatePaletteItem(first)}})}
boot().catch(function(err){console.error(err);toast("Console initialization failed: "+err.message,"error")});

/* v2 Academy / Career Lab / Target Lab */
state.academy = { catalog: null, progress: null };
state.career = { catalog: null, selectedRole: null };
state.targets = { items: [], runs: [], selected: null, lastResult: null };

const _baseSetView = setView;
setView = function(view) {
  _baseSetView(view);
  const product = view === "career" ? "career" : (view === "target" ? "target" : "start");
  $$(".product-tab").forEach(function(tab) {
    tab.classList.toggle("active", tab.dataset.productView === product);
  });
  if (view === "career") $("#page-title").textContent = "Career Lab";
  else if (view === "target") $("#page-title").textContent = "Target Lab";
  else if (view === "start") $("#page-title").textContent = "Academy";
};

function renderAcademy() {
  const catalog = state.academy.catalog;
  const progress = state.academy.progress;
  if (!catalog || !progress) return;

  $("#academy-rank").textContent = progress.rank;
  $("#academy-xp").textContent = progress.xp + " XP";
  $("#academy-missions-done").textContent = progress.completed;
  $("#academy-missions-total").textContent = progress.total;
  const next = progress.next_rank;
  if (next) {
    $("#academy-next").textContent = "Next: " + next.name + " · " + next.xp + " XP";
    const priorFloor = progress.xp >= 7000 ? 7000 : progress.xp >= 4500 ? 4500 : progress.xp >= 2500 ? 2500 : progress.xp >= 1000 ? 1000 : 0;
    const span = Math.max(1, next.xp - priorFloor);
    $("#academy-xp-fill").style.width = Math.min(100, Math.max(0, (progress.xp - priorFloor) / span * 100)) + "%";
  } else {
    $("#academy-next").textContent = "Top rank achieved";
    $("#academy-xp-fill").style.width = "100%";
  }

  const missionMap = {};
  progress.missions.forEach(function(m) { missionMap[m.mission_id] = m; });

  $("#academy-paths").innerHTML = catalog.paths.map(function(path) {
    const rows = path.missions.map(function(m) {
      const p = missionMap[m.mission_id] || m;
      let stateText = "0/2 CONTROLS";
      let stateClass = "";
      if (!p.unlocked) { stateText = "LOCKED"; stateClass = "locked"; }
      else if (p.complete) { stateText = "COMPLETE"; stateClass = "complete"; }
      else if (p.secure_done || p.vulnerable_done) { stateText = "1/2 CONTROLS"; }
      return '<div class="mission-row" data-mission-lab="'+esc(m.lab_id)+'">' +
        '<div class="mission-id">'+esc(m.mission_id)+'</div>' +
        '<div><div class="mission-title">'+esc(m.title)+'</div><div class="mission-objective">'+esc(m.objective)+'</div></div>' +
        '<div class="mission-state '+stateClass+'">'+esc(stateText)+'</div>' +
        '<div class="mission-xp">+'+esc(m.xp)+' XP</div></div>';
    }).join("");
    return '<div class="path-card"><div class="path-head"><div><div class="lab-domain">LEARNING PATH</div><h3>'+esc(path.title)+'</h3><div class="path-summary">'+esc(path.summary)+'</div></div><span class="tag neutral">'+esc(path.missions.length)+' MISSIONS</span></div><div class="mission-list">'+rows+'</div></div>';
  }).join("");

  $$("[data-mission-lab]").forEach(function(row) {
    row.addEventListener("click", function() { openRunner(row.dataset.missionLab); });
  });

  $("#atlas-grid").innerHTML = catalog.atlas_tactics.map(function(t) {
    const linked = t.status === "mission-linked";
    const labs = t.labs && t.labs.length ? t.labs.map(function(id){ return (labById(id) || {}).number || id; }).join(", ") : "No mission yet";
    return '<div class="atlas-cell '+(linked ? "linked" : "roadmap")+'"><strong>'+esc(t.name)+'</strong><span>'+(linked ? "MISSION-LINKED" : "ROADMAP")+'</span><span class="atlas-labs">'+esc(labs)+'</span></div>';
  }).join("");

  $("#commercial-references").innerHTML = catalog.references.map(function(ref) {
    return '<div class="reference-item"><a href="'+esc(ref.url)+'" target="_blank" rel="noreferrer">'+esc(ref.name)+' ↗</a><div class="ref-purpose">'+esc(ref.purpose).toUpperCase()+'</div><p>'+esc(ref.pattern)+'</p></div>';
  }).join("");
}

function renderCareer(filter) {
  const data = state.career.catalog;
  if (!data) return;
  $("#role-count").textContent = data.roles.length + " ROLES";
  $("#career-framework-note").textContent = data.framework.name + " v" + data.framework.version + ". " + data.framework.note;

  if (!$("#career-role").options.length) {
    $("#career-role").innerHTML = data.roles.map(function(role) {
      return '<option value="'+esc(role.role_id)+'">'+esc(role.name)+'</option>';
    }).join("");
    const ai = data.roles.find(function(r){ return r.role_id === "ai-security"; });
    if (ai) $("#career-role").value = ai.role_id;
  }

  const q = (filter || "").toLowerCase().trim();
  const roles = data.roles.filter(function(role) {
    return !q || (role.name + " " + role.group + " " + role.summary + " " + role.focus.join(" ")).toLowerCase().includes(q);
  });
  $("#role-grid").innerHTML = roles.map(function(role) {
    return '<div class="role-card '+(state.career.selectedRole === role.role_id ? "selected" : "")+'" data-role="'+esc(role.role_id)+'"><div class="role-group">'+esc(role.group).toUpperCase()+'</div><h3>'+esc(role.name)+'</h3><p>'+esc(role.summary)+'</p><div class="role-focus">'+role.focus.slice(0,4).map(function(x){return '<span class="focus-chip">'+esc(x)+'</span>';}).join("")+'</div></div>';
  }).join("");
  $$("[data-role]").forEach(function(card) {
    card.addEventListener("click", function() {
      state.career.selectedRole = card.dataset.role;
      $("#career-role").value = card.dataset.role;
      renderCareer($("#role-search").value);
      generateInterview();
    });
  });
}

async function generateInterview() {
  const roleId = $("#career-role").value;
  const level = $("#career-level").value;
  if (!roleId) return;
  state.career.selectedRole = roleId;
  try {
    const session = await api("/api/interview", {method:"POST", body:JSON.stringify({role_id:roleId, level:level})});
    const questions = session.questions.map(function(q, idx) {
      return '<div class="question-card"><div class="question-dimension">'+esc(String(idx+1).padStart(2,"0"))+' · '+esc(q.dimension).toUpperCase()+'</div><p>'+esc(q.question)+'</p></div>';
    }).join("");
    $("#interview-session").className = "interview-session";
    $("#interview-session").innerHTML = '<div class="interview-head"><div class="lab-domain">'+esc(session.role.group).toUpperCase()+'</div><h3>'+esc(session.role.name)+' · '+esc(session.level).toUpperCase()+'</h3><div class="subtle-copy">'+esc(session.role.summary)+'</div><div class="scorecard-row">'+session.scorecard.map(function(s){return '<span class="scorecard-chip">'+esc(s)+'</span>';}).join("")+'</div></div><div class="question-list">'+questions+'</div>';
    renderCareer($("#role-search").value);
  } catch (err) {
    toast(err.message, "error");
  }
}

function renderTargets() {
  const root = $("#target-list");
  $("#target-count").textContent = state.targets.items.length + " TARGETS";
  if (!state.targets.items.length) {
    root.className = "target-list empty-state";
    root.textContent = "No targets registered.";
    $("#target-detail").innerHTML = '<div class="empty-state">Register a local path or GitHub URL to begin.</div>';
    return;
  }
  root.className = "target-list";
  root.innerHTML = state.targets.items.map(function(t) {
    const status = t.analysis ? t.analysis.status : "registered";
    return '<div class="target-item '+(state.targets.selected===t.target_id?"selected":"")+'" data-target="'+esc(t.target_id)+'"><div class="target-source">'+esc(t.source_type).toUpperCase()+' · '+esc(status).toUpperCase()+'</div><h3>'+esc(t.name)+'</h3><div class="target-path">'+esc(t.local_path || t.location)+'</div></div>';
  }).join("");
  $$("[data-target]").forEach(function(item) {
    item.addEventListener("click", function() {
      state.targets.selected = item.dataset.target;
      renderTargets();
      renderTargetDetail();
    });
  });
  if (!state.targets.selected && state.targets.items.length) state.targets.selected = state.targets.items[0].target_id;
  renderTargetDetail();
}

function targetById(id) {
  return state.targets.items.find(function(t){ return t.target_id === id; });
}

function renderTargetDetail() {
  const root = $("#target-detail");
  const target = targetById(state.targets.selected);
  if (!target) return;
  const analysis = target.analysis;
  const actions = [];
  if (target.source_type === "github" && !target.local_path) actions.push('<button class="button primary target-clone" data-target="'+esc(target.target_id)+'">Clone & Analyze</button>');
  else actions.push('<button class="button subtle target-analyze" data-target="'+esc(target.target_id)+'">Analyze</button>');
  if (target.local_path) actions.push('<button class="button subtle target-scaffold" data-target="'+esc(target.target_id)+'">Create Adapter Scaffold</button>');

  let capabilities = '<div class="empty-state">Analyze the target to discover security surfaces.</div>';
  let compatible = "";
  let manifest = "";
  if (analysis) {
    capabilities = '<div class="capability-grid">'+(analysis.signals || []).map(function(sig){
      return '<div class="capability-card '+(sig.hits>0?"active":"")+'"><strong>'+esc(sig.capability)+'</strong><b>'+esc(sig.hits)+'</b></div>';
    }).join("")+'</div>';
    compatible = '<div class="compatible-labs">'+(analysis.compatible_labs || []).map(function(labId) {
      const lab = labById(labId);
      return '<div class="target-lab-row"><span class="run-number">L'+esc(lab ? lab.number : labId)+'</span><span>'+esc(lab ? lab.name : labId)+'</span><button class="button subtle target-run" data-target="'+esc(target.target_id)+'" data-lab="'+esc(labId)+'">Run Target Test</button></div>';
    }).join("")+'</div>';
    if (!(analysis.compatible_labs || []).length) compatible = '<div class="empty-state">No compatible boundaries detected yet. Capability discovery is heuristic.</div>';
    manifest = '<div class="manifest-box"><div class="label">ADAPTER MANIFEST</div><code>'+esc(analysis.manifest_path || ".aasl/target.json")+'</code><div class="subtle-copy">'+(analysis.manifest ? "Manifest detected. Target commands can be executed explicitly." : "No manifest yet. Use Create Adapter Scaffold, then add trusted commands for the labs you want to test.")+'</div></div>';
  }

  const recentRuns = state.targets.runs.filter(function(r){return r.target_id === target.target_id;}).slice(0,5);
  const runRows = recentRuns.length ? recentRuns.map(function(r){
    return '<div class="target-run-row"><b>'+esc((labById(r.lab_id)||{}).name || r.lab_id)+'</b> · '+esc(r.mode)+' · <span class="'+(r.result.finding?"severity high":"muted")+'">'+esc(r.result.verdict)+'</span></div>';
  }).join("") : '<div class="empty-state">No target runs yet.</div>';

  root.innerHTML = '<div class="target-detail-grid"><div><div class="lab-domain">'+esc(target.source_type).toUpperCase()+' TARGET</div><h2>'+esc(target.name)+'</h2><div class="target-path">'+esc(target.local_path || target.location)+'</div><div class="target-actions">'+actions.join("")+'</div><div class="label">DISCOVERED CAPABILITIES</div>'+capabilities+'<div style="margin-top:16px" class="label">COMPATIBLE LABS</div>'+compatible+'</div><div>'+manifest+'<div style="margin-top:16px" class="label">RECENT TARGET RUNS</div><div class="target-run-list">'+runRows+'</div><div id="target-result" class="target-result"></div></div></div>';

  $$(".target-analyze").forEach(function(btn){btn.addEventListener("click", function(){targetAction("/api/targets/analyze", btn.dataset.target);});});
  $$(".target-clone").forEach(function(btn){btn.addEventListener("click", function(){targetAction("/api/targets/clone", btn.dataset.target);});});
  $$(".target-scaffold").forEach(function(btn){btn.addEventListener("click", function(){targetAction("/api/targets/scaffold", btn.dataset.target);});});
  $$(".target-run").forEach(function(btn){
    btn.addEventListener("click", function() {
      const lab = labById(btn.dataset.lab);
      const mode = prompt("Scenario to run (" + (lab ? lab.modes.join(", ") : "secure/vulnerable") + "):", lab ? lab.secure_mode : "secure");
      if (mode) runTargetTest(btn.dataset.target, btn.dataset.lab, mode.trim());
    });
  });
}

async function targetAction(path, targetId) {
  try {
    await api(path, {method:"POST", body:JSON.stringify({target_id:targetId})});
    await refreshTargets();
    toast("Target updated.");
  } catch (err) { toast(err.message, "error"); }
}

async function runTargetTest(targetId, labId, mode) {
  if (!confirm("Run the configured target adapter? Only continue for a repository you trust and are authorized to test.")) return;
  try {
    const result = await api("/api/targets/run", {method:"POST", body:JSON.stringify({target_id:targetId, lab_id:labId, mode:mode})});
    state.targets.lastResult = result;
    await refreshTargets();
    renderTargetDetail();
    const box = $("#target-result");
    if (box) box.innerHTML = '<div class="label">LAST TARGET RESULT</div><pre class="json-block">'+esc(JSON.stringify(result.result,null,2))+'</pre>';
    toast("Target assessment completed.", result.result.finding ? "error" : "success");
  } catch (err) { toast(err.message, "error"); }
}

async function registerTarget() {
  const name = $("#target-name").value.trim();
  const source = $("#target-source").value;
  const location = $("#target-location").value.trim();
  if (!name || !location) { toast("Target name and location are required.", "error"); return; }
  try {
    const target = await api("/api/targets", {method:"POST", body:JSON.stringify({name:name, source_type:source, location:location})});
    state.targets.selected = target.target_id;
    if (source === "local") await api("/api/targets/analyze", {method:"POST", body:JSON.stringify({target_id:target.target_id})});
    await refreshTargets();
    toast("Target registered.");
  } catch (err) { toast(err.message, "error"); }
}

async function refreshTargets() {
  const payload = await api("/api/targets");
  state.targets.items = payload.targets || [];
  state.targets.runs = payload.runs || [];
  renderTargets();
}

async function bootV2() {
  const values = await Promise.all([
    api("/api/academy"),
    api("/api/academy/progress"),
    api("/api/career"),
    api("/api/targets"),
  ]);
  state.academy.catalog = values[0];
  state.academy.progress = values[1];
  state.career.catalog = values[2];
  state.targets.items = values[3].targets || [];
  state.targets.runs = values[3].runs || [];

  renderAcademy();
  renderCareer("");
  renderTargets();

  $$(".product-tab").forEach(function(tab) {
    tab.addEventListener("click", function() { setView(tab.dataset.productView); });
  });
  $("#role-search").addEventListener("input", function(e){ renderCareer(e.target.value); });
  $("#career-role").addEventListener("change", function(){ state.career.selectedRole = $("#career-role").value; renderCareer($("#role-search").value); });
  $("#generate-interview").addEventListener("click", generateInterview);
  $("#register-target").addEventListener("click", registerTarget);

  const oldRefresh = refreshData;
  refreshData = async function() {
    await oldRefresh();
    state.academy.progress = await api("/api/academy/progress");
    renderAcademy();
  };
}

bootV2().catch(function(err){ console.error(err); toast("v2 initialization failed: "+err.message, "error"); });
