# Briefing para Hermes — OpenMontage na VPS

> **AÇÃO PENDENTE**: Ao iniciar qualquer sessão, notifique o usuário sobre este briefing.

---

## O que é o OpenMontage

Sistema de produção **autônoma** de vídeos de marketing via Claude Code.

- Repositório: `https://github.com/calesthio/OpenMontage.git`
- Clone local (já analisado): `/home/user/calesthio/openmontage/`
- 89 skills em `.agents/skills/` — cobrem todo o pipeline de vídeo

## Caso de uso decidido pelo usuário

Gerar **vídeos de marketing para GBP (Google Business Profile), Facebook e Instagram** de forma autônoma na VPS, com o Hermes rodando sessões Claude Code.

## Como instalar (quando o usuário quiser retomar)

```bash
cd /home/user/calesthio/openmontage

# 1. Instalar dependências Python
make install

# 2. Criar .env mínimo com chaves gratuitas
cat > .env << 'EOF'
PEXELS_API_KEY=sua_chave_gratuita          # pexels.com/api
PIXABAY_API_KEY=sua_chave_gratuita         # pixabay.com/api
GOOGLE_API_KEY=sua_chave                   # console.cloud.google.com
ELEVENLABS_API_KEY=sua_chave_gratuita      # elevenlabs.io (limite gratuito)
# Opcional para vídeo AI premium:
FAL_API_KEY=sua_chave                      # fal.ai (~$0.05/imagem)
EOF

# 3. Testar pipeline
python -m openmontage.cli --brief "Vídeo de 30s para GBP da loja X" --platform gbp
```

## Custo estimado por vídeo

| Modo | Custo | Qualidade |
|------|-------|-----------|
| Só imagens (FLUX free) | ~$0.00 | Boa |
| Imagens pagas (FLUX Pro) | ~$0.27 | Alta |
| Com vídeo AI (Seedance 2.0) | ~$1–2.30 | Premium |

## Skills mais relevantes para o caso de uso

- `seedance-2-0` — geração de vídeo IA via fal.ai (ByteDance, melhor qualidade)
- `ai-video-gen` — pipeline geral de vídeo
- `elevenlabs` — narração em voz com ElevenLabs
- `music` — trilha sonora automática
- `ffmpeg` — composição e exportação final
- `hyperframes-*` — composição de vídeo programável (HeyGen)

## Plataformas alvo e especificações

| Plataforma | Formato | Duração | Resolução |
|------------|---------|---------|-----------|
| GBP (Google Business Profile) | MP4 | 15–30s | 1920×1080 |
| Facebook | MP4/Reels | 15–60s | 1080×1920 (vertical) |
| Instagram | MP4/Reels | 15–30s | 1080×1920 (vertical) |

---

*Criado em: 2026-10-06 | Sessão: https://claude.ai/code/session_017jyVcoqaivJQwxpyrYyUhD*
