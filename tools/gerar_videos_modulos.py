"""
Gera vídeos de demonstração para cada um dos 12 módulos do cockpit CineForge.
Usa o pipeline Frankenstein existente (edge-tts + Pillow + MoviePy + Pollinations.ai).

Rodar na VPS Hermes:
    cd /home/ubuntu/cineforge-assets
    python3 tools/gerar_videos_modulos.py

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
                "prompt_imagem": "AI writing script on holographic screen, dark studio, blue neon lights, cinematic",
            },
            {
                "titulo": "COMO FUNCIONA",
                "corpo": "Informe o tópico, nicho e duração desejada.",
                "narracao": "Basta informar o tópico, o nicho do canal e a duração. A IA gera título, introdução, corpo e call to action.",
                "prompt_imagem": "futuristic AI interface showing script generation, dark background, green data streams",
            },
            {
                "titulo": "ATIVE AGORA",
                "corpo": "Clique no módulo ROTEIRO IA no cockpit para começar.",
                "narracao": "Clique no módulo Roteiro IA no cockpit e comece a produzir conteúdo profissional imediatamente.",
                "prompt_imagem": "person typing on glowing keyboard, holographic displays, dark room, cyberpunk aesthetic",
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
                "prompt_imagem": "neural network visualized as musical waves, dark background, purple and blue colors, cinematic",
            },
            {
                "titulo": "MOODS DISPONÍVEIS",
                "corpo": "Epic, suspense, drama, action, calm, inspirational.",
                "narracao": "Escolha entre diversos moods: épico para documentários, suspense para true crime, inspiracional para motivação.",
                "prompt_imagem": "soundwave equalizer visualization, dark studio, glowing audio waveforms, cinematic",
            },
            {
                "titulo": "SEM ROYALTIES",
                "corpo": "Música 100% original. Zero problemas de copyright.",
                "narracao": "Todas as trilhas geradas são únicas e livres de royalties. Publique sem medo de demonetização.",
                "prompt_imagem": "music notes floating in dark space, golden glow, cinematic, 4K",
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
                "prompt_imagem": "DNA helix made of sound waves, dark laboratory, blue bioluminescent light, cinematic",
            },
            {
                "titulo": "COMO CLONAR",
                "corpo": "Grave 30 segundos de áudio e deixe a IA fazer o resto.",
                "narracao": "Basta gravar trinta segundos da sua voz. O sistema aprende seus padrões e reproduz qualquer texto.",
                "prompt_imagem": "voice waveform cloning visualization, neural network, dark tech background, cyan glow",
            },
            {
                "titulo": "ESCALE SUA VOZ",
                "corpo": "Gere horas de narração sem gravar uma única palavra.",
                "narracao": "Com o clone pronto, você pode gerar horas de narração sem precisar gravar nada. Escale sua produção.",
                "prompt_imagem": "infinite microphone clones fading into distance, dark studio, dramatic lighting",
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
                "prompt_imagem": "epic game universe portal, floating islands, neon colors, cinematic game art, 4K",
            },
            {
                "titulo": "ARTE INSTANTÂNEA",
                "corpo": "Thumbnails épicas geradas em segundos.",
                "narracao": "Descreva a cena que imagina e o sistema gera a imagem perfeita para sua thumbnail de games.",
                "prompt_imagem": "game thumbnail template showing epic battle scene, bright colors, bold text space, cinematic",
            },
            {
                "titulo": "SEM LIMITES",
                "corpo": "Qualquer universo, qualquer estilo visual.",
                "narracao": "Do pixel art ao hiper-realismo. Qualquer estilo de jogo, qualquer universo. Sem limites criativos.",
                "prompt_imagem": "multiple game genre collage, retro to modern, diverse art styles, dark background, dramatic",
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
                "prompt_imagem": "digital AI influencer avatar presenting to camera, studio setup, professional lighting, 4K",
            },
            {
                "titulo": "CRIE SEU AVATAR",
                "corpo": "Defina nome, personalidade e estilo visual.",
                "narracao": "Você escolhe o nome, a personalidade e o estilo visual. O avatar fica ativo enquanto você dorme.",
                "prompt_imagem": "holographic avatar creator interface, multiple character options, dark background, blue light",
            },
            {
                "titulo": "AUTONOMIA TOTAL",
                "corpo": "Produção de conteúdo sem aparecer na câmera.",
                "narracao": "Produza conteúdo sem precisar aparecer. Seu avatar trabalha para você em qualquer idioma.",
                "prompt_imagem": "AI avatar speaking to millions of viewers, global reach visualization, cinematic, dramatic",
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
                "prompt_imagem": "DNA helix made of YouTube metrics, dark background, red and gold colors, data visualization",
            },
            {
                "titulo": "ANÁLISE PROFUNDA",
                "corpo": "Frequência, ganchos, títulos, thumbnails — tudo analisado.",
                "narracao": "Cole a URL de qualquer canal concorrente e receba uma análise completa: frequência, ganchos usados, padrões de título.",
                "prompt_imagem": "competitive analysis dashboard showing channel metrics, dark UI, graphs, cinematic",
            },
            {
                "titulo": "REPLICAR O SUCESSO",
                "corpo": "Descubra o que funciona antes de investir tempo.",
                "narracao": "Descubra o que funciona no seu nicho antes de produzir qualquer vídeo. Economize meses de tentativa e erro.",
                "prompt_imagem": "success blueprint being revealed, dark background, golden light, strategic map, cinematic",
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
                "prompt_imagem": "storyboard panels on dark table, film production planning, professional studio, dramatic light",
            },
            {
                "titulo": "CENAS PLANEJADAS",
                "corpo": "Cada corte planejado para máximo impacto.",
                "narracao": "Cada corte, cada transição, cada momento de impacto planejado com precisão antes de gravar.",
                "prompt_imagem": "film director reviewing storyboard frames, dark cinema background, spotlight effect",
            },
            {
                "titulo": "DO ROTEIRO AO VÍDEO",
                "corpo": "Cole seu roteiro JSON e visualize em segundos.",
                "narracao": "Cole o roteiro gerado pela IA e o sistema monta automaticamente os frames visuais do seu vídeo.",
                "prompt_imagem": "script transforming into visual storyboard panels, dark background, cinematic transition",
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
                "prompt_imagem": "professional voice actor recording in dark studio, sound waves visible, dramatic lighting",
            },
            {
                "titulo": "VOZES DISPONÍVEIS",
                "corpo": "Masculinas e femininas, diferentes estilos e tons.",
                "narracao": "Múltiplas vozes disponíveis: femininas, masculinas, jovens, maduras. Cada uma com características únicas.",
                "prompt_imagem": "multiple audio waveforms representing different voices, dark background, colorful spectrum",
            },
            {
                "titulo": "SEM GRAVAR",
                "corpo": "Produza narrações sem usar seu próprio microfone.",
                "narracao": "Produza narrações profissionais sem usar microfone. A IA faz o trabalho com qualidade de estúdio.",
                "prompt_imagem": "AI microphone generating voice audio, neural network visualization, dark studio, blue light",
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
                "prompt_imagem": "video editing timeline interface, dark UI, multiple tracks, cinematic post-production",
            },
            {
                "titulo": "PIPELINE COMPLETA",
                "corpo": "Roteiro → Imagens → Narração → Música → MP4.",
                "narracao": "Roteiro, imagens de IA, narração neural, trilha musical. Tudo automático. Um MP4 pronto em minutos.",
                "prompt_imagem": "automated video production pipeline visualization, dark background, glowing workflow arrows",
            },
            {
                "titulo": "PUBLIQUE HOJE",
                "corpo": "De ideia a vídeo publicado em menos de 30 minutos.",
                "narracao": "De uma ideia a um vídeo publicado no YouTube em menos de trinta minutos. Isso é o CineForge.",
                "prompt_imagem": "video being published to YouTube, rocket launching, success visualization, dramatic cinematic",
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
                "prompt_imagem": "color grading process showing before after, dark cinematic, dramatic color transformation",
            },
            {
                "titulo": "PRESETS PRONTOS",
                "corpo": "Dark, thriller, drama, epic, vintage — escolha seu estilo.",
                "narracao": "Presets prontos para cada nicho: dark para true crime, épico para documentários, drama para narrativas.",
                "prompt_imagem": "multiple color palette presets displayed, dark room, professional color grading monitor",
            },
            {
                "titulo": "IDENTIDADE VISUAL",
                "corpo": "Seu canal reconhecível em qualquer frame.",
                "narracao": "Uma identidade visual consistente faz o espectador reconhecer seu canal em qualquer frame da thumbnail.",
                "prompt_imagem": "brand identity visual consistency, dark studio, recognizable color signature, cinematic",
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
                "prompt_imagem": "render farm with multiple GPUs processing, dark server room, blue indicator lights, cinematic",
            },
            {
                "titulo": "JOBS EM TEMPO REAL",
                "corpo": "Progresso, ETA e status de cada vídeo.",
                "narracao": "Acompanhe o progresso de cada vídeo em produção, o tempo estimado e eventuais erros.",
                "prompt_imagem": "server monitoring dashboard with job queues, dark UI interface, green status indicators",
            },
            {
                "titulo": "ESCALA SUA PRODUÇÃO",
                "corpo": "Produza vários vídeos em paralelo.",
                "narracao": "Com a fila de render, você pode ter múltiplos vídeos sendo processados simultaneamente.",
                "prompt_imagem": "parallel video processing visualization, multiple streams, dark background, speed motion blur",
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
                "prompt_imagem": "global video distribution network, world map with connection lines, dark space background",
            },
            {
                "titulo": "PLATAFORMAS",
                "corpo": "YouTube, Instagram, TikTok, Facebook e Google Drive.",
                "narracao": "YouTube, Instagram Reels, TikTok, Facebook Watch. Todos os canais alcançados de uma vez.",
                "prompt_imagem": "social media platform logos floating in dark space, connected by light beams, cinematic",
            },
            {
                "titulo": "ALCANCE MÁXIMO",
                "corpo": "Maximize o alcance com distribuição automática.",
                "narracao": "Maximiza seu alcance publicando nas horas de pico de cada plataforma de forma automática.",
                "prompt_imagem": "global audience reach visualization, millions of viewers, world network, dramatic cinematic",
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
            # Usa VPS_OUTPUT_DIR para salvar no lugar certo
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
