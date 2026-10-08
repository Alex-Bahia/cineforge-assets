"""
Frankenstein Video Generator
Pipeline: Google Sheets → Claude roteiro → edge-tts → Pillow slides → MoviePy MP4
100% gratuito, roda na VPS Hermes sem APIs pagas.
"""

import asyncio
import os
import sys
import textwrap
import tempfile
import shutil
from pathlib import Path
from typing import Optional

# ── Dependências (todas listadas em requirements.txt) ─────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

try:
    import edge_tts
    _EDGETTS_OK = True
except ImportError:
    _EDGETTS_OK = False

try:
    from moviepy.editor import (
        ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip,
        TextClip, ColorClip,
    )
    _MOVIEPY_OK = True
except ImportError:
    _MOVIEPY_OK = False

# ── Configuração via variáveis de ambiente ─────────────────────────────────────
VOICE = os.getenv("EDGE_TTS_VOICE", "pt-BR-FranciscaNeural")
OUTPUT_DIR = Path(os.getenv("VIDEO_OUTPUT_DIR", "output/videos"))
ASSETS_DIR = Path(os.getenv("VIDEO_ASSETS_DIR", "assets"))
SLIDE_W = int(os.getenv("SLIDE_WIDTH", "1920"))
SLIDE_H = int(os.getenv("SLIDE_HEIGHT", "1080"))
FPS = int(os.getenv("VIDEO_FPS", "30"))

# Paleta dark padrão (personalizável via env)
BG_COLOR = tuple(int(x) for x in os.getenv("SLIDE_BG", "15,15,25").split(","))
TEXT_COLOR = tuple(int(x) for x in os.getenv("SLIDE_TEXT", "240,240,255").split(","))
ACCENT_COLOR = tuple(int(x) for x in os.getenv("SLIDE_ACCENT", "80,160,255").split(","))


def check_dependencies() -> bool:
    missing = []
    if not _PIL_OK:
        missing.append("Pillow (pip install Pillow)")
    if not _EDGETTS_OK:
        missing.append("edge-tts (pip install edge-tts)")
    if not _MOVIEPY_OK:
        missing.append("moviepy (pip install moviepy)")
    if missing:
        print("❌ Dependências faltando:", ", ".join(missing))
        return False
    return True


