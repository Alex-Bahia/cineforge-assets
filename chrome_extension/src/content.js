/**
 * CineForge Studio — Content Script (injeta painel no YouTube Studio)
 *
 * Injeta um painel flutuante no YouTube Studio para disparar o pipeline
 * CineForge diretamente enquanto está gerenciando os canais.
 */

(function () {
  if (document.getElementById("cineforge-panel")) return;

  // Create floating panel
  const panel = document.createElement("div");
  panel.id = "cineforge-panel";
  panel.innerHTML = `
    <div id="cf-header">
      <span>🎬 CineForge</span>
      <button id="cf-toggle">▼</button>
    </div>
    <div id="cf-body">
      <div id="cf-stats">
        <span class="cf-stat"><span id="cf-running">0</span> ativos</span>
        <span class="cf-stat"><span id="cf-pending">0</span> fila</span>
        <span class="cf-stat" style="color:#4ade80;"><span id="cf-done">0</span> prontos</span>
      </div>
      <select id="cf-niche">
        <option value="finance_dark">💰 Finance Dark</option>
        <option value="dark" selected>🔎 Dark</option>
        <option value="kids">🎨 Kids</option>
        <option value="tech">💻 Tech</option>
      </select>
      <input id="cf-topic" type="text" placeholder="Tópico (opcional)">
      <div style="display:flex;gap:6px;margin-top:6px;">
        <button id="cf-add" class="cf-btn cf-primary">+ Gerar</button>
        <button id="cf-scan" class="cf-btn cf-secondary">🔍 Scan</button>
      </div>
      <div id="cf-msg"></div>
    </div>
  `;
  document.body.appendChild(panel);

  // Toggle collapse
  let collapsed = false;
  document.getElementById("cf-toggle").addEventListener("click", () => {
    collapsed = !collapsed;
    document.getElementById("cf-body").style.display = collapsed ? "none" : "block";
    document.getElementById("cf-toggle").textContent = collapsed ? "▲" : "▼";
  });

  function setMsg(txt, ok = true) {
    const el = document.getElementById("cf-msg");
    el.textContent = txt;
    el.style.color = ok ? "#4ade80" : "#e94560";
    setTimeout(() => { el.textContent = ""; }, 4000);
  }

  function updateStats() {
    chrome.runtime.sendMessage({ action: "GET_STATS" }, resp => {
      if (!resp?.ok) return;
      const s = resp.stats;
      document.getElementById("cf-running").textContent = s.running ?? 0;
      document.getElementById("cf-pending").textContent = s.pending ?? 0;
      document.getElementById("cf-done").textContent    = s.done    ?? 0;
    });
  }

  document.getElementById("cf-add").addEventListener("click", () => {
    const niche = document.getElementById("cf-niche").value;
    const topic = document.getElementById("cf-topic").value.trim();
    chrome.runtime.sendMessage(
      { action: "ADD_JOB", payload: { niche, topic: topic || null } },
      resp => {
        if (resp?.ok) {
          setMsg("✅ Adicionado à fila");
          document.getElementById("cf-topic").value = "";
          setTimeout(updateStats, 600);
        } else {
          setMsg("❌ " + (resp?.error || "offline"), false);
        }
      }
    );
  });

  document.getElementById("cf-scan").addEventListener("click", () => {
    const niche = document.getElementById("cf-niche").value;
    setMsg("🔍 Escaneando…");
    chrome.runtime.sendMessage({ action: "SCAN_OPPORTUNITIES", niche }, resp => {
      if (resp?.ok) setMsg(`✅ ${resp.opportunities?.length ?? 0} oportunidades`);
      else setMsg("❌ Backend offline", false);
    });
  });

  updateStats();
  setInterval(updateStats, 20_000);
})();
