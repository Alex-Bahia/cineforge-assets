# 📁 Canais Dark Youtube Music — Memória do Projeto

> Criado por: Alexandre Bahia (goforitbrasil@gmail.com)
> Data de início: Outubro 2026
> Sessão Claude: https://claude.ai/code/session_01LhgKquZ94E61BCT9956KLo

---

## 🎯 Objetivo do Projeto

Construir e escalar múltiplos canais anônimos (dark) de música no YouTube com 100% Inteligência Artificial.
- Sem aparecer em câmera
- Sem gravar voz
- Sem estúdio ou conhecimento musical
- Expansão para Spotify, Lives 24h e monetização automatizada

---

## 📚 Curso Base: Sinfonia Oculta

| Campo | Detalhe |
|---|---|
| **Nome** | Sinfonia Oculta |
| **Instrutor** | Ramon Roque de Assis |
| **Plataforma** | Hotmart Club |
| **URL** | https://hotmart.com/pt-br/club/ramon-roque-de-assis-40247765848/products/7635496 |
| **Subdomínio Hotmart** | `ramon-roque-de-assis-40247765848` |
| **Total de Aulas** | 29 aulas |
| **Progresso** | 7% (2/29 aulas) — Módulo 1 em 67% |

### Estrutura Completa do Curso

| # | Módulo | Aulas | Status |
|---|---|---|---|
| 1 | Módulo 1 — O Atalho Por Dentro | 3 | 67% ✅ |
| 2 | Módulo 2 — Engenharia Reversa do Lucro | 2 | 0% |
| 3 | Módulo 3 — Sequestre o Clique | 2 | 0% |
| 4 | Módulo 4 — Sua Primeira Sinfonia em 30 Minutos | 3 | 0% |
| 5 | Módulo 5 — O Lançamento Silencioso | 3 | 0% |
| B1 | Bônus 1 — Modele Qualquer Hit (Covers com IA) | 1 | 0% |
| B2 | Bônus 2 — Spotify + Como Registrar Músicas | 2 | 0% |
| B3 | Bônus 3 — Lives 24h no Piloto Automático | 1 | 0% |
| + | Ferramentas que vão facilitar seu trabalho 100x | 3 | 0% |
| + | Atualizações | 3 | 0% |
| + | Mentoria em Grupo | 5 | 0% |
| + | Gostou do curso? Indique para amigos e ganhe | 1 | 0% |
| **TOTAL** | | **29 aulas** | **7%** |

### Proposta de Valor do Curso
> "Aprenda o método completo para criar canais dark de música no YouTube usando 100% inteligência artificial — sem aparecer, sem gravar voz, sem precisar de estúdio ou conhecimento musical. 5 módulos passo a passo + bônus exclusivo de Covers com IA (legal, sem strike), estratégia de expansão para Spotify e Lives 24h no piloto automático."

---

## 🛠️ Ferramentas Instaladas no Mac

### Python e Ambiente Virtual
```bash
# Ambiente virtual criado em:
~/hotmart-env/

# Ativar sempre antes de usar:
source ~/hotmart-env/bin/activate
```

### FFmpeg
```bash
brew install ffmpeg   # instalado via Homebrew
ffmpeg -version       # verificar instalação
```

### Node.js
```bash
# Em instalação via Homebrew (processo demorado — compilando LLVM)
node --version        # verificar quando concluir
```

---

## 📥 Ferramentas de Download do Curso

### Opção 1 — hotmart-course-downloader (GRATUITO ⭐)
- **Repositório:** https://github.com/magosheimus/hotmart-course-downloader
- **Clonado em:** `/home/user/hotmart-downloader/`
- **O que baixa:** vídeos (Hotmart, Vimeo, YouTube), PDFs, anexos, Google Drive PDFs, descrições
- **Organização:** pastas por módulo e aula
- **Status (2026):** subdomínio manual obrigatório (API retorna `resources: []` vazio)

#### Como usar:
```bash
# 1. Ativar ambiente Python
source ~/hotmart-env/bin/activate

# 2. Instalar dependências
pip install m3u8 beautifulsoup4 youtube_dl requests

# 3. Configurar subdomínio em config_cursos.py:
CURSOS_SUBDOMINIOS = ["ramon-roque-de-assis-40247765848"]

# 4. Rodar
python hotmark.py
# → informar email e senha do Hotmart quando pedir
```

#### Arquivos do projeto:
```
hotmart-downloader/
├── hotmark.py          ← script principal
├── config_cursos.py    ← configurar subdomínio aqui
├── requirements.txt    ← dependências
└── README.md
```

### Opção 2 — Katomart (APP PAGO)
- **Site:** katomaro.com/store/katomart
- **Plataformas:** 114 plataformas EAD incluindo Hotmart
- **Instalação:** app nativo para macOS (sem dependências)
- **Módulo necessário:** Aquisição — R$ 12,90/mês
- **Plano gratuito:** 3 cursos / 80 aulas para testar
- **Repositório GitHub:** apenas documentação (código removido)

