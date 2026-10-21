# CineForge — RunPod Persistent Pod: Wan2.2 (WanGP)
# Base: CUDA 12.4 + Python 3.11 no RunPod serverless runtime necessário aqui
# GPU alvo: NVIDIA A100 80 GB (recomendado) ou RTX 4090 24 GB (clips curtos)
#
# Variáveis de ambiente esperadas no pod (injetadas pelo RunPod):
#   WAN22_MODEL_PATH  — caminho local dos pesos (padrão: /workspace/models/wan2.2)
#   WANGP_PATH        — raiz do clone WanGP   (padrão: /workspace/WanGP)
#   WAN22_OUTPUT_DIR  — pasta de saída dos mp4 (padrão: /tmp/wan22_outputs)

FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# --------------------------------------------------------------------------- #
# Sistema
# --------------------------------------------------------------------------- #
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-dev python3-pip \
        git wget curl ffmpeg libsm6 libxext6 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3    /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------------------------- #
# Dependências Python
# --------------------------------------------------------------------------- #
WORKDIR /workspace

COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------------------------------- #
# WanGP (engine Wan2.2) — clonado uma vez na imagem, pesos montados em volume
# --------------------------------------------------------------------------- #
RUN git clone --depth 1 https://github.com/deepbeepmeep/WanGP.git /workspace/WanGP \
    && pip install --no-cache-dir -r /workspace/WanGP/requirements.txt 2>/dev/null || true

# --------------------------------------------------------------------------- #
# Servidor FastAPI CineForge
# --------------------------------------------------------------------------- #
COPY server.py /workspace/server.py

# --------------------------------------------------------------------------- #
# Variáveis de ambiente padrão (substituídas pelo painel RunPod se necessário)
# --------------------------------------------------------------------------- #
ENV WANGP_PATH=/workspace/WanGP
ENV WAN22_MODEL_PATH=/workspace/models/wan2.2
ENV WAN22_OUTPUT_DIR=/tmp/wan22_outputs

# Porta exposta (mapeada pelo proxy RunPod: {pod_id}-8080.proxy.runpod.net)
EXPOSE 8080

# --------------------------------------------------------------------------- #
# Entrypoint — o modelo é pré-carregado no startup para zero cold start
# --------------------------------------------------------------------------- #
CMD ["python", "-m", "uvicorn", "server:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1", \
     "--log-level", "info"]
