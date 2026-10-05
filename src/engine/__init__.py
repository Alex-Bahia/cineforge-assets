"""
CineForge Engine — orquestrador central de geração de vídeo em massa.

Arquitetura de 3 camadas:
  1. Provider Layer  — Veo3.1, Kling 3.0, fal.ai (LTX/Wan), Higgsfield (adaptadores intercambiáveis)
  2. Pipeline Layer  — Script → TTS → Visuals → Edit → Upload (6 passos originais)
  3. Engine Layer    — Orquestrador, fila de jobs, rate limiting, multi-canal
"""
from .job_queue import JobQueue, VideoJob, JobStatus
from .channel_engine import ChannelEngine
from .youtube_uploader import YouTubeUploader, UploadResult, get_youtube_uploader
from .narrative_engine import NarrativeEngine, NarrativeConfig, get_narrative_engine

__all__ = [
    "JobQueue", "VideoJob", "JobStatus", "ChannelEngine",
    "YouTubeUploader", "UploadResult", "get_youtube_uploader",
    "NarrativeEngine", "NarrativeConfig", "get_narrative_engine",
]
