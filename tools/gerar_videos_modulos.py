"""
Gera vídeos de demonstração para cada um dos 12 módulos do cockpit CineForge.
Usa o pipeline Frankenstein existente (edge-tts + Pillow + MoviePy + Pollinations.ai).

Estilo visual: alien predador sci-fi — personagem caçador intergaláctico,
armadura metálica cromada PRETA com LEDs e neon VERMELHO intenso,
fundo preto puro, telas holográficas vermelhas, render 3D hyper-realista cinematográfico.

Rodar na VPS Hermes:
    cd /home/ubuntu/cineforge-assets
    python3 tools/gerar_videos_modulos.py --no-ai-images

Os MP4s serão salvos em:
    iai-studios/public/videos/briefing/card{1..12}/demo.mp4

Depois fazer o commit dos arquivos gerados:
    git add iai-studios/public/videos/briefing/
    git commit -m "assets: add module demo videos"
    git push
"""

import asyncio
import sys
from pathlib import Path

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.video_generator import gerar_video_frankenstein

# ── Estilo base dos prompts de imagem ─────────────────────────────────────────
# Sufixo fixo para manter coerência visual entre todos os cards.
# Estilo baseado nos vídeos reais do card 1 e card 2: predador metálico cromado
# preto com neon VERMELHO, fundo preto puro, render 3D hyper-realista cinematográfico.
_STYLE = (
    "alien predator with black chrome metallic armor, pure black background, "
    "intense red neon glow, red LED accents on armor joints, glowing red eyes, "
    "red holographic UI displays, red laser lights, hyper-realistic 3D render, "
    "cinematic dark sci-fi, dramatic lighting, no watermark, no text overlay"
)

# ── Roteiros dos 12 módulos ────────────────────────────────────────────────────
# Cada módulo tem 3 cenas curtas (≈8s cada = vídeo ~24s)

