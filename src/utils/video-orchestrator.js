/**
 * Video generation orchestrator — routes to the right provider
 */

const PROVIDERS = {
  heygen: HeyGenProvider,
  higgsfield: HiggsProvider,
  motion: MotionProvider,
};

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

    const apiKey = config[`${provider}ApiKey`];
    return Provider.checkStatus(jobId, apiKey);
  },
};

// ─── HeyGen ───
function HeyGenProvider() {}

HeyGenProvider.submit = async function(scriptText, settings, apiKey) {
  const aspectMap = {
    '16:9': 'landscape',
    '9:16': 'portrait',
    '1:1': 'square',
    '4:5': 'portrait',
  };

  const response = await fetch('https://api.heygen.com/v2/video/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Api-Key': apiKey,
    },
    body: JSON.stringify({
      video_inputs: [{
        character: {
          type: 'text',
          input_text: scriptText,
        },
        voice: {
          type: 'text',
          input_text: scriptText,
          voice_id: 'default',
        },
      }],
      dimension: {
        width: settings.format === '9:16' ? 720 : settings.format === '1:1' ? 720 : 1280,
        height: settings.format === '9:16' ? 1280 : settings.format === '1:1' ? 720 : 720,
      },
      aspect_ratio: aspectMap[settings.format] || 'landscape',
      duration: parseInt(settings.duration),
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.message || `HeyGen error: ${response.status}`);
  }

  const data = await response.json();
  return data.data?.video_id || data.video_id;
};

HeyGenProvider.checkStatus = async function(jobId, apiKey) {
  const response = await fetch(`https://api.heygen.com/v1/video_status.get?video_id=${jobId}`, {
    headers: { 'X-Api-Key': apiKey },
  });

  if (!response.ok) throw new Error(`HeyGen status error: ${response.status}`);

  const data = await response.json();
  const status = data.data?.status;

  if (status === 'completed') return { status: 'completed', videoUrl: data.data.video_url };
  if (status === 'failed') return { status: 'failed', error: data.data?.error || 'Falha desconhecida' };
  return { status: 'processing' };
};

// ─── Higgsfield ───
function HiggsProvider() {}

HiggsProvider.submit = async function(scriptText, settings, apiKey) {
  const response = await fetch('https://api.higgsfield.ai/v1/generations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'hf_video_gen',
      prompt: scriptText,
      duration: parseInt(settings.duration),
      aspect_ratio: settings.format,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.message || `Higgsfield error: ${response.status}`);
  }

  const data = await response.json();
  return data.id || data.generation_id;
};

HiggsProvider.checkStatus = async function(jobId, apiKey) {
  const response = await fetch(`https://api.higgsfield.ai/v1/generations/${jobId}`, {
    headers: { 'Authorization': `Bearer ${apiKey}` },
  });

  if (!response.ok) throw new Error(`Higgsfield status error: ${response.status}`);

  const data = await response.json();

  if (data.status === 'completed') return { status: 'completed', videoUrl: data.video_url };
  if (data.status === 'failed') return { status: 'failed', error: data.error };
  return { status: 'processing' };
};

// ─── Motion ───
function MotionProvider() {}

MotionProvider.submit = async function(scriptText, settings, apiKey) {
  const response = await fetch('https://api.usemotion.com/v1/videos', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      brief: scriptText,
      duration: parseInt(settings.duration),
      aspect_ratio: settings.format,
      mode: 'medium',
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.message || `Motion error: ${response.status}`);
  }

  const data = await response.json();
  return data.id || data.session_id;
};

MotionProvider.checkStatus = async function(jobId, apiKey) {
  const response = await fetch(`https://api.usemotion.com/v1/videos/${jobId}`, {
    headers: { 'Authorization': `Bearer ${apiKey}` },
  });

  if (!response.ok) throw new Error(`Motion status error: ${response.status}`);

  const data = await response.json();

  if (data.status === 'completed') return { status: 'completed', videoUrl: data.video_url || data.output_url };
  if (data.status === 'failed') return { status: 'failed', error: data.error };
  return { status: 'processing' };
};
