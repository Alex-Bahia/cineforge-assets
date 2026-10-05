/**
 * CineForge Studio — Popup UI Logic
 */

const $ = id => document.getElementById(id);

function toast(msg, isError = false) {
  const t = $("toast");
  t.textContent = msg;
  t.className = `toast${isError ? " error" : ""}`;
  t.style.display = "block";
  setTimeout(() => { t.style.display = "none"; }, 3000);
}

function badgeClass(status) {
  return { running: "badge-running", done: "badge-done", failed: "badge-failed" }[status] || "badge-pending";
}

function renderJobs(jobs) {
  const list = $("job-list");
  if (!jobs || jobs.length === 0) {
    list.innerHTML = '<div style="color:#555;text-align:center;padding:20px 0;">Sem jobs na fila</div>';
    return;
  }
  list.innerHTML = jobs.slice(0, 10).map(j => `
    <div class="job-item">
      <span class="topic">${j.topic || "(sem tópico)"}</span>
      <span class="badge ${badgeClass(j.status)}">${j.status}</span>
    </div>
  `).join("");
}

async function loadStats() {
  chrome.runtime.sendMessage({ action: "GET_STATS" }, resp => {
    if (chrome.runtime.lastError || !resp?.ok) {
      $("status-dot").className = "status-dot offline";
      return;
    }
    $("status-dot").className = "status-dot online";
    const s = resp.stats;
    $("stat-running").textContent = s.running ?? 0;
    $("stat-pending").textContent = s.pending ?? 0;
    $("stat-done").textContent    = s.done    ?? 0;
    $("total-cost").textContent   = `$${(s.total_cost_usd || 0).toFixed(2)}`;
    renderJobs(s.recent_jobs || []);
  });
}

$("btn-add").addEventListener("click", () => {
  const niche = $("niche-select").value;
  const topic = $("topic-input").value.trim();
  chrome.runtime.sendMessage(
    { action: "ADD_JOB", payload: { niche, topic: topic || null } },
    resp => {
      if (resp?.ok) {
        toast("✅ Job adicionado: " + (topic || `auto/${niche}`));
        $("topic-input").value = "";
        setTimeout(loadStats, 500);
      } else {
        toast("❌ Erro: " + (resp?.error || "backend offline"), true);
      }
    }
  );
});

$("btn-scan").addEventListener("click", () => {
  const niche = $("niche-select").value;
  toast("🔍 Escaneando " + niche + "…");
  chrome.runtime.sendMessage(
    { action: "SCAN_OPPORTUNITIES", niche },
    resp => {
      if (resp?.ok) {
        toast(`✅ ${resp.opportunities?.length || 0} oportunidades encontradas`);
        setTimeout(loadStats, 500);
      } else {
        toast("❌ " + (resp?.error || "backend offline"), true);
      }
    }
  );
});

// Auto-refresh every 15s
loadStats();
setInterval(loadStats, 15_000);
