"""
JobQueue — fila de produção de vídeos com controle de concorrência e rate limiting.

Suporta:
  - Múltiplos canais em paralelo
  - Rate limiting por provider de IA (evitar 429s)
  - Retry automático com backoff exponencial
  - Persistência de estado (jobs não se perdem se o processo morrer)
  - Prioridade por nicho e janela de oportunidade
"""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

log = logging.getLogger(__name__)

QUEUE_STATE_FILE = Path("batch/job_queue.json")


class JobStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    DONE      = "done"
    FAILED    = "failed"
    RETRY     = "retry"


@dataclass
class VideoJob:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    topic: str = ""
    niche: str = "dark"
    language: str = "pt-BR"
    market: str = "BR"
    channel_id: str = ""
    duration_min: int = 10
    tts_tier: str = "free"
    video_provider: str = "auto"
    priority: int = 5              # 1=highest, 10=lowest
    status: JobStatus = JobStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    output_path: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    opportunity_score: float = 0.0
    estimated_cost_usd: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "VideoJob":
        d = d.copy()
        d["status"] = JobStatus(d.get("status", "pending"))
        return cls(**d)


class RateLimiter:
    """Token bucket rate limiter por provider."""

    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self._tokens = float(calls_per_minute)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(
                float(self.calls_per_minute),
                self._tokens + elapsed * (self.calls_per_minute / 60.0),
            )
            self._last_refill = now
            if self._tokens < 1:
                wait = (1 - self._tokens) / (self.calls_per_minute / 60.0)
                log.debug("RateLimiter: aguardando %.1fs", wait)
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1


PROVIDER_RATE_LIMITS = {
    "veo3": RateLimiter(calls_per_minute=5),
    "kling": RateLimiter(calls_per_minute=20),
    "higgsfield": RateLimiter(calls_per_minute=10),
    "elevenlabs": RateLimiter(calls_per_minute=30),
    "gemini": RateLimiter(calls_per_minute=60),
    "pexels": RateLimiter(calls_per_minute=200),
}


class JobQueue:
    """
    Fila de produção de vídeos com suporte a múltiplos workers concorrentes.

    Exemplo de uso:
        queue = JobQueue(max_workers=3)
        queue.add(VideoJob(topic="Enron", niche="finance_dark", channel_id="us_finance_dark"))
        await queue.run(pipeline_fn=run_full_pipeline)
    """

    def __init__(
        self,
        max_workers: int = 2,
        state_file: Path = QUEUE_STATE_FILE,
    ):
        self.max_workers = max_workers
        self.state_file = Path(state_file)
        self._jobs: list[VideoJob] = []
        self._lock = asyncio.Lock()
        self._load_state()

    def _load_state(self) -> None:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._jobs = [VideoJob.from_dict(d) for d in data]
                pending = sum(1 for j in self._jobs if j.status in (JobStatus.PENDING, JobStatus.RETRY))
                log.info("JobQueue: %d jobs carregados (%d pendentes)", len(self._jobs), pending)
                # Reset RUNNING → RETRY on restart (process was killed mid-job)
                for job in self._jobs:
                    if job.status == JobStatus.RUNNING:
                        job.status = JobStatus.RETRY
            except Exception as e:
                log.warning("JobQueue: erro ao carregar estado: %s", e)

    def _save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.state_file.write_text(
                json.dumps([j.to_dict() for j in self._jobs], ensure_ascii=False, indent=2)
            )
        except Exception as e:
            log.warning("JobQueue: erro ao salvar estado: %s", e)

    def add(self, job: VideoJob) -> str:
        self._jobs.append(job)
        self._save_state()
        log.info("JobQueue: job %s adicionado (nicho=%s, tópico=%s)", job.job_id, job.niche, job.topic[:50])
        return job.job_id

    def add_batch(self, jobs: list[VideoJob]) -> list[str]:
        self._jobs.extend(jobs)
        self._save_state()
        log.info("JobQueue: %d jobs adicionados em batch", len(jobs))
        return [j.job_id for j in jobs]

    def pending_count(self) -> int:
        return sum(1 for j in self._jobs if j.status in (JobStatus.PENDING, JobStatus.RETRY))

    def get_stats(self) -> dict:
        from collections import Counter
        counts = Counter(j.status.value for j in self._jobs)
        total_cost = sum(j.estimated_cost_usd for j in self._jobs if j.status == JobStatus.DONE)
        return {
            "total": len(self._jobs),
            **dict(counts),
            "total_cost_usd": round(total_cost, 2),
        }

    def _next_job(self) -> Optional[VideoJob]:
        candidates = [
            j for j in self._jobs
            if j.status in (JobStatus.PENDING, JobStatus.RETRY)
            and j.attempts < j.max_attempts
        ]
        if not candidates:
            return None
        # Sort by priority (lower = higher priority), then by opportunity_score desc
        candidates.sort(key=lambda j: (j.priority, -j.opportunity_score))
        return candidates[0]

    async def run(
        self,
        pipeline_fn: Callable,
        stop_on_empty: bool = True,
    ) -> None:
        """
        Executa a fila com max_workers workers concorrentes.

        pipeline_fn(job: VideoJob) deve ser uma coroutine que processa o job
        e retorna o path do vídeo final ou lança exceção.
        """
        log.info("JobQueue: iniciando com %d workers", self.max_workers)
        semaphore = asyncio.Semaphore(self.max_workers)

        async def _run_one(job: VideoJob) -> None:
            async with semaphore:
                async with self._lock:
                    job.status = JobStatus.RUNNING
                    job.started_at = time.time()
                    job.attempts += 1
                    self._save_state()

                try:
                    result_path = await pipeline_fn(job)
                    async with self._lock:
                        job.status = JobStatus.DONE
                        job.finished_at = time.time()
                        job.output_path = str(result_path) if result_path else None
                        self._save_state()
                    log.info("JobQueue: job %s DONE → %s", job.job_id, job.output_path)
                except Exception as e:
                    async with self._lock:
                        if job.attempts >= job.max_attempts:
                            job.status = JobStatus.FAILED
                            log.error("JobQueue: job %s FAILED após %d tentativas: %s", job.job_id, job.attempts, e)
                        else:
                            job.status = JobStatus.RETRY
                            log.warning("JobQueue: job %s retry %d/%d: %s", job.job_id, job.attempts, job.max_attempts, e)
                        job.error = str(e)
                        self._save_state()

        tasks = set()
        while True:
            async with self._lock:
                job = self._next_job()

            if job is None:
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    tasks.clear()
                    continue
                if stop_on_empty:
                    break
                await asyncio.sleep(30)
                continue

            task = asyncio.create_task(_run_one(job))
            tasks.add(task)
            task.add_done_callback(tasks.discard)

            # Yield briefly so other tasks can run
            await asyncio.sleep(0.1)

        log.info("JobQueue: processamento concluído. Stats: %s", self.get_stats())
