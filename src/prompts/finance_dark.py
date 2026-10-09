"""
Finance Dark Prompts — High-RPM hybrid niche: True Crime + Finanças.

This niche achieves $15-45 CPM (vs $2-8 for general content).
Key techniques:
  1. Second-person perspective ("Você é o CEO...")
  2. Hybrid true crime + finance angle
  3. 8-12 minute sweet spot for maximum RPM
  4. US English audience = highest CPM
  5. Short 60-second summaries for discovery, long-form for RPM

Proven hook formula:
  "Em [timeframe], você [shocking financial event]. E não foi por acaso."
"""

FINANCE_DARK_SYSTEM_PROMPT = """
You are an expert scriptwriter for high-RPM YouTube finance/dark channels.
Your specialty is the hybrid "True Crime + Finance" format that achieves $15-45 CPM.

CORE TECHNIQUE — SECOND PERSON IMMERSIVE:
Never use "João Silva era CEO..." — always use "Você é CEO..."
The viewer must feel they ARE the protagonist experiencing the story.

PROVEN STRUCTURE:
1. Hook (0-8s): Shocking financial revelation in second person
2. Scene-setting (8-30s): "It's [date]. You are [role]. You have [resources]."
3. Escalation: The scheme unfolds — viewer is inside it
4. Revelation: The hidden mechanism/fraud exposed
5. Consequence: What happened to YOU (the protagonist)
6. CTA: "Like if this made your blood run cold"

TONE: Investigative documentary meets financial thriller. Think "The Big Short" narration style.
"""

FINANCE_DARK_SCRIPT_PROMPT = """\
Create a complete YouTube script for a FINANCE DARK channel. Duration: {duration_min} minutes.

TOPIC: {topic}
MARKET: {market}
LANGUAGE: {language}
AUDIENCE: {audience}

MANDATORY TECHNIQUE — SECOND PERSON IMMERSIVE:
Write ENTIRELY in second person. The viewer IS the protagonist.
WRONG: "Carlos Silva criou um esquema..."
RIGHT: "Você criou o esquema. Você sabia exatamente o que estava fazendo."

HOOK FORMULA (use one of these exact patterns):
- "Em [TIMEFRAME], você vai [SHOCKING CONSEQUENCE]. Não porque é idiota. Porque eles planejaram cada detalhe."
- "Você está sentado na sua mesa. [DATE]. Sua conta tem [AMOUNT]. Em [TIMEFRAME], vai ter zero."
- "Você é o CEO. Você assinou o contrato. Você não sabia que estava roubando de você mesmo."

CONTENT REQUIREMENTS:
- 8-12 minutes ideal (sweet spot for finance dark RPM)
- Based on REAL financial crimes/schemes (Madoff, Enron, Wirecard, FTX, Americanas, etc.)
- Include actual numbers: $X billion lost, X thousand victims
- Thumbnail text: SINGLE POWERFUL WORD or short phrase (ex: "ESQUEMA", "TRAÍDO", "R$ 0")
- Second-person throughout ALL narration scenes

Return ONLY valid JSON in {language} (no markdown):
{{
  "titulo": "attention-grabbing SEO title, 60 chars max, number or $ symbol if possible",
  "descricao": "YouTube description 200 words, 3 paragraphs, natural keywords",
  "tags": ["tag1", "tag2", "...up to 15 tags, mix finance + true crime terms"],
  "thumbnail_text": "1-3 WORDS CAPS — shocking, urgent",
  "gancho_inicial": "Second-person hook line (8 seconds)",
  "duracao_estimada_segundos": 0,
  "cenas": [
    {{
      "id": 1,
      "texto_narracao": "SECOND PERSON narration text for this scene",
      "prompt_visual": "English prompt for AI video: specific cinematic scene matching the narrative",
      "duracao_segundos": 6,
      "emocao": "suspense|shock|anger|curiosity|dread",
      "texto_legenda_destaque": "power word to show on screen (optional)"
    }}
  ]
}}

Requirements:
- First scene = second-person hook (max 8s)
- Scene change every 5-7 seconds
- Min {min_scenes} scenes, max {max_scenes} scenes
- Last scene = CTA in second person
- prompt_visual ALWAYS in English
- All narrative text in {language} in SECOND PERSON
"""

