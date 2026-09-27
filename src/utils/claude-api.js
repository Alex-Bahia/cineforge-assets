export const ClaudeAPI = {
  async generateScript(userPrompt, settings, apiKey) {
    const systemPrompt = `Você é um diretor criativo e roteirista especializado em vídeos de marketing e publicidade. Crie roteiros profissionais em JSON com esta estrutura: {"title","duration","format","tone","voiceover","scenes":[{"id","duration","visual","narration","transition"}],"music_direction","fullText"}.`;
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' },
      body: JSON.stringify({
        model: 'claude-opus-5-5',
        max_tokens: 4096,
        system: systemPrompt,
        messages: [{ role: 'user', content: `Crie um roteiro para: ${userPrompt}\n\nDuração: ${settings.duration}s, Formato: ${settings.format}, Provedor: ${settings.provider}\n\nRetorne APENAS o JSON.` }],
      }),
    });
    if (!response.ok) { const err = await response.json().catch(() => ({})); throw new Error(err.error?.message || `Claude API error: ${response.status}`); }
    const data = await response.json();
    const text = data.content?.[0]?.text || '';
    try { return JSON.parse(text); } catch { return { fullText: text, scenes: [], title: 'Vídeo Gerado', duration: settings.duration }; }
  },
};
