"""
Frankenstein Video Generator
Pipeline: Google Sheets → Claude roteiro → Pollinations.ai imagem → edge-tts → MoviePy MP4
100% gratuito, roda na VPS Hermes sem APIs pagas.
"""

import asyncio
import os
import sys
import textwrap
import tempfile
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional

# ── Dependências (todas listadas em requirements.txt) ─────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

try:
    import edge_tts
    _EDGETTS_OK = True
except ImportError:
    _EDGETTS_OK = False

try:
    try:
        from moviepy.editor import (
            ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip,
            TextClip, ColorClip,
        )
    except ImportError:
        from moviepy import (
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

# Pollinations.ai — API de imagem 100% gratuita, sem chave
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&nologo=true&model=flux"
USE_AI_IMAGES = os.getenv("USE_AI_IMAGES", "true").lower() == "true"


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


def _find_font(size: int):
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


def buscar_imagem_ia(prompt_imagem: str, caminho: Path, tentativas: int = 3) -> bool:
    """Busca imagem da Pollinations.ai (gratuito, sem chave). Retorna True se OK.
    Faz até `tentativas` retries com backoff exponencial para evitar rate-limit 402.
    """
    import time, random
    for tentativa in range(1, tentativas + 1):
        # Backoff exponencial: 5-8s na 1ª, 10-14s na 2ª, 20-26s na 3ª
        delay = random.uniform(5, 8) * (2 ** (tentativa - 1))
        if tentativa > 1:
            print(f"  🔄 Retry {tentativa}/{tentativas} Pollinations (aguardando {delay:.0f}s)...")
        time.sleep(delay)
        try:
            prompt_enc = urllib.parse.quote(prompt_imagem)
            url = POLLINATIONS_URL.format(prompt=prompt_enc, w=SLIDE_W, h=SLIDE_H)
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"
            })
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            if len(data) < 1000:
                raise ValueError("Resposta muito pequena — provável erro")
            with open(caminho, "wb") as f:
                f.write(data)
            Image.open(caminho).verify()
            return True
        except Exception as e:
            if tentativa < tentativas:
                print(f"  ⚠️  Pollinations tentativa {tentativa} falhou ({e}), tentando novamente...")
            else:
                print(f"  ⚠️  Pollinations falhou após {tentativas} tentativas ({e}), usando slide gradiente.")
    return False


def gerar_slide(
    titulo: str,
    corpo: str,
    indice: int,
    total: int,
    caminho: Path,
    imagem_fundo: Optional[Path] = None,
) -> None:
    """Gera slide PNG. Se imagem_fundo fornecida, usa como fundo com overlay de texto."""
    if imagem_fundo and imagem_fundo.exists():
        # Modo IA: imagem de fundo + overlay escuro + texto
        img = Image.open(imagem_fundo).convert("RGB").resize((SLIDE_W, SLIDE_H))

        # Overlay escuro semitransparente para legibilidade
        overlay = Image.new("RGBA", (SLIDE_W, SLIDE_H), (0, 0, 0, 170))
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay).convert("RGB")
    else:
        # Fallback: gradiente colorido cinematográfico em vez de cor sólida preta
        import random as _rnd
        paletas = [
            [(10, 20, 60), (40, 10, 80)],    # azul-roxo
            [(60, 10, 10), (20, 40, 10)],    # vermelho-verde escuro
            [(10, 40, 60), (5, 15, 45)],     # azul petróleo
            [(40, 20, 5),  (60, 40, 10)],    # âmbar escuro
            [(15, 10, 50), (50, 10, 30)],    # índigo-vinho
        ]
        cor_a, cor_b = _rnd.choice(paletas)
        img = Image.new("RGB", (SLIDE_W, SLIDE_H))
        pixels = img.load()
        for y in range(SLIDE_H):
            t = y / SLIDE_H
            r = int(cor_a[0] * (1 - t) + cor_b[0] * t)
            g = int(cor_a[1] * (1 - t) + cor_b[1] * t)
            b = int(cor_a[2] * (1 - t) + cor_b[2] * t)
            for x in range(SLIDE_W):
                pixels[x, y] = (r, g, b)

    draw = ImageDraw.Draw(img)

    # Barra superior com acento
    draw.rectangle([(0, 0), (SLIDE_W, 8)], fill=ACCENT_COLOR)

    # Número do slide
    fonte_num = _find_font(32)
    draw.text((60, 40), f"{indice}/{total}", font=fonte_num, fill=ACCENT_COLOR)

    # Título com sombra para contraste sobre imagem
    fonte_titulo = _find_font(72)
    titulo_wrapped = "\n".join(textwrap.wrap(titulo, width=38))
    # Sombra
    draw.text((63, 123), titulo_wrapped, font=fonte_titulo, fill=(0, 0, 0))
    draw.text((60, 120), titulo_wrapped, font=fonte_titulo, fill=TEXT_COLOR)

    # Corpo com sombra
    fonte_corpo = _find_font(44)
    corpo_wrapped = "\n".join(textwrap.wrap(corpo, width=60))
    draw.text((63, 323), corpo_wrapped, font=fonte_corpo, fill=(0, 0, 0))
    draw.text((60, 320), corpo_wrapped, font=fonte_corpo, fill=TEXT_COLOR)

    # Barra inferior
    draw.rectangle([(0, SLIDE_H - 6), (SLIDE_W, SLIDE_H)], fill=ACCENT_COLOR)

    img.save(str(caminho), "PNG")