FINANCE_DARK_TOPICS = {
    "pt-BR": [
        "O Esquema que Quebrou o Banco Santos — Você Era Um dos 150.000 Correntistas",
        "Eike Batista: Como Você Perdeu R$ 60 Bilhões em 18 Meses",
        "O Golpe da OAS: Você Assinou o Contrato com o Estado",
        "Telexfree: Como Você Entrou na Maior Pirâmide do Brasil",
        "BTG Pactual em 2015: A Noite que Você Percebeu que o Dinheiro Sumiu",
        "Americanas: Você Tinha Ações. Você Não Sabia o que Eles Estavam Fazendo",
        "O Esquema FTX: Como Você Perdeu Suas Criptomoedas da Noite para o Dia",
        "Madoff: Você Investiu com Ele. Você Achou que Era Diferente",
        "O Crash de 1929: Você Estava Lá. Você Achou que Ia Continuar Subindo",
        "Enron: Você Trabalhou Lá. Você Não Fazia Ideia",
    ],
    "en-US": [
        "Enron: You Were the Last to Know Your Retirement Was Gone",
        "FTX Collapse: You Trusted Him With Your Life Savings",
        "Bernie Madoff: You Were One of 37,000. You Thought You Were Different",
        "Theranos: You Invested $700M Based on a Lie You Never Questioned",
        "Wirecard: You Were the CFO When $2.1B Disappeared",
        "The 2008 Crash: You Had a Mortgage. You Had No Idea What Was Happening",
        "Sam Bankman-Fried: You Donated to His Cause. He Used It to Cover Losses",
        "WeWork: You Believed the Vision. $47B to $0 in 6 Months",
        "Lehman Brothers: Your Pension Was There When It Collapsed",
        "The Silk Road: You Used It. You Thought It Was Untraceable",
    ],
    "en-GB": [
        "LIBOR: You Had a Mortgage. They Were Rigging the Rate All Along",
        "Nick Leeson: You Were Barings Bank. He Lost Everything in 2 Years",
        "The London Whale: You Were JP Morgan. $6B Vanished in 6 Weeks",
        "PPI Scandal: You Paid For Insurance That Was Designed to Fail You",
        "Northern Rock: You Queued Outside to Get Your Money Back",
    ],
}

FINANCE_DARK_HOOKS = {
    "pt-BR": [
        "É {date}. Você está sentado na sua mesa. Sua conta tem R$ {amount}. Em {timeframe}, vai ter zero.",
        "Você assinou o contrato. Você fez a due diligence. Você não sabia que estava sendo roubado.",
        "Em {timeframe}, você vai descobrir que {company} nunca teve o dinheiro que dizia ter.",
        "Você é um dos {number} investidores que acreditou. E eles contavam exatamente com isso.",
        "Enquanto você lê isso, existe um esquema exatamente como este acontecendo agora.",
    ],
    "en-US": [
        "It's {date}. You're at your desk. Your account has {amount}. In {timeframe}, it will have zero.",
        "You signed the contract. You did the due diligence. You had no idea you were being robbed.",
        "In {timeframe}, you're going to find out that {company} never had the money it claimed.",
        "You are one of {number} investors who believed. And they counted on exactly that.",
        "While you read this, there's a scheme exactly like this one happening right now.",
    ],
    "en-GB": [
        "It's {date}. You're in the City. Your fund shows {amount} in gains. None of it is real.",
        "You signed the prospectus. You trusted the regulator. You had no idea.",
        "You are one of {number} British investors who lost everything. They planned it that way.",
    ],
}


def get_finance_dark_system_prompt() -> str:
    return FINANCE_DARK_SYSTEM_PROMPT


def get_finance_dark_script_prompt(
    topic: str,
    duration_min: int,
    audience: str,
    language: str,
    market: str,
    content_rating: str = "mature",
) -> str:
    min_scenes = duration_min * 9
    max_scenes = duration_min * 13
    return FINANCE_DARK_SCRIPT_PROMPT.format(
        topic=topic,
        duration_min=duration_min,
        audience=audience,
        language=language,
        market=market,
        content_rating=content_rating,
        min_scenes=min_scenes,
        max_scenes=max_scenes,
    )


def get_finance_dark_topics(language: str) -> list:
    return FINANCE_DARK_TOPICS.get(language, FINANCE_DARK_TOPICS["en-US"])


def get_finance_dark_hooks(language: str) -> list:
    return FINANCE_DARK_HOOKS.get(language, FINANCE_DARK_HOOKS["en-US"])
