"""
Competitor Analyzer — Extracts the narrative DNA of YouTube channels.

Inspired by the NotebookLM workflow from "21 Million Views Engine" video:
  - Feed competitor channel titles/descriptions/comments -> extract pattern
  - Use Gemini as proxy for NotebookLM analysis
  - Output: narrative style template, hook patterns, title formulas

Works WITHOUT NotebookLM API (uses Gemini instead).
"""
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class ChannelDNA:
    """Extracted narrative pattern from a YouTube channel."""
    channel_name: str
    niche: str
    hook_formula: str
    narrative_style: str
    title_patterns: list = field(default_factory=list)
    emotional_triggers: list = field(default_factory=list)
    average_video_length_min: int = 10
    thumbnail_style: str = ""
    cta_style: str = ""
    pov_style: str = "third_person"  # first_person | second_person | third_person
    top_performing_topics: list = field(default_factory=list)
    weakness: str = ""
    our_edge: str = ""
    recommended_hook_template: str = ""


ANALYSIS_PROMPT_TEMPLATE = """
Você é um analista especialista em canais do YouTube. Analise os dados abaixo de um canal concorrente
e extraia o DNA narrativo dele para que possamos criar conteúdo superior.

DADOS DO CANAL:
Nome: {channel_name}
Nicho: {niche}
Idioma: {language}

AMOSTRA DE TÍTULOS (do mais popular ao menos):
{titles}

AMOSTRA DE DESCRIÇÕES:
{descriptions}

AMOSTRA DE COMENTÁRIOS MAIS CURTIDOS:
{top_comments}

MÉTRICAS (se disponíveis):
{metrics}

Retorne APENAS um JSON válido com este schema (sem markdown):
{{
  "hook_formula": "fórmula do gancho inicial",
  "narrative_style": "descrição do estilo narrativo",
  "title_patterns": ["padrão 1", "padrão 2", "padrão 3"],
  "emotional_triggers": ["gatilho1", "gatilho2", "gatilho3"],
  "thumbnail_style": "descrição do estilo visual das thumbnails",
  "cta_style": "como eles pedem like/inscrição",
  "pov_style": "first_person|second_person|third_person",
  "top_performing_topics": ["tópico1", "tópico2", "tópico3"],
  "weakness": "principal fraqueza que podemos superar",
  "our_edge": "como podemos fazer MELHOR que este canal",
  "recommended_hook_template": "template de gancho específico para usar nos nossos vídeos"
}}
"""

SECOND_PERSON_HOOKS = {
    "finance_dark": [
        "Em {timeframe}, você vai descobrir que {shocking_fact}. E não será por acaso.",
        "Você achou que {common_belief}. Você estava errado. E eles contavam com isso.",
        "Imagine acordar com {amount} a menos na sua conta. Isso aconteceu com {X_people}.",
        "Você está sendo monitorado. E os dados que têm sobre você valem mais do que imagina.",
        "O CEO olhou para os números e sorriu. Você era um dos {number} que não percebeu.",
    ],
    "dark": [
        "Você está prestes a descobrir algo que vai mudar como você vê {topic}.",
        "Em {year}, alguém exatamente como você desapareceu. A polícia nunca soube o porquê.",
        "Você mora a {X} km do lugar mais perigoso do Brasil. E nunca soube disso.",
    ],
    "tech": [
        "Enquanto você lê isso, sua câmera está coletando dados que você nunca autorizou.",
        "Você tem {X} apps no celular. {Y} deles sabem exatamente onde você está agora.",
    ],
}

TITLE_FORMULAS = {
    "finance_dark": [
        "O Golpe de {amount} que Ninguém Viu Vir (e Como Funciona)",
        "Como {company} Roubou {amount} em Plena Vista — A História Completa",
        "O CEO que Enganou {number} Pessoas com Uma Simples Planilha",
        "Você Investiu {amount}. Ele Ficou Rico. Veja Como Funciona o Esquema",
        "{name}: O Maior Fraudador do {market} que Quase Escapou",
    ],
    "dark": [
        "O Crime que Chocou o Brasil (e a Verdade que Nunca Foi Contada)",
        "Desapareceu em {year}: A História que a Mídia Escondeu",
        "O Caso {name}: Por Que Ninguém Fala Sobre Isso?",
    ],
}


