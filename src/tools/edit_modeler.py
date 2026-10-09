"""
EditModeler — analisa vídeos virais e extrai padrões de edição para modelagem.

A partir de vídeos com alto engajamento, extrai:
  - Ritmo de cortes (cuts per minute, scene duration distribution)
  - Estrutura do hook (primeiros 15-30s: o que acontece)
  - Arco emocional (muda de tom ao longo do vídeo?)
  - Padrão de música/áudio (BGM, cuts síncronos com beat)
  - Estrutura de legenda (tamanho de linha, frequência de destaque)
  - Template de thumbnail (cor dominante, posição do texto, emoção da face)

Os padrões extraídos são usados como "moldes" para o CineForge gerar
vídeos com edição similar à dos vídeos validados pelo mercado.

Requer: ffprobe (via ffmpeg), opcional: whisper para análise de script
"""
import json
import logging
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import re

log = logging.getLogger(__name__)

MODELS_BASE = Path("batch/edit_models")
ANALYSIS_BASE = Path("batch/video_analysis")


@dataclass
class SceneSegment:
    start_sec: float
    end_sec: float
    duration_sec: float
    has_speech: bool = False
    has_music: bool = False
    is_hook: bool = False
    is_cta: bool = False
    visual_type: str = "unknown"  # talking_head | b_roll | text_overlay | transition


@dataclass
class EditPattern:
    """Padrão de edição extraído de vídeo viral."""
    source_video_id: str
    source_url: str
    platform: str
    views: int
    niche: str

    # Ritmo
    total_duration_sec: float = 0.0
    avg_scene_duration_sec: float = 0.0
    scenes_per_minute: float = 0.0
    hook_duration_sec: float = 0.0

    # Estrutura
    total_scenes: int = 0
    has_intro: bool = True
    has_cta: bool = True
    hook_pct_of_video: float = 0.0    # % do vídeo dedicado ao hook

    # Áudio
    has_bgm: bool = True
    speech_pct: float = 0.0           # % do vídeo com voz
    silence_pct: float = 0.0

    # Legenda
    subtitle_line_chars: int = 40     # tamanho médio de linha
    subtitle_words_per_sec: float = 2.5

    # Cenas por tipo
    scene_distribution: dict = field(default_factory=dict)

    # Script extraído (primeiros 2 minutos)
    hook_transcript: str = ""
    full_transcript: str = ""

    # Qualidade do padrão
    confidence: float = 0.5           # 0-1, baseado em quantos dados foram extraídos
    extracted_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_prompt_template(self) -> str:
        """Converte padrão em template de prompt para geração de roteiro."""
        return f"""TEMPLATE DE EDIÇÃO (baseado em vídeo com {self.views:,} views):

- Duração total: {self.total_duration_sec:.0f}s ({self.total_duration_sec/60:.1f} min)
- Cenas: {self.total_scenes} cenas, média {self.avg_scene_duration_sec:.1f}s cada
- Ritmo: {self.scenes_per_minute:.1f} cortes/minuto
- Hook: primeiros {self.hook_duration_sec:.0f}s ({self.hook_pct_of_video:.0f}% do vídeo)
- Fala: {self.speech_pct:.0f}% do vídeo com narração
- BGM: {"sim" if self.has_bgm else "não"}
- CTA no final: {"sim" if self.has_cta else "não"}

ESTRUTURA DO HOOK ORIGINAL:
{self.hook_transcript[:500] if self.hook_transcript else "(sem transcrição disponível)"}

Use esse ritmo e estrutura como referência para o novo roteiro."""


