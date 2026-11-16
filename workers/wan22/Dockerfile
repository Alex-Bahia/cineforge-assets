# syntax=docker/dockerfile:1
# =============================================================================
# Worker RunPod Serverless — Wan 2.2 (diffusers) multi-shot, linux/amd64.
#
# Funciona com dois contextos de build:
#   a) raiz do repositório cineforge-assets (GitHub integration do RunPod, com
#      Dockerfile Path = workers/wan22/Dockerfile; ou no Mac:
#      docker build --platform linux/amd64 -f workers/wan22/Dockerfile .)
#   b) a própria pasta workers/wan22 (docker build .)
#
# Os pesos NÃO entram na imagem: ficam no Network Volume (/runpod-volume/wan22).
# Nenhum repositório de terceiros é clonado: o diffusers vem do PyPI em versão fixa.
# Imagem final ~9 GB (CUDA runtime + PyTorch cu124); só rodas pré-compiladas,
# então o build cabe no limite de 30 min do build pelo GitHub.
# =============================================================================

# --- Estágio 0: separa só os arquivos do worker, seja qual for o contexto -----
FROM busybox:1.36.1@sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662 AS ctx
COPY . /ctx
RUN set -eu; \
    if [ -f /ctx/workers/wan22/handler.py ]; then W=/ctx/workers/wan22; \
    elif [ -f /ctx/handler.py ]; then W=/ctx; \
    else echo "ERRO: handler.py não encontrado no contexto de build" >&2; exit 1; fi; \
    mkdir -p /out; \
    cp "$W/handler.py" "$W/requirements.txt" "$W/constraints.txt" /out/

# --- Estágio final -------------------------------------------------------------
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04@sha256:517da2300c184c9999ec203c2665244bdebd3578d12fcc7065e83667932643d9

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    TOKENIZERS_PARALLELISM=false \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    MODEL_VARIANT=a14b \
    WAN_MODEL_ROOT=/runpod-volume/wan22

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && python3 --version \
 && python3 -m pip install "pip==24.3.1"

# PyTorch 2.6.0 + CUDA 12.4 (rodas oficiais). Atenção via SDPA do próprio torch.
RUN python3 -m pip install --index-url https://download.pytorch.org/whl/cu124 "torch==2.6.0+cu124"

COPY --from=ctx /out/requirements.txt /out/constraints.txt /app/
RUN python3 -m pip install -r /app/requirements.txt -c /app/constraints.txt \
 && python3 -m pip check

COPY --from=ctx /out/handler.py /app/handler.py
WORKDIR /app
# Falha o build cedo se alguma dependência quebrar a importação (sem GPU no build).
RUN python3 -m py_compile /app/handler.py \
 && python3 -c "import handler; from diffusers import WanPipeline, AutoencoderKLWan, WanTransformer3DModel, UniPCMultistepScheduler; from transformers import UMT5EncoderModel; print('imports OK')"

CMD ["python3", "-u", "/app/handler.py"]
