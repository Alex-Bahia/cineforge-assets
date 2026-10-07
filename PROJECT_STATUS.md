# CineForge — Status do Projeto
> Última atualização: 2026-10-07

---

## Visão Geral

**CineForge** é uma plataforma de criação de conteúdo de vídeo para e-commerce e anúncios de performance, especializada em GBP, Meta Ads e TikTok Ads. Posicionamento: interface sem código em cima de pipelines de IA open-source existentes, com loop fechado de métricas de conversão.

---

## Repositório

- **Repo:** `alex-bahia/cineforge-assets`
- **Branch ativa:** `claude/vibrant-volta-f1hzbv`
- **PR aberto:** #4

---

## Pesquisas Concluídas

| Arquivo | Tema | Data |
|---------|------|------|
| `research/COMPETITIVE_ANALYSIS.md` | 13 players globais + 7 BR, tabela de preços comparativa | Out/2026 |
| `research/AINFLU_ANALYSIS.md` | Stack técnica do concorrente ainflu.ai (React + Fal.ai + Replicate + Asaas) | Out/2026 |
| `research/INEMA_ANALYSIS.md` | 318 cursos INEMA, trilhas de automação, oportunidades de aprendizado | Out/2026 |
| `research/DARK_CHANNEL_ANALYSIS.md` | Pipelines completos de canais dark/faceless, stacks $0–$333/mês | Out/2026 |
| `research/AGNES_ANALYSIS.md` | Agnes AI — API gratuita texto + imagem indefinido, vídeo flash limitado | Out/2026 |

---

## Infraestrutura Técnica

### VPS (Hermes)
- **Status:** Briefing criado em `HERMES_BRIEFING.md`
- **Pendente:** Instalar OpenMontage + configurar pipelines GBP/Facebook/Instagram
- **Próximo passo:** `git clone` + `make install` + `.env` na VPS

### Ferramentas disponíveis
| Ferramenta | Arquivo | Uso |
|-----------|---------|-----|
| Scraper ainflu.ai | `tools/scraper-ainflu.py` | Playwright — rodar localmente |
| Pipeline principal | `run_pipeline.py` | Pipeline CineForge existente |
| Engine | `run_engine.py` | Motor de geração de conteúdo |

---

## Stack Recomendada (Com Base nas Pesquisas)

### Backend Gratuito (Drafts / Prototipagem)
```
LLM          → agnes-3.0-flash (apihub.agnes-ai.com/v1, OpenAI-compatible)
Imagens      → agnes-image-2.5-flash (gratuito indefinidamente)
Vídeo        → agnes-video-2.5-flash (gratuito por tempo limitado)
TTS PT-BR    → Edge TTS pt-BR-FranciscaNeural ($0)
Montagem     → FFmpeg (Verticals v3 pipeline)
```

### Backend Premium (Entregáveis Finais)
```
LLM          → Claude Sonnet (qualidade editorial)
Imagens      → Produção própria / Runway
Vídeo        → Kling / Runway / Veo (qualidade cinemática)
TTS          → ElevenLabs Creator ($99/mês)
```

### Automação
```
Orquestração → n8n self-hosted (template #3442 / #5683)
Upload YT    → YouTube Data API v3 (publishAt para agendamento)
SEO          → Verticals v3 open-source (título + descrição + tags automáticos)
```

---

## Insights Estratégicos

### Diferencial CineForge vs Concorrência
1. **Interface sem código** sobre pipelines técnicos (Verticals v3, n8n, FFmpeg)
2. **Especialização e-commerce** — não é canal dark genérico, é anúncio de produto
3. **Loop de métricas** — não só gera, mas rastreia se o anúncio converteu
4. **Compliance YouTube** — revisão humana automatizada (10-15 min) evita ban de monetização
5. **Custo reduzido em 60-80%** usando Agnes como camada de custo zero

### Alerta Crítico
> YouTube (jul/2025): "mass-produced template content without creative input" pode ter monetização negada. Solução: sempre incluir toque humano antes do upload.

### Concorrentes Principais
| Player | Ponto Fraco | Oportunidade CineForge |
|--------|-------------|----------------------|
| ainflu.ai | Genérico, sem foco em e-commerce | Especialização em produto |
| Clipbee.ai | Sem loop de métricas | Analytics de conversão |
| Virvid.ai | $47/mês, sem customização | Preço + personalização |
| n8n templates | Técnico demais | Interface visual |

---

## Próximos Passos Prioritários

### Imediatos (Esta Semana)
- [ ] Instalar OpenMontage na VPS (Hermes) — briefing já pronto
- [ ] Configurar pipeline GBP + Facebook + Instagram no Hermes
- [ ] Testar Agnes API como backend de LLM no pipeline existente

### Curto Prazo (Este Mês)
- [ ] MVP da interface sem código sobre o pipeline atual
- [ ] Integrar Edge TTS pt-BR para narração automática
- [ ] Pipeline completo: produto → roteiro → voz → vídeo → upload YT

### Médio Prazo
- [ ] Loop de métricas: tracking de conversão por vídeo publicado
- [ ] Integração n8n para automação de publicação multi-plataforma
- [ ] Painel de criação para lojistas sem conhecimento técnico

---

## Recursos e Links Chave

| Recurso | URL / Localização |
|---------|-------------------|
| Agnes AI API | `https://apihub.agnes-ai.com/v1` |
| Verticals v3 | `github.com/rushindrasinha/youtube-shorts-pipeline` |
| n8n template YouTube | `n8n.io/workflows/3442` |
| INEMA (cursos) | `inema.club` — R$42/mês ou R$300/ano PIX |
| Hermes VPS | Ver `HERMES_BRIEFING.md` |
