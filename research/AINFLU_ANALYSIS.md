# Análise de Benchmark — ainflu.ai
> Data: 2026-10-06 | Fonte: Firecrawl MCP (scraping via sub-agentes)

---

## 1. Empresa

- **Razão Social**: WEB SOLUÇÕES INTERATIVAS LTDA – ME
- **CNPJ**: 05.970.555/0001-80 — Marília/SP, Brasil
- **Contato**: contato@ainflu.ai | privacidade@ainflu.ai
- **Métricas públicas**: +2.000 criadores ativos, 75+ modelos de IA integrados

---

## 2. URLs e Estrutura Pública

**Landing (ainflu.ai):**
- `/` — homepage
- `/termos` — Termos de Uso
- `/politica` — Política de Privacidade
- `/blog` — 404 (descontinuado)
- `/sitemap.xml` — 404 (sem sitemap público)

**App (app.ainflu.ai — SPA, requer auth):**
- `/planos` — assinaturas/créditos
- `/aula/{slug}` — Academy (aulas públicas)
- `/?ref={codigo}` — sistema de referral/afiliados

**CDN:**
- `ainflu.b-cdn.net` — imagens de usuários
- `vz-d0ecacc0-5be.b-cdn.net` — vídeos (Bunny.net)
- `iframe.mediadelivery.net/embed/370065/...` — player (Bunny library ID: 370065)

---

## 3. Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React SPA (`app.ainflu.ai`) |
| Servidor web | LiteSpeed Web Server |
| CDN vídeo | Bunny.net (`vz-d0ecacc0-5be.b-cdn.net`) |
| Player vídeo | Bunny MediaDelivery (library `370065`) |
| CDN imagens | `ainflu.b-cdn.net` |
| Pagamentos | **Asaas** (PIX, boleto, cartão, assinaturas) |
| Inferência IA | **Fal.ai** + **Replicate.com** (intermediários) |

---

## 4. APIs de IA Integradas

| Provedor | Categoria |
|----------|-----------|
| Fal.ai | Plataforma de inferência (intermediário principal) |
| Replicate.com | Inferência de modelos open-source |
| OpenAI | LLMs para roteiros + Sora para vídeo |
| Kling (Kuaishou) | Geração de vídeo |
| Runway | Geração de vídeo |
| Google Veo 3 | Geração de vídeo |
| Hailuo / MiniMax | Geração de vídeo |
| Luma AI (Dream Machine) | Geração de vídeo |
| Seedance (ByteDance) | Geração de vídeo |
| Ideogram | Geração de imagem |
| Recraft | Geração de imagem (vetorial/design) |
| Topaz Labs | Upscale / pós-produção de vídeo |
| Suno AI | Geração de música |

---

## 5. Modelo de Negócio

- **Sistema de créditos + assinaturas recorrentes** via Asaas
- Créditos expiram em 12 meses; sem reembolso após uso
- Foro jurídico: Comarca de Marília/SP (LGPD declarada)

---

## 6. Funcionalidades por Área

| Área | Funcionalidades |
|------|-----------------|
| Personagens | Personagem consistente, guarda-roupa digital, avatar falante, UGC AI |
| Vídeo | Kling, Veo 3, Runway, Sora, Hailuo, Seedance, MiniMax, Luma |
| Imagens | Photo Studio, Upscale 4K, remoção de fundo, Templates Virais |
| Áudio | TTS PT-BR, Clone de Voz, Música IA, Suno integrado |
| Agentes | StoryFlow, Story Director, Komik (HQs), Lyra (e-books), Roteiros 7C, Social Post Generator, Carrosséis, Kit de Marca |
| YouTube | Radar Viral YT, Thumb Viral, Storyboard Pipeline |
| Automação | **Fluxo Criativo** — canvas visual com nós conectáveis (tipo n8n) |
| Academy | Aulas e tutoriais em `/aula/...` |

---

## 7. Arquitetura de Backend (Inferência)

```
Usuário
  └→ React SPA (app.ainflu.ai)
       └→ API interna (não documentada publicamente)
            ├→ Fal.ai / Replicate.com  ←→  Modelos de IA (Kling, Runway, etc.)
            ├→ OpenAI API              ←→  LLMs + Sora
            └→ Bunny.net CDN          ←→  Armazenamento de mídia gerada
```

**Padrão arquitetural**: Orquestrador de APIs de terceiros com sistema de créditos como camada de abstração de custos.

**Canvas visual (Fluxo Criativo)**: Pipeline visual sem código, nós disponíveis:
`Personagem → Guarda-Roupa → Avatar Falante → Gerar Imagem → Gerar Vídeo → Upscale → Texto p/ Voz → Música IA → Storyboard → UGC → Pós-Produção`

---

## 8. Skills Relevantes Identificadas (awesomeskill.ai)

| Skill | URL | Relevância CineForge |
|-------|-----|---------------------|
| ai-video-generation | awesomeskill.ai/skill/inferen-sh-skills-ai-video-generation | ★★★★★ |
| media-processing | awesomeskill.ai/skill/claudekit-skills-media-processing | ★★★★★ |
| social-publisher | awesomeskill.ai/skill/claude-office-skills-skills-social-publisher | ★★★★☆ |
| platform-optimization | awesomeskill.ai/skill/claude-vibes-platform-optimization | ★★★★☆ |
| elevenlabs | awesomeskill.ai/skill/skillz-elevenlabs | ★★★★☆ |
| youtube-collector | awesomeskill.ai/skill/cc-system-youtube-collector | ★★★☆☆ |
| blog-repurpose | awesomeskill.ai/skill/agricidaniel-claude-blog-blog-repurpose | ★★★☆☆ |
| ckm:banner-design | awesomeskill.ai/skill/nextlevelbuilder-ui-ux-pro-max-skill-ckm:banner-design | ★★★☆☆ |