class CompetitorAnalyzer:
    """Analyzes competitor YouTube channels to extract their narrative DNA."""

    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client

    def build_analysis_prompt(
        self,
        channel_name: str,
        niche: str,
        language: str,
        titles: list,
        descriptions: list = None,
        top_comments: list = None,
        metrics: dict = None,
    ) -> str:
        return ANALYSIS_PROMPT_TEMPLATE.format(
            channel_name=channel_name,
            niche=niche,
            language=language,
            titles="\n".join(f"  {i+1}. {t}" for i, t in enumerate(titles[:20])),
            descriptions="\n".join((descriptions or [])[:3]),
            top_comments="\n".join((top_comments or [])[:5]),
            metrics=json.dumps(metrics or {}, ensure_ascii=False, indent=2),
        )

    def analyze(
        self,
        channel_name: str,
        niche: str,
        language: str,
        titles: list,
        descriptions: list = None,
        top_comments: list = None,
        metrics: dict = None,
    ) -> Optional[ChannelDNA]:
        """Analyze a channel and return its ChannelDNA."""
        if not self.gemini_client:
            log.warning("CompetitorAnalyzer: gemini_client not set, returning mock DNA")
            return self._mock_dna(channel_name, niche)

        prompt = self.build_analysis_prompt(
            channel_name, niche, language, titles, descriptions, top_comments, metrics
        )

        try:
            response = self.gemini_client.generate_content(prompt)
            text = response.text.strip()
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
            data = json.loads(text)
            return ChannelDNA(
                channel_name=channel_name,
                niche=niche,
                hook_formula=data.get("hook_formula", ""),
                narrative_style=data.get("narrative_style", ""),
                title_patterns=data.get("title_patterns", []),
                emotional_triggers=data.get("emotional_triggers", []),
                thumbnail_style=data.get("thumbnail_style", ""),
                cta_style=data.get("cta_style", ""),
                pov_style=data.get("pov_style", "third_person"),
                top_performing_topics=data.get("top_performing_topics", []),
                weakness=data.get("weakness", ""),
                our_edge=data.get("our_edge", ""),
                recommended_hook_template=data.get("recommended_hook_template", ""),
            )
        except Exception as e:
            log.error("CompetitorAnalyzer error: %s", e)
            return None

    def _mock_dna(self, channel_name: str, niche: str) -> ChannelDNA:
        return ChannelDNA(
            channel_name=channel_name,
            niche=niche,
            hook_formula="Pergunta chocante nos primeiros 5 segundos + promessa de revelação",
            narrative_style="Terceira pessoa dramática, ritmo acelerado, cliffhangers",
            title_patterns=[
                "O {evento} que Chocou o {local}",
                "A Verdade Sobre {pessoa/empresa} que Ninguém Conta",
            ],
            emotional_triggers=["curiosidade", "choque", "indignação"],
            pov_style="third_person",
        )

    def get_second_person_hooks(self, niche: str) -> list:
        return SECOND_PERSON_HOOKS.get(niche, SECOND_PERSON_HOOKS.get("dark", []))

    def get_title_formulas(self, niche: str) -> list:
        return TITLE_FORMULAS.get(niche, TITLE_FORMULAS.get("dark", []))


def analyze_channel_dna(
    channel_name: str,
    titles: list,
    niche: str = "dark",
    language: str = "pt-BR",
    gemini_client=None,
) -> Optional[ChannelDNA]:
    analyzer = CompetitorAnalyzer(gemini_client=gemini_client)
    return analyzer.analyze(channel_name, niche, language, titles)
