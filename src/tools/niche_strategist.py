"""
NicheStrategist — motor de pesquisa, validação e estratégia de nicho para canais YouTube.

Implementa o framework completo de 4 fases identificado via pesquisa:
  Fase 1: Mapeamento — Google Trends, YouTube autocomplete, AnswerThePublic
  Fase 2: Validação — Análise de outliers, saturação, CPM/RPM estimado
  Fase 3: Produção — Guidelines de hook, SEO técnico, thumbnail, ritmo
  Fase 4: Análise — CTR alvo, Watch Time, relatório de auditoria

Nichos de alto CPM (dados 2025-2026):
  finance/negócios → $15-40 CPM
  tech/SaaS        → $12-35 CPM
  saúde/bem-estar  → $10-25 CPM
  educação         → $8-20 CPM
  e-commerce       → $10-22 CPM
  kids (PT-BR)     → $3-8 CPM (volume compensa)
"""
import json
import logging
import time
import urllib.request
import urllib.parse
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

STRATEGY_BASE = Path("batch/niche_strategy")

# CPM médio estimado por nicho (USD por 1000 impressões) — dados outubro 2026
NICHE_CPM_ESTIMATES = {
    "finance": {"cpm_low": 15, "cpm_high": 40, "rpm_avg": 8},
    "finance_dark": {"cpm_low": 12, "cpm_high": 30, "rpm_avg": 6},
    "business": {"cpm_low": 14, "cpm_high": 35, "rpm_avg": 7},
    "tech": {"cpm_low": 12, "cpm_high": 35, "rpm_avg": 6},
    "health": {"cpm_low": 10, "cpm_high": 25, "rpm_avg": 5},
    "education": {"cpm_low": 8, "cpm_high": 20, "rpm_avg": 4},
    "ecommerce": {"cpm_low": 10, "cpm_high": 22, "rpm_avg": 5},
    "dark": {"cpm_low": 5, "cpm_high": 15, "rpm_avg": 3},
    "kids": {"cpm_low": 3, "cpm_high": 8, "rpm_avg": 2},
    "entertainment": {"cpm_low": 2, "cpm_high": 8, "rpm_avg": 1.5},
}

# CPM por mercado geográfico (multiplicadores)
MARKET_CPM_MULTIPLIERS = {
    "US": 3.0,
    "UK": 2.5,
    "CA": 2.3,
    "AU": 2.2,
    "DE": 2.0,
    "FR": 1.8,
    "BR": 1.0,  # base
    "MX": 0.8,
    "IN": 0.5,
}

# Canais de referência por nicho para análise de outliers
REFERENCE_CHANNELS = {
    "finance_dark": [
        "https://www.youtube.com/@FinancialEducation",
        "https://www.youtube.com/@grahamstephan",
    ],
    "dark": [
        "https://www.youtube.com/@Kurzgesagt",
    ],
    "kids": [
        "https://www.youtube.com/@Cocomelon",
        "https://www.youtube.com/@ChuChuTV",
    ],
    "tech": [
        "https://www.youtube.com/@MKBHD",
        "https://www.youtube.com/@Fireship",
    ],
    "education": [
        "https://www.youtube.com/@TED",
        "https://www.youtube.com/@crashcourse",
    ],
}


@dataclass
class NicheOpportunity:
    niche: str
    keyword: str
    search_volume_score: float = 0.0     # 0-100 (relativo)
    competition_score: float = 0.0       # 0-100 (maior = mais competitivo)
    opportunity_score: float = 0.0       # 0-100 (volume - competição + CPM)
    cpm_estimate_usd: float = 0.0
    market: str = "BR"
    has_outlier_channels: bool = False
    outlier_evidence: str = ""
    monetization_options: list = field(default_factory=list)
    barrier_score: float = 0.5           # 0=fácil, 1=muito difícil
    recommendation: str = ""
    analyzed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChannelAuditResult:
    """Resultado de auditoria de desempenho via YouTube Analytics simulado."""
    channel_id: str
    audit_date: str
    ctr_estimate: float = 0.0           # % de CTR atual estimado
    ctr_target: float = 7.0             # % alvo (>6-7%)
    avg_view_duration_pct: float = 0.0  # % de retenção média
    hook_retention_15s: float = 0.0     # % que ficam nos primeiros 15s
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    priority_actions: list = field(default_factory=list)


