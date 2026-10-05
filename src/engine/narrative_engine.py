"""
Motor de Narrativa 2ª Pessoa — diferencial proprietário do CineForge.

Gera roteiros em perspectiva imersiva (você/POV) adaptados por nicho.
Diferencia o conteúdo do AI-slop genérico que o YouTube demonetiza desde jul/2025.

Estratégias por nicho:
  finance_dark  → narrativa de ameaça iminente ("Sua conta bancária está em risco")
  dark          → narrativa de revelação perturbadora ("O que eles não te contam")
  kids          → narrativa de aventura participativa ("Você encontrou um tesouro!")
  tech          → narrativa de descoberta insider ("O segredo que os devs escondem")
  education     → narrativa de transformação ("Em 5 minutos você vai entender")
"""
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class NarrativeConfig:
    niche: str
    language: str = "pt-BR"
    pov_intensity: float = 0.8     # 0=terceira pessoa, 1=segunda pessoa máxima
    hook_style: str = "shock"      # shock | curiosity | fear | aspiration | adventure
    emotional_arc: str = "tension_release"  # tension_release | progressive_revelation | transformation
    persona_voice: str = "insider"  # insider | mentor | peer | investigator | guide


NICHE_NARRATIVE_CONFIGS: dict[str, NarrativeConfig] = {
    "finance_dark": NarrativeConfig(
        niche="finance_dark",
        pov_intensity=0.95,
        hook_style="fear",
        emotional_arc="tension_release",
        persona_voice="insider",
    ),
    "dark": NarrativeConfig(
        niche="dark",
        pov_intensity=0.85,
        hook_style="shock",
        emotional_arc="progressive_revelation",
        persona_voice="investigator",
    ),
    "kids": NarrativeConfig(
        niche="kids",
        pov_intensity=0.90,
        hook_style="adventure",
        emotional_arc="transformation",
        persona_voice="guide",
    ),
    "tech": NarrativeConfig(
        niche="tech",
        pov_intensity=0.75,
        hook_style="curiosity",
        emotional_arc="progressive_revelation",
        persona_voice="peer",
    ),
    "education": NarrativeConfig(
        niche="education",
        pov_intensity=0.70,
        hook_style="aspiration",
        emotional_arc="transformation",
        persona_voice="mentor",
    ),
}

HOOK_TEMPLATES = {
    "fear": [
        "Você está cometendo um erro que pode custar {price} — e não sabe disso.",
        "O que você faz todo dia está destruindo seu {asset} silenciosamente.",
        "Enquanto você lê isso, alguém pode estar usando seu {asset}.",
    ],
    "shock": [
        "O que você prestes a descobrir vai mudar como você vê {topic}.",
        "Isso foi escondido de você por anos. {topic} não é o que parece.",
        "Ninguém fala sobre isso. A verdade sobre {topic} que eles escondem.",
    ],
    "curiosity": [
        "Por que os especialistas em {topic} fazem exatamente o oposto do que ensinam?",
        "O truque de {topic} que apenas 1% das pessoas conhece.",
        "Isso parece impossível sobre {topic} — mas funciona.",
    ],
    "aspiration": [
        "Em {time}, você vai entender {topic} melhor do que 90% das pessoas.",
        "O método que transforma completos iniciantes em especialistas em {topic}.",
        "Após esse vídeo, {topic} nunca vai parecer difícil de novo.",
    ],
    "adventure": [
        "Você acabou de encontrar algo que a maioria das crianças nunca viu!",
        "Prepare-se: você está prestes a descobrir o segredo mais incrível de {topic}!",
        "Imagine se você pudesse {action} — hoje você vai aprender como!",
    ],
}

