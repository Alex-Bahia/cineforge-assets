# Análise Completa — Agnes AI
> Data: 2026-10-07 | Fonte: Firecrawl MCP (scraping direto via sub-agentes)

---

## 1. O que é o Produto

**Agnes AI** é uma empresa de IA de fronteira que treina seus próprios modelos full-modality (texto, imagem, vídeo, raciocínio). A plataforma funciona em três camadas:

1. **AI Gateway / Free AI API Platform** — API estilo OpenAI com modelos próprios, gratuita para acesso básico
2. **Ecossistema de apps AI** — Agnes (assistente), Echo (voz), Pavo (vídeo)
3. **Agnes Code Desktop** — cliente desktop macOS/Windows para workbench de IA

**Empresa:** SapiensAI (Singapura)
**Métricas:** 6M usuários | ~$100M valuation
**Posicionamento:** "From a Global Top 10 AI Lab"
**Missão:** "Make high-quality AI more accessible and scalable, easy to plug into any product or platform"

---

## 2. Modelos de IA Próprios

### Modelos de Texto
| Modelo | Status | Benchmarks |
|--------|--------|-----------|
| `agnes-2.5-flash` | **GRATUITO** (indefinidamente) | — |
| `agnes-3.0-flash` | **GRATUITO** (indefinidamente) | Artificial Analysis Index v4.3: 36pts (vs GPT-5.6 luna: 38, DeepSeek V4 Pro: 36) |
| `agnes-2.5-pro` | Pago | — |
| `agnes-3.0-pro` | Coming soon | — |

### Modelos de Imagem
| Modelo | Status |
|--------|--------|
| `agnes-image-2.0-flash` | **GRATUITO** |
| `agnes-image-2.1-flash` | **GRATUITO** |
| `agnes-image-2.5-flash` | **GRATUITO** |
| `Agnes-Image-2.0` | Elo 1178 no Artificial Analysis Image Editing Leaderboard |

### Modelos de Vídeo
| Modelo | Status |
|--------|--------|
| `agnes-video-2.5` | Pago |
| `agnes-video-2.5-flash` | **GRATUITO (tempo limitado)** |
| `Agnes-Video-2.5` | Elo 1082 no Text-to-Video Leaderboard |

### Ferramentas Agênticas
- **OpenClaw** — ferramenta agêntica
- **Hermes** — ferramenta agêntica

---

## 3. Preços e Planos

### API de Texto
| Modelo | Input | Output | Cache |
|--------|-------|--------|-------|
| `agnes-2.5-flash` | **$0/M** (lista: $0.05/M) | **$0/M** (lista: $0.15/M) | $0 |
| `agnes-3.0-flash` | **$0/M** (lista: $0.05/M) | **$0/M** (lista: $0.15/M) | $0 |
| `agnes-2.5-pro` | $0.45/M | $0.90/M | $0.045/M |

### API de Imagem (atualmente todas GRATUITAS)
| Resolução | Preço Lista | Preço Atual |
|-----------|-------------|-------------|
| 1K | $10/1.000 imagens | **$0** |
| 2K | $18/1.000 imagens | **$0** |
| 3K | $21/1.000 imagens | **$0** |
| 4K | $24/1.000 imagens | **$0** |

### API de Vídeo
| Modelo | 720P | 1080P | 2K |
|--------|------|-------|----|
| `agnes-video-2.5` | $0.025/s | $0.040/s | $0.055/s |
| `agnes-video-2.5-flash` | **$0/s** | — | — |

### Planos de Assinatura (Token Plan)
- **Starter** — uso individual, protótipos
- **Plus** — desenvolvimento contínuo, times, produção volume médio
- **Pro** — produção alto volume, workflows agênticos, multi-usuário

**Free Tier:** Sem limite de tempo para modelos core, sujeito apenas a limites de RPM.

---

## 4. Endpoint da API

```
Base URL: https://apihub.agnes-ai.com/v1
Formato: OpenAI-compatible (drop-in replacement)
```

**Exemplos de uso:**
```python
# Compatível com openai SDK
from openai import OpenAI
client = OpenAI(
    base_url="https://apihub.agnes-ai.com/v1",
    api_key="sua-agnes-api-key"
)

# Texto (gratuito)
response = client.chat.completions.create(
    model="agnes-3.0-flash",
    messages=[{"role": "user", "content": "Escreva um roteiro para vídeo"}]
)

# Imagem (gratuita)
response = client.images.generate(
    model="agnes-image-2.5-flash",
    prompt="Product shot for e-commerce, white background",
    size="1024x1024"
)
```

