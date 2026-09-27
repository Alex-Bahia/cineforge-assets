/**
 * Claude API integration — script & storyboard generation
 */
export const ClaudeAPI = {

  async generateScript(userPrompt, settings, apiKey) {
    const systemPrompt = `Você é um diretor criativo e roteirista especializado em vídeos de marketing e publicidade.
Sua tarefa é criar roteiros profissionais e detalhados para vídeos de IA.

Ao criar um roteiro, siga esta estrutura exata em JSON:
{
  "title": "Título do vídeo",
  "duration": número em segundos,
  "format": "proporção",
  "tone": "tom do vídeo",
  "voiceover": "texto completo da narração",
  "scenes": [
    {
      "id": 1,
      "duration": segundos,
      "visual": "descrição detalhada da cena visual em inglês para o gerador de vídeo",
      "narration": "texto da narração desta cena",
      "transition": "fade|cut|dissolve"
    }
  ],
  "music_direction": "descrição do estilo musical",
  "fullText": "roteiro completo formatado para exibição"
}

Crie cenas visualmente ricas com descrições em inglês otimizadas para geração de vídeo com IA (Higgsfield/HeyGen/Motion).`;

    const userMessage = `Crie um roteiro para: ${userPrompt}

Configurações:
- Duração: ${settings.duration} segundos
- Formato: ${settings.format}
- Provedor: ${settings.provider}

Retorne APENAS o JSON, sem markdown ou texto adicional.`;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-opus-5-5',
        max_tokens: 4096,
        system: systemPrompt,
        messages: [{ role: 'user', content: userMessage }],
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error?.message || `Claude API error: ${response.status}`);
    }

    const data = await response.json();
    const text = data.content?.[0]?.text || '';

    try {
      return JSON.parse(text);
    } catch {
      // Fallback: return as plain text script
      return { fullText: text, scenes: [], title: 'Vídeo Gerado', duration: settings.duration };
    }
  },

  async refineScript(originalScript, feedback, apiKey) {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-opus-5-5',
        max_tokens: 4096,
        messages: [{
          role: 'user',
          content: `Aqui está o roteiro atual:\n\n${JSON.stringify(originalScript, null, 2)}\n\nAjuste conforme este feedback:\n${feedback}\n\nRetorne o JSON atualizado.`,
        }],
      }),
    });

    if (!response.ok) throw new Error(`Claude API error: ${response.status}`);
    const data = await response.json();
    const text = data.content?.[0]?.text || '';

    try {
      return JSON.parse(text);
    } catch {
      return { ...originalScript, fullText: text };
    }
  },
};