SCENE_NARRATIVE_PROMPTS = {
    "finance_dark": {
        "hook": "Cena urgente: tela de banco com transação suspeita, mãos de pessoa nervosa digitando senha, luz vermelha piscando, ambiente tenso noturno",
        "reveal": "Revelação: documentos financeiros espalhados, pessoa olhando para dados com expressão de choque, luz de monitor no escuro",
        "solution": "Transformação: pessoa confiante em escritório organizado, gráficos verdes crescendo, expressão de alívio e controle",
        "cta": "Close no rosto determinado, ambiente profissional, fundo com cidade ao entardecer simbolizando novo começo",
    },
    "dark": {
        "hook": "Cena misteriosa: documentos confidenciais, sombras, câmera de segurança, tons escuros e atmosfera de segredo",
        "reveal": "Revelação perturbadora: imagens de contraste entre aparência e realidade, espelho quebrando, ilusão se desfazendo",
        "solution": "Conhecimento como poder: pessoa lendo com luz focal, informação fluindo, expressão de entendimento profundo",
        "cta": "Silhueta determinada em contra-luz, símbolo de poder ou conhecimento ao fundo",
    },
    "kids": {
        "hook": "Cena colorida e emocionante: criança com olhos arregalados descobrindo algo incrível, cores vibrantes, energia positiva",
        "reveal": "Descoberta mágica: portal ou mundo novo se abrindo, efeitos de luz coloridos, expressão de maravilhamento",
        "solution": "Aventura participativa: criança resolvendo desafio com sorriso, amigos ao redor, celebração de conquista",
        "cta": "Personagem acenando diretamente para câmera, estrelas e efeitos festivos, ambiente de celebração",
    },
    "tech": {
        "hook": "Interface futurista: código fluindo na tela, hologramas, ambiente de laboratório tech moderno",
        "reveal": "Insight técnico: diagrama complexo simplificando visualmente, luz de compreensão, fundo de circuitos",
        "solution": "Demonstração prática: mãos no teclado com resultado aparecing na tela, ambiente produtivo",
        "cta": "Developer em setup profissional, múltiplos monitores, expressão satisfeita de projeto concluído",
    },
    "education": {
        "hook": "Abertura inspiradora: biblioteca imponente ou ambiente de aprendizado, luz natural, sensação de possibilidade",
        "reveal": "Conceito visualizado: ideia abstrata tornando-se visual clara, diagrama se formando, momento eureka",
        "solution": "Aplicação prática: pessoa aplicando o conhecimento em situação real, resultado positivo",
        "cta": "Pessoa olhando para horizonte com confiança, ambiente de conquista, luz dourada de realização",
    },
}


