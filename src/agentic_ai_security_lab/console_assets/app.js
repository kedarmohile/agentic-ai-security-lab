const state={catalog:{labs:[],hunts:[]},status:{},runs:[],findings:[],cases:[],view:"start",selectedEvidenceRun:null};
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]})}
async function api(path,options){const o=options||{};o.headers=Object.assign({"Content-Type":"application/json"},o.headers||{});const response=await fetch(path,o);const payload=await response.json();if(!response.ok)throw new Error(payload.error||("HTTP "+response.status));return payload}
function toast(message,kind){const el=document.createElement("div");el.className="toast "+(kind||"success");el.textContent=message;$("#toast-stack").appendChild(el);setTimeout(function(){el.remove()},3200)}
function labById(id){return state.catalog.labs.find(function(l){return l.lab_id===id})}
function setView(view){state.view=view;$(".view").forEach(function(el){el.classList.toggle("active",el.id==="view-"+view)});$(".nav-item").forEach(function(el){el.classList.toggle("active",el.dataset.view===view)});const active=$('.nav-item[data-view="'+view+'"]');$("#page-title").textContent=active?active.textContent.trim().replace(/\d+$/,"").trim():"Command Center";window.scrollTo({top:0,behavior:"smooth"});if(view==="evidence")renderEvidence()}
function fillLabSelect(select){select.innerHTML=state.catalog.labs.map(function(l){return '<option value="'+esc(l.lab_id)+'">LAB '+esc(l.number)+' · '+esc(l.name)+'</option>'}).join("")}
function fillModes(labSelect,modeSelect){const lab=labById(labSelect.value);if(!lab)return;modeSelect.innerHTML=lab.modes.map(function(m){return '<option value="'+esc(m)+'">'+esc(m)+'</option>'}).join("")}
function updateDrawerQuestion(){const lab=labById($("#drawer-lab").value);$("#drawer-lab-question").innerHTML=lab?'<b>'+esc(lab.domain)+' boundary</b><br>'+esc(lab.question):""}
function postureColor(score){if(score==null)return"#42505c";if(score>=85)return"#44d39a";if(score>=60)return"#f4b860";return"#ff6577"}
function renderStatus(){const s=state.status;const score=s.posture_score;$("#posture-score").textContent=score==null?"--":score;$("#assessed-count").textContent=s.assessed_labs||0;$("#assessment-fill").style.width=((s.assessed_labs||0)/(s.total_labs||5)*100)+"%";$("#metric-findings").textContent=s.findings||0;$("#metric-high").textContent=(s.high_findings||0)+" HIGH";$("#metric-medium").textContent=(s.medium_findings||0)+" MED";$("#metric-evidence").textContent=s.evidence_confidence==null?"--":s.evidence_confidence;$("#nav-findings").textContent=s.findings||0;const circumference=314.159;const ratio=score==null?0:score/100;const ring=$("#ring-value");ring.style.strokeDashoffset=String(circumference*(1-ratio));ring.style.stroke=postureColor(score);const badge=$("#posture-state");if(score==null){badge.className="tag neutral";badge.textContent="UNASSESSED";$("#posture-title").textContent="Run a lab to establish posture";$("#posture-detail").textContent="Scores are calculated only from executed lab evidence. No demo findings are pre-seeded."}else if(score>=85){badge.className="tag pass";badge.textContent="CONTROLLED";$("#posture-title").textContent="Controls holding across assessed labs";$("#posture-detail").textContent="Posture is based on the latest executed result for each assessed lab."}else{badge.className="tag fail";badge.textContent="ATTENTION";$("#posture-title").textContent="Security boundary failures need review";$("#posture-detail").textContent="Pivot into Findings or Attack Graph for evidence-backed investigation."}}
function renderPriorityHunts(){$("#priority-hunts").innerHTML=state.catalog.hunts.map(function(h){return '<div class="hunt-row" data-hunt="'+esc(h.hunt_id)+'"><div class="hunt-id">'+esc(h.hunt_id)+'</div><div><div class="hunt-title">'+esc(h.title)+'</div><div class="subtle-copy">'+esc(h.objective)+'</div></div><div class="hunt-meta difficulty">'+esc(h.difficulty)+'</div><div class="hunt-meta">'+esc(h.points)+' PTS</div></div>'}).join("");$(".hunt-row").forEach(function(el){el.addEventListener("click",function(){setView("hunts");setTimeout(function(){const t=document.querySelector('[data-hunt-card="'+el.dataset.hunt+'"]');if(t)t.scrollIntoView({behavior:"smooth",block:"center"})},60)})})}
function renderHunts(){$("#hunts-grid").innerHTML=state.catalog.hunts.map(function(h){const steps=h.steps.map(function(step){return '<div class="step">'+esc(step)+'</div>'}).join("");return '<article class="hunt-card" data-hunt-card="'+esc(h.hunt_id)+'"><div class="hunt-card-top"><div><div class="hunt-id">'+esc(h.hunt_id)+'</div><h3>'+esc(h.title)+'</h3></div><div class="points">'+esc(h.points)+' PTS</div></div><p class="hypothesis"><b>Hypothesis:</b> '+esc(h.hypothesis)+'</p><p class="hypothesis"><b>Objective:</b> '+esc(h.objective)+'</p><div class="hunt-stats"><span>'+esc(h.difficulty).toUpperCase()+'</span><span>'+esc(h.controls)+' CONTROLS</span><span>LAB '+esc(labById(h.lab_id).number)+'</span></div><div class="steps">'+steps+'</div><div class="card-actions"><button class="button primary run-hunt" data-lab="'+esc(h.lab_id)+'" data-mode="'+esc(h.recommended_mode)+'">Run Hunt</button><button class="button subtle open-lab" data-lab="'+esc(h.lab_id)+'">Open Lab</button></div></article>'}).join("");$(".run-hunt").forEach(function(btn){btn.addEventListener("click",function(){execute(btn.dataset.lab,btn.dataset.mode)})});$(".open-lab").forEach(function(btn){btn.addEventListener("click",function(){openRunner(btn.dataset.lab)})})}
function renderLabs(){$("#labs-grid").innerHTML=state.catalog.labs.map(function(l){const modes=l.modes.map(function(m){return '<span class="mode-chip">'+esc(m)+'</span>'}).join("");return '<article class="lab-card"><div class="lab-card-top"><div><div class="lab-domain">'+esc(l.domain).toUpperCase()+' BOUNDARY</div><h3>'+esc(l.name)+'</h3></div><div class="lab-number">'+esc(l.number)+'</div></div><div class="lab-question">'+esc(l.question)+'</div><div class="mode-chips">'+modes+'</div><div class="card-actions"><button class="button primary open-runner-lab" data-lab="'+esc(l.lab_id)+'">Run Lab</button><button class="button subtle run-secure" data-lab="'+esc(l.lab_id)+'" data-mode="'+esc(l.secure_mode)+'">Secure Control</button></div></article>'}).join("");$(".open-runner-lab").forEach(function(btn){btn.addEventListener("click",function(){openRunner(btn.dataset.lab)})});$(".run-secure").forEach(function(btn){btn.addEventListener("click",function(){execute(btn.dataset.lab,btn.dataset.mode)})})}
function renderRecentRuns(){const runs=state.runs.slice(0,5);const root=$("#recent-runs");if(!runs.length){root.className="run-list empty-state";root.textContent="No runs yet. Execute a lab to create evidence.";return}root.className="run-list";root.innerHTML=runs.map(function(r){return '<div class="run-item" data-run="'+esc(r.run_id)+'"><div class="run-number">L'+esc(r.lab_number)+'</div><div><div class="run-name">'+esc(r.lab_name)+'</div><div class="run-mode">'+esc(r.mode)+'</div></div><div class="tag '+(r.result.finding?"fail":"pass")+'">'+esc(r.result.verdict).toUpperCase()+'</div><div class="score-mini">'+esc(r.scores.control)+'</div></div>'}).join("");$(".run-item").forEach(function(el){el.addEventListener("click",function(){openRunDetail(el.dataset.run)})})}
function renderRuns(){const root=$("#runs-list");if(!state.runs.length){root.innerHTML='<div class="empty-state">No run history yet.</div>';return}let body='<div class="run-table-head"><span>LAB</span><span>RUN</span><span>MODE</span><span>CONTROL</span><span>EXPOSURE</span><span>VERDICT</span></div>';body+=state.runs.map(function(r){return '<div class="run-table-row" data-run="'+esc(r.run_id)+'"><span class="run-number">L'+esc(r.lab_number)+'</span><span>'+esc(r.lab_name)+'</span><span class="mono tiny">'+esc(r.mode)+'</span><span class="score-pill">'+esc(r.scores.control)+'/100</span><span class="score-pill">'+esc(r.scores.exposure)+'/100</span><span class="tag '+(r.result.finding?"fail":"pass")+'">'+esc(r.result.verdict).toUpperCase()+'</span></div>'}).join("");root.innerHTML=body;$(".run-table-row").forEach(function(el){el.addEventListener("click",function(){openRunDetail(el.dataset.run)})})}
function renderFindings(){const root=$("#findings-list");if(!state.findings.length){root.innerHTML='<div class="empty-state">No confirmed findings. Run vulnerable scenarios to validate the investigation workflow.</div>';return}root.innerHTML=state.findings.map(function(f){return '<article class="finding-card"><div class="finding-head"><div><div class="finding-id">'+esc(f.finding_id)+'</div><h3>'+esc(f.title)+'</h3></div><span class="severity-badge '+esc(f.severity)+'">'+esc(f.severity)+'</span></div><div class="finding-summary">'+esc(f.summary)+'</div><div class="finding-meta"><span>STATUS '+esc(f.status).toUpperCase()+'</span><span>'+esc(f.lab_id).toUpperCase()+'</span><span>'+esc(f.evidence_keys.length)+' EVIDENCE FLAGS</span></div><div class="card-actions"><button class="button subtle view-finding" data-run="'+esc(f.run_id)+'">Open Evidence</button><button class="button primary create-case" data-finding="'+esc(f.finding_id)+'">Create Case</button></div></article>'}).join("");$(".view-finding").forEach(function(btn){btn.addEventListener("click",function(){openRunDetail(btn.dataset.run)})});$(".create-case").forEach(function(btn){btn.addEventListener("click",function(){createCase(btn.dataset.finding)})})}
function renderCases(){const root=$("#cases-list");if(!state.cases.length){root.innerHTML='<div class="empty-state">No cases. Create one from a confirmed finding.</div>';return}root.innerHTML=state.cases.map(function(c){return '<article class="case-card"><div class="finding-id">'+esc(c.case_id)+'</div><h3>'+esc(c.title)+'</h3><div class="finding-meta"><span>'+esc(c.status).toUpperCase()+'</span><span>'+esc(c.finding_id||"NO FINDING LINK")+'</span></div></article>'}).join("")}
function renderEvidence(){const root=$("#evidence-view");if(!state.runs.length){root.innerHTML='<div class="empty-state">Execute a lab to populate the evidence vault.</div>';return}const selected=state.runs.find(function(r){return r.run_id===state.selectedEvidenceRun})||state.runs[0];state.selectedEvidenceRun=selected.run_id;const index=state.runs.map(function(r){return '<div class="evidence-row" data-evidence-run="'+esc(r.run_id)+'"><span class="run-number">L'+esc(r.lab_number)+'</span> '+esc(r.lab_name)+'<div class="mono tiny muted">'+esc(r.mode)+' · '+esc(r.run_id.slice(-8))+'</div></div>'}).join("");root.innerHTML='<div class="evidence-index"><div class="label">RUN EVIDENCE</div><div class="subtle-copy">Select a deterministic run artifact</div><div style="margin-top:12px">'+index+'</div></div><div class="evidence-detail"><div class="panel-head"><div><div class="label">'+esc(selected.lab_name)+'</div><div class="subtle-copy">'+esc(selected.run_id)+'</div></div><span class="tag '+(selected.result.finding?"fail":"pass")+'">'+esc(selected.result.verdict).toUpperCase()+'</span></div>'+scoreMarkup(selected.scores)+'<h3 style="font-size:12px;margin-top:18px">STRUCTURED RESULT</h3><pre class="json-block">'+esc(JSON.stringify(selected.result,null,2))+'</pre></div>';$("[data-evidence-run]").forEach(function(el){el.addEventListener("click",function(){state.selectedEvidenceRun=el.dataset.evidenceRun;renderEvidence()})})}
function scoreMarkup(scores){return '<div class="score-trio"><div class="score-box control"><span>CONTROL</span><b>'+esc(scores.control)+'</b></div><div class="score-box exposure"><span>EXPOSURE</span><b>'+esc(scores.exposure)+'</b></div><div class="score-box evidence"><span>EVIDENCE</span><b>'+esc(scores.evidence)+'</b></div></div>'}
function openRunner(labId){$("#run-drawer").classList.add("open");$("#drawer-backdrop").classList.add("open");if(labId)$("#drawer-lab").value=labId;fillModes($("#drawer-lab"),$("#drawer-mode"));updateDrawerQuestion()}
function closeDrawers(){$("#run-drawer").classList.remove("open");$("#detail-drawer").classList.remove("open");$("#drawer-backdrop").classList.remove("open")}
function openRunDetail(runId){const run=state.runs.find(function(r){return r.run_id===runId});if(!run)return;$("#detail-kicker").textContent="LAB "+run.lab_number+" · "+run.mode;$("#detail-title").textContent=run.lab_name;const timeline=run.timeline.map(function(e){return '<div class="timeline-event '+esc(e.status)+'"><div class="timeline-mark"></div><div class="timeline-phase">'+esc(e.phase)+'</div><div class="timeline-message">'+esc(e.message)+'</div></div>'}).join("");let findingButton="";if(run.finding)findingButton='<button class="button primary wide detail-create-case" data-finding="'+esc(run.finding.finding_id)+'">Create Investigation Case</button>';$("#detail-body").innerHTML=scoreMarkup(run.scores)+'<div><div class="label">VERDICT</div><div style="margin-top:6px"><span class="tag '+(run.result.finding?"fail":"pass")+'">'+esc(run.result.verdict).toUpperCase()+'</span></div></div><hr class="sep"><div><div class="label">INVESTIGATION TIMELINE</div><div class="timeline">'+timeline+'</div></div><hr class="sep"><div><div class="label">HUNT POINTS</div><div class="metric-value" style="font-size:22px">'+esc(run.points.earned)+' <small>/ '+esc(run.points.possible)+'</small></div></div><div><div class="label">EVIDENCE</div><pre class="json-block">'+esc(JSON.stringify(run.result,null,2))+'</pre></div>'+findingButton;const create=$(".detail-create-case");if(create)create.addEventListener("click",function(){createCase(create.dataset.finding)});$("#detail-drawer").classList.add("open");$("#drawer-backdrop").classList.add("open")}
async function execute(labId,mode){try{toast("Executing "+labId.toUpperCase()+" / "+mode+"…","success");const record=await api("/api/run",{method:"POST",body:JSON.stringify({lab_id:labId,mode:mode})});await refreshData();closeDrawers();openRunDetail(record.run_id);toast(record.finding?("Confirmed finding: "+record.finding.title):("Run completed: "+record.result.verdict),record.finding?"error":"success")}catch(err){toast(err.message,"error")}}
async function createCase(findingId){const finding=state.findings.find(function(f){return f.finding_id===findingId});const title=finding?("Investigation · "+finding.title):"Security Investigation";try{await api("/api/cases",{method:"POST",body:JSON.stringify({title:title,finding_id:findingId})});await refreshData();closeDrawers();setView("cases");toast("Investigation case created.")}catch(err){toast(err.message,"error")}}
async function runHuntPack(){if(!confirm("Run all five deterministic vulnerable hunt scenarios? This creates local simulated findings only."))return;for(const h of state.catalog.hunts){await execute(h.lab_id,h.recommended_mode);closeDrawers()}setView("findings")}
function paletteItems(){const nav=[["Start Here","view","start"],["Pricing","view","pricing"],["Command Center","view","command"],["Hunts","view","hunts"],["Findings","view","findings"],["Runs","view","runs"],["Cases","view","cases"],["Labs","view","labs"],["Attack Graph","view","graph"],["Evidence","view","evidence"]];const labs=[];state.catalog.labs.forEach(function(l){labs.push(["Run "+l.name+" · secure","run",l.lab_id+"|"+l.secure_mode]);labs.push(["Run "+l.name+" · vulnerable","run",l.lab_id+"|"+l.vulnerable_mode])});return nav.concat(labs)}
function renderPalette(query){const q=(query||"").toLowerCase().trim();const items=paletteItems().filter(function(item){return item[0].toLowerCase().includes(q)}).slice(0,14);$("#palette-results").innerHTML=items.map(function(item,i){return '<button class="palette-item '+(i===0?"active":"")+'" data-type="'+esc(item[1])+'" data-value="'+esc(item[2])+'"><span>'+esc(item[0])+'</span><span>'+(item[1]==="run"?"EXECUTE":"OPEN")+'</span></button>'}).join("");$(".palette-item").forEach(function(btn){btn.addEventListener("click",function(){activatePaletteItem(btn)})})}
function activatePaletteItem(btn){$("#command-palette").classList.remove("open");if(btn.dataset.type==="view")setView(btn.dataset.value);else{const parts=btn.dataset.value.split("|");execute(parts[0],parts[1])}}
function openPalette(){$("#command-palette").classList.add("open");$("#palette-input").value="";renderPalette("");setTimeout(function(){$("#palette-input").focus()},20)}
async function refreshData(){const values=await Promise.all([api("/api/status"),api("/api/runs"),api("/api/findings"),api("/api/cases")]);state.status=values[0];state.runs=values[1].runs;state.findings=values[2].findings;state.cases=values[3].cases;renderStatus();renderRecentRuns();renderRuns();renderFindings();renderCases();if(state.view==="evidence")renderEvidence()}
async function boot(){state.catalog=await api("/api/catalog");fillLabSelect($("#quick-lab"));fillLabSelect($("#drawer-lab"));fillModes($("#quick-lab"),$("#quick-mode"));fillModes($("#drawer-lab"),$("#drawer-mode"));updateDrawerQuestion();renderPriorityHunts();renderHunts();renderLabs();await refreshData();$("[data-scroll-target]").forEach(function(btn){btn.addEventListener("click",function(){const target=document.getElementById(btn.dataset.scrollTarget);if(target)target.scrollIntoView({behavior:"smooth",block:"start"})})});$("#nav").addEventListener("click",function(e){const btn=e.target.closest(".nav-item");if(btn)setView(btn.dataset.view)});$("[data-jump]").forEach(function(btn){btn.addEventListener("click",function(){setView(btn.dataset.jump)})});$("#quick-lab").addEventListener("change",function(){fillModes($("#quick-lab"),$("#quick-mode"))});$("#drawer-lab").addEventListener("change",function(){fillModes($("#drawer-lab"),$("#drawer-mode"));updateDrawerQuestion()});$("#quick-run").addEventListener("click",function(){execute($("#quick-lab").value,$("#quick-mode").value)});$("#drawer-run").addEventListener("click",function(){execute($("#drawer-lab").value,$("#drawer-mode").value)});$("#open-runner").addEventListener("click",function(){openRunner()});$("#close-runner").addEventListener("click",closeDrawers);$("#close-detail").addEventListener("click",closeDrawers);$("#drawer-backdrop").addEventListener("click",closeDrawers);$("#run-pack").addEventListener("click",runHuntPack);$("#command-button").addEventListener("click",openPalette);$("#palette-input").addEventListener("input",function(e){renderPalette(e.target.value)});$("#command-palette").addEventListener("click",function(e){if(e.target.id==="command-palette")e.currentTarget.classList.remove("open")});document.addEventListener("keydown",function(e){if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openPalette()}if(e.key==="Escape"){$("#command-palette").classList.remove("open");closeDrawers()}if(e.key==="Enter"&&$("#command-palette").classList.contains("open")){const first=$(".palette-item.active");if(first)activatePaletteItem(first)}})}