async def gerar_audio(texto: str, caminho: Path) -> None:
    """Gera narração MP3 — tenta edge-tts, fallback para gTTS (funciona em VPS)."""
    # Tenta edge-tts primeiro
    if _EDGETTS_OK:
        try:
            communicate = edge_tts.Communicate(texto, VOICE)
            await communicate.save(str(caminho))
            return
        except Exception as e:
            print(f"  ⚠️  edge-tts falhou ({e}), tentando gTTS...")

    # Fallback: gTTS (Google, funciona em VPS)
    try:
        from gtts import gTTS
        tts = gTTS(text=texto, lang="pt", slow=False)
        tts.save(str(caminho))
        return
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️  gTTS falhou ({e}), usando silêncio...")

    # Último fallback: silêncio sintético via ffmpeg
    import subprocess as sp
    duracao = max(3, len(texto) // 15)
    sp.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
         "-t", str(duracao), "-q:a", "9", "-acodec", "libmp3lame", str(caminho)],
        capture_output=True, check=True,
    )


def montar_video(
    slides: list[Path],
    audios: list[Path],
    saida: Path,
) -> Path:
    """Monta o vídeo final combinando slides + áudios com MoviePy."""
    clips = []
    for slide_path, audio_path in zip(slides, audios):
        audio = AudioFileClip(str(audio_path))
        base = ImageClip(str(slide_path))
        # MoviePy 2.x usa with_duration/with_audio; 1.x usa set_duration/set_audio
        if hasattr(base, 'with_duration'):
            img_clip = base.with_duration(audio.duration + 0.5).with_audio(audio)
        else:
            img_clip = base.set_duration(audio.duration + 0.5).set_audio(audio)
        clips.append(img_clip)

    video_final = concatenate_videoclips(clips, method="compose")
    saida.parent.mkdir(parents=True, exist_ok=True)
    video_final.write_videofile(
        str(saida),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="2000k",    # bitrate mínimo para qualidade visual aceitável
        audio_bitrate="128k",
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
        print(f"🎬 Gerando {total} cenas para: {topico}")

        for i, cena in enumerate(roteiro, start=1):
            slide_path = tmpdir / f"slide_{i:03d}.png"
            audio_path = tmpdir / f"audio_{i:03d}.mp3"
            img_ia_path = tmpdir / f"img_ia_{i:03d}.jpg"

            # Imagem de IA via Pollinations (gratuito)
            imagem_fundo = None
            if USE_AI_IMAGES:
                prompt_img = cena.get("prompt_imagem") or (
                    f"{cena.get('titulo', topico)}, {topico}, "
                    "cinematic photography, high quality, 4K, realistic"
                )
                print(f"  🎨 Buscando imagem IA {i}/{total}...")
                if buscar_imagem_ia(prompt_img, img_ia_path):
                    imagem_fundo = img_ia_path
                    print(f"  ✅ Imagem IA {i}/{total}")

            # Slide com imagem de fundo (ou fallback texto)
            gerar_slide(
                titulo=cena.get("titulo", f"Parte {i}"),
                corpo=cena.get("corpo", ""),
                indice=i,
                total=total,
                caminho=slide_path,
                imagem_fundo=imagem_fundo,
            )
            slides.append(slide_path)
            print(f"  🖼️  Slide {i}/{total}")

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
            "prompt_imagem": f"{topico}, concept art, vibrant colors, cinematic, 4K",
        },
        {
            "titulo": "Por que isso importa?",
            "corpo": "Entender esse tema pode mudar a forma como você vê o mundo.",
            "narracao": "Mas por que isso é tão importante? Veja só o que a ciência diz sobre isso.",
            "prompt_imagem": f"importance of {topico}, dramatic lighting, professional photography",
        },
        {
            "titulo": "Como aplicar no dia a dia",
            "corpo": "3 passos práticos que você pode começar hoje mesmo.",
            "narracao": "Agora, veja como você pode aplicar esse conhecimento no seu dia a dia com apenas três passos.",
            "prompt_imagem": f"person applying {topico} in daily life, realistic, natural light",
        },
        {
            "titulo": "Conclusão",
            "corpo": "Agora você sabe! Compartilhe esse vídeo com quem precisa ver isso.",
            "narracao": "E aí, gostou? Se esse conteúdo foi útil, compartilhe com um amigo e não esqueça de se inscrever!",
            "prompt_imagem": f"{topico} success results, inspiring, bright colors, motivational",
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