MODULOS = [
    {
        "index": 1,
        "topico": "Roteiro IA",
        "roteiro": [
            {
                "titulo": "ROTEIRO IA",
                "corpo": "Gere roteiros profissionais em segundos com inteligência artificial.",
                "narracao": "O módulo Roteiro IA transforma qualquer tópico em um script completo e otimizado para YouTube.",
                "prompt_imagem": f"alien predator holding red holographic script floating in clawed hands, dark command center, {_STYLE}",
            },
            {
                "titulo": "COMO FUNCIONA",
                "corpo": "Informe o tópico, nicho e duração desejada.",
                "narracao": "Basta informar o tópico, o nicho do canal e a duração. A IA gera título, introdução, corpo e call to action.",
                "prompt_imagem": f"alien predator eye glowing red scanning red holographic data streams, dark tech command room, {_STYLE}",
            },
            {
                "titulo": "ATIVE AGORA",
                "corpo": "Clique no módulo ROTEIRO IA no cockpit para começar.",
                "narracao": "Clique no módulo Roteiro IA no cockpit e comece a produzir conteúdo profissional imediatamente.",
                "prompt_imagem": f"alien predator activating red glowing control panel with metallic claws, red energy sparks, dark sci-fi command station, {_STYLE}",
            },
        ],
    },
    {
        "index": 2,
        "topico": "Trilha Neural",
        "roteiro": [
            {
                "titulo": "TRILHA NEURAL",
                "corpo": "Composição musical adaptativa gerada por inteligência artificial.",
                "narracao": "O módulo Trilha Neural cria músicas únicas para cada vídeo, adaptadas ao mood e duração.",
                "prompt_imagem": f"alien predator surrounded by floating red musical soundwaves and audio frequencies, dark studio command center, {_STYLE}",
            },
            {
                "titulo": "MOODS DISPONÍVEIS",
                "corpo": "Epic, suspense, drama, action, calm, inspirational.",
                "narracao": "Escolha entre diversos moods: épico para documentários, suspense para true crime, inspiracional para motivação.",
                "prompt_imagem": f"predator mask with red audio equalizer visualization reflecting on visor, dark tech environment, {_STYLE}",
            },
            {
                "titulo": "SEM ROYALTIES",
                "corpo": "Música 100% original. Zero problemas de copyright.",
                "narracao": "Todas as trilhas geradas são únicas e livres de royalties. Publique sem medo de demonetização.",
                "prompt_imagem": f"alien predator roaring with red sound waves exploding outward, red plasma energy burst, epic sci-fi command room, {_STYLE}",
            },
        ],
    },
    {
        "index": 3,
        "topico": "Legacy Cloning",
        "roteiro": [
            {
                "titulo": "LEGACY CLONING",
                "corpo": "Clone sua voz com tecnologia de IA avançada.",
                "narracao": "O módulo Legacy Cloning replica sua voz com fidelidade impressionante usando modelos neurais.",
                "prompt_imagem": f"alien predator DNA strand cloning in red neon sci-fi lab, two identical hunters emerging from red mist, {_STYLE}",
            },
            {
                "titulo": "COMO CLONAR",
                "corpo": "Grave 30 segundos de áudio e deixe a IA fazer o resto.",
                "narracao": "Basta gravar trinta segundos da sua voz. O sistema aprende seus padrões e reproduz qualquer texto.",
                "prompt_imagem": f"alien predator voice waveform captured in glowing red orb, dark sci-fi cloning chamber, red neon lights, {_STYLE}",
            },
            {
                "titulo": "ESCALE SUA VOZ",
                "corpo": "Gere horas de narração sem gravar uma única palavra.",
                "narracao": "Com o clone pronto, você pode gerar horas de narração sem precisar gravar nada. Escale sua produção.",
                "prompt_imagem": f"army of predator clones fading into dark red mist, infinite duplication in dark corridor, {_STYLE}",
            },
        ],
    },
    {
        "index": 4,
        "topico": "Games Universe",
        "roteiro": [
            {
                "titulo": "GAMES UNIVERSE",
                "corpo": "Ambientes virtuais gerados por IA para seus vídeos de games.",
                "narracao": "O módulo Games Universe cria cenários, thumbnails e arte conceitual para conteúdo gamer.",
                "prompt_imagem": f"alien predator stepping through red portal into game universe, red energy frame around portal, {_STYLE}",
            },
            {
                "titulo": "ARTE INSTANTÂNEA",
                "corpo": "Thumbnails épicas geradas em segundos.",
                "narracao": "Descreva a cena que imagina e o sistema gera a imagem perfeita para sua thumbnail de games.",
                "prompt_imagem": f"predator metallic hand placing game thumbnail card glowing with red energy on dark surface, {_STYLE}",
            },
            {
                "titulo": "SEM LIMITES",
                "corpo": "Qualquer universo, qualquer estilo visual.",
                "narracao": "Do pixel art ao hiper-realismo. Qualquer estilo de jogo, qualquer universo. Sem limites criativos.",
                "prompt_imagem": f"alien predator surrounded by multiple red-framed game world portals, sci-fi collage of realities, dark space, {_STYLE}",
            },
        ],
    },
    {
        "index": 5,
        "topico": "Influencers IA",
        "roteiro": [
            {
                "titulo": "INFLUENCERS IA",
                "corpo": "Avatares digitais que representam sua marca 24/7.",
                "narracao": "O módulo Influencers IA cria personas digitais únicas que podem apresentar seu conteúdo automaticamente.",
                "prompt_imagem": f"alien predator creating red holographic digital avatar with metallic glowing claws, dark command center, {_STYLE}",
            },
            {
                "titulo": "CRIE SEU AVATAR",
                "corpo": "Defina nome, personalidade e estilo visual.",
                "narracao": "Você escolhe o nome, a personalidade e o estilo visual. O avatar fica ativo enquanto você dorme.",
                "prompt_imagem": f"predator helmet reflecting multiple red avatar options in visor, character selection interface glowing red, {_STYLE}",
            },
            {
                "titulo": "AUTONOMIA TOTAL",
                "corpo": "Produção de conteúdo sem aparecer na câmera.",
                "narracao": "Produza conteúdo sem precisar aparecer. Seu avatar trabalha para você em qualquer idioma.",
                "prompt_imagem": f"alien predator watching red digital avatar multiply across global red-lit screens, dark command center, {_STYLE}",
            },
        ],
    },
    {
        "index": 6,
        "topico": "DNA Viral",
        "roteiro": [
            {
                "titulo": "DNA VIRAL",
                "corpo": "Analise os segredos dos canais de maior sucesso.",
                "narracao": "O módulo DNA Viral decodifica o que faz um canal explodir no YouTube usando análise de IA.",
                "prompt_imagem": f"alien predator scanning enemy data code glowing red in dark command room, red thermal vision overlay, {_STYLE}",
            },
            {
                "titulo": "ANÁLISE PROFUNDA",
                "corpo": "Frequência, ganchos, títulos, thumbnails — tudo analisado.",
                "narracao": "Cole a URL de qualquer canal concorrente e receba uma análise completa: frequência, ganchos usados, padrões de título.",
                "prompt_imagem": f"predator analyzing red data streams with red targeting laser crosshair, competitor information decoded on red holographic screen, {_STYLE}",
            },
            {
                "titulo": "REPLICAR O SUCESSO",
                "corpo": "Descubra o que funciona antes de investir tempo.",
                "narracao": "Descubra o que funciona no seu nicho antes de produzir qualquer vídeo. Economize meses de tentativa e erro.",
                "prompt_imagem": f"alien predator trophy wall with red glowing data trophies, victory scene in dark tech chamber, {_STYLE}",
            },
        ],
    },
    {
        "index": 7,
        "topico": "Storyboard Tático",
        "roteiro": [
            {
                "titulo": "STORYBOARD",
                "corpo": "Visualize seu vídeo antes de gravar.",
                "narracao": "O módulo Storyboard transforma seu roteiro em quadros visuais para planejar cada cena.",
                "prompt_imagem": f"alien predator reviewing red holographic storyboard panels floating in dark command room, tactical planning, {_STYLE}",
            },
            {
                "titulo": "CENAS PLANEJADAS",
                "corpo": "Cada corte planejado para máximo impacto.",
                "narracao": "Cada corte, cada transição, cada momento de impacto planejado com precisão antes de gravar.",
                "prompt_imagem": f"predator red tactical vision overlay showing scene composition grids, red cinematic planning interface, {_STYLE}",
            },
            {
                "titulo": "DO ROTEIRO AO VÍDEO",
                "corpo": "Cole seu roteiro JSON e visualize em segundos.",
                "narracao": "Cole o roteiro gerado pela IA e o sistema monta automaticamente os frames visuais do seu vídeo.",
                "prompt_imagem": f"alien predator activating red holographic storyboard from datapad, text transforming to red visual frames, {_STYLE}",
            },
        ],
    },
    {
        "index": 8,
        "topico": "Dublagem AI",
        "roteiro": [
            {
                "titulo": "DUBLAGEM AI",
                "corpo": "Narração profissional em português com emoção real.",
                "narracao": "O módulo Dublagem AI gera narrações profissionais com vozes neurais de alta qualidade.",
                "prompt_imagem": f"alien predator mandibles vibrating with red sound waves and voice energy, professional voice generation, {_STYLE}",
            },
            {
                "titulo": "VOZES DISPONÍVEIS",
                "corpo": "Masculinas e femininas, diferentes estilos e tons.",
                "narracao": "Múltiplas vozes disponíveis: femininas, masculinas, jovens, maduras. Cada uma com características únicas.",
                "prompt_imagem": f"multiple alien predator silhouettes each emitting red sound auras of different intensities, dark sci-fi command room, {_STYLE}",
            },
            {
                "titulo": "SEM GRAVAR",
                "corpo": "Produza narrações sem usar seu próprio microfone.",
                "narracao": "Produza narrações profissionais sem usar microfone. A IA faz o trabalho com qualidade de estúdio.",
                "prompt_imagem": f"alien predator metallic hand holding red glowing microphone orb generating red voice waves, dark studio, {_STYLE}",
            },
        ],
    },
    {
        "index": 9,
        "topico": "Edição Tática",
        "roteiro": [
            {
                "titulo": "EDIÇÃO TÁTICA",
                "corpo": "Montagem automática de vídeos completos com IA.",
                "narracao": "O módulo Edição Tática combina roteiro, imagens IA, narração e música em um vídeo pronto para publicar.",
                "prompt_imagem": f"alien predator operating red holographic editing timeline with metallic claws, dark video production command center, {_STYLE}",
            },
            {
                "titulo": "PIPELINE COMPLETA",
                "corpo": "Roteiro → Imagens → Narração → Música → MP4.",
                "narracao": "Roteiro, imagens de IA, narração neural, trilha musical. Tudo automático. Um MP4 pronto em minutos.",
                "prompt_imagem": f"predator wristpad showing automated production pipeline glowing red, red workflow sequence display, dark sci-fi room, {_STYLE}",
            },
            {
                "titulo": "PUBLIQUE HOJE",
                "corpo": "De ideia a vídeo publicado em menos de 30 minutos.",
                "narracao": "De uma ideia a um vídeo publicado no YouTube em menos de trinta minutos. Isso é o CineForge.",
                "prompt_imagem": f"alien predator launching red energy beam into dark space, red rocket of light, publishing explosion of red energy, {_STYLE}",
            },
        ],
    },
    {
        "index": 10,
        "topico": "Color Grade",
        "roteiro": [
            {
                "titulo": "COLOR GRADE",
                "corpo": "LUTs cinematográficos para seu estilo visual.",
                "narracao": "O módulo Color Grade aplica paletas visuais cinematográficas para dar identidade única ao seu canal.",
                "prompt_imagem": f"alien predator stepping through red color grade portal, before-after visual transformation from dark to vivid red, cinematic, {_STYLE}",
            },
            {
                "titulo": "PRESETS PRONTOS",
                "corpo": "Dark, thriller, drama, epic, vintage — escolha seu estilo.",
                "narracao": "Presets prontos para cada nicho: dark para true crime, épico para documentários, drama para narrativas.",
                "prompt_imagem": f"predator visor displaying red color palette selection interface, multiple LUT previews in red tones glowing, {_STYLE}",
            },
            {
                "titulo": "IDENTIDADE VISUAL",
                "corpo": "Seu canal reconhecível em qualquer frame.",
                "narracao": "Uma identidade visual consistente faz o espectador reconhecer seu canal em qualquer frame da thumbnail.",
                "prompt_imagem": f"alien predator silhouette branded with distinctive red color signature, visual identity established, dark atmospheric, {_STYLE}",
            },
        ],
    },
    {
        "index": 11,
        "topico": "Render Queue",
        "roteiro": [
            {
                "titulo": "RENDER QUEUE",
                "corpo": "Monitore todos os vídeos em processamento.",
                "narracao": "O módulo Render Queue mostra todos os jobs de vídeo em tempo real com progresso e status.",
                "prompt_imagem": f"alien predator monitoring multiple red holographic render screens in dark command ship, red status lights, {_STYLE}",
            },
            {
                "titulo": "JOBS EM TEMPO REAL",
                "corpo": "Progresso, ETA e status de cada vídeo.",
                "narracao": "Acompanhe o progresso de cada vídeo em produção, o tempo estimado e eventuais erros.",
                "prompt_imagem": f"predator metallic claw pointing at red progress bar glowing on red holographic display, real-time monitoring, {_STYLE}",
            },
            {
                "titulo": "ESCALA SUA PRODUÇÃO",
                "corpo": "Produza vários vídeos em paralelo.",
                "narracao": "Com a fila de render, você pode ter múltiplos vídeos sendo processados simultaneamente.",
                "prompt_imagem": f"alien predator commanding army of red-lit drones all processing video simultaneously, parallel red power, {_STYLE}",
            },
        ],
    },
    {
        "index": 12,
        "topico": "Deploy Global",
        "roteiro": [
            {
                "titulo": "DEPLOY GLOBAL",
                "corpo": "Publique em múltiplas plataformas com um clique.",
                "narracao": "O módulo Deploy Global envia seu vídeo para YouTube, Instagram, TikTok e mais com um único clique.",
                "prompt_imagem": f"alien predator launching red signal beam from dark ship to planet Earth below, global deployment, dark sci-fi space, {_STYLE}",
            },
            {
                "titulo": "PLATAFORMAS",
                "corpo": "YouTube, Instagram, TikTok, Facebook e Google Drive.",
                "narracao": "YouTube, Instagram Reels, TikTok, Facebook Watch. Todos os canais alcançados de uma vez.",
                "prompt_imagem": f"predator throwing red energy projectiles hitting multiple platform icons across dark galaxy, {_STYLE}",
            },
            {
                "titulo": "ALCANCE MÁXIMO",
                "corpo": "Maximize o alcance com distribuição automática.",
                "narracao": "Maximiza seu alcance publicando nas horas de pico de cada plataforma de forma automática.",
                "prompt_imagem": f"alien predator standing on top of dark Earth with red glow conquering all screens worldwide, ultimate reach, epic, {_STYLE}",
            },
        ],
    },
]

