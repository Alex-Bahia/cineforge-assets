"""
OpportunityRouter — roteia oportunidades para o template de script correto.

Baseado no campo `niche` (ou inferido do tópico), seleciona:
  - O system prompt correto
  - O script prompt correto
  - Os defaults de duração e tom
  - O perfil de canal padrão

Usage:
    from src.trend_monitor.opportunity_router import OpportunityRouter

    router = OpportunityRouter()
    config = router.route("Fraude de R$ 2 bilhões no BTG", niche="finance_dark")
    # config = {"system_prompt": ..., "script_prompt_fn": ..., "profile_id": ..., ...}
"""

from __future__ import annotations

import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

# ── Niche detection keywords ──────────────────────────────────────────────────
NICHE_KEYWORDS = {
    "finance_dark": [
        "fraude", "esquema", "golpe", "falência", "pirâmide", "crime financeiro",
        "escândalo", "bilhões", "cvm", "b3", "investidor", "banco", "corrupção",
        "lavagem", "desvio", "recuperação judicial", "concordata",
        "fraud", "scam", "ponzi", "bankruptcy", "scandal", "billions",
        "wall street", "sec", "irs", "madoff", "enron", "wirecard", "ftx",
    ],
    "dark": [
        "assassinato", "serial killer", "crime", "mistério", "desaparecimento",
        "morte", "suicídio", "sequestro", "psicopata", "caso não resolvido",
        "murder", "missing", "unsolved", "true crime", "killer", "paranormal",
    ],
    "kids": [
        "crianças", "bebês", "infantil", "educativo", "animação kids",
        "aprender", "cores", "números", "alfabeto", "animais fazenda",
        "children", "kids", "babies", "learn", "educational kids",
    ],
    "tech": [
        "inteligência artificial", "ia", "smartphone", "celular", "apple",
        "google", "tecnologia", "gadget", "hack", "vazamento de dados",
        "ai", "tech", "iphone", "android", "cybersecurity", "data breach",
    ],
    "education": [
        "história", "ciência", "curiosidades", "documentário", "fatos",
        "como funciona", "por que", "descoberta", "inventou",
        "history", "science", "facts", "discovery", "documentary",
    ],
}

# ── Niche → pipeline config ───────────────────────────────────────────────────
NICHE_CONFIG = {
    "finance_dark": {
        "default_profile_br": "br_finance_dark",
        "default_profile_us": "us_finance_dark",
        "default_profile_gb": "gb_finance_dark",
        "default_duration_min": 10,
        "default_tone": "investigativo, segunda pessoa imersiva, true crime + finanças",
        "content_rating": "mature",
        "tts_tier": "premium",
        "veo3_enabled": True,
        "prompt_module": "src.prompts.finance_dark",
        "priority_multiplier": 1.5,  # finance_dark tem CPM alto, prioridade maior
    },
    "dark": {
        "default_profile_br": "br_dark",
        "default_profile_us": "us_dark",
        "default_profile_gb": "gb_dark",
        "default_duration_min": 8,
        "default_tone": "dark, investigativo, dramático, suspense",
        "content_rating": "mature",
        "tts_tier": "free",
        "veo3_enabled": False,
        "prompt_module": "src.prompts.scriptwriter",
        "priority_multiplier": 1.2,
    },
    "kids": {
        "default_profile_br": "br_kids",
        "default_profile_us": "us_kids",
        "default_profile_gb": None,
        "default_duration_min": 4,
        "default_tone": "educativo e divertido, musical, positivo",
        "content_rating": "general",
        "tts_tier": "free",
        "veo3_enabled": False,
        "made_for_kids": True,
        "prompt_module": "src.prompts.scriptwriter",
        "priority_multiplier": 0.5,  # CPM baixo mas lifetime alto
        "lifetime_multiplier": 5.0,  # anos de acumulação de views
    },
    "tech": {
        "default_profile_br": "br_tech",
        "default_profile_us": "us_tech",
        "default_profile_gb": None,
        "default_duration_min": 8,
        "default_tone": "informativo, objetivo, análise técnica",
        "content_rating": "general",
        "tts_tier": "free",
        "veo3_enabled": False,
        "prompt_module": "src.prompts.scriptwriter",
        "priority_multiplier": 1.8,  # CPM alto
    },
    "education": {
        "default_profile_br": "br_education",
        "default_profile_us": "us_education",
        "default_profile_gb": "gb_education",
        "default_duration_min": 8,
        "default_tone": "didático, envolvente, histórias reais",
        "content_rating": "general",
        "tts_tier": "free",
        "veo3_enabled": False,
        "prompt_module": "src.prompts.scriptwriter",
        "priority_multiplier": 1.3,
    },
}


class OpportunityRouter:
    """
    Roteia oportunidades detectadas pelo TrendMonitor/KidsMonitor
    para o template de script e perfil de canal correto.
    """

    def detect_niche(self, topic: str, source_niche: Optional[str] = None) -> str:
        """
        Detecta o nicho de uma oportunidade.
        Se `source_niche` está definido e é válido, usa diretamente.
        Caso contrário, detecta pelos keywords do tópico.
        """
        if source_niche and source_niche in NICHE_CONFIG:
            return source_niche

        topic_lower = topic.lower()
        scores: dict[str, int] = {niche: 0 for niche in NICHE_KEYWORDS}
        for niche, keywords in NICHE_KEYWORDS.items():
            for kw in keywords:
                if kw in topic_lower:
                    scores[niche] += 1

        best = max(scores, key=lambda n: scores[n])
        if scores[best] == 0:
            return "dark"  # default
        return best

    def route(
        self,
        topic: str,
        niche: Optional[str] = None,
        market: str = "BR",
    ) -> dict:
        """
        Retorna configuração completa para gerar o script de um tópico.

        Returns:
            dict com:
              - niche: nicho detectado
              - profile_id: ID do ChannelProfile recomendado
              - duration_min: duração sugerida em minutos
              - tone: tom de conteúdo
              - content_rating: general | teen | mature
              - tts_tier: free | premium
              - veo3_enabled: bool
              - made_for_kids: bool
              - prompt_module: módulo Python com os prompts
              - priority_multiplier: multiplicador de prioridade por CPM
        """
        detected = self.detect_niche(topic, niche)
        config = NICHE_CONFIG.get(detected, NICHE_CONFIG["dark"]).copy()
        config["niche"] = detected
        config["topic"] = topic
        config["market"] = market

        profile_key = f"default_profile_{market.lower()}"
        config["profile_id"] = config.get(profile_key) or config.get("default_profile_br")

        return config

    def adjust_score(self, base_score: float, niche: str) -> float:
        """Ajusta o score de oportunidade pelo multiplicador do nicho."""
        multiplier = NICHE_CONFIG.get(niche, {}).get("priority_multiplier", 1.0)
        return round(base_score * multiplier, 2)

    def is_made_for_kids(self, niche: str) -> bool:
        """Retorna True se o conteúdo deve ser marcado como Made for Kids no YouTube."""
        return NICHE_CONFIG.get(niche, {}).get("made_for_kids", False)

    def get_niches(self) -> list[str]:
        return list(NICHE_CONFIG.keys())


# ── Singleton ──────────────────────────────────────────────────────────────────
_router: Optional[OpportunityRouter] = None


def get_opportunity_router() -> OpportunityRouter:
    global _router
    if _router is None:
        _router = OpportunityRouter()
    return _router