/* v2 Academy / Career Lab / Target Lab */
state.academy = { catalog: null, progress: null };
state.career = { catalog: null, selectedRole: null, currentSession: null, mode: "interview", simulationCatalog: null, currentScenario: null, hintsUsed: {}, vmCatalog: null, vmStatus: null, evaluator: null, interviewer: null, voiceRecognition: null };
state.targets = { items: [], runs: [], selected: null, lastResult: null };
state.pricing = { catalog: null, billing: "monthly" };

const _baseSetView = setView;
setView = function(view) {
  _baseSetView(view);
  const product = view === "career" ? "career" : (view === "target" ? "target" : (view === "start" ? "start" : null));
  $(".product-tab").forEach(function(tab) {
    tab.classList.toggle("active", product !== null && tab.dataset.productView === product);
  });
  if (view === "career") $("#page-title").textContent = "Career Lab";
  else if (view === "target") $("#page-title").textContent = "Target Lab";
  else if (view === "start") $("#page-title").textContent = "Academy";
  else if (view === "pricing") $("#page-title").textContent = "Pricing";
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

  $("[data-mission-lab]").forEach(function(row) {
    row.addEventListener("click", function() { openRunner(row.dataset.missionLab); });
  });

  $("#atlas-grid").innerHTML = catalog.atlas_tactics.map(function(t) {
    const linked = t.status === "mission-linked";
    const labs = t.labs && t.labs.length ? t.labs.map(function(id){ return (labById(id) || {}).number || id; }).join(", ") : "No mission yet";
    return '<div class="atlas-cell '+(linked ? "linked" : "roadmap")+'"><strong>'+esc(t.name)+'</strong><span>'+(linked ? "MISSION-LINKED" : "ROADMAP")+'</span><span class="atlas-labs">'+esc(labs)+'</span></div>';
  }).join("");

  const frameworkOrder = ["owasp_web_2025","owasp_llm_2026","owasp_agentic_2026","mitre_atlas_agentic"];
  $("#framework-catalogs").innerHTML = frameworkOrder.map(function(key) {
    const fw = catalog.frameworks && catalog.frameworks[key];
    if (!fw) return "";
    return '<article class="framework-card"><div class="framework-head"><div><div class="lab-domain">'+esc(fw.scope).toUpperCase()+'</div><h3>'+esc(fw.name)+'</h3></div><span class="tag neutral">'+esc(fw.items.length)+' ITEMS</span></div><div class="framework-items">'+fw.items.map(function(item){return '<div class="framework-item"><b>'+esc(item.id)+'</b><span>'+esc(item.name)+'</span></div>';}).join("")+'</div></article>';
  }).join("");

  $("#commercial-references").innerHTML = catalog.references.map(function(ref) {
    return '<div class="reference-item"><strong>'+esc(ref.name)+'</strong><div class="ref-purpose">'+esc(ref.purpose).toUpperCase()+'</div><p>'+esc(ref.pattern)+'</p><small>'+esc(ref.note || "")+'</small></div>';
  }).join("");
}