class EditModeler:
    """
    Analisa vídeos virais baixados e extrai padrões de edição reutilizáveis.
    """

    def __init__(self):
        MODELS_BASE.mkdir(parents=True, exist_ok=True)
        ANALYSIS_BASE.mkdir(parents=True, exist_ok=True)

    def _run_ffprobe(self, video_path: Path) -> Optional[dict]:
        """Executa ffprobe e retorna JSON com informações do vídeo."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-show_format",
            str(video_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as exc:
            log.warning("EditModeler: ffprobe falhou para %s: %s", video_path.name, exc)
        return None

    def _detect_scene_cuts(self, video_path: Path) -> list[float]:
        """
        Detecta cortes de cena via ffmpeg scene detection.
        Retorna lista de timestamps em segundos onde ocorrem cortes.
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-f", "lavfi",
            f"movie={video_path},select=gt(scene\\,0.35)",
            "-show_frames",
            "-show_entries", "frame=pts_time",
            "-print_format", "json",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return [float(f["pts_time"]) for f in data.get("frames", [])]
        except Exception:
            pass

        # Fallback: usar scene detection do ffmpeg via subprocess
        cmd2 = [
            "ffmpeg", "-i", str(video_path),
            "-filter:v", "select='gt(scene,0.35)',metadata=print:file=-",
            "-an", "-f", "null", "/dev/null",
        ]
        try:
            result = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
            timestamps = []
            for line in result.stderr.split("\n"):
                if "pts_time:" in line:
                    match = re.search(r"pts_time:([\d.]+)", line)
                    if match:
                        timestamps.append(float(match.group(1)))
            return timestamps
        except Exception:
            return []

    def _extract_audio_segments(self, video_path: Path) -> dict:
        """
        Analisa segmentos de áudio: detecta presença de voz vs. música vs. silêncio.
        Usa silencedetect do ffmpeg.
        """
        cmd = [
            "ffprobe", "-v", "quiet",
            "-f", "lavfi",
            f"amovie={video_path},silencedetect=n=-40dB:d=0.5",
            "-show_entries", "frame_tags=lavfi.silence_start,lavfi.silence_end",
            "-print_format", "json",
        ]
        silence_periods = []
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                frames = data.get("frames", [])
                current_start = None
                for f in frames:
                    tags = f.get("tags", {})
                    if "lavfi.silence_start" in tags:
                        current_start = float(tags["lavfi.silence_start"])
                    if "lavfi.silence_end" in tags and current_start is not None:
                        silence_periods.append((current_start, float(tags["lavfi.silence_end"])))
                        current_start = None
        except Exception:
            pass

        return {"silence_periods": silence_periods}

    def _extract_subtitles_from_file(self, video_path: Path) -> str:
        """Tenta encontrar arquivo de legenda associado ao vídeo."""
        base = video_path.stem
        srt_path = video_path.parent / f"{base}.pt.srt"
        if not srt_path.exists():
            srt_path = video_path.parent / f"{base}.pt-BR.srt"
        if not srt_path.exists():
            srt_path = video_path.parent / f"{base}.en.srt"
        if not srt_path.exists():
            # Try any .srt
            srts = list(video_path.parent.glob(f"{base}*.srt"))
            srt_path = srts[0] if srts else None

        if srt_path and srt_path.exists():
            try:
                content = srt_path.read_text(encoding="utf-8", errors="replace")
                # Remove SRT formatting, keep just text
                text = re.sub(r"\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n", "", content)
                text = re.sub(r"<[^>]+>", "", text)
                return text.strip()
            except Exception:
                pass
        return ""

    def _load_info_json(self, video_path: Path) -> dict:
        """Carrega metadados do .info.json do yt-dlp se disponível."""
        info_path = video_path.parent / f"{video_path.stem}.info.json"
        if info_path.exists():
            try:
                return json.loads(info_path.read_text())
            except Exception:
                pass
        return {}

    def analyze_video(
        self,
        video_path: Path,
        niche: str = "dark",
        source_url: str = "",
        views: int = 0,
        platform: str = "youtube",
    ) -> Optional[EditPattern]:
        """
        Analisa um único vídeo e extrai seu padrão de edição.
        """
        if not video_path.exists():
            log.warning("EditModeler: arquivo não encontrado: %s", video_path)
            return None

        log.info("EditModeler: analisando %s", video_path.name)

        # Load existing metadata
        info = self._load_info_json(video_path)
        vid_id = info.get("id", video_path.stem[:20])
        actual_views = views or info.get("view_count", 0) or 0
        actual_url = source_url or info.get("webpage_url", "")
        actual_platform = platform or ("youtube" if "youtube" in actual_url else "unknown")

        pattern = EditPattern(
            source_video_id=vid_id,
            source_url=actual_url,
            platform=actual_platform,
            views=actual_views,
            niche=niche,
        )

        confidence_points = 0.0
        max_points = 0.0

        # --- Análise básica via ffprobe ---
        max_points += 3
        probe_data = self._run_ffprobe(video_path)
        if probe_data:
            format_info = probe_data.get("format", {})
            pattern.total_duration_sec = float(format_info.get("duration", 0))
            confidence_points += 2

            # Hook = primeiros 30s ou 15% do vídeo, o que for menor
            if pattern.total_duration_sec > 0:
                pattern.hook_duration_sec = min(30.0, pattern.total_duration_sec * 0.15)
                pattern.hook_pct_of_video = 100 * pattern.hook_duration_sec / pattern.total_duration_sec
                confidence_points += 1

        # --- Detecção de cortes de cena ---
        max_points += 3
        scene_timestamps = self._detect_scene_cuts(video_path)
        if scene_timestamps:
            pattern.total_scenes = len(scene_timestamps) + 1
            if pattern.total_duration_sec > 0:
                # Calcular durações das cenas
                all_times = [0.0] + scene_timestamps + [pattern.total_duration_sec]
                durations = [all_times[i+1] - all_times[i] for i in range(len(all_times)-1)]
                pattern.avg_scene_duration_sec = sum(durations) / len(durations) if durations else 5.0
                pattern.scenes_per_minute = 60 * pattern.total_scenes / pattern.total_duration_sec
            confidence_points += 3
        elif pattern.total_duration_sec > 0:
            # Estimativa padrão por nicho
            niche_defaults = {
                "finance_dark": (5.0, 12.0),  # (avg_scene, cpm)
                "dark": (4.5, 13.0),
                "kids": (3.0, 20.0),
                "tech": (6.0, 10.0),
                "education": (8.0, 7.5),
            }
            avg, cpm = niche_defaults.get(niche, (5.0, 12.0))
            pattern.avg_scene_duration_sec = avg
            pattern.scenes_per_minute = cpm
            pattern.total_scenes = int(pattern.total_duration_sec / avg)

        # --- Análise de áudio ---
        max_points += 2
        audio_data = self._extract_audio_segments(video_path)
        silence_periods = audio_data.get("silence_periods", [])
        if silence_periods and pattern.total_duration_sec > 0:
            total_silence = sum(end - start for start, end in silence_periods)
            pattern.silence_pct = 100 * total_silence / pattern.total_duration_sec
            pattern.speech_pct = max(0, 100 - pattern.silence_pct - 20)  # ~20% música instrumental
            pattern.has_bgm = pattern.silence_pct < 80
            confidence_points += 2

        # --- Transcrição via legenda ---
        max_points += 2
        transcript = self._extract_subtitles_from_file(video_path)
        if transcript:
            pattern.full_transcript = transcript[:5000]
            # Hook = primeiros ~500 chars da transcrição (aproximadamente os primeiros 30s)
            pattern.hook_transcript = transcript[:500]
            # Calcular palavras por segundo
            words = len(transcript.split())
            if pattern.total_duration_sec > 0:
                pattern.subtitle_words_per_sec = words / pattern.total_duration_sec
            confidence_points += 2

        # --- Detectar CTA e intro ---
        pattern.has_cta = len(scene_timestamps) > 3  # vídeos com muitos cortes geralmente têm CTA
        pattern.has_intro = pattern.total_duration_sec > 60

        # Calcular confiança final
        pattern.confidence = min(1.0, confidence_points / max_points) if max_points > 0 else 0.3

        log.info(
            "EditModeler: %s — %.1fs, %d cenas, %.1f cpm, %.0f%% fala, confiança %.0f%%",
            vid_id[:20],
            pattern.total_duration_sec,
            pattern.total_scenes,
            pattern.scenes_per_minute,
            pattern.speech_pct,
            pattern.confidence * 100,
        )

        return pattern

    def analyze_batch(
        self,
        videos: list,  # lista de VideoMeta ou dicts com {local_path, ...}
        niche: str = "dark",
    ) -> list[EditPattern]:
        """Analisa um lote de vídeos e retorna lista de padrões."""
        patterns = []
        for v in videos:
            # Aceita VideoMeta ou dict
            if hasattr(v, "local_path"):
                path_str = v.local_path
                url = v.url
                views = v.views
                platform = v.platform
            else:
                path_str = v.get("local_path")
                url = v.get("url", "")
                views = v.get("views", 0)
                platform = v.get("platform", "youtube")

            if not path_str:
                continue

            path = Path(path_str)
            if not path.exists():
                continue

            pattern = self.analyze_video(
                video_path=path,
                niche=niche,
                source_url=url,
                views=views,
                platform=platform,
            )
            if pattern:
                patterns.append(pattern)

        return patterns

    def build_niche_model(
        self,
        patterns: list[EditPattern],
        niche: str,
        min_views_weight: int = 100_000,
    ) -> dict:
        """
        Agrega múltiplos padrões em um modelo médio ponderado por views.
        O modelo resultante representa o "estilo de edição vencedor" do nicho.
        """
        if not patterns:
            return {}

        # Filtrar por confiança mínima e ponderar por views
        good = [p for p in patterns if p.confidence >= 0.3 and p.views >= min_views_weight]
        if not good:
            good = patterns

        total_views = sum(p.views for p in good) or 1

        def weighted_avg(values_views: list[tuple]) -> float:
            if not values_views:
                return 0.0
            total_w = sum(w for _, w in values_views) or 1
            return sum(v * w for v, w in values_views) / total_w

        model = {
            "niche": niche,
            "source_videos": len(good),
            "total_views_analyzed": sum(p.views for p in good),
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "avg_duration_sec": weighted_avg([(p.total_duration_sec, p.views) for p in good]),
            "avg_scene_duration_sec": weighted_avg([(p.avg_scene_duration_sec, p.views) for p in good if p.avg_scene_duration_sec > 0]),
            "avg_scenes_per_minute": weighted_avg([(p.scenes_per_minute, p.views) for p in good if p.scenes_per_minute > 0]),
            "avg_hook_duration_sec": weighted_avg([(p.hook_duration_sec, p.views) for p in good if p.hook_duration_sec > 0]),
            "avg_speech_pct": weighted_avg([(p.speech_pct, p.views) for p in good if p.speech_pct > 0]),
            "pct_with_bgm": 100 * sum(1 for p in good if p.has_bgm) / len(good),
            "pct_with_cta": 100 * sum(1 for p in good if p.has_cta) / len(good),
            "avg_words_per_sec": weighted_avg([(p.subtitle_words_per_sec, p.views) for p in good if p.subtitle_words_per_sec > 0]),
            "top_hooks": [p.hook_transcript for p in sorted(good, key=lambda x: x.views, reverse=True)[:5] if p.hook_transcript],
        }

        # Salvar modelo
        model_path = MODELS_BASE / f"{niche}_model.json"
        MODELS_BASE.mkdir(parents=True, exist_ok=True)
        model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2))
        log.info("EditModeler: modelo de %s salvo → %s", niche, model_path)

        return model

    def load_niche_model(self, niche: str) -> Optional[dict]:
        """Carrega modelo de edição salvo para o nicho."""
        model_path = MODELS_BASE / f"{niche}_model.json"
        if model_path.exists():
            try:
                return json.loads(model_path.read_text())
            except Exception:
                pass
        return None

    def model_to_script_guidelines(self, model: dict) -> str:
        """
        Converte modelo de nicho em diretrizes de roteiro para o NarrativeEngine.
        """
        niche = model.get("niche", "desconhecido")
        avg_dur = model.get("avg_duration_sec", 600)
        avg_scene = model.get("avg_scene_duration_sec", 6)
        cpm = model.get("avg_scenes_per_minute", 10)
        hook_dur = model.get("avg_hook_duration_sec", 25)
        speech_pct = model.get("avg_speech_pct", 80)
        has_bgm = model.get("pct_with_bgm", 80) > 50
        has_cta = model.get("pct_with_cta", 70) > 50
        wps = model.get("avg_words_per_sec", 2.5)

        top_hooks = model.get("top_hooks", [])
        hooks_text = "\n".join(f"  {i+1}. {h[:200]}" for i, h in enumerate(top_hooks[:3]))

        return f"""DIRETRIZES DE EDIÇÃO BASEADAS EM DADOS ({model.get('source_videos', 0)} vídeos virais analisados):

Nicho: {niche.upper()}
Duração ideal: {avg_dur:.0f}s ({avg_dur/60:.1f} min)
Ritmo de corte: {cpm:.1f} cortes/minuto ({avg_scene:.1f}s por cena)
Hook: primeiros {hook_dur:.0f}s precisam prender completamente
Narração: {speech_pct:.0f}% do vídeo com voz
Música de fundo: {"obrigatória" if has_bgm else "opcional"}
CTA no final: {"sim" if has_cta else "opcional"}
Velocidade de fala: {wps:.1f} palavras/segundo

EXEMPLOS DE HOOKS QUE VIRALIZARAM NESTE NICHO:
{hooks_text if hooks_text else "  (sem dados de transcrição disponíveis)"}

Use essas métricas para calibrar duração das cenas e ritmo do roteiro."""

    def run_full_pipeline(
        self,
        sources: list[dict],
        niche: str = "dark",
        top_n_per_source: int = 10,
        min_views: int = 500_000,
    ) -> dict:
        """
        Pipeline completo: baixar → analisar → construir modelo.

        Args:
            sources: lista de {url, platform?, ...} para baixar
            niche: nicho de análise
            top_n_per_source: quantos vídeos baixar por canal
            min_views: threshold mínimo de views

        Returns:
            dict com {patterns, model, guidelines}
        """
        from .media_downloader import get_downloader, DownloadConfig

        downloader = get_downloader(DownloadConfig(
            min_views=min_views,
            max_videos=top_n_per_source,
        ))

        all_videos = []
        for source in sources:
            videos = downloader.download_channel(
                channel_url=source["url"],
                niche=niche,
                top_n=top_n_per_source,
                min_views=min_views,
            )
            all_videos.extend(videos)
            log.info(
                "EditModeler: %d vídeos baixados de %s",
                len(videos), source["url"],
            )

        patterns = self.analyze_batch(all_videos, niche=niche)
        model = self.build_niche_model(patterns, niche=niche, min_views_weight=min_views)
        guidelines = self.model_to_script_guidelines(model) if model else ""

        log.info(
            "EditModeler: pipeline completo — %d padrões, modelo salvo",
            len(patterns),
        )

        return {
            "videos_downloaded": len(all_videos),
            "patterns_extracted": len(patterns),
            "model": model,
            "guidelines": guidelines,
        }


_modeler: Optional[EditModeler] = None


def get_edit_modeler() -> EditModeler:
    global _modeler
    if _modeler is None:
        _modeler = EditModeler()
    return _modeler
