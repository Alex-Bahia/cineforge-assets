import { LicenseManager } from '../utils/license.js';
import { ClaudeAPI } from '../utils/claude-api.js';
import { VideoOrchestrator } from '../utils/video-orchestrator.js';
import { Storage } from '../utils/storage.js';
import { Toast } from '../utils/toast.js';

// ─── State ───
const state = {
  currentStep: 'prompt',
  generatedScript: null,
  activeJob: null,
};

// ─── DOM references ───
const $ = id => document.getElementById(id);
const licenseOverlay = $('licenseOverlay');
const mainContent = $('mainContent');

// ─── Init ───
async function init() {
  const licensed = await LicenseManager.check();
  if (licensed) {
    licenseOverlay.classList.add('hidden');
    await loadQueueAndResults();
  }

  bindEvents();
}

// ─── License ───
$('activateBtn').addEventListener('click', async () => {
  const key = $('licenseInput').value.trim();
  if (!key) return Toast.show('Insira uma chave de licença', 'error');

  $('activateBtn').disabled = true;
  $('activateBtn').textContent = 'Verificando...';

  const ok = await LicenseManager.activate(key);
  if (ok) {
    licenseOverlay.classList.add('hidden');
    Toast.show('Licença ativada! 🎉', 'success');
    await loadQueueAndResults();
  } else {
    Toast.show('Chave inválida ou expirada', 'error');
  }

  $('activateBtn').disabled = false;
  $('activateBtn').textContent = 'Ativar';
});

// ─── Tabs ───
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    tab.classList.add('active');
    $(`tab-${tab.dataset.tab}`).classList.remove('hidden');
  });
});

// ─── Context capture ───
$('capturePageBtn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const [result] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => ({
      url: location.href,
      title: document.title,
      text: document.body.innerText.slice(0, 2000),
    }),
  });
  if (result?.result) {
    const { title, text, url } = result.result;
    const current = $('promptInput').value;
    $('promptInput').value = `${current}\n\nContexto da página: ${title}\n${url}\n\n${text}`.trim();
    Toast.show('Contexto da página adicionado', 'success');
  }
});

$('captureSelectionBtn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const [result] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.getSelection()?.toString() || '',
  });
  if (result?.result) {
    const current = $('promptInput').value;
    $('promptInput').value = `${current}\n\nTexto selecionado:\n${result.result}`.trim();
    Toast.show('Seleção adicionada', 'success');
  } else {
    Toast.show('Nenhum texto selecionado na página', 'error');
  }
});

// ─── Generate script ───
$('generateScriptBtn').addEventListener('click', async () => {
  const prompt = $('promptInput').value.trim();
  if (!prompt) return Toast.show('Descreva o vídeo que deseja criar', 'error');

  const settings = {
    duration: $('durationSelect').value,
    format: $('formatSelect').value,
    provider: $('providerSelect').value,
  };

  showStep('generating');
  setGeneratingState('Claude está criando seu roteiro...', 'Analisando o briefing', 10);

  try {
    const config = await Storage.get('config');
    if (!config?.claudeApiKey) {
      showStep('prompt');
      Toast.show('Configure sua chave Claude nas configurações', 'error');
      return;
    }

    const script = await ClaudeAPI.generateScript(prompt, settings, config.claudeApiKey);
    state.generatedScript = script;

    setGeneratingState('Roteiro pronto!', '', 100);
    await delay(600);
    showScriptStep(script, settings);

  } catch (err) {
    showStep('prompt');
    Toast.show(`Erro: ${err.message}`, 'error');
  }
});

// ─── Script step ───
$('backToPromptBtn').addEventListener('click', () => showStep('prompt'));

$('editScriptBtn').addEventListener('click', () => {
  const content = $('scriptContent');
  if (content.contentEditable === 'true') {
    content.contentEditable = 'false';
    content.style.outline = 'none';
    $('editScriptBtn').textContent = 'Editar';
  } else {
    content.contentEditable = 'true';
    content.style.outline = '1px solid var(--accent)';
    content.focus();
    $('editScriptBtn').textContent = 'Salvar';
  }
});

$('generateVideoBtn').addEventListener('click', async () => {
  const scriptText = $('scriptContent').textContent;
  const settings = {
    duration: $('durationSelect').value,
    format: $('formatSelect').value,
    provider: $('providerSelect').value,
  };

  showStep('generating');
  setGeneratingState('Enviando para geração de vídeo...', `Provedor: ${settings.provider}`, 20);

  try {
    const config = await Storage.get('config');
    const jobId = await VideoOrchestrator.submit(scriptText, settings, config);

    state.activeJob = jobId;
    await Storage.addJob({ id: jobId, prompt: scriptText.slice(0, 80), settings, status: 'processing', createdAt: Date.now() });
    updateQueueBadge();

    // Poll for completion
    await pollJob(jobId, settings.provider, config);

  } catch (err) {
    showStep('script');
    Toast.show(`Erro ao gerar vídeo: ${err.message}`, 'error');
  }
});

