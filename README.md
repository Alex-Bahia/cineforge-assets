# CineForge Assets V3

Extensão Google Chrome para geração automatizada de vídeos com IA, integrada ao Claude.

## Estrutura

```
manifest.json              # Manifest V3
src/
  popup/
    popup.html             # UI principal (380×600px)
    popup.css              # Design dark mode
    popup.js               # Lógica da extensão
  background/
    background.js          # Service worker (polling, context menu)
  content/
    content.js             # Captura de contexto da página
  utils/
    claude-api.js          # Geração de roteiro via Claude API
    video-orchestrator.js  # Roteamento para HeyGen / Higgsfield / Motion
    license.js             # Validação de licença comercial
    storage.js             # Wrapper chrome.storage.local
    toast.js               # Notificações in-app
  pages/
    options.html           # Página de configurações
icons/                     # Ícones 16/48/128px
scripts/
  package.js               # Gera .zip para Chrome Web Store
```

## Pipeline

1. Usuário descreve o vídeo (ou captura contexto da página atual)
2. Claude gera roteiro estruturado (JSON com cenas, narração, direção)
3. Roteiro é enviado ao provedor de vídeo escolhido (HeyGen / Higgsfield / Motion)
4. Extensão faz polling em background e notifica quando pronto
5. Download direto do vídeo gerado

## Instalação (desenvolvimento)

1. Abra `chrome://extensions`
2. Ative "Modo desenvolvedor"
3. Clique "Carregar sem compactação"
4. Selecione esta pasta

## Configuração

Na página de opções, configure:
- **Chave Claude API** — `console.anthropic.com`
- **HeyGen API Key** — `app.heygen.com`
- **Higgsfield API Key** — `app.higgsfield.ai`
- **Motion API Key** — `usemotion.com`
- **Licença CineForge** — `cineforge.app/pricing`
