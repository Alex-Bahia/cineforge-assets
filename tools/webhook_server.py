"""
CineForge Webhook Server
Servidor HTTP que expõe o CineForgeAgent como API REST.
Permite integração com CREAO.ai, Make, n8n e qualquer plataforma via HTTP.

Uso:
    pip install fastapi uvicorn
    uvicorn tools.webhook_server:app --host 0.0.0.0 --port 8765

Endpoints:
    POST /claude/roteiro    — Gera roteiro completo
    POST /claude/nichos     — Pesquisa nichos
    POST /claude/seo        — Otimiza SEO
    POST /claude/pipeline   — Roteiro + SEO completo
    POST /claude/chat       — Chat livre
    GET  /health            — Status do servidor
"""

import os
import logging
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError:
    raise ImportError(
        "Instale as dependências: pip install fastapi uvicorn\n"
        "Ou adicione ao requirements.txt: fastapi>=0.110.0 uvicorn>=0.29.0"
    )

from tools.claude_agent import CineForgeAgent

logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CineForge Claude API",
    description="Webhook server para integração CREAO ↔ Claude",
    version="1.0.0",
)

_agent: Optional[CineForgeAgent] = None


def get_agent() -> CineForgeAgent:
    global _agent
    if _agent is None:
        _agent = CineForgeAgent()
    return _agent


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de request
# ─────────────────────────────────────────────────────────────────────────────

class RoteiroRequest(BaseModel):
    topic: str
    estilo: str = "educativo"
    duracao_min: int = 8
    publico: str = "brasileiros interessados no tema"


class NichosRequest(BaseModel):
    categoria: str
    top_n: int = 10
    foco: str = "monetização e crescimento"


class SEORequest(BaseModel):
    tema: str
    roteiro_resumo: str = ""
    canal: str = "canal educativo brasileiro"


class ChatRequest(BaseModel):
    mensagem: str
    contexto: str = "Assistente especializado em criação de conteúdo para YouTube Brasil."


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Status do servidor e modo de operação do agente."""
    agent = get_agent()
    return {
        "status": "ok",
        "mode": agent._mode,
        "model": agent.model,
    }


@app.post("/claude/roteiro")
def gerar_roteiro(req: RoteiroRequest):
    """Gera roteiro completo para um vídeo YouTube."""
    try:
        result = get_agent().gerar_roteiro(
            req.topic, req.estilo, req.duracao_min, req.publico
        )
        return {"ok": True, "data": result}
    except Exception as e:
        logger.error("Erro ao gerar roteiro: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/claude/nichos")
def pesquisar_nichos(req: NichosRequest):
    """Identifica os melhores sub-nichos para uma categoria."""
    try:
        result = get_agent().pesquisar_nichos(req.categoria, req.top_n, req.foco)
        return {"ok": True, "data": result}
    except Exception as e:
        logger.error("Erro ao pesquisar nichos: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/claude/seo")
def otimizar_seo(req: SEORequest):
    """Gera título, descrição e tags otimizadas para YouTube SEO."""
    try:
        result = get_agent().otimizar_seo(req.tema, req.roteiro_resumo, req.canal)
        return {"ok": True, "data": result}
    except Exception as e:
        logger.error("Erro ao otimizar SEO: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/claude/pipeline")
def pipeline_completo(req: RoteiroRequest):
    """Executa o pipeline completo: roteiro + SEO em uma chamada."""
    try:
        result = get_agent().pipeline_completo(req.topic, req.estilo, req.duracao_min)
        return {"ok": True, "data": result}
    except Exception as e:
        logger.error("Erro no pipeline completo: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/claude/chat")
def chat_livre(req: ChatRequest):
    """Chat livre com Claude para qualquer tarefa do pipeline."""
    try:
        result = get_agent().chat(req.mensagem, req.contexto)
        return {"ok": True, "data": result}
    except Exception as e:
        logger.error("Erro no chat: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Execução direta
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("WEBHOOK_PORT", "8765"))
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")

    logger.info("CineForge Webhook Server iniciando em http://%s:%d", host, port)
    logger.info("Docs disponíveis em: http://%s:%d/docs", host, port)

    uvicorn.run("tools.webhook_server:app", host=host, port=port, reload=False)
