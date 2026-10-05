"""
CineForge FastAPI Server — backend que o webapp Next.js consome.

Endpoints:
  GET  /api/health
  GET  /api/jobs              — lista todos os jobs
  POST /api/jobs              — cria novo job de vídeo
  GET  /api/jobs/{job_id}     — detalhe de um job
  DELETE /api/jobs/{job_id}   — cancela um job
  GET  /api/queue/stats       — estatísticas da fila

  GET  /api/channels          — lista canais configurados
  GET  /api/channels/{id}/quota — quota YouTube do canal

  POST /api/scan              — dispara scan de oportunidades por nicho
  POST /api/downloader/start  — inicia turbo downloader de referências virais
  GET  /api/downloader/models — lista edit models gerados

  GET  /api/niche/opportunities?niche=finance_dark&market=US
  POST /api/niche/audit       — diagnóstico CTR × Retenção
  POST /api/niche/brief       — gera briefing completo de vídeo
  GET  /api/niche/report      — relatório semanal em markdown

  GET  /api/providers/status  — disponibilidade de cada provider

Roda em localhost:8765 por padrão.
Uso: uvicorn src.api.server:app --port 8765 --reload
"""
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

log = logging.getLogger(__name__)

app = FastAPI(
    title="CineForge API",
    version="2.0",
    description="Backend do sistema CineForge — geração de vídeos virais em massa",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class CreateJobRequest(BaseModel):
    topic: str = ""
    niche: str = "dark"
    language: str = "pt-BR"
    market: str = "BR"
    channel_id: str = ""
    duration_min: int = 10
    video_provider: str = "auto"
    priority: int = 5

class ScanRequest(BaseModel):
    niche: str = "dark"
    limit: int = 5

class DownloaderRequest(BaseModel):
    url: str
    niche: str = "dark"
    min_views: int = 500_000
    max_videos: int = 15

class NicheAuditRequest(BaseModel):
    ctr_estimate: float
    avg_view_duration_pct: float
    niche: str = "finance_dark"

class VideoBriefRequest(BaseModel):
    keyword: str
    niche: str = "finance_dark"
    market: str = "US"
    cpm_estimate: float = 20.0


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_queue():
    from src.engine.job_queue import JobQueue
    return JobQueue()

def _get_niche_strategist():
    from src.tools.niche_strategist import get_niche_strategist
    return get_niche_strategist()


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"ok": True, "service": "CineForge API", "version": "2.0", "timestamp": time.time()}


# ─── Jobs ────────────────────────────────────────────────────────────────────

@app.get("/api/jobs")
def list_jobs(status: Optional[str] = None, niche: Optional[str] = None, limit: int = 50):
    try:
        queue = _get_queue()
        stats = queue.get_stats()
        jobs = stats.get("jobs", [])
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        if niche:
            jobs = [j for j in jobs if j.get("niche") == niche]
        return {"jobs": jobs[:limit], "total": len(jobs)}
    except Exception as e:
        log.exception("list_jobs")
        raise HTTPException(500, str(e))