function renderPricing() {
  const catalog = state.pricing.catalog;
  if (!catalog) return;
  const billing = state.pricing.billing;
  const cards = $("#pricing-cards");
  const compare = $("#pricing-compare");
  if (!cards || !compare) return;

  cards.innerHTML = catalog.plans.map(function(plan) {
    const amount = billing === "annual" ? plan.annual : plan.monthly;
    let price = "Custom";
    let cadence = "";
    let subline = "";
    if (amount === 0) {
      price = "$0";
      cadence = "";
      subline = "No credit card";
    } else if (typeof amount === "number") {
      price = "$" + amount;
      cadence = billing === "annual" ? "/year" : "/month";
      if (billing === "annual" && typeof plan.monthly === "number" && plan.monthly > 0) {
        const monthlyEquivalent = (amount / 12).toFixed(2);
        const savings = Math.round((1 - amount / (plan.monthly * 12)) * 100);
        subline = "$"+monthlyEquivalent+"/mo effective · save "+savings+"%";
      } else if (billing === "monthly" && plan.plan_id === "pro") {
        subline = "Hosted labs are coming soon";
      }
    } else {
      subline = "Organization pricing";
    }

    const features = plan.features.map(function(feature){
      return '<li><span>✓</span>'+esc(feature)+'</li>';
    }).join("");
    const statusClass = plan.status === "available" || plan.status === "launch" ? "ready" : "roadmap";
    return '<article class="pricing-card '+(plan.highlight ? "featured" : "")+'">' +
      '<div class="pricing-card-top"><span class="pricing-badge '+statusClass+'">'+esc(plan.badge)+'</span><h3>'+esc(plan.name)+'</h3><p>'+esc(plan.audience)+'</p></div>' +
      '<div class="pricing-price"><strong>'+esc(price)+'</strong><span>'+esc(cadence)+'</span></div>' +
      '<div class="pricing-subline">'+esc(subline)+'</div>' +
      '<ul class="pricing-features">'+features+'</ul>' +
      '<button class="button '+(plan.highlight ? "primary" : "subtle")+' wide pricing-cta" data-pricing-view="'+esc(plan.cta_view)+'" data-plan="'+esc(plan.plan_id)+'">'+esc(plan.cta)+'</button>' +
      '</article>';
  }).join("");

  const rows = [
    ["Full Academy", "Selected", "✓", "✓", "Planned"],
    ["Career Lab role tracks", "Selected", "All", "All", "All"],
    ["GenAI mastery coaching", "Local / own key", "Included*", "Included*", "Included*"],
    ["Local VM labs", "✓", "✓", "✓", "✓"],
    ["Target Lab", "Local", "Local + GitHub", "Local + GitHub", "Private org targets"],
    ["Hosted cloud labs", "—", "—", "1 concurrent", "Managed ranges"],
    ["Hosted compute", "—", "—", billing === "annual" ? "300 hrs/year" : "30 hrs/month", "Custom"],
  ];
  compare.innerHTML = '<div class="pricing-table-row pricing-table-head"><span>FEATURE</span><span>FREE</span><span>CORE</span><span>PRO</span><span>TEAMS</span></div>' +
    rows.map(function(row){
      return '<div class="pricing-table-row">'+row.map(function(cell){return '<span>'+esc(cell)+'</span>';}).join("")+'</div>';
    }).join("") +
    '<div class="pricing-fair-use">* GenAI evaluation is included under fair-use limits. Local/deterministic evaluation remains available without cloud inference.</div>';

  $$(".pricing-cta").forEach(function(btn){
    btn.addEventListener("click", function(){
      const target = btn.dataset.pricingView;
      if (btn.dataset.plan === "pro") {
        toast("Hosted Pro labs are not live yet. Showing Simulation Range so you can preview the workflow.");
      } else if (btn.dataset.plan === "teams") {
        toast("Team features are on the roadmap. Showing Target Lab, the foundation for organization-specific assessment.");
      } else if (btn.dataset.plan === "core") {
        toast("Billing is not enabled in this local build. Core pricing is the launch commercial model.");
      }
      setView(target);
      if (target === "career" && typeof setCareerMode === "function") setCareerMode("simulation");
    });
  });
}