class NicheStrategist:
    """
    Implementa o framework completo de pesquisa, validação e estratégia de nicho.
    """

    def __init__(self):
        STRATEGY_BASE.mkdir(parents=True, exist_ok=True)

    # ─── FASE 1: MAPEAMENTO ────────────────────────────────────────────────

    def get_youtube_autocomplete(self, query: str, market: str = "BR") -> list[str]:
        """
        Busca sugestões de autocomplete do YouTube para descoberta de palavras-chave.
        Simula abrir aba anônima e digitar no YouTube.
        """
        suggestions = []
        hl = "pt-BR" if market == "BR" else "en"

        try:
            params = urllib.parse.urlencode({
                "client": "youtube",
                "q": query,
                "hl": hl,
                "ds": "yt",
            })
            url = f"https://suggestqueries.google.com/complete/search?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list) and len(data) > 1:
                    raw = data[1]
                    suggestions = [item[0] if isinstance(item, list) else str(item) for item in raw[:15]]
        except Exception as exc:
            log.debug("NicheStrategist: autocomplete falhou para '%s': %s", query, exc)
            # Fallback: variações padrão por nicho
            suggestions = [
                f"{query} para iniciantes",
                f"{query} como funciona",
                f"{query} passo a passo",
                f"como ganhar dinheiro com {query}",
                f"{query} 2026",
                f"melhor {query}",
                f"{query} brasil",
                f"{query} tutorial",
            ]

        return suggestions

    def get_google_trends_keywords(self, keywords: list[str], market: str = "BR") -> dict:
        """
        Verifica tendência de keywords via Google Trends pytrends (se disponível).
        Retorna scores relativos de interesse.
        """
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl="pt-BR" if market == "BR" else "en-US", tz=360)
            pytrends.build_payload(keywords[:5], timeframe="today 12-m", geo=market)
            df = pytrends.interest_over_time()
            if not df.empty:
                avg_scores = {}
                for kw in keywords[:5]:
                    if kw in df.columns:
                        avg_scores[kw] = float(df[kw].mean())
                return avg_scores
        except ImportError:
            log.debug("NicheStrategist: pytrends não instalado — usando estimativas")
        except Exception as exc:
            log.debug("NicheStrategist: Google Trends falhou: %s", exc)

        # Fallback: retornar scores neutros
        return {kw: 50.0 for kw in keywords}

    def research_keyword_questions(self, keyword: str) -> list[str]:
        """
        Gera perguntas reais do público baseadas na keyword.
        Simula AnswerThePublic/Ubersuggest.
        """
        prefixes = [
            "como", "por que", "o que é", "qual é o melhor",
            "quando", "onde", "quem", "quanto custa",
        ]
        suffixes = [
            "para iniciantes", "passo a passo", "funciona", "é bom",
            "vale a pena", "em 2026", "sem gastar dinheiro", "rápido",
        ]
        questions = []
        for prefix in prefixes[:5]:
            questions.append(f"{prefix} {keyword}")
        for suffix in suffixes[:5]:
            questions.append(f"{keyword} {suffix}")
        return questions

    # ─── FASE 2: VALIDAÇÃO ────────────────────────────────────────────────

    def estimate_competition_saturation(
        self, keyword: str, niche: str
    ) -> dict:
        """
        Analisa saturação do nicho baseado em critérios qualitativos.
        Em produção, integraria com YouTube Data API ou VidIQ API.
        """
        # Heurística baseada no tamanho do nicho e keyword
        niche_saturation = {
            "finance": 75,
            "finance_dark": 55,
            "tech": 80,
            "kids": 70,
            "dark": 45,
            "education": 65,
            "health": 72,
            "ecommerce": 60,
        }
        base_sat = niche_saturation.get(niche, 60)
        # Keywords mais longas = menos saturação
        keyword_length_bonus = max(0, (len(keyword.split()) - 1) * 5)
        saturation = max(10, base_sat - keyword_length_bonus)

        return {
            "saturation_score": saturation,
            "interpretation": (
                "Alta saturação — difícil entrar" if saturation > 70
                else "Saturação moderada — oportunidade com diferenciação" if saturation > 40
                else "Baixa saturação — boa oportunidade de entrada"
            ),
            "weak_competition_signals": [
                "Vídeos antigos (>2 anos) dominam o topo da busca",
                "Canais concorrentes com execução fraca (baixa produção)",
                "Resultados de blogs/sites nos primeiros resultados YouTube",
            ] if saturation < 50 else [],
        }

    def check_monetization_options(self, niche: str) -> list[str]:
        """Retorna opções de monetização além do AdSense para o nicho."""
        options_by_niche = {
            "finance": [
                "Afiliados de corretoras (XP, Clear, Rico) — R$50-200 por conta aberta",
                "Afiliados de cartões de crédito — R$20-80 por aprovação",
                "Cursos de finanças/investimento — R$200-2000 por venda",
                "Patrocínios de fintechs",
            ],
            "finance_dark": [
                "Afiliados de proteção financeira, seguros",
                "Afiliados de consultoria financeira",
                "Canal de membros (conteúdo exclusivo de alertas)",
            ],
            "dark": [
                "Canal de membros YouTube",
                "Merchandise/merch",
                "Cursos de investigação/pesquisa",
                "Patreon",
            ],
            "kids": [
                "Merchandise (bonecos, roupas, mochilas)",
                "Patrocínios de brinquedos/apps infantis",
                "Licenciamento de personagens",
                "Cursos de educação infantil para pais",
            ],
            "tech": [
                "Afiliados Amazon (dispositivos, gadgets)",
                "Afiliados de software/SaaS (Notion, Figma, Adobe)",
                "Patrocínios de hosting/domínios",
                "Cursos técnicos",
            ],
            "education": [
                "Cursos próprios/infoprodutos",
                "Afiliados Hotmart/Eduzz (outros cursos)",
                "Mentorias",
                "Material digital (e-books, templates)",
            ],
        }
        return options_by_niche.get(niche, ["Canal de membros", "Patrocínios", "Afiliados"])

    def calculate_opportunity_score(
        self,
        niche: str,
        keyword: str,
        market: str = "BR",
        search_volume_score: float = 50.0,
        saturation_score: float = 50.0,
    ) -> float:
        """
        Score de oportunidade ponderado: volume + CPM + mercado - saturação.
        """
        cpm_data = NICHE_CPM_ESTIMATES.get(niche, NICHE_CPM_ESTIMATES["dark"])
        cpm_avg = (cpm_data["cpm_low"] + cpm_data["cpm_high"]) / 2
        cpm_normalized = min(100, cpm_avg * 2.5)  # normalizar 0-100

        market_mult = MARKET_CPM_MULTIPLIERS.get(market, 1.0)
        market_bonus = (market_mult - 1.0) * 20  # bonus por mercado rico

        # Fórmula: 40% volume + 30% CPM - 20% saturação + 10% mercado
        score = (
            0.40 * search_volume_score
            + 0.30 * cpm_normalized
            - 0.20 * saturation_score
            + 0.10 * (50 + market_bonus)
        )
        return round(max(0, min(100, score)), 1)

    def validate_niche_opportunity(
        self,
        niche: str,
        keyword: str,
        market: str = "BR",
    ) -> NicheOpportunity:
        """
        Validação completa de uma oportunidade de nicho conforme o framework de 4 fases.
        """
        # Saturação
        sat_data = self.estimate_competition_saturation(keyword, niche)
        saturation_score = sat_data["saturation_score"]

        # Volume (via autocomplete como proxy)
        suggestions = self.get_youtube_autocomplete(keyword, market)
        search_volume_score = min(100, len(suggestions) * 7.0)

        # Tendências
        trend_scores = self.get_google_trends_keywords([keyword], market)
        trend_score = trend_scores.get(keyword, 50.0)
        search_volume_score = (search_volume_score + trend_score) / 2

        # Score final
        opp_score = self.calculate_opportunity_score(
            niche=niche,
            keyword=keyword,
            market=market,
            search_volume_score=search_volume_score,
            saturation_score=saturation_score,
        )

        # CPM estimado
        cpm_data = NICHE_CPM_ESTIMATES.get(niche, NICHE_CPM_ESTIMATES["dark"])
        market_mult = MARKET_CPM_MULTIPLIERS.get(market, 1.0)
        cpm_estimate = ((cpm_data["cpm_low"] + cpm_data["cpm_high"]) / 2) * market_mult

        # Opções de monetização
        monetization = self.check_monetization_options(niche)

        # Barreira de entrada por nicho
        barrier_scores = {
            "finance": 0.7, "finance_dark": 0.5, "tech": 0.7,
            "kids": 0.6, "dark": 0.4, "education": 0.6,
        }
        barrier = barrier_scores.get(niche, 0.5)

        # Recomendação
        if opp_score >= 70:
            rec = "✅ ALTA OPORTUNIDADE — entrar agora com diferenciação clara"
        elif opp_score >= 50:
            rec = "🟡 OPORTUNIDADE MODERADA — viável com nicho específico dentro do tema"
        else:
            rec = "🔴 BAIXA OPORTUNIDADE — saturado ou CPM baixo demais para escala"

        opportunity = NicheOpportunity(
            niche=niche,
            keyword=keyword,
            search_volume_score=search_volume_score,
            competition_score=saturation_score,
            opportunity_score=opp_score,
            cpm_estimate_usd=round(cpm_estimate, 2),
            market=market,
            has_outlier_channels=saturation_score < 50,
            outlier_evidence=sat_data.get("interpretation", ""),
            monetization_options=monetization,
            barrier_score=barrier,
            recommendation=rec,
        )

        return opportunity

    # ─── FASE 3: PRODUÇÃO — GUIDELINES ───────────────────────────────────

    def get_algorithm_guidelines(self, niche: str, video_duration_min: int = 10) -> dict:
        """
        Retorna diretrizes técnicas para otimização do algoritmo YouTube.
        Baseado nos dados de pesquisa do NotebookLM.
        """
        return {
            "ctr_target": "6-7% mínimo",
            "thumbnail": {
                "colors": "cores contrastantes e saturadas — evitar paletas neutras",
                "emotion": "expressões faciais de choque, curiosidade ou alegria extrema",
                "text": "máximo 3-4 palavras, complementar o título sem repetir",
                "elements": "elemento marcante e único que se destaca no feed",
            },
            "title": {
                "length": "50-70 caracteres (exibição completa em mobile)",
                "strategy": "curiosidade ou urgência — não revelar a conclusão",
                "keyword": "palavra-chave principal nas primeiras 3 palavras",
                "formats": [
                    "Por que [X] está [fazendo algo inesperado]",
                    "O que ninguém te conta sobre [X]",
                    "Como [resultado desejado] em [tempo/método específico]",
                    "A verdade sobre [X] que [autoridade] esconde",
                ],
            },
            "hook_15s": {
                "rule": "ZERO vinheta — começa direto no problema ou promessa",
                "elements": [
                    "Entregar elemento visual impactante imediatamente",
                    "Fazer promessa específica do que o espectador vai aprender",
                    "Pergunta instigante respondida APENAS no final",
                    "Palavra-chave principal falada verbalmente nos primeiros 10s",
                ],
            },
            "video_structure": {
                "duration": f"{video_duration_min} min (mid-rolls exigem >8 min)",
                "mid_rolls": "inserir a cada 3-4 minutos se vídeo >8 min",
                "cta_position": "aos 70-80% do vídeo + final",
                "cta_format": "sugerir próximo vídeo do canal para maximizar sessão",
            },
            "seo_technical": {
                "description": "palavra-chave principal nas primeiras 2 frases da descrição",
                "tags": "1ª tag = palavra-chave exata, depois variações long-tail",
                "spoken_keyword": "falar a keyword nos primeiros 15s (IA do YouTube transcreve)",
                "chapters": "timestamps de capítulos aumentam tempo de exibição médio",
            },
            "shorts_strategy": "usar Shorts como topo de funil — recorte de 45-60s do melhor momento do vídeo longo",
            "posting_schedule": f"2-3 vídeos/semana consistentes, mesmo horário → sinaliza qualidade para algoritmo",
        }

    def generate_video_brief(
        self,
        topic: str,
        niche: str,
        keyword: str,
        market: str = "BR",
        duration_min: int = 10,
    ) -> dict:
        """
        Gera briefing completo de produção para um vídeo: título, hook, descrição, tags.
        """
        guidelines = self.get_algorithm_guidelines(niche, duration_min)
        opp = self.validate_niche_opportunity(niche, keyword, market)
        questions = self.research_keyword_questions(keyword)
        autocomplete = self.get_youtube_autocomplete(keyword, market)

        title_ideas = [
            f"Por que {topic} está mudando tudo em 2026",
            f"A verdade sobre {topic} que ninguém fala",
            f"Como {topic} pode te custar caro (e como evitar)",
            f"{topic}: o que os especialistas fazem diferente",
            f"Erros fatais em {topic} que você provavelmente comete",
        ]

        description_template = f"""{topic} — o que você precisa saber antes de 2027.

Neste vídeo você vai descobrir os principais pontos sobre {topic}, incluindo {', '.join(questions[:3])}.

🔔 Inscreva-se para mais conteúdo sobre {niche.replace('_', ' ')}.

━━━━━━━━━━━━━━━━━━━━━
⏱️ Timestamps:
00:00 — Introdução
01:30 — Ponto 1
03:00 — Ponto 2
...

━━━━━━━━━━━━━━━━━━━━━
#{'#'.join(keyword.split()[:3])} #{niche.replace('_', '')} #youtube2026"""

        tags = list({keyword} | set(autocomplete[:8]) | {niche, topic[:20], "youtube 2026", "brasil"})
        tags = [t[:100] for t in tags[:30]]

        return {
            "topic": topic,
            "niche": niche,
            "keyword": keyword,
            "opportunity_score": opp.opportunity_score,
            "cpm_estimate_usd": opp.cpm_estimate_usd,
            "recommendation": opp.recommendation,
            "title_ideas": title_ideas,
            "hook_prompt": f"Nos primeiros 15 segundos: abrir com '{topic}' sendo citado verbalmente + elemento visual de impacto + pergunta instigante. SEM vinheta.",
            "description": description_template,
            "tags": tags,
            "thumbnail_brief": f"Elemento principal: {topic} | Emoção: choque/curiosidade | Cor dominante: vermelha/laranja | Texto: máximo 4 palavras",
            "duration_min": duration_min,
            "monetization_options": opp.monetization_options,
            "algorithm_guidelines": guidelines,
            "related_keywords": autocomplete[:10],
            "audience_questions": questions[:8],
        }

    # ─── FASE 4: ANÁLISE E AUDITORIA ─────────────────────────────────────

    def audit_ctr_performance(
        self,
        channel_id: str,
        ctr: float,
        avg_view_pct: float,
        niche: str = "dark",
    ) -> ChannelAuditResult:
        """
        Analisa performance de CTR e retenção com diagnóstico e recomendações.
        Baseado na matriz: CTR alto/baixo × Retenção alta/baixa.
        """
        result = ChannelAuditResult(
            channel_id=channel_id,
            audit_date=time.strftime("%Y-%m-%d"),
            ctr_estimate=ctr,
            avg_view_duration_pct=avg_view_pct,
        )

        # Diagnóstico matricial
        ctr_ok = ctr >= 6.0
        retention_ok = avg_view_pct >= 35.0

        if ctr_ok and retention_ok:
            result.issues = ["Nenhum problema crítico identificado"]
            result.recommendations = [
                "Manter consistência de publicação",
                "Testar formatos de Shorts para atrair novos públicos",
                "Expandir para sub-nichos relacionados",
            ]
        elif ctr_ok and not retention_ok:
            result.issues = [
                f"CTR bom ({ctr:.1f}%) mas retenção baixa ({avg_view_pct:.0f}%) — thumbnail/título promete mais do que entrega",
            ]
            result.recommendations = [
                "Revisar hook dos primeiros 15 segundos — eliminar toda vinheta",
                "Garantir que o vídeo entrega a promessa do título nos primeiros 30s",
                "Adicionar loop de curiosidade — perguntar no hook o que será revelado no final",
                "Reduzir introdução — ir direto ao conteúdo prometido",
            ]
            result.priority_actions = [
                "URGENTE: Regravar os primeiros 60s dos últimos 5 vídeos",
            ]
        elif not ctr_ok and retention_ok:
            result.issues = [
                f"Retenção boa ({avg_view_pct:.0f}%) mas CTR baixo ({ctr:.1f}%) — conteúdo é bom, packaging ruim",
            ]
            result.recommendations = [
                "A/B teste de thumbnails nos últimos 3 vídeos",
                "Adicionar elemento emocional forte na thumbnail (rosto com emoção extrema)",
                "Reescrever títulos — usar fórmulas de curiosidade/urgência",
                "Usar cores mais saturadas e contrastantes na thumbnail",
                "Testar thumbnails com texto bold de 2-3 palavras",
            ]
            result.priority_actions = [
                "AÇÃO: Trocar thumbnail dos top 10 vídeos por versão mais emocional",
                "Testar pelo menos 3 versões de título por vídeo",
            ]
        else:
            result.issues = [
                f"CTR baixo ({ctr:.1f}%) E retenção baixa ({avg_view_pct:.0f}%) — problema estrutural no conteúdo",
            ]
            result.recommendations = [
                "Rever completamente a estratégia de nicho e formatos",
                "Estudar os 5 canais mais bem-sucedidos do nicho em detalhe",
                "Produzir 5 vídeos teste com formatos completamente diferentes",
                "Considerar pivô para sub-nicho com menos concorrência",
            ]
            result.priority_actions = [
                "CRÍTICO: Pausar produção e reformular estratégia",
                "Baixar e analisar os 10 maiores hits do nicho via EditModeler",
            ]

        return result

    def generate_weekly_strategy_report(
        self,
        channels: list[dict],
        niche: str = "dark",
        market: str = "BR",
    ) -> str:
        """
        Gera relatório estratégico semanal com oportunidades e recomendações.

        Args:
            channels: lista de {channel_id, ctr, avg_view_pct, top_topics?}
        """
        lines = [
            f"# Relatório Estratégico Semanal — CineForge",
            f"Data: {time.strftime('%d/%m/%Y')}",
            f"Nicho: {niche.upper()} | Mercado: {market}",
            "",
            "## 📊 Status dos Canais",
            "",
        ]

        for ch in channels:
            ch_id = ch.get("channel_id", "desconhecido")
            ctr = ch.get("ctr", 0)
            ret = ch.get("avg_view_pct", 0)
            status = "✅" if ctr >= 6 and ret >= 35 else ("🟡" if ctr >= 6 or ret >= 35 else "🔴")
            lines.append(f"- **{ch_id}**: {status} CTR {ctr:.1f}% | Retenção {ret:.0f}%")

        lines += ["", "## 🎯 Top Oportunidades de Conteúdo", ""]

        # Gerar keywords de oportunidade para o nicho
        seed_keywords = {
            "finance_dark": ["dívida secreta banco", "fraude financeira", "golpe novo 2026"],
            "dark": ["verdade escondida", "segredo revelado", "investigação exclusiva"],
            "kids": ["personagem novo", "aventura mágica", "aprender brincando"],
            "tech": ["ferramenta IA grátis", "segredo desenvolvedor", "novo gadget"],
            "education": ["aprender rápido", "método eficaz", "estudo sem esforço"],
        }
        keywords = seed_keywords.get(niche, ["conteúdo viral", "tendência 2026"])

        for kw in keywords[:3]:
            opp = self.validate_niche_opportunity(niche, kw, market)
            lines.append(
                f"- **{kw}**: Score {opp.opportunity_score:.0f}/100 | "
                f"CPM ~${opp.cpm_estimate_usd:.1f} | {opp.recommendation}"
            )

        lines += [
            "",
            "## ⚙️ Diretrizes de Produção da Semana",
            "",
            "- Hook: primeiros 15s sem vinheta, palavra-chave falada verbalmente",
            "- Thumbnail: emoção forte, texto ≤4 palavras, cores saturadas",
            "- Título: 50-70 caracteres, curiosidade ou urgência",
            "- SEO: keyword nas primeiras 2 frases da descrição + nas primeiras palavras do título",
            "- Duração: >8 min para mid-rolls | Shorts dos melhores 45-60s",
            "",
            "## 📈 Ações Prioritárias",
            "",
        ]

        for ch in channels[:3]:
            ctr = ch.get("ctr", 0)
            ret = ch.get("avg_view_pct", 0)
            audit = self.audit_ctr_performance(
                ch.get("channel_id", "canal"), ctr, ret, niche
            )
            for action in audit.priority_actions:
                lines.append(f"- {action}")

        return "\n".join(lines)


_strategist: Optional[NicheStrategist] = None


def get_niche_strategist() -> NicheStrategist:
    global _strategist
    if _strategist is None:
        _strategist = NicheStrategist()
    return _strategist
