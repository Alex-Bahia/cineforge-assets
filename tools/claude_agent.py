"""
CineForge ── Agente Claude (Anthropic API)
Integração direta com Claude para roteiros, pesquisa e otimização de conteúdo.

Configure ANTHROPIC_API_KEY no .env.
Documentação: https://docs.anthropic.com/en/api

Uso rápido:
    from tools.claude_agent import CineForgeAgent
    agent = CineForgeAgent()
    script = agent.gerar_roteiro("Como sair das dívidas em 2025", estilo="educativo")
    nichos  = agent.pesquisar_nichos("finanças", top_n=10)
"""

import os
import json
import logging
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────────────────────

MODEL   = os.getenv("CLAUDE_MODEL",       "claude-sonnet-4-6")
MAX_TOK = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))


# ─────────────────────────────────────────────────────────────────────────────
# Prompts do sistema por papel
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_ROTEIRISTA = """
Você é um roteirista especialista em vídeos curtos para YouTube em português do Brasil.
Cria roteiros otimizados para retenção máxima: gancho forte nos primeiros 3 segundos,
ritmo acelerado, chamada para ação no final. Usa linguagem direta, acessível e envolvente.
Formato de saída: JSON estruturado com seções do vídeo.
""".strip()

SYSTEM_PESQUISADOR = """
Você é um analista de tendências e oportunidades de nicho para canais do YouTube Brasil.
Avalia volume de busca, competição, potencial de monetização e tendência de crescimento.
Usa dados reais e fornece análises objetivas com pontuações numéricas.
Formato de saída: JSON com lista de nichos ordenados por oportunidade.
""".strip()

SYSTEM_SEO = """
Você é especialista em SEO para YouTube Brasil. Cria títulos altamente clicáveis,
descrições ricas em palavras-chave e tags otimizadas para o algoritmo do YouTube.
Conhece os padrões de busca do público brasileiro. Formato de saída: JSON.
""".strip()