OUTPUT_BASE = Path(__file__).parent.parent / "iai-studios" / "public" / "videos" / "briefing"


async def gerar_todos():
    print(f"🎬 Gerando vídeos para {len(MODULOS)} módulos...")
    print(f"📁 Saída: {OUTPUT_BASE}")
    print("⚠️  Isso pode levar 20-40 minutos dependendo da Pollinations.ai")
    print()

    resultados = []
    for mod in MODULOS:
        idx = mod["index"]
        topico = mod["topico"]
        roteiro = mod["roteiro"]

        # Cria diretório do card
        card_dir = OUTPUT_BASE / f"card{idx}"
        card_dir.mkdir(parents=True, exist_ok=True)

        saida = card_dir / "demo.mp4"

        if saida.exists():
            print(f"  ⏭️  card{idx} já existe, pulando...")
            resultados.append((idx, str(saida), "skipped"))
            continue

        print(f"\n🎞️  Gerando card{idx} — {topico}...")
        try:
            import os
            os.environ["VIDEO_OUTPUT_DIR"] = str(card_dir)

            caminho = await gerar_video_frankenstein(topico, roteiro, "demo.mp4")
            print(f"  ✅ card{idx} salvo: {caminho}")
            resultados.append((idx, str(caminho), "ok"))
        except Exception as e:
            print(f"  ❌ card{idx} falhou: {e}")
            resultados.append((idx, "", f"error: {e}"))

    print("\n\n📊 RESUMO:")
    for idx, path, status in resultados:
        emoji = "✅" if status == "ok" else "⏭️" if status == "skipped" else "❌"
        print(f"  {emoji} card{idx}: {status}")

    print("\n✅ Concluído! Para commitar os vídeos gerados:")
    print("  git add iai-studios/public/videos/briefing/")
    print("  git commit -m \"assets: add module demo videos\"")
    print("  git push")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--card", type=int, help="Gerar apenas o card N (1-12)")
    parser.add_argument("--no-ai-images", action="store_true", help="Sem imagens IA (mais rápido)")
    args = parser.parse_args()

    if args.no_ai_images:
        import os
        os.environ["USE_AI_IMAGES"] = "false"
        print("ℹ️  Modo sem imagens IA (gradiente colorido)")

    if args.card:
        modulo = next((m for m in MODULOS if m["index"] == args.card), None)
        if not modulo:
            print(f"❌ Card {args.card} não encontrado.")
            sys.exit(1)
        MODULOS.clear()
        MODULOS.append(modulo)
        print(f"ℹ️  Gerando apenas card{args.card}")

    asyncio.run(gerar_todos())
