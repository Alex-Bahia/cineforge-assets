"""
CineForge Engine — orquestrador central de geração de vídeo em massa.

Arquitetura de 3 camadas:
  1. Provider Layer  — Veo3, Kling, Higgsfield, RunPod (adaptadores intercambiáveis)
  2. Pipeline Layer  — Script → TTS → Visuals → Edit → Upload (6 passos originais)
  3. Engine Layer    — Orquestrador, fila de jobs, rate limiting, multi-canal
"""
from .job_queue import JobQueue, VideoJob, JobStatus
from .channel_engine import ChannelEngine

__all__ = ["JobQueue", "VideoJob", "JobStatus", "ChannelEngine"]
