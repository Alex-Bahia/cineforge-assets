"""Step 1 — Generate script via Gemini API."""
import json
import logging
import sys
from pathlib import Path

import google.generativeai as genai

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS, GEMINI_TEMPERATURE
from src.prompts.scriptwriter import SYSTEM_PROMPT, SCRIPT_PROMPT, TITLE_VARIANTS_PROMPT

log = logging.getLogger(__name__)


def generate_script(
    topic: str,
    tone: str = "suspense e mistério",
    duration_min: int = 8,
    output_path: Path | None = None,
) -> dict:
    """Call Gemini and return parsed script JSON."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            max_output_tokens=GEMINI_MAX_TOKENS,
            temperature=GEMINI_TEMPERATURE,
            response_mime_type="application/json",
        ),
    )

    # scenes: ~10-12 per minute of video
    min_scenes = duration_min * 9
    max_scenes = duration_min * 13

    prompt = SCRIPT_PROMPT.format(
        topic=topic,
        tone=tone,
        duration_min=duration_min,
        min_scenes=min_scenes,
        max_scenes=max_scenes,
    )

    log.info("Calling Gemini for topic: %s", topic)
    response = model.generate_content(prompt)

    raw = response.text.strip()
    # Strip markdown code fences if model ignores mime type
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    script = json.loads(raw)
    script["_meta"] = {"topic": topic, "tone": tone, "model": GEMINI_MODEL}

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(script, ensure_ascii=False, indent=2))
        log.info("Script saved to %s", output_path)

    return script


def generate_title_variants(topic: str) -> list[str]:
    """Generate 5 alternative title options."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=1.0,
        ),
    )
    prompt = TITLE_VARIANTS_PROMPT.format(topic=topic)
    response = model.generate_content(prompt)
    data = json.loads(response.text)
    return data.get("titulos", [])


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="Generate dark YouTube script via Gemini")
    p.add_argument("topic", help='Topic e.g. "O caso mais perturbador da história do Brasil"')
    p.add_argument("--tone", default="suspense e mistério")
    p.add_argument("--minutes", type=int, default=8)
    p.add_argument("--out", help="Path to save JSON script")
    args = p.parse_args()

    out = Path(args.out) if args.out else Path("output") / "scripts" / f"{args.topic[:40].replace(' ', '_')}.json"
    script = generate_script(args.topic, args.tone, args.minutes, out)
    print(f"\n✅ Script generated: {len(script['cenas'])} scenes, ~{script.get('duracao_estimada_segundos', 0)//60}min")
    print(f"   Title: {script['titulo']}")
