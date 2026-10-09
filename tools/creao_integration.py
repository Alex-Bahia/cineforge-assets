"""
CineForge ↔ CREAO Integration
Integração entre o pipeline CineForge e a plataforma CREAO.ai

Configure CREAO_API_KEY no arquivo .env (veja .env.example).
Nome da API Key criada: CineForge-Integration | Plano: Pro

Uso:
    from tools.creao_integration import CREAOClient
    client = CREAOClient()
    agents = client.list_agents()
    result = client.run_agent("youtube-topic-scout", {"niche": "finanças pessoais"})
"""

import os
import time
import json
import logging
import requests
from typing import Optional, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────────────────────

CREAO_API_KEY = os.getenv("CREAO_API_KEY", "")

# Endpoints possíveis — ajuste conforme documentação oficial em app.creao.ai/settings/api
CREAO_BASE_URL = os.getenv("CREAO_BASE_URL", "https://api.creao.ai/v1")

# Confirme o endpoint correto nos docs do CREAO. Alternativas comuns:
# "https://app.creao.ai/api/v1"
# "https://api.creao.ai/v1"
# "https://creao.ai/api/v1"

POLL_INTERVAL = 5   # segundos entre polls de status
POLL_TIMEOUT  = 300 # timeout máximo em segundos


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de resposta esperados (ajuste conforme a API real)
# ─────────────────────────────────────────────────────────────────────────────

# Templates conhecidos do CREAO (descobertos via extensão):
# 1. "YouTube Topic Scout & Script Writer" → pesquisa tópicos + gera roteiro
# 2. "Thumbnail Reproducer"               → replica estilos de thumbnail

# Conectores disponíveis para uso no CineForge:
# ✅ YouTube, Google Search Console, SEMrush, Telegram, Instagram, Firecrawl
# ❌ Webhook nativo, HTTP Request nativo (indisponível no plano atual)


class CREAOError(Exception):
    """Erro da API CREAO."""
    pass


