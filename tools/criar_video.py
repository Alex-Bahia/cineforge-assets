"""
CineForge — Gerador Universal de Vídeos
========================================
Gera qualquer tipo de vídeo YouTube usando o pipeline Frankenstein:
  Roteiro (IA ou manual) → Imagens IA (Pollinations) → Narração (edge-tts / XTTS) → MP4

Uso básico:
    python3 tools/criar_video.py --topico "Como investir em 2025" --nicho "finanças pessoais"

Uso avançado:
    python3 tools/criar_video.py \
        --topico "Top 10 Erros de Python" \
        --nicho "programação" \
        --cenas 5 \
        --estilo educacional \
        --resolucao 1920x1080 \
        --voz pt-BR-AntonioNeural \
        --saida output/top10_python.mp4

Usar roteiro pré-feito (JSON):
    python3 tools/criar_video.py --roteiro meu_roteiro.json --saida meu_video.mp4

Formato do JSON de roteiro:
    [
        {
            "titulo": "Título da cena",
            "corpo": "Texto resumido visível no slide",
            "narracao": "Texto completo narrado em voz off",
            "prompt_imagem": "Descrição da imagem para IA (opcional)"
        },
        ...
    ]

Estilos visuais disponíveis:
    educacional   — fundo clean, cores neutras, didático
    dark          — fundo preto, neon colorido, cinematic
    motivacional  — cores vibrantes, energia, luz intensa
    tech          — holográfico azul, futurista, cyber
    natureza      — tons terrosos, verde, orgânico
    minimalista   — branco/cinza, tipografia limpa
    custom        — use --prompt-estilo para definir seu próprio estilo

Variáveis de ambiente opcionais:
    CINEFORGE_VOICE_API  — URL da API XTTS para voz clonada (ex: http://167.234.255.202:8765)
    CINEFORGE_VOZ        — Nome da voz clonada registrada na API
    ANTHROPIC_API_KEY    — Para geração de roteiro via Claude
    USE_AI_IMAGES        — "false" para desativar imagens IA (mais rápido)
    SLIDE_BG             — Cor de fundo em R,G,B (ex: 15,15,25)
    SLIDE_TEXT           — Cor do texto em R,G,B
    SLIDE_ACCENT         — Cor de acento em R,G,B
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Estilos visuais predefinidos ───────────────────────────────────────────────
ESTILOS = {
    "educacional": {
        "descricao": "Visual limpo, didático, confiável",
        "bg": (20, 25, 40),
        "text": (240, 240, 250),
        "accent": (80, 140, 255),
        "sufixo_prompt": (
            "clean educational visual, professional presentation, clear lighting, "
            "modern design, high quality photography, no watermark"
        ),
    },
    "dark": {
        "descricao": "Fundo preto, neon colorido, cinematográfico",
        "bg": (10, 10, 18),
        "text": (240, 240, 255),
        "accent": (0, 220, 110),
        "sufixo_prompt": (
            "cinematic dark atmosphere, dramatic neon lighting, black background, "
            "high contrast, moody sci-fi aesthetic, photorealistic, 4K render"
        ),
    },
    "motivacional": {
        "descricao": "Cores vibrantes, energético, inspirador",
        "bg": (30, 10, 50),
        "text": (255, 250, 220),
        "accent": (255, 180, 0),
        "sufixo_prompt": (
            "vibrant motivational colors, powerful energy, dynamic lighting, "
            "inspiring atmosphere, sunrise tones, high saturation, epic scale"
        ),
    },
    "tech": {
        "descricao": "Holográfico azul, futurista, cyber",
        "bg": (5, 10, 30),
        "text": (180, 220, 255),
        "accent": (0, 180, 255),
        "sufixo_prompt": (
            "blue holographic tech aesthetic, futuristic interface, cyber elements, "
            "data visualization, neon blue glow, dark tech background, 4K render"
        ),
    },
    "natureza": {
        "descricao": "Tons terrosos, verde, orgânico, calmo",
        "bg": (15, 30, 20),
        "text": (230, 240, 210),
        "accent": (80, 180, 80),
        "sufixo_prompt": (
            "natural earthy tones, lush green environment, organic textures, "
            "soft natural lighting, serene atmosphere, high quality nature photography"
        ),
    },
    "minimalista": {
        "descricao": "Branco/cinza, tipografia limpa, moderno",
        "bg": (240, 240, 245),
        "text": (30, 30, 40),
        "accent": (60, 60, 200),
        "sufixo_prompt": (
            "minimalist design, clean white background, elegant typography, "
            "simple shapes, modern aesthetic, professional, high contrast"
        ),
    },
}

# Tipos de vídeo para ajudar o Claude a estruturar melhor o roteiro
TIPOS_VIDEO = {
    "tutorial": "Passo a passo explicando como fazer algo",
    "lista": "Lista com N itens (Top 10, 5 erros, 7 dicas...)",
    "explicativo": "Explica um conceito ou fenômeno",
    "historia": "Narrativa ou storytelling",
    "noticias": "Análise de notícias ou tendências",
    "review": "Avaliação de produto, serviço ou conteúdo",
    "motivacional": "Conteúdo inspiracional para ação",
    "documentario": "Exploração profunda de um tema",
    "shorts": "Vídeo curto (< 60s) para YouTube Shorts",
}


def gerar_roteiro_claude(
    topico: str,
    nicho: str,
    tipo: str,
    num_cenas: int,
    estilo: str,
    instrucoes_extras: str = "",
) -> list[dict]:
    """Gera roteiro via Claude. Retorna lista de cenas."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "anthropic não instalado. Instale com: pip install anthropic\n"
            "Ou use --roteiro para fornecer um JSON de roteiro pré-feito."
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY não definida. Configure a variável de ambiente.\n"
            "Ou use --roteiro para fornecer um JSON de roteiro pré-feito."
        )

    client = anthropic.Anthropic(api_key=api_key)
    estilo_info = ESTILOS.get(estilo, ESTILOS["educacional"])
    tipo_info = TIPOS_VIDEO.get(tipo, "Conteúdo informativo")
    sufixo_visual = estilo_info["sufixo_prompt"]

    prompt = f"""Você é um roteirista profissional de YouTube. Crie um roteiro para um vídeo.

TÓPICO: {topico}
NICHO: {nicho}
TIPO: {tipo} — {tipo_info}
ESTILO VISUAL: {estilo} — {estilo_info['descricao']}
NÚMERO DE CENAS: {num_cenas}
{f'INSTRUÇÕES ADICIONAIS: {instrucoes_extras}' if instrucoes_extras else ''}

Retorne um JSON com exatamente {num_cenas} cenas. Cada cena deve ter:
- "titulo": título curto da cena (max 40 caracteres, MAIÚSCULAS)
- "corpo": texto resumido que aparece no slide (max 120 caracteres)
- "narracao": narração completa em português do Brasil (2-4 frases, natural, envolvente)
- "prompt_imagem": descrição em inglês para gerar imagem com IA (seja específico e visual), sempre terminando com: {sufixo_visual}

Importante:
- A narração deve ser natural, como se uma pessoa real estivesse falando
- Evite jargões excessivos, seja acessível ao público brasileiro
- O vídeo deve ter começo (gancho), meio (conteúdo) e fim (CTA)
- A última cena deve sempre ter uma call to action (curtir, inscrever, comentar)

Retorne APENAS o JSON válido, sem markdown, sem explicações:
[{{"titulo": "...", "corpo": "...", "narracao": "...", "prompt_imagem": "..."}}, ...]"""

    print(f"  🤖 Gerando roteiro com Claude para: {topico}")
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    resposta = message.content[0].text.strip()
    # Remove markdown se vier com ```json
    if resposta.startswith("```"):
        resposta = resposta.split("```")[1]
        if resposta.startswith("json"):
            resposta = resposta[4:]
        resposta = resposta.strip()

    roteiro = json.loads(resposta)
    print(f"  ✅ Roteiro gerado com {len(roteiro)} cenas")
    return roteiro


