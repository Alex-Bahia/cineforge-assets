# CineForge — Dark YouTube Channel Automation

Sistema completo de piloto automático para criar vídeos de canais dark no YouTube.
**Você só precisa: criar o e-mail do Google → configurar as chaves de API → rodar.**

---

## Arquitetura do Pipeline

```
[ topics.csv / Google Sheets ]
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ 01_scriptwriter.py  │  Gemini API (gratuito) → JSON com │
│                     │  roteiro por cenas + metadados SEO │
└─────────────────────┴─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ 02_narrator.py      │  edge-tts (gratuito, ilimitado)   │
│                     │  → MP3 narrado + SRT sincronizado  │
└─────────────────────┴─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ 03_visuals.py       │  Pexels API → Pixabay API →       │
│                     │  Pollinations.ai (todos gratuitos) │
└─────────────────────┴─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ 04_editor.py        │  MoviePy + FFmpeg:                 │
│                     │  áudio + vídeo + legendas + música │
└─────────────────────┴─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ 06_thumbnail.py     │  Pollinations.ai + Pillow:        │
│                     │  thumbnail automática com texto    │
└─────────────────────┴─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ 05_uploader.py      │  YouTube Data API v3:             │
│                     │  upload + agendamento automático   │
└─────────────────────┴─────────────────────────────────────┘
```

---

## Instalação Rápida

### Pré-requisitos
- Python 3.10+
- FFmpeg instalado no sistema

### 1. Instalar tudo

```bash
git clone <este-repo>
cd cineforge-assets
bash setup.sh
```

### 2. Configurar chaves de API

Edite o arquivo `.env` (criado automaticamente pelo setup):

