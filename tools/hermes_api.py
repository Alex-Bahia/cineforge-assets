"""
Hermes API — Servidor de comandos para a VPS
Claude chama este servidor via HTTP para executar scripts remotamente.

Uso: python3 tools/hermes_api.py
Porta: 8765 (ou defina HERMES_PORT)
Token: defina HERMES_TOKEN no .env da VPS
"""

import os
import subprocess
import json
import hashlib
import hmac
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = int(os.getenv("HERMES_PORT", "8765"))
TOKEN = os.getenv("HERMES_TOKEN", "")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def verificar_token(token_recebido: str) -> bool:
    if not TOKEN:
        return False
    return hmac.compare_digest(TOKEN, token_recebido)


class HermesHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[Hermes] {self.address_string()} — {format % args}")

    def send_json(self, code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/status":
            self.send_json(200, {"status": "ok", "hermes": "online", "base_dir": BASE_DIR})
            return

        self.send_json(404, {"erro": "rota não encontrada"})

    def do_POST(self):
        parsed = urlparse(self.path)
        token = self.headers.get("X-Hermes-Token", "")

        if not verificar_token(token):
            self.send_json(401, {"erro": "token inválido"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body)
        except Exception:
            self.send_json(400, {"erro": "JSON inválido"})
            return

        if parsed.path == "/executar":
            self._executar_script(payload)
        elif parsed.path == "/status-job":
            self._status_job(payload)
        else:
            self.send_json(404, {"erro": "rota não encontrada"})

    def _executar_script(self, payload: dict):
        """
        Executa um script Python da pasta tools/.
        payload: { "script": "criar_video.py", "args": ["--topico", "IA", "--rapido"] }
        """
        script = payload.get("script", "")
        args = payload.get("args", [])

        # Segurança: só permite scripts da pasta tools/
        scripts_permitidos = [
            "criar_video.py",
            "gerar_videos_modulos.py",
            "video_generator.py",
        ]
        if script not in scripts_permitidos:
            self.send_json(403, {"erro": f"script não permitido: {script}"})
            return

        script_path = os.path.join(BASE_DIR, "tools", script)
        if not os.path.exists(script_path):
            self.send_json(404, {"erro": f"script não encontrado: {script}"})
            return

        cmd = ["python3", script_path] + [str(a) for a in args]
        print(f"[Hermes] Executando: {' '.join(cmd)}")

        try:
            resultado = subprocess.run(
                cmd,
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 min máx
            )
            self.send_json(200, {
                "ok": resultado.returncode == 0,
                "codigo": resultado.returncode,
                "stdout": resultado.stdout[-8000:],   # últimos 8k chars
                "stderr": resultado.stderr[-2000:],
            })
        except subprocess.TimeoutExpired:
            self.send_json(408, {"erro": "timeout após 30 minutos"})
        except Exception as e:
            self.send_json(500, {"erro": str(e)})

    def _status_job(self, payload: dict):
        """Verifica se um arquivo de saída existe (confirma que o vídeo foi gerado)."""
        arquivo = payload.get("arquivo", "")
        # Segurança: não permite path traversal
        if ".." in arquivo or arquivo.startswith("/"):
            self.send_json(403, {"erro": "path inválido"})
            return
        caminho = os.path.join(BASE_DIR, arquivo)
        existe = os.path.exists(caminho)
        tamanho = os.path.getsize(caminho) if existe else 0
        self.send_json(200, {"existe": existe, "tamanho_bytes": tamanho, "caminho": caminho})


if __name__ == "__main__":
    if not TOKEN:
        print("⚠️  HERMES_TOKEN não definido. Defina no .env antes de usar em produção.")
        print("   Exemplo: echo 'HERMES_TOKEN=minha-chave-secreta' >> .env")
        exit(1)

    print(f"🚀 Hermes API iniciando na porta {PORT}...")
    print(f"   Base dir: {BASE_DIR}")
    server = HTTPServer(("0.0.0.0", PORT), HermesHandler)
    print(f"✅ Hermes online — http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Hermes encerrada.")