---

## 5. Aplicações do Ecossistema

| App | Descrição | Plataforma |
|-----|-----------|-----------|
| **Agnes** | Assistente AI principal | Web + Desktop |
| **Echo** | App de voz e áudio IA | Web |
| **Pavo** | Geração e edição de vídeo IA | Web |
| **Agnes Code Desktop** | Workbench local para desenvolvedores | macOS / Windows |

### Agnes Code Desktop — Funcionalidades
- Caixa de entrada única para controlar todo o workbench
- **Modo Inteligente** — seleciona automaticamente modelo, ferramentas e caminho de execução
- **Modo Expert** — controle manual de modelos, contextos, ferramentas, budgets
- Espaço de projeto local — organiza documentos, contexto e entregáveis
- Multi-modelo e Auto — alterna entre modelos Agnes, externos e roteamento automático

---

## 6. Relevância para o CineForge

### ⭐⭐⭐⭐⭐ Uso como Backend Gratuito

**Caso de uso prioritário:** Agnes como backend de LLM + imagem para o pipeline do CineForge sem custo de API.

| Serviço | Provider Atual | Custo | Com Agnes |
|---------|----------------|-------|-----------|
| LLM (roteiros, copy) | Claude/GPT | $5-40/mês | **$0 (agnes-3.0-flash)** |
| Geração de imagem | DALL-E / Leonardo | $10-20/mês | **$0 (agnes-image-2.5-flash)** |
| Geração de vídeo | Runway / Kling | $28-95/mês | **$0 (agnes-video-2.5-flash, tempo limitado)** |

### ⭐⭐⭐⭐ Vantagens Estratégicas

1. **Drop-in para OpenAI** — troca imediata no código existente, sem refatoração
2. **Modelos flash gratuitos indefinidamente** para texto e imagem
3. **Vídeo flash gratuito** (enquanto durar promoção) — útil para testes e MVP
4. **Ferramenta Hermes** — coincidência interessante com nosso projeto Hermes na VPS

### ⭐⭐ Limitações / Riscos

1. **Benchmark baixo** — agnes-3.0-flash: 36pts (bom mas não state-of-art para geração criativa)
2. **"Tempo limitado"** no vídeo free — pode ficar pago a qualquer momento
3. **RPM limitado** no free tier — adequado para desenvolvimento, pode ter gargalos em produção
4. **Empresa jovem** — histórico menor que Anthropic/OpenAI/Google

### Recomendação de Uso

```
CineForge Pipeline:
- Roteiro/copy → agnes-3.0-flash (gratuito) como fallback barato
- Imagens de produto → agnes-image-2.5-flash (gratuito) para drafts
- Vídeos finais → Kling/Runway/Veo (qualidade) ou agnes-video-2.5-flash (gratuito para testes)
- Revisão/qualidade → Claude Sonnet (pago, melhor qualidade)
```

**Estratégia:** Usar Agnes para camada de custo zero (drafts, variações, volume baixo) e modelos premium para entregáveis finais. Reduz custo total de API em 60-80%.

---

## 7. Comparação com Concorrentes Diretos

| Provider | Texto Free | Imagem Free | Vídeo Free | Benchmark |
|----------|-----------|-------------|------------|-----------|
| **Agnes AI** | ✅ (indefinido) | ✅ (indefinido) | ✅ (tempo limitado) | ★★★☆☆ |
| **Gemini Flash** | ✅ (1M tokens/dia) | ❌ | ❌ | ★★★★☆ |
| **OpenAI** | ❌ | ❌ | ❌ | ★★★★★ |
| **Anthropic** | ❌ | ❌ | ❌ | ★★★★★ |
| **Groq** | ✅ (rate limited) | ❌ | ❌ | ★★★★☆ |

**Conclusão:** Agnes é o único provider com texto + imagem + vídeo tudo gratuito simultaneamente. Isso o torna único para prototipagem e projetos com budget limitado.

---

## 8. URLs Chave

| Recurso | URL |
|---------|-----|
| Homepage | https://agnes-ai.com/ |
| API Hub | https://apihub.agnes-ai.com |
| Pricing | https://platform.agnes-ai.com/pricing |
| Subscribe | https://platform.agnes-ai.com/subscribe/subscription |
| Agnes Code (Desktop) | https://agnes-ai.com/agnes-code |
| Pavo (Vídeo) | https://agnes-ai.com/pavo |
