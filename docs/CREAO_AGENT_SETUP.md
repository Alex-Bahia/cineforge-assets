# Agente CREAO ↔ Claude — Guia de Configuração

## Visão Geral

Arquitetura recomendada: o CREAO.ai orquestra os fluxos e gerencia conectores (YouTube, GSC, Telegram), e o Claude faz o raciocínio pesado (roteiros, análise de nichos, SEO, estratégia).

```
CREAO Workflow
     │
     ├─ Conector YouTube (pesquisa trending)
     ├─ Conector GSC (dados de busca)
     │
     ▼
HTTP Request → Claude API (Anthropic)
     │
     ▼
Processamento pelo Claude (roteiro, SEO, análise)
     │
     ▼
Resultado → CREAO → Telegram / YouTube Upload
```

## Passo a Passo no CREAO.ai

### 1. Criar um novo Workflow

1. Acesse `app.creao.ai` → **Workflows** → **New Workflow**
2. Nomeie: `CineForge Claude Pipeline`

### 2. Adicionar módulo HTTP Request para Claude API

> ⚠️ O CREAO não tem conector nativo do Claude/Anthropic ainda.
> Use o módulo **HTTP Request** (se disponível no seu plano) ou
> o módulo **Webhook** para chamar o CineForge local via ngrok.

**Configuração do HTTP Request para Claude:**

```
Method: POST
URL: https://api.anthropic.com/v1/messages
Headers:
  x-api-key: {{ANTHROPIC_API_KEY}}          ← variável segura no CREAO
  anthropic-version: 2023-06-01
  content-type: application/json

Body (JSON):
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 4096,
  "system": "Você é um roteirista especialista em vídeos YouTube Brasil...",
  "messages": [
    {
      "role": "user",
      "content": "Crie um roteiro para: {{topic}}"
    }
  ]
}
```

### 3. Alternativa — Webhook para CineForge Local/VPS

Se preferir não expor a chave Anthropic no CREAO, rode o CineForge
como servidor e deixe o CREAO chamar via Webhook:

**No CineForge (sua VPS/Hermes):**
```bash
# Instalar FastAPI
pip install fastapi uvicorn

# Rodar o servidor de webhook (tools/webhook_server.py)
uvicorn tools.webhook_server:app --host 0.0.0.0 --port 8765
```

**No CREAO:**
```
HTTP Request → POST https://sua-vps.com:8765/claude/roteiro
Body: {"topic": "{{youtube_trending_topic}}"}
```

### 4. Fluxo Completo Recomendado no CREAO

```
[Trigger: Cron diário às 06:00]
         │
         ▼
[YouTube Conector: buscar trending Brasil]
         │
         ▼
[HTTP → Claude: analisar nichos e escolher melhor tópico]
         │
         ▼
[HTTP → Claude: gerar roteiro completo]
         │
         ▼
[HTTP → Claude: otimizar SEO (título, descrição, tags)]
         │
         ▼
[Google Sheets: salvar fila de vídeos]
         │
         ▼
[Telegram: notificar "Roteiro pronto para: {{título}}"]
```

### 5. Variáveis de Ambiente no CREAO

Em `app.creao.ai/settings/api` ou nas configurações do workflow:

| Variável             | Valor                        |
|----------------------|------------------------------|
| `ANTHROPIC_API_KEY`  | `sk-ant-...` (console.anthropic.com) |
| `TELEGRAM_CHAT_ID`   | Seu chat ID do Telegram      |
| `YOUTUBE_API_KEY`    | Sua YouTube Data API Key     |

## Opção Sem Conta console.anthropic.com

Se preferir usar seu plano claude.ai existente sem custo adicional:

1. O `claude_agent.py` do CineForge já tem suporte a CLI fallback
2. Configure um servidor HTTP local (webhook_server.py) na sua VPS
3. O CREAO chama o webhook → o webhook usa `claude -p "..."` internamente
4. Sem necessidade de chave Anthropic separada

## Testando a Integração

```bash
# Testar o agente Claude localmente
python tools/claude_agent.py nichos "finanças pessoais"

# Testar com CLI fallback (sem ANTHROPIC_API_KEY)
unset ANTHROPIC_API_KEY
python tools/claude_agent.py chat "Olá, funciona?"

# Testar integração CREAO
python tools/creao_integration.py ping
python tools/creao_integration.py list-agents
```

## Webhook Server (para integrar com CREAO)

Crie `tools/webhook_server.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from tools.claude_agent import CineForgeAgent

app = FastAPI()
agent = CineForgeAgent()

class RoteiroRequest(BaseModel):
    topic: str
    estilo: str = "educativo"
    duracao_min: int = 8

@app.post("/claude/roteiro")
def gerar_roteiro(req: RoteiroRequest):
    return agent.gerar_roteiro(req.topic, req.estilo, req.duracao_min)

@app.post("/claude/nichos")
def pesquisar_nichos(categoria: str, top_n: int = 10):
    return agent.pesquisar_nichos(categoria, top_n)

@app.post("/claude/seo")
def otimizar_seo(tema: str, resumo: str = ""):
    return agent.otimizar_seo(tema, resumo)

@app.post("/claude/pipeline")
def pipeline_completo(req: RoteiroRequest):
    return agent.pipeline_completo(req.topic, req.estilo, req.duracao_min)
```