def _find_font(size: int) -> ImageFont.ImageFont:
    """Tenta fontes do sistema; fallback para default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def gerar_slide(
    titulo: str,
    corpo: str,
    indice: int,
    total: int,
    caminho: Path,
) -> None:
    """Gera um slide PNG com título e corpo de texto."""
    img = Image.new("RGB", (SLIDE_W, SLIDE_H), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Barra superior com acento
    draw.rectangle([(0, 0), (SLIDE_W, 8)], fill=ACCENT_COLOR)

    # Número do slide
    fonte_num = _find_font(32)
    draw.text((60, 40), f"{indice}/{total}", font=fonte_num, fill=ACCENT_COLOR)

    # Título
    fonte_titulo = _find_font(72)
    titulo_wrapped = "\n".join(textwrap.wrap(titulo, width=38))
    draw.text((60, 120), titulo_wrapped, font=fonte_titulo, fill=TEXT_COLOR)

    # Corpo
    fonte_corpo = _find_font(44)
    corpo_wrapped = "\n".join(textwrap.wrap(corpo, width=60))
    draw.text((60, 320), corpo_wrapped, font=fonte_corpo, fill=(*TEXT_COLOR[:3], 200))

    # Barra inferior
    draw.rectangle([(0, SLIDE_H - 6), (SLIDE_W, SLIDE_H)], fill=ACCENT_COLOR)

    img.save(str(caminho), "PNG")


async def gerar_audio(texto: str, caminho: Path) -> None:
    """Gera narração MP3 via edge-tts (Microsoft, gratuito)."""
    communicate = edge_tts.Communicate(texto, VOICE)
    await communicate.save(str(caminho))


def montar_video(
    slides: list[Path],
    audios: list[Path],
    saida: Path,
) -> Path:
    """Monta o vídeo final combinando slides + áudios com MoviePy."""
    clips = []
    for slide_path, audio_path in zip(slides, audios):
        audio = AudioFileClip(str(audio_path))
        img_clip = (
            ImageClip(str(slide_path))
            .set_duration(audio.duration + 0.5)
            .set_audio(audio)
        )
        clips.append(img_clip)

    video_final = concatenate_videoclips(clips, method="compose")
    saida.parent.mkdir(parents=True, exist_ok=True)
    video_final.write_videofile(
        str(saida),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )
    video_final.close()
    return saida


async def gerar_video_frankenstein(
    topico: str,
    roteiro: list[dict],  # [{"titulo": ..., "corpo": ..., "narracao": ...}]
    nome_saida: Optional[str] = None,
) -> Path:
    """
    Pipeline principal. Recebe o roteiro já gerado pelo Claude
    e produz o MP4 final.

    roteiro: lista de dicts com chaves titulo, corpo, narracao
    """
    if not check_dependencies():
        raise RuntimeError("Dependências faltando — veja mensagem acima.")

    tmpdir = Path(tempfile.mkdtemp(prefix="cineforge_"))
    slides: list[Path] = []
    audios: list[Path] = []

    try:
        total = len(roteiro)
        print(f"🎬 Gerando {total} slides para: {topico}")

        for i, cena in enumerate(roteiro, start=1):
            slide_path = tmpdir / f"slide_{i:03d}.png"
            audio_path = tmpdir / f"audio_{i:03d}.mp3"

            # Slide visual
            gerar_slide(
                titulo=cena.get("titulo", f"Parte {i}"),
                corpo=cena.get("corpo", ""),
                indice=i,
                total=total,
                caminho=slide_path,
            )
            slides.append(slide_path)
            print(f"  ✅ Slide {i}/{total}")

            # Narração
            narracao = cena.get("narracao") or cena.get("corpo", "")
            await gerar_audio(narracao, audio_path)
            audios.append(audio_path)
            print(f"  🎙️  Áudio {i}/{total}")

        # Montagem final
        if nome_saida is None:
            slug = "".join(c if c.isalnum() else "_" for c in topico[:40]).lower()
            nome_saida = f"{slug}.mp4"

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        caminho_saida = OUTPUT_DIR / nome_saida

        print("🎞️  Montando vídeo final...")
        montar_video(slides, audios, caminho_saida)
        print(f"✅ Vídeo salvo: {caminho_saida}")
        return caminho_saida

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def roteiro_exemplo(topico: str) -> list[dict]:
    """Roteiro de exemplo para testar sem chamar o Claude."""
    return [
        {
            "titulo": f"O que é {topico}?",
            "corpo": f"Vamos entender tudo sobre {topico} de forma simples e direta.",
            "narracao": f"Você sabe o que é {topico}? Neste vídeo vou te explicar tudo de forma simples.",
        },
        {
            "titulo": "Por que isso importa?",
            "corpo": "Entender esse tema pode mudar a forma como você vê o mundo.",
            "narracao": "Mas por que isso é tão importante? Veja só o que a ciência diz sobre isso.",
        },
        {
            "titulo": "Como aplicar no dia a dia",
            "corpo": "3 passos práticos que você pode começar hoje mesmo.",
            "narracao": "Agora, veja como você pode aplicar esse conhecimento no seu dia a dia com apenas três passos.",
        },
        {
            "titulo": "Conclusão",
            "corpo": "Agora você sabe! Compartilhe esse vídeo com quem precisa ver isso.",
            "narracao": "E aí, gostou? Se esse conteúdo foi útil, compartilhe com um amigo e não esqueça de se inscrever!",
        },
    ]


# ── CLI direto ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gera vídeo Frankenstein sem APIs pagas")
    parser.add_argument("topico", help="Tópico do vídeo")
    parser.add_argument("--saida", help="Nome do arquivo de saída (ex: meu_video.mp4)")
    parser.add_argument("--teste", action="store_true", help="Usa roteiro de exemplo")
    args = parser.parse_args()

    if args.teste:
        roteiro = roteiro_exemplo(args.topico)
    else:
        # Importa o agente Claude para gerar o roteiro real
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            from claude_agent import CineForgeAgent  # type: ignore
            agente = CineForgeAgent()
            resultado = agente.gerar_roteiro_video(args.topico)
            roteiro = resultado.get("roteiro", roteiro_exemplo(args.topico))
        except Exception as e:
            print(f"⚠️  Claude indisponível ({e}), usando roteiro de exemplo.")
            roteiro = roteiro_exemplo(args.topico)

    asyncio.run(gerar_video_frankenstein(args.topico, roteiro, args.saida))