SYSTEM_ANALISTA = """
Você é um analista de negócios digital especializado em canais YouTube monetizados.
Avalia métricas, identifica padrões de sucesso e sugere estratégias baseadas em dados.
Responde de forma objetiva e acionável. Formato de saída: JSON ou markdown estruturado.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# Cliente
# ─────────────────────────────────────────────────────────────────────────────

class CineForgeAgent:
    """
    Agente Claude integrado ao pipeline CineForge.

    Capacidades:
    - Geração de roteiros otimizados para YouTube
    - Pesquisa e análise de nichos
    - Otimização de SEO (título, descrição, tags)
    - Análise de desempenho e sugestões estratégicas
    - Chat livre para qualquer tarefa criativa
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = MODEL,
        max_tokens: int = MAX_TOK,
    ):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model      = model
        self.max_tokens = max_tokens

    # ─────────────────────────────────────────────────────────────────────
    # Método base
    # ─────────────────────────────────────────────────────────────────────

    def _chat(
        self,
        system: str,
        prompt: str,
        as_json: bool = False,
    ) -> str | dict:
        """Envia uma mensagem ao Claude e retorna a resposta."""
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text

        if as_json:
            # Extrai JSON da resposta (que pode vir dentro de markdown ```json ```)
            try:
                start = text.find("{") if "{" in text else text.find("[")
                end   = text.rfind("}") + 1 if "{" in text else text.rfind("]") + 1
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("Resposta não é JSON válido; retornando texto")
                return {"raw": text}

        return text

    # ─────────────────────────────────────────────────────────────────────
    # Roteirização
    # ─────────────────────────────────────────────────────────────────────

    def gerar_roteiro(
        self,
        titulo: str,
        estilo: str = "educativo",
        duracao_min: int = 8,
        publico: str = "brasileiros interessados no tema",
    ) -> dict:
        """
        Gera um roteiro completo para um vídeo YouTube.

        Args:
            titulo:     Título ou tema do vídeo
            estilo:     "educativo" | "entretenimento" | "motivacional" | "tutorial"
            duracao_min: Duração alvo em minutos
            publico:    Descrição do público-alvo

        Returns:
            {
              "titulo_final": str,
              "duracao_estimada": str,
              "gancho": str,           # primeiros 3 segundos
              "introducao": str,
              "desenvolvimento": [     # lista de seções
                {"titulo": str, "conteudo": str, "duracao_seg": int}
              ],
              "conclusao": str,
              "cta": str,              # chamada para ação
              "palavras_chave": list,
              "thumbnail_conceito": str
            }
        """
        prompt = f"""
Crie um roteiro completo para um vídeo YouTube de {duracao_min} minutos.

Título/Tema: {titulo}
Estilo: {estilo}
Público-alvo: {publico}

Retorne JSON com esta estrutura exata:
{{
  "titulo_final": "título otimizado para YouTube",
  "duracao_estimada": "{duracao_min}-{duracao_min+2} minutos",
  "gancho": "frase poderosa para os primeiros 3 segundos",
  "introducao": "parágrafo de abertura (30 segundos)",
  "desenvolvimento": [
    {{"titulo": "Seção 1", "conteudo": "...", "duracao_seg": 90}},
    {{"titulo": "Seção 2", "conteudo": "...", "duracao_seg": 90}}
  ],
  "conclusao": "resumo e fechamento",
  "cta": "chamada para ação (inscrição/like/comentário)",
  "palavras_chave": ["kw1", "kw2", "kw3"],
  "thumbnail_conceito": "descrição visual da thumbnail ideal"
}}
"""
        result = self._chat(SYSTEM_ROTEIRISTA, prompt, as_json=True)
        logger.info("Roteiro gerado para: %s", titulo)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # Pesquisa de nichos
    # ─────────────────────────────────────────────────────────────────────

    def pesquisar_nichos(
        self,
        categoria: str,
        top_n: int = 10,
        foco: str = "monetização e crescimento",
    ) -> list[dict]:
        """
        Identifica os melhores sub-nichos dentro de uma categoria.

        Args:
            categoria: Categoria principal (ex: "finanças", "saúde", "tecnologia")
            top_n:     Número de nichos a retornar
            foco:      Critério principal de avaliação

        Returns:
            Lista de dicts:
            [{
              "nicho": str,
              "pontuacao": int,          # 0-100
              "volume_busca": str,       # "alto" | "médio" | "baixo"
              "competicao": str,         # "alta" | "média" | "baixa"
              "cpm_estimado": str,       # faixa de CPM em USD
              "tendencia": str,          # "crescendo" | "estável" | "caindo"
              "exemplo_titulo": str,
              "publico": str
            }]
        """
        prompt = f"""
Análise de nichos para YouTube Brasil — categoria: {categoria}
Foco: {foco}
Retorne os {top_n} melhores sub-nichos.

JSON:
{{
  "nichos": [
    {{
      "nicho": "nome do sub-nicho",
      "pontuacao": 85,
      "volume_busca": "alto",
      "competicao": "média",
      "cpm_estimado": "$3-8",
      "tendencia": "crescendo",
      "exemplo_titulo": "título atraente de exemplo",
      "publico": "quem assiste esse conteúdo"
    }}
  ]
}}
"""
        result = self._chat(SYSTEM_PESQUISADOR, prompt, as_json=True)
        nichos = result.get("nichos", result if isinstance(result, list) else [])
        logger.info("%d nichos pesquisados para categoria: %s", len(nichos), categoria)
        return nichos

    # ─────────────────────────────────────────────────────────────────────
    # SEO
    # ─────────────────────────────────────────────────────────────────────

    def otimizar_seo(
        self,
        tema: str,
        roteiro_resumo: str = "",
        canal: str = "canal educativo brasileiro",
    ) -> dict:
        """
        Gera título, descrição e tags otimizados para YouTube SEO.

        Returns:
            {
              "titulos": [str, str, str],   # 3 opções rankeadas
              "titulo_recomendado": str,
              "descricao": str,             # 2500 chars com timestamps
              "tags": [str, ...],           # 15-20 tags
              "thumbnail_texto": str,       # texto curto para a thumbnail
              "categoria_yt": str,
              "idioma": "pt-BR"
            }
        """
        prompt = f"""
Otimize SEO para YouTube Brasil.

Tema: {tema}
Canal: {canal}
{f"Resumo do conteúdo: {roteiro_resumo}" if roteiro_resumo else ""}

Retorne JSON:
{{
  "titulos": ["opção 1", "opção 2", "opção 3"],
  "titulo_recomendado": "melhor opção",
  "descricao": "descrição completa com timestamps e CTAs (até 2500 chars)",
  "tags": ["tag1", "tag2", "..."],
  "thumbnail_texto": "texto curto e impactante para a imagem",
  "categoria_yt": "Educação",
  "idioma": "pt-BR"
}}
"""
        result = self._chat(SYSTEM_SEO, prompt, as_json=True)
        logger.info("SEO otimizado para: %s", tema)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # Análise estratégica
    # ─────────────────────────────────────────────────────────────────────

    def analisar_canal(
        self,
        dados_canal: dict,
        pergunta: str = "Como crescer mais rápido?",
    ) -> str:
        """
        Analisa métricas de canal e responde perguntas estratégicas.

        Args:
            dados_canal: Dict com métricas (views, inscritos, CPM, etc.)
            pergunta:    Pergunta específica sobre o canal

        Returns:
            Análise em markdown com recomendações acionáveis
        """
        prompt = f"""
Analise os dados deste canal YouTube e responda a pergunta.

Dados do canal:
{json.dumps(dados_canal, ensure_ascii=False, indent=2)}

Pergunta: {pergunta}

Responda com análise objetiva, 3-5 recomendações práticas e prioridades claras.
"""
        return self._chat(SYSTEM_ANALISTA, prompt, as_json=False)

    # ─────────────────────────────────────────────────────────────────────
    # Chat livre
    # ─────────────────────────────────────────────────────────────────────

    def chat(
        self,
        mensagem: str,
        contexto: str = "Assistente especializado em criação de conteúdo para YouTube Brasil.",
    ) -> str:
        """Chat livre com Claude para qualquer tarefa do pipeline CineForge."""
        return self._chat(contexto, mensagem, as_json=False)

    # ─────────────────────────────────────────────────────────────────────
    # Pipeline completo: tema → roteiro → SEO
    # ─────────────────────────────────────────────────────────────────────

    def pipeline_completo(
        self,
        tema: str,
        estilo: str = "educativo",
        duracao_min: int = 8,
    ) -> dict:
        """
        Executa o pipeline completo: roteiro + SEO em uma só chamada.

        Returns:
            {
              "roteiro": dict,
              "seo": dict,
              "tema": str,
              "pronto_para_producao": bool
            }
        """
        logger.info("Pipeline completo iniciado para: %s", tema)

        roteiro = self.gerar_roteiro(tema, estilo=estilo, duracao_min=duracao_min)

        resumo = roteiro.get("introducao", "")[:300] if isinstance(roteiro, dict) else ""
        seo    = self.otimizar_seo(tema, roteiro_resumo=resumo)

        return {
            "tema":                  tema,
            "roteiro":               roteiro,
            "seo":                   seo,
            "pronto_para_producao":  bool(roteiro and seo),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI de teste
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")

    parser = argparse.ArgumentParser(description="CineForge Claude Agent CLI")
    sub    = parser.add_subparsers(dest="cmd")

    # roteiro
    r = sub.add_parser("roteiro", help="Gerar roteiro para um vídeo")
    r.add_argument("titulo")
    r.add_argument("--estilo",  default="educativo")
    r.add_argument("--duracao", type=int, default=8)

    # nichos
    n = sub.add_parser("nichos", help="Pesquisar nichos numa categoria")
    n.add_argument("categoria")
    n.add_argument("--top", type=int, default=10)

    # seo
    s = sub.add_parser("seo", help="Otimizar SEO de um tema")
    s.add_argument("tema")

    # pipeline
    p = sub.add_parser("pipeline", help="Roteiro + SEO completo")
    p.add_argument("tema")
    p.add_argument("--estilo",  default="educativo")
    p.add_argument("--duracao", type=int, default=8)

    # chat
    c = sub.add_parser("chat", help="Chat livre com Claude")
    c.add_argument("mensagem")

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
    else:
        agent = CineForgeAgent()

        if args.cmd == "roteiro":
            result = agent.gerar_roteiro(args.titulo, args.estilo, args.duracao)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.cmd == "nichos":
            result = agent.pesquisar_nichos(args.categoria, args.top)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.cmd == "seo":
            result = agent.otimizar_seo(args.tema)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.cmd == "pipeline":
            result = agent.pipeline_completo(args.tema, args.estilo, args.duracao)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.cmd == "chat":
            print(agent.chat(args.mensagem))