function setBillingPeriod(period) {
  state.pricing.billing = period === "annual" ? "annual" : "monthly";
  $(".billing-option").forEach(function(btn){
    btn.classList.toggle("active", btn.dataset.billing === state.pricing.billing);
  });
  renderPricing();
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
  $("[data-role]").forEach(function(card) {
    card.addEventListener("click", function() {
      state.career.selectedRole = card.dataset.role;
      $("#career-role").value = card.dataset.role;
      $("#simulation-role").value = card.dataset.role;
      renderCareer($("#role-search").value);
      if (state.career.mode === "simulation") {
        loadRoleSimulations(card.dataset.role);
      } else {
        generateInterview();
      }
    });
  });
}


function selectedInterviewer() {
  const data = state.career.catalog;
  if (!data || !data.interviewers || !data.interviewers.length) return null;
  const id = $("#career-interviewer") ? $("#career-interviewer").value : "";
  return data.interviewers.find(function(p){ return p.persona_id === id; }) || data.interviewers[0];
}

function updateCareerLevelExpectation() {
  const data = state.career.catalog;
  const level = $("#career-level") ? $("#career-level").value : "senior";
  const profile = data && data.level_profiles ? data.level_profiles[level] : null;
  const root = $("#career-level-expectation");
  if (!root) return;
  if (!profile) {
    root.textContent = "";
    return;
  }
  root.innerHTML = '<b>'+esc(profile.label)+' expectation:</b> '+esc(profile.expectation);
}

