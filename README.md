# CineForge — Universal YouTube Channel Automation

Sistema completo de piloto automático para criar vídeos de YouTube em **qualquer nicho e qualquer mercado**.
**Você só precisa: criar o e-mail do Google → configurar as chaves de API → rodar.**

Suporta **Brasil 🇧🇷 | USA 🇺🇸 | UK 🇬🇧 | França 🇫🇷 | Alemanha 🇩🇪 | Espanha 🇪🇸 | Itália 🇮🇹**

Suporta qualquer nicho: **dark/crime · esportes · infantil · tecnologia · finanças · educação · saúde · culinária · entretenimento · notícias**

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

Baixe trilhas **gratuitas e sem copyright** da [YouTube Audio Library](https://www.youtube.com/audiolibrary) e coloque na pasta:

```
Canal Dark Automação/Canais Dark Youtube Music/
```

Formatos aceitos: MP3 ou WAV. O sistema escolhe uma faixa aleatória a cada vídeo e mistura no volume baixo (8%) para não cobrir a narração.

---

## Como Usar

### Ver todos os perfis de canal disponíveis

```bash
python run_pipeline.py --list-profiles
```

### Vídeo único — Canal dark BR (padrão)

```bash
source .venv/bin/activate
python run_pipeline.py "O assassino serial mais misterioso do Brasil"
```

### Vídeo único — USA dark channel

```bash
python run_pipeline.py "The most disturbing unsolved murder in America" --profile us_dark
```

### Vídeo único — Canal esportes BR

```bash
python run_pipeline.py "Os 10 gols mais bonitos do Brasileirão" --profile br_sports
```

### Vídeo único — Canal finanças USA

```bash
python run_pipeline.py "How to invest $1000 in the S&P 500" --profile us_finance
```

### Vídeo único — Canal dark França

```bash
python run_pipeline.py "Le crime parfait qui fascina la France" --profile fr_dark
```

### Vídeo único — Canal kids BR

```bash
python run_pipeline.py "Por que o céu é azul? Explicando para crianças" --profile br_kids
```

### Vídeo único + upload para YouTube (privado)

```bash
python run_pipeline.py "O crime que dividiu o Brasil" --upload --profile br_dark
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

### Descobrir novas oportunidades — Brasil

```bash
python run_pipeline.py --hunt --region BR
```

### Descobrir novas oportunidades — USA

```bash
python run_pipeline.py --hunt --region US --language en-US
```

### Agendador diário automático (roda todo dia às 06:00)

```bash
# Em segundo plano permanente (servidor/VPS)
nohup python run_pipeline.py --schedule > logs/scheduler.log 2>&1 &
```

---

## Perfis de Canal (Multi-mercado e Multi-nicho)

O CineForge suporta perfis pré-configurados para criar canais em qualquer mercado e nicho:

| Perfil | Mercado | Idioma | Nicho | Voz TTS |
|---|---|---|---|---|
| `br_dark` | 🇧🇷 Brasil | pt-BR | Dark/Crime | Antonio Neural |
| `br_sports` | 🇧🇷 Brasil | pt-BR | Esportes | Antonio Neural |
| `br_kids` | 🇧🇷 Brasil | pt-BR | Infantil | Francisca Neural |
| `br_tech` | 🇧🇷 Brasil | pt-BR | Tecnologia | Antonio Neural |
| `br_finance` | 🇧🇷 Brasil | pt-BR | Finanças | Antonio Neural |
| `br_education` | 🇧🇷 Brasil | pt-BR | Educação | Antonio Neural |
| `br_health` | 🇧🇷 Brasil | pt-BR | Saúde | Francisca Neural |
| `us_dark` | 🇺🇸 USA | en-US | Dark/Crime | Guy Neural |
| `us_sports` | 🇺🇸 USA | en-US | Sports | Guy Neural |
| `us_kids` | 🇺🇸 USA | en-US | Kids | Ana Neural |
| `us_tech` | 🇺🇸 USA | en-US | Technology | Guy Neural |
| `us_finance` | 🇺🇸 USA | en-US | Finance | Guy Neural |
| `us_education` | 🇺🇸 USA | en-US | Education | Guy Neural |
| `gb_dark` | 🇬🇧 UK | en-GB | Dark/Crime | Ryan Neural |
| `gb_education` | 🇬🇧 UK | en-GB | Education | Ryan Neural |
| `fr_dark` | 🇫🇷 France | fr-FR | Dark/Crime | Henri Neural |
| `fr_education` | 🇫🇷 France | fr-FR | Education | Henri Neural |
| `de_dark` | 🇩🇪 Germany | de-DE | Dark/Crime | Conrad Neural |
| `de_tech` | 🇩🇪 Germany | de-DE | Technology | Conrad Neural |
| `es_dark` | 🇪🇸 Spain | es-ES | Dark/Crime | Alvaro Neural |
| `es_education` | 🇪🇸 Spain | es-ES | Education | Alvaro Neural |
| `it_dark` | 🇮🇹 Italy | it-IT | Dark/Crime | Diego Neural |

**Ver todos:** `python run_pipeline.py --list-profiles`

---

## Editar a Fila de Vídeos

Abra `batch/topics.csv` e adicione seus temas:

```csv
topic,tone,minutes,profile,status,youtube_id
Meu novo tema dark,suspense e terror,8,br_dark,,
How to invest in crypto for beginners,,8,us_finance,,
The most haunting unsolved murder in UK,,,9,gb_dark,,
Les 5 recettes françaises incontournables,,8,fr_education,,
```

**Colunas:**
- `topic` — tema do vídeo (no idioma do mercado alvo)
- `tone` — tom da narração (deixe vazio para usar o padrão do perfil)
- `minutes` — duração alvo em minutos (8–15 recomendado)
- `profile` — ID do perfil de canal (ex: `br_dark`, `us_sports`). Veja `--list-profiles`
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
├── Canal Dark Automação/
│   └── Canais Dark Youtube Music/  ← coloque suas trilhas aqui (MP3/WAV)
├── assets/
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
| `No music files in ...` | Adicione MP3s em `Canal Dark Automação/Canais Dark Youtube Music/` |
| `FFmpeg not found` | `sudo apt install ffmpeg` ou `brew install ffmpeg` |
| `YouTube auth failed` | Delete `config/youtube_token.json` e re-autorize |
| `Pexels returns empty` | A query do visual está muito específica; o Pollinations.ai entra automaticamente |