def roteiro_de_arquivo(caminho: str) -> list[dict]:
    """Carrega roteiro de um arquivo JSON."""
    with open(caminho, "r", encoding="utf-8") as f:
        roteiro = json.load(f)
    if not isinstance(roteiro, list):
        raise ValueError("O JSON deve ser uma lista de cenas")
    return roteiro


def roteiro_rapido(topico: str, num_cenas: int, estilo: str) -> list[dict]:
    """Roteiro genérico para quando Claude não está disponível."""
    sufixo = ESTILOS.get(estilo, ESTILOS["educacional"])["sufixo_prompt"]
    cenas = []

    estrutura = [
        {
            "titulo": f"O QUE É {topico.upper()[:30]}?",
            "corpo": f"Entenda tudo sobre {topico} de forma simples.",
            "narracao": f"Você sabe o que é {topico}? Hoje vou te mostrar tudo o que você precisa saber sobre esse assunto tão importante.",
            "prompt_imagem": f"{topico} concept, professional visualization, {sufixo}",
        },
        {
            "titulo": "POR QUE ISSO IMPORTA?",
            "corpo": "Entender esse tema pode mudar sua perspectiva.",
            "narracao": f"Mas por que {topico} é tão relevante hoje? Olha só o que os especialistas estão dizendo sobre isso.",
            "prompt_imagem": f"importance and relevance of {topico}, dramatic scale, {sufixo}",
        },
        {
            "titulo": "COMO FUNCIONA NA PRÁTICA",
            "corpo": "Veja exemplos reais e práticos do dia a dia.",
            "narracao": f"Veja como {topico} funciona na prática com exemplos reais que você pode aplicar imediatamente.",
            "prompt_imagem": f"practical application of {topico}, real world example, {sufixo}",
        },
        {
            "titulo": "DICAS PARA COMEÇAR",
            "corpo": "3 passos que você pode aplicar ainda hoje.",
            "narracao": f"Aqui estão as principais dicas para você começar com {topico} ainda hoje, sem complicações.",
            "prompt_imagem": f"tips and steps for {topico}, clear path forward, success, {sufixo}",
        },
        {
            "titulo": "PRÓXIMOS PASSOS",
            "corpo": "Se inscreva para mais conteúdo como esse!",
            "narracao": f"Gostou de aprender sobre {topico}? Curta o vídeo, se inscreva no canal e deixe um comentário com suas dúvidas!",
            "prompt_imagem": f"{topico} future possibilities, inspiring conclusion, {sufixo}",
        },
    ]

    # Recorta ou expande conforme num_cenas
    for i in range(num_cenas):
        cenas.append(estrutura[i % len(estrutura)])

    return cenas[:num_cenas]