@app.post("/api/jobs", status_code=201)
def create_job(req: CreateJobRequest):
    try:
        from src.engine.job_queue import JobQueue, VideoJob
        queue = JobQueue()
        job = VideoJob(
            topic=req.topic,
            niche=req.niche,
            language=req.language,
            market=req.market,
            channel_id=req.channel_id,
            duration_min=req.duration_min,
            video_provider=req.video_provider,
            priority=req.priority,
        )
        job_id = queue.add(job)
        log.info("Job criado: %s — %s (%s)", job_id, job.topic or "auto", job.niche)
        return {"ok": True, "job_id": job_id, "job": job.to_dict()}
    except Exception as e:
        log.exception("create_job")
        raise HTTPException(500, str(e))


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    try:
        queue = _get_queue()
        stats = queue.get_stats()
        for j in stats.get("jobs", []):
            if j.get("job_id") == job_id:
                return j
        raise HTTPException(404, f"Job {job_id} não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str):
    try:
        queue = _get_queue()
        # Marca como failed para cancelamento
        stats = queue.get_stats()
        for j in stats.get("jobs", []):
            if j.get("job_id") == job_id and j.get("status") in ("pending", "retry"):
                # JobQueue carrega state do arquivo — atualiza diretamente
                import json
                from src.engine.job_queue import QUEUE_STATE_FILE
                if QUEUE_STATE_FILE.exists():
                    data = json.loads(QUEUE_STATE_FILE.read_text())
                    for item in data.get("jobs", []):
                        if item["job_id"] == job_id:
                            item["status"] = "failed"
                            item["error"] = "Cancelado pelo usuário"
                    QUEUE_STATE_FILE.write_text(json.dumps(data, indent=2))
                return {"ok": True, "job_id": job_id}
        raise HTTPException(404, f"Job {job_id} não encontrado ou já finalizado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/queue/stats")
def queue_stats():
    try:
        queue = _get_queue()
        return queue.get_stats()
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Channels ────────────────────────────────────────────────────────────────

@app.get("/api/channels")
def list_channels():
    """Lista canais configurados via config/youtube_*.json ou env vars."""
    try:
        import os
        channels = []
        config_dir = Path("config")
        if config_dir.exists():
            for f in config_dir.glob("youtube_*.json"):
                channel_id = f.stem.replace("youtube_", "")
                channels.append({"channel_id": channel_id, "config_file": str(f), "source": "file"})
        if os.environ.get("YOUTUBE_CHANNEL_ID"):
            channels.append({"channel_id": os.environ["YOUTUBE_CHANNEL_ID"], "source": "env"})
        return {"channels": channels, "total": len(channels)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/channels/{channel_id}/quota")
def channel_quota(channel_id: str):
    try:
        from src.engine.youtube_uploader import QuotaManager
        qm = QuotaManager()
        return {
            "channel_id": channel_id,
            "used_today": qm.used_today(channel_id),
            "remaining_today": qm.remaining_today(channel_id),
            "can_upload": qm.can_upload(channel_id),
            "daily_limit": 10_000,
            "cost_per_upload": 100,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Scan ────────────────────────────────────────────────────────────────────

@app.post("/api/scan")
def scan_opportunities(req: ScanRequest):
    try:
        from src.trend_monitor.opportunity_router import get_opportunity_router
        router = get_opportunity_router()
        topics = router.get_sample_topics(req.niche, limit=req.limit)
        from src.engine.job_queue import JobQueue, VideoJob
        queue = JobQueue()
        jobs = [VideoJob(topic=t, niche=req.niche) for t in topics]
        ids = queue.add_batch(jobs)
        return {"ok": True, "niche": req.niche, "jobs_created": len(ids), "topics": topics}
    except Exception as e:
        log.exception("scan")
        raise HTTPException(500, str(e))


# ─── Downloader ──────────────────────────────────────────────────────────────

_downloader_tasks: dict[str, dict] = {}

@app.post("/api/downloader/start", status_code=202)
def start_downloader(req: DownloaderRequest, background_tasks: BackgroundTasks):
    try:
        import uuid
        task_id = str(uuid.uuid4())[:8]
        _downloader_tasks[task_id] = {"status": "queued", "url": req.url, "niche": req.niche}

        def _run():
            try:
                _downloader_tasks[task_id]["status"] = "running"
                from src.tools.media_downloader import MediaDownloader, DownloadConfig
                cfg = DownloadConfig(min_views=req.min_views, max_videos=req.max_videos)
                dl = MediaDownloader(cfg)
                results = dl.download_channel(req.url, req.niche)
                _downloader_tasks[task_id]["status"] = "done"
                _downloader_tasks[task_id]["downloaded"] = len(results)
            except Exception as exc:
                _downloader_tasks[task_id]["status"] = "error"
                _downloader_tasks[task_id]["error"] = str(exc)

        background_tasks.add_task(_run)
        return {"ok": True, "task_id": task_id}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/downloader/status/{task_id}")
def downloader_status(task_id: str):
    task = _downloader_tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task não encontrada")
    return task


@app.get("/api/downloader/models")
def list_edit_models():
    """Lista modelos de edição gerados pelo EditModeler."""
    try:
        models_dir = Path("batch/edit_models")
        if not models_dir.exists():
            return {"models": []}
        import json
        models = []
        for f in models_dir.glob("*_model.json"):
            try:
                data = json.loads(f.read_text())
                models.append(data)
            except Exception:
                pass
        return {"models": models}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Niche Strategist ────────────────────────────────────────────────────────

@app.get("/api/niche/opportunities")
async def niche_opportunities(niche: str = "finance_dark", market: str = "US", limit: int = 10):
    try:
        ns = _get_niche_strategist()
        keywords = await ns.get_youtube_autocomplete(niche.replace("_", " "))
        results = []
        for kw in keywords[:limit]:
            try:
                opp = ns.validate_niche_opportunity(kw, niche=niche, market=market)
                results.append({
                    "keyword": opp.keyword,
                    "scores": opp.scores,
                    "cpm_estimate": opp.cpm_estimate,
                    "opportunity_score": opp.opportunity_score,
                    "monetization_options": opp.monetization_options,
                })
            except Exception:
                pass
        results.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return {"niche": niche, "market": market, "opportunities": results}
    except Exception as e:
        log.exception("niche_opportunities")
        raise HTTPException(500, str(e))


@app.post("/api/niche/audit")
def niche_audit(req: NicheAuditRequest):
    try:
        ns = _get_niche_strategist()
        result = ns.audit_ctr_performance(
            ctr_estimate=req.ctr_estimate,
            avg_view_duration_pct=req.avg_view_duration_pct,
            niche=req.niche,
        )
        return {
            "ctr_estimate": result.ctr_estimate,
            "ctr_target": result.ctr_target,
            "avg_view_duration_pct": result.avg_view_duration_pct,
            "quadrant": getattr(result, "quadrant", None),
            "issues": result.issues,
            "recommendations": result.recommendations,
            "priority_actions": result.priority_actions,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/niche/brief")
def niche_brief(req: VideoBriefRequest):
    try:
        ns = _get_niche_strategist()
        brief = ns.generate_video_brief(
            keyword=req.keyword,
            niche=req.niche,
            market=req.market,
            cpm_estimate=req.cpm_estimate,
        )
        return brief
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/niche/report")
def niche_report(niche: str = "finance_dark", market: str = "US"):
    try:
        ns = _get_niche_strategist()
        report = ns.generate_weekly_strategy_report(niche=niche, market=market)
        return {"niche": niche, "market": market, "report": report}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Providers ───────────────────────────────────────────────────────────────

@app.get("/api/providers/status")
def providers_status():
    status = {}
    try:
        from src.providers.fal_provider import get_fal_provider
        fal = get_fal_provider()
        status["fal_ai"] = {"available": fal.is_available(), "models": list(fal.MODELS.keys())}
    except Exception as e:
        status["fal_ai"] = {"available": False, "error": str(e)}
    try:
        from src.providers.veo3_provider import get_veo3_provider
        veo = get_veo3_provider()
        status["veo3"] = {"available": veo.is_available()}
    except Exception as e:
        status["veo3"] = {"available": False, "error": str(e)}
    try:
        from src.providers.kling_provider import get_kling_provider
        kling = get_kling_provider()
        status["kling"] = {"available": kling.is_available()}
    except Exception as e:
        status["kling"] = {"available": False, "error": str(e)}
    try:
        from src.providers.elevenlabs_provider import get_elevenlabs_provider
        el = get_elevenlabs_provider()
        status["elevenlabs"] = {"available": el.is_available()}
    except Exception as e:
        status["elevenlabs"] = {"available": False, "error": str(e)}
    return status


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8765, reload=True)