| Variável | Onde obter | Custo |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) | **Gratuito** |
| `PEXELS_API_KEY` | [pexels.com/api](https://www.pexels.com/api/) | **Gratuito** |
| `PIXABAY_API_KEY` | [pixabay.com/api/docs](https://pixabay.com/api/docs/) | **Gratuito** |
| `YOUTUBE_CLIENT_ID` | [console.cloud.google.com](https://console.cloud.google.com/) → Credentials | Gratuito |
| `YOUTUBE_CLIENT_SECRET` | Mesmo lugar acima | Gratuito |

### 3. Configurar YouTube OAuth

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto novo
3. Ative a **YouTube Data API v3**
4. Em Credentials → Create Credentials → OAuth 2.0 Client ID → Desktop App
5. Baixe o JSON e salve como `config/client_secrets.json`
6. Na primeira execução com `--upload`, um browser abrirá para autorizar — faça isso uma vez por canal

### 4. Adicionar músicas de fundo

Baixe trilhas **gratuitas e sem copyright** da [YouTube Audio Library](https://www.youtube.com/audiolibrary) e coloque em `assets/music/` (formato MP3 ou WAV).

---

## Como Usar

### Vídeo único (teste)

```bash
source .venv/bin/activate
python run_pipeline.py "O assassino serial mais misterioso do Brasil"
```

### Vídeo único + upload para YouTube (privado)

```bash
python run_pipeline.py "O crime que dividiu o Brasil" --upload
```

### Vídeo agendado para publicação específica

```bash
python run_pipeline.py "Rituais proibidos do Brasil" --upload --publish-at "2024-12-31T18:00:00Z"
```

### Processar fila inteira do CSV

```bash
python run_pipeline.py --batch
```

### Lote completo + upload + agendamento automático (1 vídeo/dia)

```bash
python run_pipeline.py --batch --upload --auto-schedule
```

### Agendador diário automático (roda todo dia às 06:00)

```bash
# Em segundo plano permanente (servidor/VPS)
nohup python run_pipeline.py --schedule > logs/scheduler.log 2>&1 &
```

---

## Editar a Fila de Vídeos

Abra `batch/topics.csv` e adicione seus temas:

```csv
topic,tone,minutes,status,youtube_id
Meu novo tema dark,suspense e terror,8,,
Outro tema assustador,investigativo,10,,
```

**Colunas:**
- `topic` — tema do vídeo (em português)
- `tone` — tom da narração (suspense / terror / investigativo / mistério)
- `minutes` — duração alvo em minutos (8–15 recomendado)
- `status` — deixe vazio; o sistema preenche automaticamente
- `youtube_id` — preenchido automaticamente após upload

---

## Estrutura de Arquivos

```
cineforge-assets/
├── run_pipeline.py          ← ponto de entrada principal
├── setup.sh                 ← instalação com um comando
├── requirements.txt
├── .env.example             ← copie para .env e preencha
├── batch/
│   └── topics.csv           ← sua fila de vídeos
├── config/
│   ├── settings.py          ← todas as configurações
│   └── client_secrets.json  ← OAuth YouTube (você baixa)
├── src/
│   ├── pipeline/
│   │   ├── 01_scriptwriter.py   ← Gemini gera roteiro JSON
│   │   ├── 02_narrator.py       ← edge-tts gera áudio + SRT
│   │   ├── 03_visuals.py        ← busca imagens/vídeos grátis
│   │   ├── 04_editor.py         ← monta o vídeo final
│   │   ├── 05_uploader.py       ← sobe para o YouTube
│   │   └── 06_thumbnail.py      ← gera thumbnail automática
│   ├── prompts/
│   │   └── scriptwriter.py      ← prompts Gemini
│   └── utils/
│       ├── sheets.py            ← lê Google Sheets ou CSV
│       ├── video_id.py          ← gerador de IDs únicos
│       └── logger.py            ← logs coloridos + arquivo
├── assets/
│   ├── music/               ← coloque suas trilhas aqui (MP3/WAV)
│   └── fonts/               ← Anton.ttf (baixado pelo setup.sh)
└── output/                  ← gerado automaticamente
    ├── scripts/             ← roteiros JSON
    ├── audio/               ← narração MP3 por cena
    ├── subtitles/           ← legendas SRT por cena
    ├── images/              ← visuais baixados/gerados
    ├── videos/              ← vídeos renderizados FINAIS
    └── thumbnails/          ← thumbnails JPG
```

---

## Configurações Avançadas (`.env`)

```env
# Voz — lista completa: https://aka.ms/edge-tts-voices
TTS_VOICE=pt-BR-AntonioNeural    # masculina grave (padrão)
# TTS_VOICE=pt-BR-FranciscaNeural  # feminina

# Ritmo (valores negativos = mais lento/grave = mais suspense)
TTS_RATE=-5%
TTS_PITCH=-10Hz

# Duração padrão de cada cena visual em segundos
SCENE_DURATION=5

# Privacidade do upload: private | unlisted | public
YT_PRIVACY=private

# Hora do agendador diário (formato 24h)
SCHEDULE_HOUR=6

# Vídeos renderizados em paralelo (reduzir se PC for lento)
MAX_PARALLEL=2
```

---

## Dicas de Retenção e Monetização

1. **Gancho obrigatório nos primeiros 5s** — o prompt já exige isso; nunca edite essa parte
2. **Troca de cena a cada 4–6s** — configurável em `SCENE_DURATION`
3. **Legendas no centro inferior** — ativas por padrão, mantêm o viewer focado
4. **Música ambiente** — coloque trilhas dark/suspense em `assets/music/`; o volume é automático (8%)
5. **Consistência visual** — use o mesmo estilo de thumbnail em todos os vídeos
6. **Upload privado primeiro** — revise antes de publicar (`YT_PRIVACY=private` é o padrão)
7. **Títulos com palavra-chave no início** — o Gemini já é instruído para isso

---

## Solução de Problemas

| Erro | Solução |
|---|---|
| `GEMINI_API_KEY not set` | Preencha `.env` com sua chave do AI Studio |
| `No music files in assets/music` | Adicione MP3s na pasta `assets/music/` |
| `FFmpeg not found` | `sudo apt install ffmpeg` ou `brew install ffmpeg` |
| `YouTube auth failed` | Delete `config/youtube_token.json` e re-autorize |
| `Pexels returns empty` | A query do visual está muito específica; o Pollinations.ai entra automaticamente |
