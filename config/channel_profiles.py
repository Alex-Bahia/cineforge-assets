"""
Channel Profiles — Market + Niche + Language configuration.

A channel profile defines the complete identity of a YouTube channel:
  market, language, TTS voice, content niche, audience, and defaults.

Usage:
    from config.channel_profiles import get_profile, list_profiles
    profile = get_profile("br_dark")  # Brazil dark channel
    profile = get_profile("us_sports")  # USA sports channel
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChannelProfile:
    id: str
    name: str
    market: str          # BR | US | GB | FR | DE | ES | IT | PT | ...
    language: str        # pt-BR | en-US | en-GB | fr-FR | de-DE | es-ES | it-IT
    tts_voice: str       # edge-tts voice name
    tts_voice_female: str
    tts_rate: str        # e.g. "-5%" (slower) or "+0%"
    tts_pitch: str       # e.g. "-10Hz" (deeper)
    niche: str           # dark | sports | kids | tech | finance | health | cooking | education | entertainment | news | finance_dark
    audience: str        # e.g. "Brazilian adults 18-45"
    content_style: str   # e.g. "dark, investigative, dramatic"
    content_rating: str  # general | teen | mature
    yt_category_id: str  # YouTube category ID
    region_code: str     # for YouTube API trending
    extra_tags: list[str] = field(default_factory=list)
    # Premium TTS (ElevenLabs)
    tts_tier: str = "free"                          # "free" (edge-tts) | "premium" (ElevenLabs)
    elevenlabs_voice_id: Optional[str] = None       # override ElevenLabs voice
    # Character consistency (Método Grid)
    character_name: str = ""
    character_description: str = ""
    character_contact_sheet_path: Optional[str] = None
    # Veo3 AI video generation
    veo3_enabled: bool = False
    veo3_tier: str = "fast"                         # lite | fast | standard


# ── Profiles registry ──────────────────────────────────────────────────────────

PROFILES: dict[str, ChannelProfile] = {

    # ── BRAZIL ────────────────────────────────────────────────────────────────

    "br_dark": ChannelProfile(
        id="br_dark",
        name="Canal Dark BR",
        market="BR",
        language="pt-BR",
        tts_voice="pt-BR-AntonioNeural",
        tts_voice_female="pt-BR-FranciscaNeural",
        tts_rate="-5%",
        tts_pitch="-10Hz",
        niche="dark",
        audience="Brasileiros adultos 18-45, curiosos por histórias sombrias, crimes, mistérios",
        content_style="dark, investigativo, dramático, suspense",
        content_rating="mature",
        yt_category_id="27",  # Education/Documentary
        region_code="BR",
        extra_tags=["crime brasil", "mistério", "serial killer", "paranormal", "dark"],
    ),

    "br_sports": ChannelProfile(
        id="br_sports",
        name="Canal Esportes BR",
        market="BR",
        language="pt-BR",
        tts_voice="pt-BR-AntonioNeural",
        tts_voice_female="pt-BR-FranciscaNeural",
        tts_rate="+0%",
        tts_pitch="+0Hz",
        niche="sports",
        audience="Brasileiros fãs de esportes, principalmente futebol",
        content_style="dinâmico, empolgante, esportivo, análise tática",
        content_rating="general",
        yt_category_id="17",  # Sports
        region_code="BR",
        extra_tags=["futebol", "esportes", "brasileirão", "copa", "atletas"],
    ),

    "br_kids": ChannelProfile(
        id="br_kids",
        name="Canal Infantil BR",
        market="BR",
        language="pt-BR",
        tts_voice="pt-BR-FranciscaNeural",
        tts_voice_female="pt-BR-FranciscaNeural",
        tts_rate="+10%",
        tts_pitch="+5Hz",
        niche="kids",
        audience="Crianças brasileiras 4-10 anos e seus pais",
        content_style="educativo, divertido, colorido, animado, positivo",
        content_rating="general",
        yt_category_id="20",  # Gaming / Education for kids
        region_code="BR",
        extra_tags=["infantil", "crianças", "educativo", "animação", "aprendizado"],
    ),

    "br_tech": ChannelProfile(
        id="br_tech",
        name="Canal Tech BR",
        market="BR",
        language="pt-BR",
        tts_voice="pt-BR-AntonioNeural",
        tts_voice_female="pt-BR-FranciscaNeural",
        tts_rate="-2%",
        tts_pitch="+0Hz",
        niche="tech",
        audience="Brasileiros entusiastas de tecnologia, 20-40 anos",
        content_style="informativo, objetivo, análise técnica, novidades",
        content_rating="general",
        yt_category_id="28",  # Science & Technology
        region_code="BR",
        extra_tags=["tecnologia", "celular", "ia", "iphone", "android", "tech"],
    ),

    "br_finance": ChannelProfile(
        id="br_finance",
        name="Canal Finanças BR",
        market="BR",
        language="pt-BR",
        tts_voice="pt-BR-AntonioNeural",
        tts_voice_female="pt-BR-FranciscaNeural",
        tts_rate="-3%",
        tts_pitch="-5Hz",
        niche="finance",
        audience="Brasileiros interessados em investimentos, 25-50 anos",
        content_style="didático, confiável, análise financeira, cases de sucesso",
        content_rating="general",
        yt_category_id="27",  # Education
        region_code="BR",
        extra_tags=["finanças", "investimentos", "bolsa", "bitcoin", "renda passiva"],
    ),

    "br_education": ChannelProfile(
        id="br_education",
        name="Canal Educação BR",
        market="BR",
        language="pt-BR",
        tts_voice="pt-BR-AntonioNeural",
        tts_voice_female="pt-BR-FranciscaNeural",
        tts_rate="-3%",
        tts_pitch="+0Hz",
        niche="education",
        audience="Estudantes e curiosos brasileiros, 15-35 anos",
        content_style="didático, envolvente, histórias reais, curiosidades",
        content_rating="general",
        yt_category_id="27",  # Education
        region_code="BR",
        extra_tags=["educação", "história", "ciência", "curiosidades", "aprender"],
    ),

    "br_health": ChannelProfile(
        id="br_health",
        name="Canal Saúde BR",
        market="BR",
        language="pt-BR",
        tts_voice="pt-BR-FranciscaNeural",
        tts_voice_female="pt-BR-FranciscaNeural",
        tts_rate="-3%",
        tts_pitch="+0Hz",
        niche="health",
        audience="Brasileiros preocupados com saúde e bem-estar, 25-55 anos",
        content_style="informativo, cuidadoso, baseado em evidências, motivacional",
        content_rating="general",
        yt_category_id="26",  # Howto & Style
        region_code="BR",
        extra_tags=["saúde", "bem-estar", "dicas", "alimentação", "exercícios"],
    ),

    # ── USA ───────────────────────────────────────────────────────────────────

    "us_dark": ChannelProfile(
        id="us_dark",
        name="Dark Channel US",
        market="US",
        language="en-US",
        tts_voice="en-US-GuyNeural",
        tts_voice_female="en-US-JennyNeural",
        tts_rate="-5%",
        tts_pitch="-10Hz",
        niche="dark",
        audience="American adults 18-45, interested in true crime, mysteries, paranormal",
        content_style="dark, investigative, dramatic, thriller, suspenseful",
        content_rating="mature",
        yt_category_id="27",
        region_code="US",
        extra_tags=["true crime", "mystery", "serial killer", "paranormal", "dark", "unsolved"],
    ),

    "us_sports": ChannelProfile(
        id="us_sports",
        name="Sports Channel US",
        market="US",
        language="en-US",
        tts_voice="en-US-GuyNeural",
        tts_voice_female="en-US-JennyNeural",
        tts_rate="+5%",
        tts_pitch="+0Hz",
        niche="sports",
        audience="American sports fans, NFL, NBA, MLB, NHL enthusiasts",
        content_style="energetic, analytical, passionate, highlight-driven",
        content_rating="general",
        yt_category_id="17",  # Sports
        region_code="US",
        extra_tags=["NFL", "NBA", "sports", "highlights", "analysis", "American football"],
    ),

    "us_kids": ChannelProfile(
        id="us_kids",
        name="Kids Channel US",
        market="US",
        language="en-US",
        tts_voice="en-US-AnaNeural",
        tts_voice_female="en-US-AnaNeural",
        tts_rate="+10%",
        tts_pitch="+5Hz",
        niche="kids",
        audience="American children 4-10 years and their parents",
        content_style="educational, fun, colorful, animated, positive, age-appropriate",
        content_rating="general",
        yt_category_id="20",
        region_code="US",
        extra_tags=["kids", "children", "educational", "learning", "fun", "animation"],
    ),

    "us_tech": ChannelProfile(
        id="us_tech",
        name="Tech Channel US",
        market="US",
        language="en-US",
        tts_voice="en-US-GuyNeural",
        tts_voice_female="en-US-JennyNeural",
        tts_rate="+0%",
        tts_pitch="+0Hz",
        niche="tech",
        audience="American tech enthusiasts and professionals, 20-45 years",
        content_style="informative, objective, technical analysis, news-driven",
        content_rating="general",
        yt_category_id="28",  # Science & Technology
        region_code="US",
        extra_tags=["technology", "AI", "iPhone", "Android", "tech news", "gadgets"],
    ),

    "us_finance": ChannelProfile(
        id="us_finance",
        name="Finance Channel US",
        market="US",
        language="en-US",
        tts_voice="en-US-GuyNeural",
        tts_voice_female="en-US-JennyNeural",
        tts_rate="-3%",
        tts_pitch="-5Hz",
        niche="finance",
        audience="Americans interested in investing, personal finance, 25-55 years",
        content_style="authoritative, data-driven, financial analysis, success stories",
        content_rating="general",
        yt_category_id="27",
        region_code="US",
        extra_tags=["finance", "investing", "stock market", "crypto", "passive income", "wealth"],
    ),

    "us_education": ChannelProfile(
        id="us_education",
        name="Education Channel US",
        market="US",
        language="en-US",
        tts_voice="en-US-GuyNeural",
        tts_voice_female="en-US-JennyNeural",
        tts_rate="-2%",
        tts_pitch="+0Hz",
        niche="education",
        audience="American students and curious minds, 15-40 years",
        content_style="engaging, educational, storytelling, real facts",
        content_rating="general",
        yt_category_id="27",
        region_code="US",
        extra_tags=["history", "science", "education", "facts", "learning", "documentary"],
    ),

    "us_health": ChannelProfile(
        id="us_health",
        name="Health Channel US",
        market="US",
        language="en-US",
        tts_voice="en-US-JennyNeural",
        tts_voice_female="en-US-JennyNeural",
        tts_rate="-2%",
        tts_pitch="+0Hz",
        niche="health",
        audience="Americans focused on health and wellness, 25-55 years",
        content_style="informative, evidence-based, motivational, wellness",
        content_rating="general",
        yt_category_id="26",
        region_code="US",
        extra_tags=["health", "fitness", "nutrition", "wellness", "diet", "exercise"],
    ),

    # ── FINANCE DARK — High-RPM hybrid True Crime + Finance ($15-45 CPM) ────────

    "br_finance_dark": ChannelProfile(
        id="br_finance_dark",
        name="Finance Dark BR",
        market="BR",
        language="pt-BR",
        tts_voice="pt-BR-AntonioNeural",
        tts_voice_female="pt-BR-FranciscaNeural",
        tts_rate="-8%",
        tts_pitch="-15Hz",
        niche="finance_dark",
        audience="Brasileiros adultos 25-50, investidores e curiosos por crimes financeiros",
        content_style="investigativo, segunda pessoa imersiva, true crime + finanças, dramático",
        content_rating="mature",
        yt_category_id="27",
        region_code="BR",
        extra_tags=["crime financeiro", "fraude", "esquema", "golpe", "fraude financeira", "true crime finanças"],
        tts_tier="premium",
        elevenlabs_voice_id="pNInz6obpgDQGcFmaJgB",  # Adam deep narration pt-BR
        veo3_enabled=True,
        veo3_tier="fast",
    ),

    "us_finance_dark": ChannelProfile(
        id="us_finance_dark",
        name="Finance Dark US",
        market="US",
        language="en-US",
        tts_voice="en-US-GuyNeural",
        tts_voice_female="en-US-JennyNeural",
        tts_rate="-8%",
        tts_pitch="-15Hz",
        niche="finance_dark",
        audience="American adults 25-55, investors and true crime fans, highest CPM audience",
        content_style="investigative, second-person immersive, true crime + finance, thriller",
        content_rating="mature",
        yt_category_id="27",
        region_code="US",
        extra_tags=["financial crime", "fraud", "scam", "ponzi scheme", "true crime finance", "wall street crime"],
        tts_tier="premium",
        elevenlabs_voice_id="onwK4e9ZLuTAKqWW03F9",  # Daniel deep narrative en-US
        veo3_enabled=True,
        veo3_tier="fast",
    ),

    "gb_finance_dark": ChannelProfile(
        id="gb_finance_dark",
        name="Finance Dark UK",
        market="GB",
        language="en-GB",
        tts_voice="en-GB-RyanNeural",
        tts_voice_female="en-GB-SoniaNeural",
        tts_rate="-8%",
        tts_pitch="-15Hz",
        niche="finance_dark",
        audience="British adults 25-55, investors and true crime enthusiasts",
        content_style="investigative, second-person immersive, City of London scandals, BBC documentary tone",
        content_rating="mature",
        yt_category_id="27",
        region_code="GB",
        extra_tags=["financial crime UK", "city of london", "LIBOR scandal", "fraud UK", "true crime finance"],
        tts_tier="premium",
        elevenlabs_voice_id="VR6AewLTigWG4xSOukaG",  # Arnold British
        veo3_enabled=True,
        veo3_tier="fast",
    ),

    # ── EUROPE — United Kingdom ────────────────────────────────────────────────

    "gb_dark": ChannelProfile(
        id="gb_dark",
        name="Dark Channel UK",
        market="GB",
        language="en-GB",
        tts_voice="en-GB-RyanNeural",
        tts_voice_female="en-GB-SoniaNeural",
        tts_rate="-5%",
        tts_pitch="-10Hz",
        niche="dark",
        audience="British adults 18-45, interested in true crime, mysteries, British history",
        content_style="dark, investigative, dramatic, British storytelling, gothic",
        content_rating="mature",
        yt_category_id="27",
        region_code="GB",
        extra_tags=["true crime UK", "British mysteries", "serial killer", "unsolved UK", "dark"],
    ),

    "gb_education": ChannelProfile(
        id="gb_education",
        name="Education Channel UK",
        market="GB",
        language="en-GB",
        tts_voice="en-GB-RyanNeural",
        tts_voice_female="en-GB-SoniaNeural",
        tts_rate="-2%",
        tts_pitch="+0Hz",
        niche="education",
        audience="British students and curious minds, 15-40 years",
        content_style="engaging, BBC-style documentary, educational, factual",
        content_rating="general",
        yt_category_id="27",
        region_code="GB",
        extra_tags=["history", "British history", "science", "education", "documentary"],
    ),

    # ── EUROPE — France ───────────────────────────────────────────────────────

    "fr_dark": ChannelProfile(
        id="fr_dark",
        name="Canal Sombre FR",
        market="FR",
        language="fr-FR",
        tts_voice="fr-FR-HenriNeural",
        tts_voice_female="fr-FR-DeniseNeural",
        tts_rate="-5%",
        tts_pitch="-10Hz",
        niche="dark",
        audience="Français adultes 18-45, passionnés de crimes, mystères, histoire sombre",
        content_style="sombre, investigatif, dramatique, suspense, style documentaire français",
        content_rating="mature",
        yt_category_id="27",
        region_code="FR",
        extra_tags=["crime", "mystère", "serial killer", "paranormal", "affaires criminelles"],
    ),

    "fr_education": ChannelProfile(
        id="fr_education",
        name="Chaîne Éducation FR",
        market="FR",
        language="fr-FR",
        tts_voice="fr-FR-HenriNeural",
        tts_voice_female="fr-FR-DeniseNeural",
        tts_rate="-3%",
        tts_pitch="+0Hz",
        niche="education",
        audience="Français 15-40 ans, curieux et étudiants",
        content_style="éducatif, captivant, histoire vraie, curiosités scientifiques",
        content_rating="general",
        yt_category_id="27",
        region_code="FR",
        extra_tags=["histoire", "science", "éducation", "documentaire", "culture"],
    ),

    # ── EUROPE — Germany ─────────────────────────────────────────────────────

    "de_dark": ChannelProfile(
        id="de_dark",
        name="Dunkler Kanal DE",
        market="DE",
        language="de-DE",
        tts_voice="de-DE-ConradNeural",
        tts_voice_female="de-DE-KatjaNeural",
        tts_rate="-5%",
        tts_pitch="-10Hz",
        niche="dark",
        audience="Deutsche Erwachsene 18-45, interessiert an wahren Verbrechen, Mysterien",
        content_style="dunkel, investigativ, dramatisch, Spannung, Dokumentarstil",
        content_rating="mature",
        yt_category_id="27",
        region_code="DE",
        extra_tags=["wahre Verbrechen", "Mysteries", "Serial Killer", "Paranormal", "Dark"],
    ),

    "de_tech": ChannelProfile(
        id="de_tech",
        name="Tech Kanal DE",
        market="DE",
        language="de-DE",
        tts_voice="de-DE-ConradNeural",
        tts_voice_female="de-DE-KatjaNeural",
        tts_rate="+0%",
        tts_pitch="+0Hz",
        niche="tech",
        audience="Deutsche Technik-Enthusiasten und Profis, 20-45 Jahre",
        content_style="informativ, technisch präzise, Analyse, Neuigkeiten",
        content_rating="general",
        yt_category_id="28",
        region_code="DE",
        extra_tags=["Technologie", "KI", "Smartphones", "Tech News", "Gadgets"],
    ),

    # ── EUROPE — Spain ────────────────────────────────────────────────────────

    "es_dark": ChannelProfile(
        id="es_dark",
        name="Canal Oscuro ES",
        market="ES",
        language="es-ES",
        tts_voice="es-ES-AlvaroNeural",
        tts_voice_female="es-ES-ElviraNeural",
        tts_rate="-5%",
        tts_pitch="-10Hz",
        niche="dark",
        audience="Adultos españoles e hispanohablantes 18-45, crímenes, misterios, paranormal",
        content_style="oscuro, investigativo, dramático, suspenso, estilo documental",
        content_rating="mature",
        yt_category_id="27",
        region_code="ES",
        extra_tags=["crimen", "misterio", "asesino serial", "paranormal", "casos sin resolver"],
    ),

    "es_education": ChannelProfile(
        id="es_education",
        name="Canal Educación ES",
        market="ES",
        language="es-ES",
        tts_voice="es-ES-AlvaroNeural",
        tts_voice_female="es-ES-ElviraNeural",
        tts_rate="-3%",
        tts_pitch="+0Hz",
        niche="education",
        audience="Hispanohablantes 15-40 años, estudiantes y curiosos",
        content_style="educativo, entretenido, histórico, científico, documental",
        content_rating="general",
        yt_category_id="27",
        region_code="ES",
        extra_tags=["historia", "ciencia", "educación", "documental", "curiosidades"],
    ),

    # ── EUROPE — Italy ────────────────────────────────────────────────────────

    "it_dark": ChannelProfile(
        id="it_dark",
        name="Canale Oscuro IT",
        market="IT",
        language="it-IT",
        tts_voice="it-IT-DiegoNeural",
        tts_voice_female="it-IT-IsabellaNeural",
        tts_rate="-5%",
        tts_pitch="-10Hz",
        niche="dark",
        audience="Italiani adulti 18-45, interessati a crimini, misteri, storia oscura",
        content_style="oscuro, investigativo, drammatico, suspense, stile documentaristico",
        content_rating="mature",
        yt_category_id="27",
        region_code="IT",
        extra_tags=["crimine", "mistero", "serial killer", "paranormale", "casi irrisolti"],
    ),

}


def get_profile(profile_id: str) -> ChannelProfile:
    """Get a channel profile by ID. Raises KeyError if not found."""
    if profile_id not in PROFILES:
        available = ", ".join(sorted(PROFILES.keys()))
        raise KeyError(f"Profile '{profile_id}' not found. Available: {available}")
    return PROFILES[profile_id]


def list_profiles(market: Optional[str] = None, niche: Optional[str] = None) -> list[ChannelProfile]:
    """List profiles, optionally filtered by market and/or niche."""
    profiles = list(PROFILES.values())
    if market:
        profiles = [p for p in profiles if p.market.upper() == market.upper()]
    if niche:
        profiles = [p for p in profiles if p.niche.lower() == niche.lower()]
    return profiles


def get_markets() -> list[str]:
    return sorted(set(p.market for p in PROFILES.values()))


def get_niches() -> list[str]:
    return sorted(set(p.niche for p in PROFILES.values()))
