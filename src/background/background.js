/**
 * Service worker — handles background polling and context menu
 */

// ─── Context menu ───
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'cineforge-selection',
    title: 'Criar vídeo com CineForge',
    contexts: ['selection'],
  });

  chrome.contextMenus.create({
    id: 'cineforge-page',
    title: 'Criar vídeo desta página',
    contexts: ['page'],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const text = info.selectionText || info.pageUrl;
  chrome.storage.local.set({ pendingContext: { text, tabId: tab.id, tabUrl: tab.url } });
  chrome.action.openPopup();
});

// ─── Alarm-based polling for background jobs ───
chrome.alarms.onAlarm.addListener(async alarm => {
  if (!alarm.name.startsWith('poll-')) return;

  const jobId = alarm.name.replace('poll-', '');
  const { jobs = [], config = {} } = await chrome.storage.local.get(['jobs', 'config']);
  const job = jobs.find(j => j.id === jobId);

  if (!job || job.status !== 'processing') return;

  try {
    const result = await checkJobStatus(job, config);
    if (result.status === 'completed') {
      await updateJob(jobId, { status: 'done', videoUrl: result.videoUrl });
      chrome.alarms.clear(alarm.name);
      chrome.notifications.create(`done-${jobId}`, {
        type: 'basic',
        iconUrl: '../icons/icon48.png',
        title: 'CineForge — Vídeo pronto!',
        message: `Seu vídeo "${job.prompt?.slice(0, 50)}" foi gerado.`,
      });
    } else if (result.status === 'failed') {
      await updateJob(jobId, { status: 'error', error: result.error });
      chrome.alarms.clear(alarm.name);
    }
  } catch (err) {
    console.error('Poll error:', err);
  }
});

async function checkJobStatus(job, config) {
  const apiKey = config[`${job.settings?.provider}ApiKey`];
  if (!apiKey) return { status: 'failed', error: 'API key missing' };

  const urls = {
    heygen: `https://api.heygen.com/v1/video_status.get?video_id=${job.id}`,
    higgsfield: `https://api.higgsfield.ai/v1/generations/${job.id}`,
    motion: `https://api.usemotion.com/v1/videos/${job.id}`,
  };

  const headers = {
    heygen: { 'X-Api-Key': apiKey },
    higgsfield: { 'Authorization': `Bearer ${apiKey}` },
    motion: { 'Authorization': `Bearer ${apiKey}` },
  };

  const provider = job.settings?.provider || 'heygen';
  const response = await fetch(urls[provider], { headers: headers[provider] });
  if (!response.ok) throw new Error(`Status check failed: ${response.status}`);

  const data = await response.json();
  const status = data.data?.status || data.status;

  if (status === 'completed') {
    return { status: 'completed', videoUrl: data.data?.video_url || data.video_url || data.output_url };
  }
  if (status === 'failed') {
    return { status: 'failed', error: data.data?.error || data.error };
  }
  return { status: 'processing' };
}

async function updateJob(id, updates) {
  const { jobs = [] } = await chrome.storage.local.get('jobs');
  const idx = jobs.findIndex(j => j.id === id);
  if (idx !== -1) {
    jobs[idx] = { ...jobs[idx], ...updates };
    await chrome.storage.local.set({ jobs });
  }
}

// ─── Message handler from popup ───
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'START_POLL') {
    chrome.alarms.create(`poll-${msg.jobId}`, {
      delayInMinutes: 0.5,
      periodInMinutes: 0.5,
    });
    sendResponse({ ok: true });
  }

  if (msg.type === 'STOP_POLL') {
    chrome.alarms.clear(`poll-${msg.jobId}`);
    sendResponse({ ok: true });
  }

  return true;
});
