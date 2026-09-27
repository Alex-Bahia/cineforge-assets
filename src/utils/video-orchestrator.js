const PROVIDERS = { heygen: HeyGenProvider, higgsfield: HiggsProvider, motion: MotionProvider };

export const VideoOrchestrator = {
  async submit(scriptText, settings, config) {
    const Provider = PROVIDERS[settings.provider];
    if (!Provider) throw new Error(`Provedor desconhecido: ${settings.provider}`);
    const apiKey = config[`${settings.provider}ApiKey`];
    if (!apiKey) throw new Error(`Configure a chave API do ${settings.provider} nas configurações`);
    return Provider.submit(scriptText, settings, apiKey);
  },
  async checkStatus(jobId, provider, config) {
    const Provider = PROVIDERS[provider];
    if (!Provider) throw new Error(`Provedor desconhecido: ${provider}`);
    return Provider.checkStatus(jobId, config[`${provider}ApiKey`]);
  },
};

function HeyGenProvider() {}
HeyGenProvider.submit = async function(scriptText, settings, apiKey) {
  const r = await fetch('https://api.heygen.com/v2/video/generate', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Api-Key': apiKey }, body: JSON.stringify({ video_inputs: [{ character: { type: 'text', input_text: scriptText }, voice: { type: 'text', input_text: scriptText, voice_id: 'default' } }], dimension: { width: settings.format === '9:16' ? 720 : 1280, height: settings.format === '9:16' ? 1280 : 720 }, aspect_ratio: settings.format === '9:16' ? 'portrait' : 'landscape', duration: parseInt(settings.duration) }) });
  if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.message || `HeyGen error: ${r.status}`); }
  const d = await r.json(); return d.data?.video_id || d.video_id;
};
HeyGenProvider.checkStatus = async function(jobId, apiKey) {
  const r = await fetch(`https://api.heygen.com/v1/video_status.get?video_id=${jobId}`, { headers: { 'X-Api-Key': apiKey } });
  if (!r.ok) throw new Error(`HeyGen status error: ${r.status}`);
  const d = await r.json(); const s = d.data?.status;
  if (s === 'completed') return { status: 'completed', videoUrl: d.data.video_url };
  if (s === 'failed') return { status: 'failed', error: d.data?.error };
  return { status: 'processing' };
};

function HiggsProvider() {}
HiggsProvider.submit = async function(scriptText, settings, apiKey) {
  const r = await fetch('https://api.higgsfield.ai/v1/generations', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` }, body: JSON.stringify({ model: 'hf_video_gen', prompt: scriptText, duration: parseInt(settings.duration), aspect_ratio: settings.format }) });
  if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.message || `Higgsfield error: ${r.status}`); }
  const d = await r.json(); return d.id || d.generation_id;
};
HiggsProvider.checkStatus = async function(jobId, apiKey) {
  const r = await fetch(`https://api.higgsfield.ai/v1/generations/${jobId}`, { headers: { 'Authorization': `Bearer ${apiKey}` } });
  if (!r.ok) throw new Error(`Higgsfield status error: ${r.status}`);
  const d = await r.json();
  if (d.status === 'completed') return { status: 'completed', videoUrl: d.video_url };
  if (d.status === 'failed') return { status: 'failed', error: d.error };
  return { status: 'processing' };
};

function MotionProvider() {}
MotionProvider.submit = async function(scriptText, settings, apiKey) {
  const r = await fetch('https://api.usemotion.com/v1/videos', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` }, body: JSON.stringify({ brief: scriptText, duration: parseInt(settings.duration), aspect_ratio: settings.format, mode: 'medium' }) });
  if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.message || `Motion error: ${r.status}`); }
  const d = await r.json(); return d.id || d.session_id;
};
MotionProvider.checkStatus = async function(jobId, apiKey) {
  const r = await fetch(`https://api.usemotion.com/v1/videos/${jobId}`, { headers: { 'Authorization': `Bearer ${apiKey}` } });
  if (!r.ok) throw new Error(`Motion status error: ${r.status}`);
  const d = await r.json();
  if (d.status === 'completed') return { status: 'completed', videoUrl: d.video_url || d.output_url };
  if (d.status === 'failed') return { status: 'failed', error: d.error };
  return { status: 'processing' };
};