function voiceCapabilities() {
  const recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  return {
    synthesis: "speechSynthesis" in window,
    recognition: Boolean(recognition),
    Recognition: recognition
  };
}

function updateVoiceStatus() {
  const caps = voiceCapabilities();
  const root = $("#career-voice-status");
  if (!root) return;
  if (caps.synthesis && caps.recognition) root.textContent = "Speak + Dictate";
  else if (caps.synthesis) root.textContent = "Speak only";
  else root.textContent = "Typed fallback";
}

function speakInterviewText(text) {
  const caps = voiceCapabilities();
  if (!caps.synthesis) {
    toast("Speech synthesis is not available in this browser.", "error");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.96;
  utterance.pitch = 1.0;
  const voices = window.speechSynthesis.getVoices().filter(function(v){
    return !v.lang || v.lang.toLowerCase().startsWith("en");
  });
  const persona = selectedInterviewer();
  if (voices.length) {
    const personaIndex = persona ? Math.abs((persona.persona_id || "").split("").reduce(function(a,ch){return a+ch.charCodeAt(0);},0)) % voices.length : 0;
    utterance.voice = voices[personaIndex];
  }
  window.speechSynthesis.speak(utterance);
}

function dictateInto(textarea) {
  const caps = voiceCapabilities();
  if (!caps.recognition) {
    toast("Speech recognition is not supported by this browser. You can still type your answer.", "error");
    return;
  }
  if (state.career.voiceRecognition) {
    try { state.career.voiceRecognition.stop(); } catch (err) {}
  }
  const recognition = new caps.Recognition();
  state.career.voiceRecognition = recognition;
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = true;
  const original = textarea.value.trim();
  let finalText = "";
  recognition.onresult = function(event) {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += transcript + " ";
      else interim += transcript;
    }
    textarea.value = [original, finalText.trim(), interim.trim()].filter(Boolean).join(original ? " " : "");
  };
  recognition.onerror = function(event) {
    toast("Voice transcription error: "+event.error, "error");
  };
  recognition.onend = function() {
    state.career.voiceRecognition = null;
  };
  recognition.start();
  toast("Listening… speak your answer, then pause or click the microphone again.");
}

async function generateInterview() {
  const roleId = $("#career-role").value;
  const level = $("#career-level").value;
  const persona = selectedInterviewer();
  if (!roleId) return;
  state.career.selectedRole = roleId;
  state.career.interviewer = persona;
  $("#simulation-role").value = roleId;
  updateCareerLevelExpectation();

  try {
    const session = await api("/api/interview", {
      method:"POST",
      body:JSON.stringify({role_id:roleId, level:level})
    });
    state.career.currentSession = session;

    const questions = session.questions.map(function(q, idx) {
      return '<div class="question-card interactive-question" data-question-index="'+idx+'">' +
        '<div class="question-dimension">'+esc(String(idx+1).padStart(2,"0"))+' · '+esc(q.dimension).toUpperCase()+'</div>' +
        '<p class="interview-question-text">'+esc(q.question)+'</p>' +
        '<div class="voice-actions"><button class="button subtle speak-question" data-question-index="'+idx+'">🔊 Ask aloud</button><button class="button subtle dictate-answer" data-question-index="'+idx+'">🎙 Answer by voice</button></div>' +
        '<textarea class="answer-editor interview-answer" rows="7" data-question-index="'+idx+'" placeholder="Answer as you would in the interview. Use concrete decisions, technical mechanisms, evidence, tradeoffs, scale, and metrics appropriate to the selected level."></textarea>' +
        '<div class="answer-actions"><button class="button primary evaluate-interview" data-question-index="'+idx+'">Evaluate Answer</button><span class="subtle-copy">Revise and resubmit until you reach mastery.</span></div>' +
        '<div class="evaluation-result" id="interview-result-'+idx+'"></div>' +
        '</div>';
    }).join("");

    const personaMarkup = persona
      ? '<div class="interviewer-card"><div class="interviewer-avatar">'+esc(persona.initials)+'</div><div><b>'+esc(persona.name)+'</b><span>'+esc(persona.title)+'</span><p>'+esc(persona.style)+'</p></div></div>'
      : "";

    $("#interview-session").className = "interview-session";
    $("#interview-session").innerHTML =
      '<div class="interview-head"><div><div class="lab-domain">'+esc(session.role.group).toUpperCase()+'</div>' +
      '<h3>'+esc(session.role.name)+' · '+esc(session.level_profile ? session.level_profile.label.toUpperCase() : session.level.toUpperCase())+'</h3>' +
      '<div class="subtle-copy">'+esc(session.role.summary)+'</div></div>'+personaMarkup+'</div>' +
      '<div class="level-session-expectation">'+esc(session.level_profile ? session.level_profile.expectation : "")+'</div>' +
      '<div class="scorecard-row">'+session.scorecard.map(function(s){return '<span class="scorecard-chip">'+esc(s)+'</span>';}).join("")+'</div>' +
      '<div class="interview-instructions"><b>Mastery loop:</b> answer → evaluate → study the critique and exemplar → revise → submit again. The target score is <b>'+esc(state.career.evaluator ? state.career.evaluator.mastery_score : 95)+'/100</b>.</div>' +
      '<div class="question-list">'+questions+'</div>';

    $(".evaluate-interview").forEach(function(btn) {
      btn.addEventListener("click", function() {
        evaluateInterviewQuestion(Number(btn.dataset.questionIndex));
      });
    });
    $(".speak-question").forEach(function(btn) {
      btn.addEventListener("click", function() {
        const q = session.questions[Number(btn.dataset.questionIndex)];
        if (q) speakInterviewText((persona ? persona.name + " asks: " : "") + q.question);
      });
    });
    $(".dictate-answer").forEach(function(btn) {
      btn.addEventListener("click", function() {
        const editor = $('.interview-answer[data-question-index="'+btn.dataset.questionIndex+'"]');
        if (editor) dictateInto(editor);
      });
    });
    renderCareer($("#role-search").value);
  } catch (err) {
    toast(err.message, "error");
  }
}

