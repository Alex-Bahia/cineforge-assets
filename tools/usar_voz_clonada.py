"""
Módulo auxiliar: usa a CineForge Voice API (XTTS v2) em vez do edge-tts
Importar em gerar_videos_modulos.py quando a API estiver ativa na VPS
"""

import os
import requests
from pathlib import Path

VOICE_API = os.getenv("CINEFORGE_VOICE_API", "http://167.234.255.202:8765")
VOZ_PADRAO = os.getenv("CINEFORGE_VOZ", "minha_voz")


def registrar_voz_referencia(caminho_audio: str, nome_voz: str = "minha_voz") -> dict:
    """Envia arquivo de referência para a API. Mínimo 6 segundos de áudio."""
    with open(caminho_audio, "rb") as f:
        ext = Path(caminho_audio).suffix.lower()
        mime = "audio/wav" if ext == ".wav" else "audio/mpeg"
        r = requests.post(
            f"{VOICE_API}/clonar-voz",
            params={"nome": nome_voz},
            files={"arquivo": (Path(caminho_audio).name, f, mime)},
            timeout=60
        )
    r.raise_for_status()
    return r.json()


def gerar_audio_com_voz(
    texto: str,
    caminho_saida: str,
    voz: str = VOZ_PADRAO,
    idioma: str = "pt"
) -> str:
    """Gera áudio com voz clonada via XTTS v2 e salva em caminho_saida."""
    r = requests.post(
        f"{VOICE_API}/gerar-voz",
        json={"texto": texto, "voz": voz, "idioma": idioma},
        timeout=120,
        stream=True
    )
    r.raise_for_status()

    with open(caminho_saida, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"  [XTTS] Áudio gerado → {caminho_saida}")
    return caminho_saida


def api_disponivel() -> bool:
    """Verifica se a API de voz está online."""
    try:
        r = requests.get(f"{VOICE_API}/healthcheck", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


if __name__ == "__main__":
    print("Testando CineForge Voice API...")
    if not api_disponivel():
        print(f"API offline em {VOICE_API}.")
        print("Suba a API primeiro: ssh ubuntu@167.234.255.202 'sudo systemctl start xtts-api'")
        exit(1)

    # Teste de geração
    print("API online! Gerando áudio de teste...")
    saida = "/tmp/teste_voz.wav"
    gerar_audio_com_voz(
        "Bem-vindos ao CineForge, o sistema de produção cinematográfica com inteligência artificial.",
        saida
    )
    print(f"Sucesso! Arquivo salvo em: {saida}")
