/**
 * CineForge Studio — Background Service Worker (Manifest V3)
 *
 * Responsável por:
 *   - Comunicação com o CineForge backend (localhost:8765 ou API remota)
 *   - Polling de jobs em andamento
 *   - Notificações quando vídeos ficam prontos
 *   - Agendamento diário automático via chrome.alarms
 */

const CINEFORGE_API = "http://localhost:8765";
const POLL_INTERVAL_MS = 30_000; // 30 segundos

// ── API Client ──────────────────────────────────────────────────────────────

async function cfetch(path, options = {}) {
  const url = `${CINEFORGE_API}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`CineForge API ${res.status}: ${await res.text()}`);
  return res.json();
}

// ── Job Queue Polling ───────────────────────────────────────────────────────

async function pollJobs() {
  try {
    const stats = await cfetch("/api/queue/stats");
    const badge = stats.running > 0 ? String(stats.running) : "";
    chrome.action.setBadgeText({ text: badge });
    chrome.action.setBadgeBackgroundColor({ color: "#e94560" });

    // Notify on completions
    if (stats.just_done && stats.just_done.length > 0) {
      for (const job of stats.just_done) {
        chrome.notifications.create(`job_done_${job.job_id}`, {
          type: "basic",
          iconUrl: "../icons/icon48.png",
          title: "CineForge — Vídeo Pronto! 🎬",
          message: `"${job.topic.substring(0, 60)}" foi gerado com sucesso.`,
          priority: 2,
        });
      }
    }
  } catch (e) {
    // Backend offline — clear badge
    chrome.action.setBadgeText({ text: "" });
  }
}

// ── Commands from Popup / Content Script ───────────────────────────────────

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    try {
      switch (msg.action) {
        case "ADD_JOB": {
          const result = await cfetch("/api/queue/add", {
            method: "POST",
            body: JSON.stringify(msg.payload),
          });
          sendResponse({ ok: true, job_id: result.job_id });
          break;
        }
        case "SCAN_OPPORTUNITIES": {
          const result = await cfetch("/api/scan", {
            method: "POST",
            body: JSON.stringify({ niche: msg.niche }),
          });
          sendResponse({ ok: true, opportunities: result.opportunities });
          break;
        }
        case "GET_STATS": {
          const stats = await cfetch("/api/queue/stats");
          sendResponse({ ok: true, stats });
          break;
        }
        case "GET_SETTINGS": {
          const settings = await chrome.storage.sync.get([
            "cineforgeUrl", "apiKey", "defaultNiche", "autoSchedule",
          ]);
          sendResponse({ ok: true, settings });
          break;
        }
        case "SAVE_SETTINGS": {
          await chrome.storage.sync.set(msg.settings);
          sendResponse({ ok: true });
          break;
        }
        default:
          sendResponse({ ok: false, error: `Unknown action: ${msg.action}` });
      }
    } catch (err) {
      sendResponse({ ok: false, error: err.message });
    }
  })();
  return true; // Keep channel open for async response
});

// ── Scheduled Daily Scan (chrome.alarms) ───────────────────────────────────

chrome.alarms.create("daily_scan", {
  when: Date.now() + 5000, // First run 5s after install
  periodInMinutes: 90,     // Repeat every 90 minutes
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "daily_scan") {
    const settings = await chrome.storage.sync.get(["autoSchedule", "defaultNiche"]);
    if (!settings.autoSchedule) return;

    try {
      await cfetch("/api/scan", {
        method: "POST",
        body: JSON.stringify({ niche: settings.defaultNiche || "dark" }),
      });
    } catch (e) {
      console.log("CineForge: backend offline durante scan agendado");
    }
  }
  if (alarm.name === "poll_jobs") {
    await pollJobs();
  }
});

// Start polling
chrome.alarms.create("poll_jobs", { periodInMinutes: 0.5 }); // Every 30s
