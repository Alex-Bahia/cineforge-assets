# CineForge — RunPod Serverless Worker: LTX-Video
#
# Imagem base do RunPod com CUDA 12.2 + Python 3.10 pré-instalados.
# O SDK runpod.serverless gerencia toda a camada HTTP; sem porta exposta.
#
# Build:
#   docker build -t cineforge-ltx-serverless:latest .
#
# Variáveis de ambiente obrigatórias (injetar via RunPod Secrets):
#   AWS_BUCKET            — bucket S3/R2 para upload dos vídeos gerados
#   AWS_ACCESS_KEY_ID     — credencial de acesso
#   AWS_SECRET_ACCESS_KEY — credencial secreta
#
# Variáveis opcionais (com defaults seguros):
#   LTX_MODEL_ID     — repo HuggingFace (padrão: Lightricks/LTX-Video)
#   LTX_OUTPUT_DIR   — diretório temporário dentro do container (padrão: /tmp/ltx_outputs)
#   AWS_REGION       — região S3 ou "auto" para R2 (padrão: auto)
#   AWS_ENDPOINT_URL — endpoint Cloudflare R2 ou S3-compatível (opcional)

FROM runpod/base:0.6.2-cuda12.2.0

# ---------------------------------------------------------------------------
# Dependências de sistema
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Dependências Python
# ---------------------------------------------------------------------------
WORKDIR /workspace

COPY requirements.txt /workspace/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /workspace/requirements.txt

# ---------------------------------------------------------------------------
# Código do worker
# ---------------------------------------------------------------------------
COPY handler.py /workspace/handler.py

# ---------------------------------------------------------------------------
# Variáveis de ambiente com defaults seguros
# (credenciais NUNCA são definidas aqui — apenas via RunPod Secrets)
# ---------------------------------------------------------------------------
ENV LTX_MODEL_ID="Lightricks/LTX-Video" \
    LTX_OUTPUT_DIR="/tmp/ltx_outputs" \
    AWS_REGION="auto"

# Serverless: sem porta exposta (o RunPod SDK gerencia a comunicação)

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
# -u desabilita o buffer do stdout/stderr para que os logs apareçam em tempo
# real no painel do RunPod.
CMD ["python", "-u", "/workspace/handler.py"]