// ─── Poll job ───
async function pollJob(jobId, provider, config) {
  const maxAttempts = 60;
  let attempts = 0;

  while (attempts < maxAttempts) {
    await delay(5000);
    attempts++;

    const progress = Math.min(20 + Math.floor((attempts / maxAttempts) * 70), 90);
    setGeneratingState('Gerando vídeo com IA...', `${provider} está processando...`, progress);

    try {
      const result = await VideoOrchestrator.checkStatus(jobId, provider, config);

      if (result.status === 'completed') {
        await Storage.updateJob(jobId, { status: 'done', videoUrl: result.videoUrl });
        updateQueueBadge();
        showDoneStep(result.videoUrl);
        return;
      }

      if (result.status === 'failed') {
        throw new Error(result.error || 'Geração falhou');
      }

    } catch (err) {
      await Storage.updateJob(jobId, { status: 'error', error: err.message });
      updateQueueBadge();
      showStep('script');
      Toast.show(`Falha na geração: ${err.message}`, 'error');
      return;
    }
  }

  Toast.show('Timeout — verifique a aba Fila', 'error');
  showStep('prompt');
}

// ─── Done step ───
$('downloadBtn').addEventListener('click', async () => {
  const jobs = await Storage.get('jobs') || [];
  const lastDone = jobs.find(j => j.status === 'done');
  if (lastDone?.videoUrl) {
    chrome.downloads.download({ url: lastDone.videoUrl, filename: `cineforge-video-${Date.now()}.mp4` });
  }
});

$('newVideoBtn').addEventListener('click', () => {
  $('promptInput').value = '';
  state.generatedScript = null;
  showStep('prompt');
});

// ─── Settings button ───
$('settingsBtn').addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});

// ─── History button ───
$('historyBtn').addEventListener('click', () => {
  document.querySelector('[data-tab="results"]').click();
});

// ─── Helpers ───
function showStep(name) {
  state.currentStep = name;
  document.querySelectorAll('.step').forEach(s => s.classList.add('hidden'));
  $(`step-${name}`).classList.remove('hidden');
}

function showScriptStep(script, settings) {
  $('scriptMeta').innerHTML = `
    <span>⏱ ${settings.duration}s</span>
    <span>📐 ${settings.format}</span>
    <span>🎬 ${script.scenes?.length || 0} cenas</span>
    <span>🤖 ${settings.provider}</span>
  `;
  $('scriptContent').textContent = script.fullText || script;
  showStep('script');
}

function showDoneStep(videoUrl) {
  const preview = $('videoPreview');
  if (videoUrl) {
    preview.innerHTML = `<video src="${videoUrl}" controls preload="metadata"></video>`;
  }
  setGeneratingState('', '', 100);
  showStep('done');
  Toast.show('Vídeo gerado com sucesso! 🎬', 'success');
}

function setGeneratingState(title, sub, progress) {
  $('generatingTitle').textContent = title;
  $('generatingSub').textContent = sub;
  $('progressFill').style.width = `${progress}%`;
  $('progressText').textContent = `${progress}%`;
}

async function loadQueueAndResults() {
  const jobs = await Storage.get('jobs') || [];

  const processing = jobs.filter(j => j.status === 'processing');
  const done = jobs.filter(j => j.status === 'done');

  // Queue tab
  const jobList = $('jobList');
  const queueEmpty = $('queueEmpty');
  if (processing.length > 0) {
    queueEmpty.classList.add('hidden');
    jobList.innerHTML = processing.map(renderJobCard).join('');
  } else {
    queueEmpty.classList.remove('hidden');
    jobList.innerHTML = '';
  }

  // Results tab
  const resultsList = $('resultsList');
  const resultsEmpty = $('resultsEmpty');
  if (done.length > 0) {
    resultsEmpty.classList.add('hidden');
    resultsList.innerHTML = done.map(renderResultCard).join('');
  } else {
    resultsEmpty.classList.remove('hidden');
    resultsList.innerHTML = '';
  }

  updateQueueBadge();
}

function renderJobCard(job) {
  return `
    <div class="job-card">
      <div class="job-title">${job.prompt}</div>
      <div class="job-meta">
        <span>${job.settings?.provider || 'AI'}</span>
        <span>${job.settings?.duration || '?'}s · ${job.settings?.format || ''}</span>
        <span>${timeAgo(job.createdAt)}</span>
      </div>
      <div class="job-status">
        <div class="status-dot processing"></div>
        Processando...
      </div>
    </div>`;
}

function renderResultCard(job) {
  return `
    <div class="job-card">
      <div class="job-title">${job.prompt}</div>
      <div class="job-meta">
        <span>${job.settings?.provider || 'AI'}</span>
        <span>${job.settings?.duration || '?'}s</span>
        <span>${timeAgo(job.createdAt)}</span>
      </div>
      <div style="display:flex;gap:6px;margin-top:4px">
        ${job.videoUrl ? `<a href="${job.videoUrl}" target="_blank" style="color:var(--accent2);font-size:11px;text-decoration:none">▶ Assistir</a>` : ''}
        <div class="job-status">
          <div class="status-dot done"></div>
          Pronto
        </div>
      </div>
    </div>`;
}

function updateQueueBadge() {
  Storage.get('jobs').then(jobs => {
    const count = (jobs || []).filter(j => j.status === 'processing').length;
    $('queueBadge').textContent = count;
    $('queueBadge').style.display = count > 0 ? 'inline' : 'none';
  });
}

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - ts;
  if (diff < 60000) return 'agora';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}min atrás`;
  return `${Math.floor(diff / 3600000)}h atrás`;
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function bindEvents() {
  // Re-load queue/results when switching to those tabs
  document.querySelector('[data-tab="queue"]').addEventListener('click', loadQueueAndResults);
  document.querySelector('[data-tab="results"]').addEventListener('click', loadQueueAndResults);
}

// ─── Boot ───
init();
