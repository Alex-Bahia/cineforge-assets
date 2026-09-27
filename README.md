# CineForge Assets V3

Extensão Google Chrome para geração automatizada de vídeos com IA, integrada ao Claude.

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