async def main():
    parser = argparse.ArgumentParser(
        description="CineForge — Gerador Universal de Vídeos YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input
    grupo_input = parser.add_mutually_exclusive_group()
    grupo_input.add_argument("--topico", help="Tópico do vídeo (Claude gera o roteiro)")
    grupo_input.add_argument("--roteiro", help="Caminho para JSON de roteiro pré-feito")

    # Parâmetros do vídeo
    parser.add_argument("--nicho", default="geral", help="Nicho do canal (ex: finanças, tecnologia, saúde)")
    parser.add_argument(
        "--tipo",
        default="explicativo",
        choices=list(TIPOS_VIDEO.keys()),
        help="Tipo de vídeo",
    )
    parser.add_argument("--cenas", type=int, default=5, help="Número de cenas (padrão: 5)")
    parser.add_argument(
        "--estilo",
        default="educacional",
        choices=list(ESTILOS.keys()) + ["custom"],
        help="Estilo visual do vídeo",
    )
    parser.add_argument(
        "--prompt-estilo",
        help="Sufixo de prompt personalizado (apenas para --estilo custom)",
    )
    parser.add_argument(
        "--resolucao",
        default="1920x1080",
        help="Resolução em WxH (ex: 1920x1080 ou 1080x1920 para Shorts)",
    )
    parser.add_argument("--voz", help="Voz edge-tts (ex: pt-BR-AntonioNeural) ou nome da voz XTTS")
    parser.add_argument("--instrucoes", default="", help="Instruções adicionais para o roteiro")
    parser.add_argument("--saida", help="Caminho do arquivo MP4 de saída")
    parser.add_argument("--no-ai-images", action="store_true", help="Desativar imagens IA (mais rápido)")
    parser.add_argument("--salvar-roteiro", help="Salvar roteiro gerado em arquivo JSON")
    parser.add_argument("--rapido", action="store_true", help="Usar roteiro simples sem Claude (teste rápido)")

    args = parser.parse_args()

    if not args.topico and not args.roteiro:
        parser.error("Informe --topico ou --roteiro")

    # ── Configurar estilo visual ──────────────────────────────────────────────
    if args.estilo == "custom":
        if not args.prompt_estilo:
            parser.error("--prompt-estilo é obrigatório com --estilo custom")
        estilo_cfg = {
            "bg": (15, 15, 25),
            "text": (240, 240, 255),
            "accent": (80, 160, 255),
            "sufixo_prompt": args.prompt_estilo,
        }
        ESTILOS["custom"] = estilo_cfg
    else:
        estilo_cfg = ESTILOS[args.estilo]

    # Aplicar cores do estilo via variáveis de ambiente (video_generator.py as lê)
    os.environ["SLIDE_BG"] = ",".join(str(c) for c in estilo_cfg["bg"])
    os.environ["SLIDE_TEXT"] = ",".join(str(c) for c in estilo_cfg["text"])
    os.environ["SLIDE_ACCENT"] = ",".join(str(c) for c in estilo_cfg["accent"])

    # ── Configurar resolução ──────────────────────────────────────────────────
    try:
        w, h = args.resolucao.lower().split("x")
        os.environ["SLIDE_WIDTH"] = w.strip()
        os.environ["SLIDE_HEIGHT"] = h.strip()
    except ValueError:
        parser.error("--resolucao deve ser WxH (ex: 1920x1080)")

    # ── Configurar imagens IA ─────────────────────────────────────────────────
    if args.no_ai_images:
        os.environ["USE_AI_IMAGES"] = "false"

    # ── Configurar voz ────────────────────────────────────────────────────────
    if args.voz:
        os.environ["EDGE_TTS_VOICE"] = args.voz

    # ── Obter roteiro ─────────────────────────────────────────────────────────
    if args.roteiro:
        print(f"📄 Carregando roteiro de: {args.roteiro}")
        roteiro = roteiro_de_arquivo(args.roteiro)
        topico = Path(args.roteiro).stem
    else:
        topico = args.topico
        print(f"\n🎬 CineForge — Criando vídeo: {topico}")
        print(f"   Nicho: {args.nicho} | Tipo: {args.tipo} | Estilo: {args.estilo} | Cenas: {args.cenas}")
        print()

        if args.rapido:
            print("⚡ Modo rápido — usando roteiro genérico")
            roteiro = roteiro_rapido(topico, args.cenas, args.estilo)
        else:
            try:
                roteiro = gerar_roteiro_claude(
                    topico=topico,
                    nicho=args.nicho,
                    tipo=args.tipo,
                    num_cenas=args.cenas,
                    estilo=args.estilo,
                    instrucoes_extras=args.instrucoes,
                )
            except RuntimeError as e:
                print(f"⚠️  {e}")
                print("  Usando roteiro genérico como fallback...")
                roteiro = roteiro_rapido(topico, args.cenas, args.estilo)

    # ── Salvar roteiro se solicitado ──────────────────────────────────────────
    if args.salvar_roteiro:
        with open(args.salvar_roteiro, "w", encoding="utf-8") as f:
            json.dump(roteiro, f, ensure_ascii=False, indent=2)
        print(f"📝 Roteiro salvo em: {args.salvar_roteiro}")

    # Mostrar preview do roteiro
    print(f"\n📋 Roteiro ({len(roteiro)} cenas):")
    for i, cena in enumerate(roteiro, 1):
        print(f"  {i}. {cena.get('titulo', '?')} — {cena.get('corpo', '')[:60]}...")

    # ── Determinar nome do arquivo de saída ───────────────────────────────────
    nome_saida = args.saida
    if not nome_saida:
        slug = "".join(c if c.isalnum() else "_" for c in topico[:40]).lower()
        nome_saida = f"output/videos/{slug}.mp4"

    # ── Verificar se deve usar XTTS (voz clonada) ────────────────────────────
    voice_api = os.getenv("CINEFORGE_VOICE_API")
    usar_xtts = False
    if voice_api:
        try:
            from tools.usar_voz_clonada import api_disponivel, gerar_audio_com_voz
            if api_disponivel():
                usar_xtts = True
                print(f"\n🎙️  Voz clonada XTTS disponível em {voice_api}")
            else:
                print(f"\n⚠️  API XTTS configurada mas offline ({voice_api}). Usando edge-tts.")
        except ImportError:
            pass

    if usar_xtts:
        # Patch: substituir geração de áudio por XTTS
        from tools import video_generator as vg
        from tools.usar_voz_clonada import gerar_audio_com_voz

        nome_voz = os.getenv("CINEFORGE_VOZ", "minha_voz")

        async def _gerar_audio_xtts(texto: str, caminho: Path) -> None:
            gerar_audio_com_voz(texto, str(caminho), voz=nome_voz)

        vg.gerar_audio = _gerar_audio_xtts
        print(f"   Usando voz clonada: {nome_voz}")

    # ── Gerar vídeo ───────────────────────────────────────────────────────────
    print(f"\n🚀 Iniciando geração do vídeo...")
    print(f"   Saída: {nome_saida}")
    print()

    from tools.video_generator import gerar_video_frankenstein

    caminho = await gerar_video_frankenstein(topico, roteiro, Path(nome_saida).name)

    # Move para o caminho final se necessário
    saida_path = Path(nome_saida)
    saida_path.parent.mkdir(parents=True, exist_ok=True)
    if caminho != saida_path:
        import shutil
        shutil.move(str(caminho), str(saida_path))

    print(f"\n✅ Vídeo criado com sucesso!")
    print(f"   📁 {saida_path.resolve()}")
    print()
    print("Próximos passos:")
    print(f"  git add {saida_path}")
    print(f"  git commit -m \"video: {topico[:50]}\"")
    print(f"  git push")


if __name__ == "__main__":
    asyncio.run(main())