class NarrativeEngine:
    """
    Gera roteiros, hooks e prompts visuais com narrativa em 2ª pessoa.
    Diferencial proprietário: cada vídeo tem voz única adaptada ao nicho.
    """

    def __init__(self, niche: str = "dark", language: str = "pt-BR"):
        self.niche = niche
        self.language = language
        self.config = NICHE_NARRATIVE_CONFIGS.get(niche, NICHE_NARRATIVE_CONFIGS["dark"])
        self._llm_available = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))

    def generate_hook(self, topic: str, duration_seconds: int = 15) -> str:
        """Gera hook inicial em 2ª pessoa para o tópico e nicho."""
        templates = HOOK_TEMPLATES.get(self.config.hook_style, HOOK_TEMPLATES["shock"])
        template = templates[hash(topic) % len(templates)]

        hook = template.format(
            topic=topic,
            price="R$10.000",
            asset="poupança",
            time="5 minutos",
            action="voar como um pássaro",
        )
        return hook

    def generate_script_prompt(self, topic: str, duration_minutes: int = 10) -> str:
        """
        Gera prompt para LLM criar roteiro em 2ª pessoa com narrativa imersiva.

        O prompt instrui o LLM a escrever como se o espectador fosse o protagonista.
        """
        config = self.config
        hook = self.generate_hook(topic)
        scene_prompts = SCENE_NARRATIVE_PROMPTS.get(self.niche, SCENE_NARRATIVE_PROMPTS["dark"])

        arc_instructions = {
            "tension_release": f"Construa tensão progressiva nos primeiros 70% do vídeo, depois libere com revelação e solução nos 30% finais.",
            "progressive_revelation": f"Revele informações em camadas, cada revelação mais surpreendente que a anterior, mantendo o espectador preso.",
            "transformation": f"Mostre a transformação do espectador de 'sem saber' para 'especialista' como jornada pessoal dele mesmo.",
        }.get(config.emotional_arc, "")

        voice_instructions = {
            "insider": "Escreva como alguém que tem acesso a informações privilegiadas e está compartilhando um segredo exclusivo.",
            "investigator": "Escreva como investigador revelando uma verdade escondida, usando linguagem de exposé jornalístico.",
            "guide": "Escreva como guia em uma aventura, usando linguagem animada, direta e encorajadora.",
            "peer": "Escreva como colega que acabou de descobrir algo incrível e quer compartilhar com urgência.",
            "mentor": "Escreva como mentor experiente que simplifica o complexo com clareza e autoridade.",
        }.get(config.persona_voice, "")

        prompt = f"""Você é um roteirista especialista em conteúdo viral para YouTube no nicho {self.niche.upper()}.

TÓPICO: {topic}
DURAÇÃO ALVO: {duration_minutes} minutos
IDIOMA: {self.language}

REGRA PRINCIPAL — NARRATIVA EM 2ª PESSOA:
Escreva SEMPRE dirigindo-se ao espectador como "você". Nunca use "as pessoas", "muitos" ou impessoal.
O espectador é o PROTAGONISTA do vídeo. Tudo acontece COM ELE, não com terceiros.

HOOK DE ABERTURA (primeiros 15 segundos):
"{hook}"

VOZ E TOM:
{voice_instructions}

ARCO EMOCIONAL:
{arc_instructions}

ESTRUTURA OBRIGATÓRIA (em JSON):
{{
  "titulo": "título chamativo em 2ª pessoa (máx 60 chars)",
  "descricao_youtube": "descrição SEO com 3 parágrafos e palavras-chave naturais",
  "tags": ["tag1", "tag2", ...] (15-20 tags relevantes),
  "cenas": [
    {{
      "id": 1,
      "tipo": "hook|reveal|build|climax|solution|cta",
      "duracao_segundos": 8,
      "narração": "texto narrado em 2ª pessoa (máx 3 frases)",
      "prompt_visual": "descrição cinematográfica detalhada da cena para geração de vídeo AI",
      "emocao": "tension|shock|curiosity|revelation|relief|excitement",
      "nota_producao": "instrução técnica opcional para editor"
    }}
  ]
}}

DIRETRIZES DE PROMPT VISUAL:
- Cada prompt_visual deve ser em inglês (otimizado para modelos de vídeo AI)
- Incluir: composição, iluminação, emoção visual, estilo cinematográfico
- Evitar: pessoas específicas, logos, texto na cena
- Usar: câmeras cinematográficas (close-up, wide shot, POV shot)
- Tom visual para este nicho: {scene_prompts.get('hook', '')}

ANTI-AI-SLOP: O roteiro deve ter perspectiva genuína, não ser genérico.
Inclua dados específicos, história real do tópico, ou insight único que agregue valor real."""

        return prompt

    def enhance_visual_prompt(self, base_prompt: str, scene_type: str = "hook") -> str:
        """
        Melhora prompt visual para geração de vídeo AI com detalhes cinematográficos.
        Adiciona estilo visual específico do nicho.
        """
        niche_visuals = {
            "finance_dark": "cinematic dark finance aesthetic, dramatic lighting, high contrast, tension-filled atmosphere, documentary style",
            "dark": "mysterious noir atmosphere, dramatic shadows, cinematic mystery, high contrast, investigative documentary style",
            "kids": "bright vibrant colors, magical fairy tale atmosphere, warm cheerful lighting, animated-inspired live action, joyful energy",
            "tech": "sleek futuristic interface, neon glow, tech startup aesthetic, clean modern minimalism, cinematic sci-fi elements",
            "education": "warm inspiring atmosphere, golden hour lighting, academic gravitas, documentary educational style, knowledge visualization",
        }

        scene_types = {
            "hook": "extreme close-up or dramatic wide establishing shot, immediate visual impact",
            "reveal": "slow reveal camera movement, dramatic lighting change, visual metaphor for discovery",
            "build": "medium shots with rising tension, dynamic camera movement, progressive energy",
            "climax": "peak dramatic moment, maximum visual impact, cinematic peak",
            "solution": "warm resolution lighting, relief and positivity, success visual metaphor",
            "cta": "direct eye-contact framing, confident composed shot, memorable final image",
        }

        niche_style = niche_visuals.get(self.niche, niche_visuals["dark"])
        scene_style = scene_types.get(scene_type, "cinematic shot")

        return f"{base_prompt}, {scene_style}, {niche_style}, 8K ultra HD, professional cinematography, no text overlay, no watermarks"

    def generate_thumbnail_prompt(self, topic: str, hook_text: str) -> str:
        """Gera prompt para thumbnail com fórmula de alto CTR."""
        thumbnail_styles = {
            "finance_dark": f"shocked person with money/financial charts, dark dramatic background, bright red warning elements, face showing alarm, text: AVOID THIS, high contrast thumbnail style",
            "dark": f"mysterious revealed truth, shadowy figure with bright spotlight, conspiracy board aesthetic, dramatic face reaction, text: THEY HIDE THIS",
            "kids": f"excited child with glowing magical object, bright saturated colors, wonder and amazement expression, cartoon-style effects, sparkles and stars",
            "tech": f"split screen before/after showing tech transformation, futuristic interface elements, confident person at computer, bright tech aesthetic",
            "education": f"person having eureka moment, lightbulb visual metaphor, inspiring academic setting, confident expert expression, warm golden tones",
        }

        base_style = thumbnail_styles.get(self.niche, thumbnail_styles["dark"])
        return f"YouTube thumbnail about '{topic}': {base_style}, 1280x720px, eye-catching, high CTR optimized, professional thumbnail design, no small text, bold visual impact"

    def calculate_retention_score(self, script: dict) -> float:
        """
        Heurística de score de retenção baseado na estrutura do roteiro.
        Score 0-100. Vídeos acima de 75 têm maior probabilidade de monetização.
        """
        score = 0.0
        scenes = script.get("cenas", [])

        if not scenes:
            return 0.0

        # Hook strength (primeiros 30 segundos = crítico)
        first_scene = scenes[0] if scenes else {}
        hook_duration = first_scene.get("duracao_segundos", 0)
        if hook_duration <= 15:
            score += 20  # Hook rápido e impactante

        # Variety of scene types
        types = {s.get("tipo") for s in scenes}
        score += min(25, len(types) * 5)

        # Emotional variety
        emotions = {s.get("emocao") for s in scenes}
        score += min(20, len(emotions) * 5)

        # Pacing (cenas curtas = melhor retenção)
        avg_duration = sum(s.get("duracao_segundos", 8) for s in scenes) / len(scenes)
        if avg_duration <= 8:
            score += 20
        elif avg_duration <= 12:
            score += 10

        # Has CTA
        has_cta = any(s.get("tipo") == "cta" for s in scenes)
        if has_cta:
            score += 15

        return min(100.0, score)


_engines: dict[str, NarrativeEngine] = {}


def get_narrative_engine(niche: str = "dark", language: str = "pt-BR") -> NarrativeEngine:
    key = f"{niche}_{language}"
    if key not in _engines:
        _engines[key] = NarrativeEngine(niche=niche, language=language)
    return _engines[key]
