"""
CineForge API Server — backend local que a extensão Chrome usa.

Expõe:
  GET  /api/queue/stats     — estado atual da fila
  POST /api/queue/add       — adiciona job à fila
  POST /api/scan            — dispara scan de oportunidades
  GET  /api/health          — health check

Roda em localhost:8765 por padrão.
Uso: python -m src.api.server
"""
import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

log = logging.getLogger(__name__)

PORT = 8765


def _json_response(handler: BaseHTTPRequestHandler, data: Any, status: int = 200) -> None:
    body = json.dumps(data, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    return json.loads(handler.rfile.read(length))


class CineForgeHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        log.debug("HTTP %s", fmt % args)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            _json_response(self, {"ok": True, "service": "CineForge API", "version": "1.0"})

        elif self.path == "/api/queue/stats":
            try:
                from src.engine.job_queue import JobQueue
                queue = JobQueue()
                stats = queue.get_stats()
                _json_response(self, stats)
            except Exception as e:
                _json_response(self, {"error": str(e)}, 500)

        else:
            _json_response(self, {"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/api/queue/add":
            try:
                payload = _read_body(self)
                from src.engine.job_queue import JobQueue, VideoJob
                queue = JobQueue()
                job = VideoJob(
                    topic=payload.get("topic") or "",
                    niche=payload.get("niche", "dark"),
                    language=payload.get("language", "pt-BR"),
                    market=payload.get("market", "BR"),
                    channel_id=payload.get("channel_id", ""),
                    duration_min=int(payload.get("duration_min", 10)),
                    video_provider=payload.get("video_provider", "auto"),
                    priority=int(payload.get("priority", 5)),
                )
                job_id = queue.add(job)
                log.info("API: job adicionado %s (%s)", job_id, job.topic or "auto")
                _json_response(self, {"ok": True, "job_id": job_id})
            except Exception as e:
                _json_response(self, {"ok": False, "error": str(e)}, 500)

        elif self.path == "/api/scan":
            try:
                payload = _read_body(self)
                niche = payload.get("niche", "dark")
                # Async scan in background thread
                from src.trend_monitor.opportunity_router import get_opportunity_router
                router = get_opportunity_router()
                topics = router.get_sample_topics(niche, limit=5)
                from src.engine.job_queue import JobQueue, VideoJob
                queue = JobQueue()
                jobs = [VideoJob(topic=t, niche=niche) for t in topics]
                queue.add_batch(jobs)
                log.info("API: scan %s → %d jobs adicionados", niche, len(jobs))
                _json_response(self, {
                    "ok": True,
                    "niche": niche,
                    "opportunities": [{"topic": t} for t in topics],
                })
            except Exception as e:
                _json_response(self, {"ok": False, "error": str(e)}, 500)

        else:
            _json_response(self, {"error": "Not found"}, 404)


def run_server(port: int = PORT) -> None:
    server = HTTPServer(("localhost", port), CineForgeHandler)
    log.info("CineForge API rodando em http://localhost:%d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    run_server()
