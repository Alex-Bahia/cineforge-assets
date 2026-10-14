#!/bin/bash
# =============================================================================
# XTTS v2 — Instalação na VPS Hermes (Ubuntu 22.04)
# Rodar na VPS via SSH: ssh ubuntu@167.234.255.202
# =============================================================================

set -e  # para em caso de erro

echo "========================================"
echo "  XTTS v2 — Setup CineForge Voice API"
echo "========================================"

# --- 1. Atualizar sistema e instalar dependências base ---
echo ""
echo "[1/7] Atualizando sistema..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv git ffmpeg curl wget

# --- 2. Criar ambiente virtual isolado ---
echo ""
echo "[2/7] Criando ambiente virtual Python..."
cd /home/ubuntu
python3 -m venv venv_xtts
source venv_xtts/bin/activate

# --- 3. Instalar PyTorch (CPU-only para Oracle Cloud free tier) ---
echo ""
echo "[3/7] Instalando PyTorch (CPU-only)..."
pip install --upgrade pip wheel setuptools
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# --- 4. Instalar TTS (Coqui XTTS v2) ---
echo ""
echo "[4/7] Instalando Coqui TTS com XTTS v2..."
pip install TTS==0.22.0
pip install fastapi uvicorn python-multipart

# --- 5. Pré-baixar modelo XTTS v2 (~1.8GB) ---
echo ""
echo "[5/7] Baixando modelo XTTS v2 (~1.8GB — pode demorar)..."
python3 - <<'PYEOF'
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True)
print("Modelo XTTS v2 baixado com sucesso!")
PYEOF

# --- 6. Criar diretório de referências de voz ---
echo ""
echo "[6/7] Criando estrutura de diretórios..."
mkdir -p /home/ubuntu/xtts_voices/referencias
mkdir -p /home/ubuntu/xtts_voices/geradas

echo "========================================"
echo "  Estrutura criada:"
echo "  /home/ubuntu/xtts_voices/referencias  <- coloque aqui seus .wav/.mp3"
echo "  /home/ubuntu/xtts_voices/geradas      <- áudios gerados ficam aqui"
echo "========================================"

# --- 7. Criar API FastAPI ---
echo ""
echo "[7/7] Criando servidor API..."
cat > /home/ubuntu/xtts_api.py << 'APIEOF'
"""
CineForge Voice API — XTTS v2
Porta: 8765
Endpoints:
  POST /gerar-voz       — gera áudio com voz clonada
  POST /clonar-voz      — registra nova voz de referência
  GET  /vozes           — lista vozes disponíveis
  GET  /healthcheck     — status da API
"""

import os
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from TTS.api import TTS

app = FastAPI(title="CineForge Voice API", version="1.0.0")

VOICES_DIR = Path("/home/ubuntu/xtts_voices/referencias")
OUTPUT_DIR = Path("/home/ubuntu/xtts_voices/geradas")
VOICES_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Carrega modelo uma vez ao subir a API
print("Carregando modelo XTTS v2...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
print("Modelo carregado!")


class GerarVozRequest(BaseModel):
    texto: str
    voz: str = "minha_voz"           # nome do arquivo de referência (sem extensão)
    idioma: str = "pt"               # pt, en, es, fr, de, it, etc.
    nome_arquivo: Optional[str] = None  # nome do arquivo de saída


@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok", "modelo": "xtts_v2", "idioma_padrao": "pt"}


@app.get("/vozes")
def listar_vozes():
    vozes = []
    for f in VOICES_DIR.iterdir():
        if f.suffix.lower() in [".wav", ".mp3", ".flac"]:
            vozes.append({"nome": f.stem, "arquivo": f.name, "tamanho_mb": round(f.stat().st_size / 1024 / 1024, 2)})
    return {"vozes": vozes, "total": len(vozes)}


@app.post("/clonar-voz")
async def clonar_voz(nome: str, arquivo: UploadFile = File(...)):
    """Registra um arquivo de referência de voz. Mínimo 6 segundos de áudio."""
    if not arquivo.filename.lower().endswith((".wav", ".mp3", ".flac")):
        raise HTTPException(status_code=400, detail="Formato suportado: .wav .mp3 .flac")

    ext = Path(arquivo.filename).suffix.lower()
    destino = VOICES_DIR / f"{nome}{ext}"

    with open(destino, "wb") as f:
        shutil.copyfileobj(arquivo.file, f)

    tamanho_mb = destino.stat().st_size / 1024 / 1024
    return {
        "status": "ok",
        "voz": nome,
        "arquivo": destino.name,
        "tamanho_mb": round(tamanho_mb, 2),
        "instrucoes": f"Use 'voz': '{nome}' no endpoint /gerar-voz"
    }


@app.post("/gerar-voz")
async def gerar_voz(req: GerarVozRequest):
    """Gera áudio em português usando XTTS v2 com voz de referência."""

    if len(req.texto.strip()) < 2:
        raise HTTPException(status_code=400, detail="Texto muito curto")
    if len(req.texto) > 5000:
        raise HTTPException(status_code=400, detail="Texto máximo: 5000 caracteres")

    # Localiza arquivo de referência
    referencia = None
    for ext in [".wav", ".mp3", ".flac"]:
        candidato = VOICES_DIR / f"{req.voz}{ext}"
        if candidato.exists():
            referencia = candidato
            break

    if referencia is None:
        vozes_disponiveis = [f.stem for f in VOICES_DIR.iterdir() if f.suffix in [".wav", ".mp3", ".flac"]]
        raise HTTPException(
            status_code=404,
            detail=f"Voz '{req.voz}' não encontrada. Disponíveis: {vozes_disponiveis}. Use /clonar-voz para registrar."
        )

    # Nome do arquivo de saída
    if req.nome_arquivo:
        nome_saida = req.nome_arquivo if req.nome_arquivo.endswith(".wav") else f"{req.nome_arquivo}.wav"
    else:
        hash_texto = hashlib.md5(req.texto.encode()).hexdigest()[:8]
        nome_saida = f"{req.voz}_{req.idioma}_{hash_texto}.wav"

    caminho_saida = OUTPUT_DIR / nome_saida

    # Gera o áudio
    try:
        tts.tts_to_file(
            text=req.texto,
            speaker_wav=str(referencia),
            language=req.idioma,
            file_path=str(caminho_saida)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na geração: {str(e)}")

    tamanho_kb = caminho_saida.stat().st_size / 1024
    return FileResponse(
        path=str(caminho_saida),
        media_type="audio/wav",
        filename=nome_saida,
        headers={"X-Tamanho-KB": str(round(tamanho_kb, 1))}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")
APIEOF

echo ""
echo "========================================"
echo "  Instalação concluída!"
echo ""
echo "  Para testar agora:"
echo "  source /home/ubuntu/venv_xtts/bin/activate"
echo "  python3 /home/ubuntu/xtts_api.py"
echo ""
echo "  API rodará em http://167.234.255.202:8765"
echo "========================================"