### Opção 3 — yt-dlp (GRATUITO, só vídeos)
```bash
brew install yt-dlp

# Com cookies exportados do Chrome:
yt-dlp --cookies ~/cookies.txt \
       --write-info-json \
       -o "~/hotmart-videos/%(title)s.%(ext)s" \
       "https://hotmart.com/pt-br/club/ramon-roque-de-assis-40247765848/products/7635496"
```

---

## 🔑 Extensões Chrome Úteis

| Extensão | Para que serve |
|---|---|
| **Get cookies.txt LOCALLY** | Exportar cookies para uso no terminal |
| **SingleFile** | Salvar páginas completas como um único HTML |
| **Video DownloadHelper** | Baixar vídeos de qualquer página |

---

## 📊 Modelo de Negócio

| Fonte de Receita | Valor Estimado |
|---|---|
| YouTube AdSense (música) | RPM R$ 8–R$ 25 / mil views |
| Spotify Streams | R$ 0,02–R$ 0,04 por stream |
| Lives 24h | Super Chats + anúncios contínuos |
| Covers com IA (licenciados) | Distribuição via plataformas legais |

---

## 🤖 Stack de IA Recomendada

| Função | Ferramentas |
|---|---|
| Geração de música | Suno AI / Udio |
| Geração de vídeo | Canva / CapCut / Pika Labs |
| Thumbnails em massa | AdRoque (R$97/mês) / Canva / Midjourney |
| Automação YouTube | TubeBuddy / VidIQ |
| Distribuição musical | DistroKid / TuneCore |
| Lives 24h | Streamyard / OBS automatizado |

---

## 📂 Estrutura de Pastas Sugerida

```
📁 Canais Dark Youtube Music/
├── 📂 Curso - Sinfonia Oculta/
│   ├── Módulo 1 — O Atalho Por Dentro/
│   ├── Módulo 2 — Engenharia Reversa do Lucro/
│   ├── Módulo 3 — Sequestre o Clique/
│   ├── Módulo 4 — Sua Primeira Sinfonia em 30 Minutos/
│   ├── Módulo 5 — O Lançamento Silencioso/
│   ├── Bônus 1 — Modele Qualquer Hit/
│   ├── Bônus 2 — Spotify + Registro de Músicas/
│   ├── Bônus 3 — Lives 24h/
│   ├── Ferramentas 100x/
│   ├── Atualizações/
│   └── Mentoria em Grupo/
├── 📂 Ferramentas/
│   ├── hotmart-downloader/
│   └── scripts/
├── 📂 Músicas Geradas/
│   ├── Originais/
│   └── Covers IA/
├── 📂 Canais/
│   ├── Canal 01/
│   └── Canal 02/
├── 📂 Thumbnails e Arte/
├── 📂 Roteiros e Descrições/
├── 📂 Resultados e Métricas/
└── 📄 MEMORY.md  ← este arquivo
```

---

## ✅ Regras do Projeto

- ✅ Apenas músicas autorais ou covers licenciados (sem strike)
- ✅ Metadados otimizados por IA para SEO do YouTube
- ✅ Identidade visual padronizada por canal
- ✅ Upload agendado e automatizado
- ❌ Nenhum conteúdo copiado sem licença
- ❌ Nenhuma aparição pessoal nos canais

---

## ✅ Concluído nesta sessão

- [x] FFmpeg 9.0.2 instalado via Homebrew
- [x] Repositório `hotmart-course-downloader` clonado em `~/hotmart-downloader/`
- [x] `config_cursos.py` configurado com `CURSOS_SUBDOMINIOS = ["ramon-roque-de-assis-40247765848"]`
- [x] Dependências Python instaladas (`pip install m3u8 beautifulsoup4 youtube_dl requests`)
- [x] Pasta `Canais Dark Youtube Music/` criada no repositório com estrutura completa
- [x] MEMORY.md criado e commitado no repositório

## ⚠️ Problema Identificado

O script `hotmark.py` falha na autenticação porque a **Hotmart exige 2FA** (código enviado por email).
O script não consegue lidar com isso automaticamente.

### Solução pendente — autenticar via cookies:
1. Fazer login manual no Hotmart pelo Chrome (incluindo código 2FA do email)
2. Instalar extensão **"Get cookies.txt LOCALLY"** no Chrome
3. Exportar cookies com a aba do Hotmart aberta
4. Salvar como `~/cookies.txt`
5. Passar os cookies para o script (próximo chat vai orientar o comando exato)

## 📋 Próximos Passos

- [ ] Exportar cookies do Hotmart (ver seção acima)
- [ ] Rodar `python hotmark.py` com cookies e baixar as 29 aulas
- [ ] Assistir Módulo 1 completo (67% → 100%)
- [ ] Completar Módulo 2 — Engenharia Reversa do Lucro
- [ ] Configurar primeira ferramenta de geração de música (Suno AI)
- [ ] Criar primeiro canal dark no YouTube

---

*Última atualização: Outubro 2026*