async function evaluateInterviewQuestion(index) {
  const session = state.career.currentSession;
  if (!session || !session.questions[index]) return;
  const q = session.questions[index];
  const editor = $('.interview-answer[data-question-index="'+index+'"]');
  const answer = editor ? editor.value.trim() : "";
  if (!answer) {
    toast("Write an answer before evaluating it.", "error");
    return;
  }
  try {
    const result = await api("/api/career/evaluate-interview", {
      method:"POST",
      body:JSON.stringify({
        role_id: session.role.role_id,
        level: session.level,
        dimension: q.dimension,
        question: q.question,
        answer: answer
      })
    });
    const root = $("#interview-result-"+index);
    root.innerHTML = evaluationMarkup(result);
    root.classList.add("visible");
    const apply = root.querySelector(".apply-improved");
    if (apply) apply.addEventListener("click", function(){
      editor.value = result.improved_answer || result.model_answer || editor.value;
      editor.focus();
      toast("Improved draft loaded. Edit it in your own words, then evaluate again.");
    });
  } catch (err) {
    toast(err.message, "error");
  }
}

function evaluationMarkup(result) {
  const strengths = (result.strengths || []).map(function(x){return '<li>'+esc(x)+'</li>';}).join("");
  const improvements = (result.improvements || []).map(function(x){return '<li>'+esc(x)+'</li>';}).join("");
  const mastered = Boolean(result.mastered);
  const mode = result.evaluation_mode || "deterministic";
  const improved = result.improved_answer || result.model_answer || "";
  const weights = result.rubric_weights || {};
  const weightMarkup = Object.keys(weights).length
    ? '<div class="rubric-weights">'+Object.entries(weights).map(function(entry){
        return '<span><b>'+esc(entry[1])+'%</b> '+esc(entry[0].replaceAll("_"," "))+'</span>';
      }).join("")+'</div>'
    : "";
  const attemptMarkup = result.attempt_number
    ? '<div class="attempt-strip"><span>ATTEMPT <b>#'+esc(result.attempt_number)+'</b></span><span>PREVIOUS BEST <b>'+esc(result.previous_best_score || 0)+'</b></span><span>BEST <b>'+esc(result.best_score || result.score)+'</b></span><span>DELTA <b>'+((result.score_delta_from_previous_best || 0) >= 0 ? "+" : "")+esc(result.score_delta_from_previous_best || 0)+'</b></span></div>'
    : "";
  const modelMarkup = result.model
    ? '<span class="evaluation-model">'+esc(result.model)+'</span>'
    : '<span class="evaluation-model">'+esc(mode)+'</span>';

  return attemptMarkup +
    '<div class="evaluation-head"><div><div class="label">EVALUATION · '+esc(mode.toUpperCase())+'</div><strong>'+esc(result.score)+'/100 · '+esc(result.quality)+'</strong>'+modelMarkup+'</div><div class="mastery-badge '+(mastered ? "mastered" : "retry")+'">'+(mastered ? "MASTERED" : "RETRY TO "+esc(result.mastery_score || 95))+'</div><div class="score-meter"><i style="width:'+Math.max(0,Math.min(100,result.score))+'%"></i></div></div>' +
    weightMarkup +
    '<div class="feedback-grid"><div><div class="feedback-title good">WHAT WORKED</div><ul>'+strengths+'</ul></div><div><div class="feedback-title improve">WHAT TO STRENGTHEN</div><ul>'+improvements+'</ul></div></div>' +
    '<div class="model-answer"><div class="feedback-title">BEST SAMPLE ANSWER</div><p>'+esc(result.model_answer || "")+'</p></div>' +
    (improved ? '<div class="model-answer improved-answer"><div class="feedback-title">IMPROVED VERSION OF YOUR ANSWER</div><p>'+esc(improved)+'</p><button class="button subtle apply-improved">Load this into my answer</button></div>' : '') +
    '<div class="next-step"><b>Next attempt:</b> '+esc(result.retry_instruction || result.next_step || "Refine the answer and retry.")+'</div>';
}

function setCareerMode(mode) {
  state.career.mode = mode;
  $(".career-mode-tab").forEach(function(tab){tab.classList.toggle("active", tab.dataset.careerMode === mode);});
  $("#career-interview-panel").classList.toggle("active", mode === "interview");
  $("#career-simulation-panel").classList.toggle("active", mode === "simulation");
  if (mode === "simulation") {
    const roleId = $("#simulation-role").value || $("#career-role").value;
    loadRoleSimulations(roleId);
  }
}

async function loadRoleSimulations(roleId) {
  if (!roleId) return;
  $("#simulation-role").value = roleId;
  try {
    const data = await api("/api/career/simulations", {
      method:"POST",
      body:JSON.stringify({role_id:roleId})
    });
    state.career.simulationCatalog = data;
    const select = $("#simulation-scenario");
    select.innerHTML = (data.scenarios || []).map(function(s) {
      return '<option value="'+esc(s.scenario_id)+'">'+esc(s.category)+' · '+esc(s.title)+'</option>';
    }).join("");
    if (!(data.scenarios || []).length) {
      $("#simulation-workspace").className = "simulation-workspace empty-state";
      $("#simulation-workspace").textContent = "No simulation is mapped to this role yet.";
      return;
    }
    loadSimulation();
  } catch (err) {
    toast(err.message, "error");
  }
}

