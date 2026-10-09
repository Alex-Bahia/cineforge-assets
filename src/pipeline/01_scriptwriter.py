"""Step 1 — Generate script via Gemini API (multi-market, multi-niche)."""
import json
import logging
import sys
from pathlib import Path

import google.generativeai as genai

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS, GEMINI_TEMPERATURE
from src.prompts.scriptwriter import (
    get_system_prompt, get_script_prompt, get_thumbnail_prompt, get_title_variants_prompt,
    DEFAULT_TONE, DEFAULT_TONE_EN,
    # Legacy compat
    SYSTEM_PROMPT, SCRIPT_PROMPT, TITLE_VARIANTS_PROMPT,
)

log = logging.getLogger(__name__)


def generate_script(
    topic: str,
    tone: str = "",
    duration_min: int = 8,
    output_path: Path | None = None,
    # Channel profile parameters
    language: str = "pt-BR",
    niche: str = "dark",
    audience: str = "",
    content_style: str = "",
    content_rating: str = "mature",
) -> dict:
    """
    Call Gemini and return parsed script JSON.

    Supports any market/language/niche via channel profile parameters.
    Defaults to Brazilian dark channel for backwards compatibility.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env")

    # Resolve defaults from niche/language if not provided
    if not tone:
        if language.startswith("pt"):
            tone = DEFAULT_TONE.get(niche, "informativo e envolvente")
        else:
            tone = DEFAULT_TONE_EN.get(niche, "informative and engaging")

    if not audience:
        audience = f"YouTube viewers interested in {niche} content"

    if not content_style:
        content_style = tone

    system_prompt = get_system_prompt(niche, language)

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=GEMINI_MAX_TOKENS,
            temperature=GEMINI_TEMPERATURE,
            response_mime_type="application/json",
        ),
    )

    prompt = get_script_prompt(
        topic=topic,
        tone=tone,
        duration_min=duration_min,
        audience=audience,
        content_style=content_style,
        language=language,
        niche=niche,
        content_rating=content_rating,
    )

    log.info("Calling Gemini for topic: %s [%s/%s]", topic, niche, language)
    response = model.generate_content(prompt)

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    script = json.loads(raw)
    script["_meta"] = {
        "topic": topic,
        "tone": tone,
        "model": GEMINI_MODEL,
        "language": language,
        "niche": niche,
        "market": language.split("-")[-1] if "-" in language else language,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(script, ensure_ascii=False, indent=2))
        log.info("Script saved to %s", output_path)

    return script


def generate_title_variants(topic: str, language: str = "pt-BR") -> list[str]:
    """Generate 5 alternative title options in the target language."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=1.0,
        ),
    )
    prompt = get_title_variants_prompt(topic=topic, language=language)
    response = model.generate_content(prompt)
    data = json.loads(response.text)
    return data.get("titulos", [])


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="Generate YouTube script via Gemini (any market/niche)")
    p.add_argument("topic", help='Topic e.g. "The most disturbing serial killer case"')
    p.add_argument("--tone", default="")
    p.add_argument("--minutes", type=int, default=8)
    p.add_argument("--out", help="Path to save JSON script")
    p.add_argument("--language", default="pt-BR", help="Language code: pt-BR, en-US, en-GB, fr-FR, de-DE, es-ES, it-IT")
    p.add_argument("--niche", default="dark", help="Niche: dark, sports, kids, tech, finance, education, health, entertainment, news, cooking")
    p.add_argument("--audience", default="")
    p.add_argument("--content-style", default="")
    p.add_argument("--content-rating", default="general", choices=["general", "teen", "mature"])
    args = p.parse_args()

    out = Path(args.out) if args.out else Path("output") / "scripts" / f"{args.topic[:40].replace(' ', '_')}.json"
    script = generate_script(
        args.topic, args.tone, args.minutes, out,
        language=args.language,
        niche=args.niche,
        audience=args.audience,
        content_style=args.content_style,
        content_rating=args.content_rating,
    )
    print(f"\n✅ Script generated: {len(script['cenas'])} scenes, ~{script.get('duracao_estimada_segundos', 0)//60}min")
    print(f"   Title: {script.get('titulo', 'N/A')}")
    print(f"   Language: {args.language} | Niche: {args.niche}")