class CREAOClient:
    """
    Cliente REST para a plataforma CREAO.ai.

    Autenticação via Bearer token (X-API-Key header como fallback).
    Suporta: listar agentes, disparar execuções, polling de resultados.
    """

    def __init__(
        self,
        api_key: str = CREAO_API_KEY,
        base_url: str = CREAO_BASE_URL,
    ):
        self.api_key  = api_key
        self.base_url = base_url.rstrip("/")
        self.session  = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,       # fallback para plataformas que usam X-API-Key
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    # ─────────────────────────────────────────────────────────────────────
    # Métodos internos
    # ─────────────────────────────────────────────────────────────────────

    def _get(self, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        resp = self.session.post(url, json=payload, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # ─────────────────────────────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        """Testa conectividade e validade da API Key."""
        try:
            # Tenta o endpoint mais comum; ajuste se o CREAO usar outro path
            self._get("/health")
            return True
        except Exception:
            try:
                self._get("/me")
                return True
            except Exception as e:
                logger.error("CREAO ping falhou: %s", e)
                return False

    def list_agents(self) -> list[dict]:
        """
        Lista todos os agentes/workflows disponíveis na conta.

        Endpoint esperado: GET /agents ou GET /workflows
        Retorna lista de dicts com ao menos: id, name, description, status
        """
        try:
            data = self._get("/agents")
            return data.get("agents", data.get("data", data if isinstance(data, list) else []))
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                # Alguns sistemas usam /workflows em vez de /agents
                data = self._get("/workflows")
                return data.get("workflows", data.get("data", []))
            raise CREAOError(f"Erro ao listar agentes: {e}") from e

    def get_agent(self, agent_id: str) -> dict:
        """Retorna detalhes de um agente específico."""
        try:
            return self._get(f"/agents/{agent_id}")
        except requests.HTTPError as e:
            raise CREAOError(f"Agente '{agent_id}' não encontrado") from e

    def run_agent(
        self,
        agent_id: str,
        inputs: dict[str, Any],
        wait: bool = True,
        timeout: int = POLL_TIMEOUT,
    ) -> dict:
        """
        Dispara um agente e opcionalmente aguarda o resultado.

        Args:
            agent_id: ID ou slug do agente (ex: "youtube-topic-scout")
            inputs:   Parâmetros de entrada do agente
            wait:     Se True, faz polling até o agente terminar
            timeout:  Timeout máximo em segundos

        Returns:
            Dict com o resultado da execução (outputs, status, etc.)
        """
        payload = {"inputs": inputs, "agent_id": agent_id}
        try:
            resp = self._post("/executions", payload)
        except requests.HTTPError as e:
            # Alternativa: alguns sistemas usam /runs ou /agents/{id}/run
            try:
                resp = self._post(f"/agents/{agent_id}/run", {"inputs": inputs})
            except Exception:
                raise CREAOError(f"Erro ao disparar agente '{agent_id}': {e}") from e

        execution_id = resp.get("execution_id") or resp.get("id") or resp.get("run_id")
        if not execution_id:
            logger.warning("Resposta de execução sem ID: %s", resp)
            return resp

        logger.info("Execução iniciada: %s (id=%s)", agent_id, execution_id)

        if not wait:
            return {"execution_id": execution_id, "status": "running", "raw": resp}

        return self.wait_for_result(execution_id, timeout=timeout)

    def wait_for_result(self, execution_id: str, timeout: int = POLL_TIMEOUT) -> dict:
        """
        Polling de uma execução até conclusão ou timeout.

        Estados terminais esperados: completed, failed, error, done, success
        """
        deadline = time.time() + timeout
        terminal = {"completed", "failed", "error", "done", "success", "cancelled"}

        while time.time() < deadline:
            try:
                status = self._get(f"/executions/{execution_id}")
            except requests.HTTPError:
                status = self._get(f"/runs/{execution_id}")

            state = (
                status.get("status") or
                status.get("state") or
                status.get("execution_status", "")
            ).lower()

            logger.info("Execução %s: %s", execution_id, state)

            if state in terminal:
                if state in {"failed", "error"}:
                    raise CREAOError(
                        f"Execução falhou: {status.get('error') or status.get('message', state)}"
                    )
                return status

            time.sleep(POLL_INTERVAL)

        raise CREAOError(f"Timeout ({timeout}s) aguardando execução {execution_id}")

    def get_execution(self, execution_id: str) -> dict:
        """Retorna o status/resultado de uma execução pelo ID."""
        return self._get(f"/executions/{execution_id}")

    # ─────────────────────────────────────────────────────────────────────
    # Helpers específicos CineForge
    # ─────────────────────────────────────────────────────────────────────

    def scout_youtube_topics(
        self,
        niche: str,
        language: str = "pt-BR",
        max_results: int = 10,
    ) -> list[dict]:
        """
        Usa o agente "YouTube Topic Scout & Script Writer" do CREAO
        para pesquisar tópicos virais num nicho.

        Args:
            niche:       Nicho alvo (ex: "finanças pessoais", "fitness")
            language:    Idioma dos resultados
            max_results: Número máximo de tópicos

        Returns:
            Lista de dicts: [{title, search_volume, competition, script_outline}]
        """
        result = self.run_agent(
            "youtube-topic-scout",   # confirme o ID real no painel CREAO
            inputs={
                "niche": niche,
                "language": language,
                "max_results": max_results,
                "connectors": ["youtube", "google_search_console", "semrush"],
            },
        )

        outputs = result.get("outputs") or result.get("data") or result.get("result") or {}
        topics  = outputs.get("topics") or outputs.get("results") or []

        if not topics:
            logger.warning("Nenhum tópico retornado para nicho '%s'", niche)

        return topics

    def reproduce_thumbnail(
        self,
        reference_url: str,
        title: str,
        output_style: str = "cinematic",
    ) -> dict:
        """
        Usa o agente "Thumbnail Reproducer" do CREAO para replicar
        o estilo visual de uma thumbnail existente.

        Args:
            reference_url: URL da thumbnail de referência
            title:         Texto a exibir na nova thumbnail
            output_style:  Estilo de renderização

        Returns:
            Dict com URL da thumbnail gerada e metadados
        """
        result = self.run_agent(
            "thumbnail-reproducer",  # confirme o ID real no painel CREAO
            inputs={
                "reference_url": reference_url,
                "title": title,
                "style": output_style,
            },
        )

        outputs = result.get("outputs") or result.get("data") or {}
        return {
            "image_url": outputs.get("image_url") or outputs.get("url"),
            "execution_id": result.get("execution_id") or result.get("id"),
            "raw": outputs,
        }

    def notify_telegram(
        self,
        message: str,
        chat_id: Optional[str] = None,
    ) -> dict:
        """
        Envia notificação via conector Telegram do CREAO.
        Útil para alertas do pipeline CineForge.
        """
        return self.run_agent(
            "telegram-notify",       # confirme o ID real no painel CREAO
            inputs={
                "message": message,
                "chat_id": chat_id,
            },
        )


# ─────────────────────────────────────────────────────────────────────────────
# Integração com o pipeline CineForge
# ─────────────────────────────────────────────────────────────────────────────

class CineForgeCreaoOrchestrator:
    """
    Orquestrador de alto nível que conecta o CREAO ao pipeline CineForge.

    Fluxo:
    1. CREAO scout YouTube → lista de tópicos virais
    2. CineForge gera roteiro (LLM local ou Agnes)
    3. CineForge produz vídeo (TTS + imagens + vídeo)
    4. CineForge faz upload para YouTube
    5. CREAO notifica Telegram com resultado
    """

    def __init__(self, creao_client: Optional[CREAOClient] = None):
        self.creao = creao_client or CREAOClient()

    def research_and_queue(
        self,
        niche: str,
        max_videos: int = 5,
        language: str = "pt-BR",
    ) -> list[dict]:
        """
        Pesquisa tópicos no CREAO e retorna fila de vídeos para produção.

        Args:
            niche:      Nicho do canal (ex: "finanças pessoais")
            max_videos: Máximo de vídeos a encaminhar para produção
            language:   Idioma

        Returns:
            Lista de dicts prontos para o pipeline CineForge:
            [{title, script_outline, thumbnail_ref, priority}]
        """
        logger.info("Pesquisando tópicos via CREAO para nicho: %s", niche)

        topics = self.creao.scout_youtube_topics(
            niche=niche,
            language=language,
            max_results=max_videos * 2,  # busca o dobro para ter margem de filtro
        )

        # Ordena por volume de busca (maior primeiro) e recorta
        topics_sorted = sorted(
            topics,
            key=lambda t: t.get("search_volume", 0),
            reverse=True,
        )[:max_videos]

        queue = []
        for i, topic in enumerate(topics_sorted):
            queue.append({
                "title":          topic.get("title", f"Vídeo {i+1}"),
                "script_outline": topic.get("script_outline") or topic.get("outline", ""),
                "keywords":       topic.get("keywords", []),
                "search_volume":  topic.get("search_volume", 0),
                "competition":    topic.get("competition", "medium"),
                "thumbnail_ref":  topic.get("thumbnail_reference_url"),
                "priority":       i + 1,
                "niche":          niche,
                "language":       language,
                "source":         "creao_youtube_scout",
            })

        logger.info("%d tópicos enfileirados para produção", len(queue))
        return queue

    def pipeline_complete_notify(
        self,
        video_title: str,
        youtube_url: str,
        stats: dict,
    ) -> None:
        """Notifica via Telegram quando um vídeo completa o pipeline."""
        msg = (
            f"✅ *CineForge Pipeline Concluído*\n\n"
            f"📹 {video_title}\n"
            f"🔗 {youtube_url}\n"
            f"⏱ Tempo: {stats.get('duration_seconds', '?')}s\n"
            f"💾 Tamanho: {stats.get('file_size_mb', '?')} MB"
        )
        try:
            self.creao.notify_telegram(msg)
        except Exception as e:
            logger.warning("Notificação Telegram falhou: %s", e)


# ─────────────────────────────────────────────────────────────────────────────
# CLI de teste
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")

    parser = argparse.ArgumentParser(description="CREAO Integration CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("ping",         help="Testar conectividade com a API")
    sub.add_parser("list-agents",  help="Listar agentes disponíveis")

    scout = sub.add_parser("scout", help="Pesquisar tópicos YouTube num nicho")
    scout.add_argument("niche",                       help="Nicho alvo (ex: 'finanças pessoais')")
    scout.add_argument("--max",   type=int, default=5, help="Máximo de tópicos")
    scout.add_argument("--lang",  default="pt-BR",    help="Idioma")

    args = parser.parse_args()
    client = CREAOClient()

    if args.cmd == "ping":
        ok = client.ping()
        print("✅ API conectada" if ok else "❌ Falha na conexão")

    elif args.cmd == "list-agents":
        agents = client.list_agents()
        if agents:
            for a in agents:
                print(f"  {a.get('id','?'):30s} │ {a.get('name','?')}")
        else:
            print("Nenhum agente encontrado (verifique endpoint e API Key)")

    elif args.cmd == "scout":
        orch   = CineForgeCreaoOrchestrator(client)
        queue  = orch.research_and_queue(args.niche, args.max, args.lang)
        print(json.dumps(queue, ensure_ascii=False, indent=2))

    else:
        parser.print_help()