function loadSimulation() {
  const data = state.career.simulationCatalog;
  if (!data) return;
  const scenarioId = $("#simulation-scenario").value;
  const scenario = (data.scenarios || []).find(function(s){return s.scenario_id === scenarioId;});
  if (!scenario) return;
  state.career.currentScenario = scenario;
  state.career.hintsUsed = {};

  const objectives = scenario.objectives.map(function(x){return '<li>'+esc(x)+'</li>';}).join("");
  const artifacts = scenario.artifacts.map(function(a, idx) {
    return '<article class="artifact-card" data-artifact-id="'+esc(a.artifact_id)+'"><div class="artifact-head"><span>'+esc(a.kind).toUpperCase()+'</span><b>'+esc(a.title)+'</b></div><pre>'+esc(a.content)+'</pre></article>';
  }).join("");
  const tasks = scenario.tasks.map(function(t, idx) {
    return '<article class="simulation-task" data-task="'+esc(t.task_id)+'">' +
      '<div class="question-dimension">TASK '+esc(String(idx+1).padStart(2,"0"))+' · '+esc(t.answer_type).toUpperCase()+'</div>' +
      '<h3>'+esc(t.title)+'</h3><p>'+esc(t.prompt)+'</p>' +
      '<div class="hint-panel" id="hints-'+esc(t.task_id)+'"></div>' +
      '<div class="answer-actions"><button class="button subtle reveal-hint" data-task="'+esc(t.task_id)+'">Show Hint</button></div>' +
      '<textarea class="answer-editor simulation-answer" rows="7" data-task="'+esc(t.task_id)+'" placeholder="Write your finding, analysis, query/tool idea, decision, or remediation here."></textarea>' +
      '<div class="answer-actions"><button class="button subtle dictate-simulation" data-task="'+esc(t.task_id)+'">🎙 Answer by voice</button><button class="button primary evaluate-simulation" data-task="'+esc(t.task_id)+'">Validate Task</button></div>' +
      '<div class="evaluation-result" id="simulation-result-'+esc(t.task_id)+'"></div>' +
      '</article>';
  }).join("");

  function mapGroup(title, items, cssClass) {
    if (!items || !items.length) return "";
    return '<div class="scenario-map-group '+cssClass+'"><div class="feedback-title">'+esc(title)+'</div><div class="atlas-technique-row">'+items.map(function(t){return '<span class="atlas-technique"><b>'+esc(t.id)+'</b> '+esc(t.name)+'</span>';}).join("")+'</div></div>';
  }
  const frameworkMarkup =
    mapGroup("OWASP TOP 10:2025", scenario.owasp_web || [], "owasp-web") +
    mapGroup("OWASP LLM TOP 10:2026", scenario.owasp_llm || [], "owasp-llm") +
    mapGroup("OWASP AGENTIC TOP 10:2026", scenario.owasp_agentic || [], "owasp-agentic") +
    mapGroup("MITRE ATLAS", scenario.atlas || [], "mitre-atlas");
  const frameworkEmpty = frameworkMarkup
    ? frameworkMarkup
    : '<div class="subtle-copy">This exercise is core cybersecurity practice and has no direct AI-specific framework mapping.</div>';
  const runtime = scenario.runtime || {tier:"inline", blueprint_id:null};
  let vmMarkup = '';
  if (runtime.blueprint_id) {
    const host = state.career.vmCatalog && state.career.vmCatalog.host ? state.career.vmCatalog.host : {available:false};
    vmMarkup = '<div class="vm-panel"><div><div class="label">PORTABLE VM LAB</div><strong>'+esc(runtime.tier.replace("-", " ").toUpperCase())+'</strong><span>Blueprint: '+esc(runtime.blueprint_id)+'</span></div>' +
      '<div class="vm-actions"><button class="button primary vm-start" data-blueprint="'+esc(runtime.blueprint_id)+'">Start VM</button><button class="button subtle vm-reset" data-blueprint="'+esc(runtime.blueprint_id)+'">Reset VM</button><button class="button subtle vm-stop" data-blueprint="'+esc(runtime.blueprint_id)+'">Stop VM</button></div>' +
      '<div class="vm-host-status '+(host.available ? "ready" : "missing")+'">'+(host.available ? 'Multipass detected on this host.' : 'Multipass not detected. The browser exercise still works; install Multipass to materialize the Linux guest.')+'</div>' +
      '<div id="vm-status-box" class="vm-status-box"></div></div>';
  }

  $("#simulation-workspace").className = "simulation-workspace";
  $("#simulation-workspace").innerHTML =
    '<div class="scenario-head"><div><div class="lab-domain">'+esc(scenario.category).toUpperCase()+'</div><h2>'+esc(scenario.title)+'</h2><div class="scenario-meta">'+esc(scenario.difficulty)+' · '+esc(scenario.skills.join(" · "))+'</div></div><span class="tag '+((scenario.atlas||[]).length ? "pass" : "neutral")+'">'+esc(scenario.specialization || "Core Cybersecurity")+'</span></div>' +
    '<p class="scenario-brief">'+esc(scenario.briefing)+'</p>' +
    '<div class="atlas-mapping"><div class="label">FRAMEWORK CROSSWALK</div>'+frameworkEmpty+'</div>' +
    vmMarkup +
    '<div class="scenario-objectives"><div class="label">OBJECTIVES</div><ul>'+objectives+'</ul></div>' +
    '<div class="workbench"><div class="panel-head"><div><div class="label">SEARCH WORKBENCH</div><div class="subtle-copy">Search the synthetic artifacts without leaving Career Lab.</div></div></div><div class="workbench-controls"><input id="simulation-search" class="large-input" placeholder="Try: token, admin, registry, MRN, approval, error…"><button id="run-simulation-search" class="button subtle">Search Artifacts</button></div><div id="simulation-search-results" class="search-results empty-state">Enter a term to search the artifacts.</div></div>' +
    '<div class="label section-label">ARTIFACTS</div><div class="artifact-grid">'+artifacts+'</div>' +
    '<div class="label section-label">TASKS</div><div class="simulation-task-list">'+tasks+'</div>';

  $("#run-simulation-search").addEventListener("click", runSimulationSearch);
  $("#simulation-search").addEventListener("keydown", function(e){if(e.key === "Enter") runSimulationSearch();});
  $(".reveal-hint").forEach(function(btn){btn.addEventListener("click", function(){revealHint(btn.dataset.task);});});
  $(".evaluate-simulation").forEach(function(btn){btn.addEventListener("click", function(){evaluateSimulationTaskUI(btn.dataset.task);});});
  $(".vm-start").forEach(function(btn){btn.addEventListener("click", function(){vmAction("/api/vm/start", btn.dataset.blueprint);});});
  $(".vm-reset").forEach(function(btn){btn.addEventListener("click", function(){vmAction("/api/vm/reset", btn.dataset.blueprint);});});
  $(".vm-stop").forEach(function(btn){btn.addEventListener("click", function(){vmAction("/api/vm/stop", btn.dataset.blueprint);});});
  if (runtime.blueprint_id && state.career.vmCatalog && state.career.vmCatalog.host && state.career.vmCatalog.host.available) {
    vmAction("/api/vm/status", runtime.blueprint_id, true);
  }
}

async function vmAction(path, blueprintId, quiet) {
  try {
    if (!quiet && (path === "/api/vm/start" || path === "/api/vm/reset")) {
      toast(path === "/api/vm/reset" ? "Recreating Linux guest from Git blueprint…" : "Starting Linux guest from Git blueprint…");
    }
    const result = await api(path, {method:"POST", body:JSON.stringify({blueprint_id:blueprintId})});
    state.career.vmStatus = result;
    const box = $("#vm-status-box");
    if (box) {
      const instance = result.instance;
      const stateText = instance ? (instance.state || "unknown") : "not created";
      box.innerHTML = '<div class="vm-status-line"><span>INSTANCE</span><b>'+esc(result.instance_name)+'</b></div>' +
        '<div class="vm-status-line"><span>STATE</span><b>'+esc(stateText)+'</b></div>' +
        '<div class="vm-shell-command"><span>OPEN GUEST</span><code>'+esc(result.shell_command || "")+'</code></div>';
    }
    if (!quiet) toast("VM status: "+(result.instance ? (result.instance.state || "ready") : "not created"), "success");
  } catch (err) {
    if (!quiet) toast(err.message, "error");
  }
}

function runSimulationSearch() {
  const scenario = state.career.currentScenario;
  if (!scenario) return;
  const query = $("#simulation-search").value.trim().toLowerCase();
  const root = $("#simulation-search-results");
  if (!query) {
    root.className = "search-results empty-state";
    root.textContent = "Enter a term to search the artifacts.";
    return;
  }
  const hits = [];
  scenario.artifacts.forEach(function(a) {
    a.content.split(/\n/).forEach(function(line, idx) {
      if (line.toLowerCase().includes(query)) hits.push({artifact:a.title, line:idx+1, text:line});
    });
  });
  root.className = "search-results";
  root.innerHTML = hits.length ? hits.slice(0,40).map(function(h){
    return '<div class="search-hit"><span>'+esc(h.artifact)+' · L'+esc(h.line)+'</span><code>'+esc(h.text)+'</code></div>';
  }).join("") : '<div class="empty-state">No matches. Try another term or use a hint.</div>';
}

function revealHint(taskId) {
  const scenario = state.career.currentScenario;
  if (!scenario) return;
  const task = scenario.tasks.find(function(t){return t.task_id === taskId;});
  if (!task) return;
  const used = state.career.hintsUsed[taskId] || 0;
  if (used >= task.hints.length) {
    toast("All hints for this task are already visible.");
    return;
  }
  state.career.hintsUsed[taskId] = used + 1;
  const visible = task.hints.slice(0, used+1);
  $("#hints-"+taskId).innerHTML = visible.map(function(h, idx){return '<div class="hint-item"><b>Hint '+(idx+1)+'</b><span>'+esc(h)+'</span></div>';}).join("");
}

async function evaluateSimulationTaskUI(taskId) {
  const scenario = state.career.currentScenario;
  if (!scenario) return;
  const editor = $('.simulation-answer[data-task="'+taskId+'"]');
  const answer = editor ? editor.value.trim() : "";
  if (!answer) {
    toast("Write your analysis before validating the task.", "error");
    return;
  }
  try {
    const result = await api("/api/career/evaluate-simulation", {
      method:"POST",
      body:JSON.stringify({
        scenario_id: scenario.scenario_id,
        task_id: taskId,
        answer: answer,
        hints_used: state.career.hintsUsed[taskId] || 0
      })
    });
    const root = $("#simulation-result-"+taskId);
    root.innerHTML = evaluationMarkup(result);
    root.classList.add("visible");
    const apply = root.querySelector(".apply-improved");
    if (apply) apply.addEventListener("click", function(){
      editor.value = result.improved_answer || result.model_answer || editor.value;
      editor.focus();
      toast("Improved draft loaded. Refine it, then validate again.");
    });
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
  $("[data-target]").forEach(function(item) {
    item.addEventListener("click", function() {
      state.targets.selected = item.dataset.target;
      renderTargets();
  renderPricing();
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

  $(".target-analyze").forEach(function(btn){btn.addEventListener("click", function(){targetAction("/api/targets/analyze", btn.dataset.target);});});
  $(".target-clone").forEach(function(btn){btn.addEventListener("click", function(){targetAction("/api/targets/clone", btn.dataset.target);});});
  $(".target-scaffold").forEach(function(btn){btn.addEventListener("click", function(){targetAction("/api/targets/scaffold", btn.dataset.target);});});
  $(".target-run").forEach(function(btn){
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
    api("/api/career/attempts"),
    api("/api/vm/catalog"),
    api("/api/career/evaluator"),
    api("/api/pricing"),
  ]);
  state.academy.catalog = values[0];
  state.academy.progress = values[1];
  state.career.catalog = values[2];
  state.targets.items = values[3].targets || [];
  state.targets.runs = values[3].runs || [];
  state.career.attempts = values[4].attempts || [];
  state.career.vmCatalog = values[5];
  state.career.evaluator = values[6];
  state.pricing.catalog = values[7];

  const evaluator = state.career.evaluator || {};
  $("#career-evaluator-status").textContent = evaluator.available ? ("GenAI · "+(evaluator.model || "OpenAI")) : "Deterministic fallback";
  $("#career-evaluator-note").textContent = evaluator.note || "";
  $("#career-mastery-score").textContent = (evaluator.mastery_score || 95)+"/100";
  updateVoiceStatus();

  renderAcademy();
  renderCareer("");
  renderTargets();
  renderPricing();
  $("#career-interviewer").innerHTML = (state.career.catalog.interviewers || []).map(function(p){
    return '<option value="'+esc(p.persona_id)+'">'+esc(p.name)+' · '+esc(p.title)+'</option>';
  }).join("");
  if ((state.career.catalog.interviewers || []).length) {
    state.career.interviewer = state.career.catalog.interviewers[0];
  }
  updateCareerLevelExpectation();
  $("#simulation-role").innerHTML = state.career.catalog.roles.map(function(role){return '<option value="'+esc(role.role_id)+'">'+esc(role.name)+'</option>';}).join("");
  const defaultRole = $("#career-role").value || "ai-security";
  $("#simulation-role").value = defaultRole;
  loadRoleSimulations(defaultRole);

  $(".product-tab").forEach(function(tab) {
    tab.addEventListener("click", function() { setView(tab.dataset.productView); });
  });
  $("#pricing-button").addEventListener("click", function(){ setView("pricing"); });
  $(".billing-option").forEach(function(btn){
    btn.addEventListener("click", function(){ setBillingPeriod(btn.dataset.billing); });
  });
  $("#role-search").addEventListener("input", function(e){ renderCareer(e.target.value); });
  $("#career-role").addEventListener("change", function(){
    state.career.selectedRole = $("#career-role").value;
    $("#simulation-role").value = $("#career-role").value;
    renderCareer($("#role-search").value);
    if (state.career.mode === "simulation") loadRoleSimulations($("#career-role").value);
  });
  $("#career-level").addEventListener("change", function(){
    updateCareerLevelExpectation();
    if (state.career.currentSession) generateInterview();
  });
  $("#career-interviewer").addEventListener("change", function(){
    state.career.interviewer = selectedInterviewer();
    if (state.career.currentSession) generateInterview();
  });
  $("#generate-interview").addEventListener("click", generateInterview);
  $("#simulation-role").addEventListener("change", function(){
    state.career.selectedRole = $("#simulation-role").value;
    $("#career-role").value = $("#simulation-role").value;
    renderCareer($("#role-search").value);
    loadRoleSimulations($("#simulation-role").value);
  });
  $("#simulation-scenario").addEventListener("change", loadSimulation);
  $("#load-simulation").addEventListener("click", loadSimulation);
  $(".career-mode-tab").forEach(function(tab){tab.addEventListener("click", function(){setCareerMode(tab.dataset.careerMode);});});
  $("#register-target").addEventListener("click", registerTarget);

  const oldRefresh = refreshData;
  refreshData = async function() {
    await oldRefresh();
    state.academy.progress = await api("/api/academy/progress");
    renderAcademy();
  };
}

boot().then(bootV2).catch(function(err){ console.error(err); toast("Console initialization failed: "+err.message, "error"); });
