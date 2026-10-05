"""
MediaDownloader — Turbo Downloader de vídeos virais para modelagem de edição.

Suporta:
  - YouTube: canal completo, playlist, vídeo único
  - Instagram: perfil público, reels, posts com vídeo
  - TikTok: perfil, hashtag, vídeo único

Filtros automáticos:
  - Threshold de visualizações mínimas
  - Duração mínima/máxima
  - Data de publicação (recentes ou evergreen)
  - Top-N por visualizações

Uso:
  downloader = MediaDownloader()
  results = downloader.download_channel(
      "https://www.youtube.com/@MrBeast",
      min_views=1_000_000,
      top_n=20,
      niche="kids",
  )
"""
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import re

log = logging.getLogger(__name__)

DOWNLOAD_BASE = Path("batch/viral_reference")
METADATA_BASE = Path("batch/viral_metadata")


@dataclass
class DownloadConfig:
    min_views: int = 500_000
    max_videos: int = 30
    min_duration_sec: int = 30
    max_duration_sec: int = 1200
    video_quality: str = "720p"        # 360p | 480p | 720p | 1080p (menor = mais rápido)
    download_audio: bool = True
    download_subtitles: bool = True    # para análise de script/hook
    max_concurrent: int = 4
    rate_limit: str = "2M"             # bandwidth cap por download
    cookies_from_browser: Optional[str] = None   # "chrome" | "firefox" para conteúdo com login


@dataclass
class VideoMeta:
    id: str
    title: str
    url: str
    platform: str
    channel: str
    views: int
    likes: int = 0
    duration_sec: int = 0
    upload_date: str = ""
    description: str = ""
    tags: list = field(default_factory=list)
    local_path: Optional[str] = None
    audio_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    niche: str = "unknown"
    downloaded_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


class MediaDownloader:
    """
    Turbo downloader de vídeos virais usando yt-dlp como motor.
    Suporta YouTube, Instagram e TikTok com filtros de qualidade/views.
    """

    def __init__(self, config: Optional[DownloadConfig] = None):
        self.config = config or DownloadConfig()
        self._check_ytdlp()

    def _check_ytdlp(self) -> None:
        try:
            import yt_dlp  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "yt-dlp não instalado. Execute: pip install yt-dlp"
            )

    def _build_ydl_opts(
        self,
        output_dir: Path,
        quality: Optional[str] = None,
        audio_only: bool = False,
        subtitles: bool = True,
        max_downloads: Optional[int] = None,
        date_after: Optional[str] = None,
    ) -> dict:
        """Constrói opções do yt-dlp baseado na configuração."""
        q = quality or self.config.video_quality

        if audio_only:
            format_spec = "bestaudio/best"
        elif q == "360p":
            format_spec = "bestvideo[height<=360]+bestaudio/best[height<=360]"
        elif q == "480p":
            format_spec = "bestvideo[height<=480]+bestaudio/best[height<=480]"
        elif q == "1080p":
            format_spec = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        else:  # 720p padrão
            format_spec = "bestvideo[height<=720]+bestaudio/best[height<=720]"

        output_dir.mkdir(parents=True, exist_ok=True)
        outtmpl = str(output_dir / "%(id)s_%(title).60s.%(ext)s")
        # Sanitize filename
        outtmpl = outtmpl.replace(":", "_")

        opts = {
            "format": format_spec,
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "writeinfojson": True,
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": False,
            "ratelimit": self._parse_rate(self.config.rate_limit),
            "concurrent_fragment_downloads": self.config.max_concurrent,
            "retries": 5,
            "fragment_retries": 5,
            "ignoreerrors": True,
            "nooverwrites": True,
            "match_filter": self._build_match_filter(),
        }

        if subtitles and self.config.download_subtitles:
            opts.update({
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["pt", "pt-BR", "en"],
                "subtitlesformat": "srt",
            })

        if max_downloads:
            opts["max_downloads"] = max_downloads

        if date_after:
            opts["dateafter"] = date_after

        if self.config.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.config.cookies_from_browser,)

        return opts

    def _parse_rate(self, rate_str: str) -> Optional[int]:
        """Converte '2M' → 2_000_000 bytes/s."""
        match = re.match(r"^(\d+(?:\.\d+)?)([KMG]?)$", rate_str.upper())
        if not match:
            return None
        val = float(match.group(1))
        unit = match.group(2)
        multipliers = {"K": 1000, "M": 1_000_000, "G": 1_000_000_000, "": 1}
        return int(val * multipliers[unit])

    def _build_match_filter(self):
        """Cria filtro yt-dlp para excluir vídeos fora dos critérios."""
        min_views = self.config.min_views
        min_dur = self.config.min_duration_sec
        max_dur = self.config.max_duration_sec

        def match_filter(info, *, incomplete):
            views = info.get("view_count") or 0
            duration = info.get("duration") or 0

            if views and views < min_views:
                return f"Ignorado: {views:,} views < mínimo {min_views:,}"
            if duration and duration < min_dur:
                return f"Ignorado: {duration}s < mínimo {min_dur}s"
            if duration and duration > max_dur:
                return f"Ignorado: {duration}s > máximo {max_dur}s"
            return None

        return match_filter

    def _extract_metadata_from_info(self, info: dict, platform: str, niche: str) -> VideoMeta:
        """Converte dict de info do yt-dlp em VideoMeta."""
        return VideoMeta(
            id=info.get("id", ""),
            title=info.get("title", ""),
            url=info.get("webpage_url", info.get("original_url", "")),
            platform=platform,
            channel=info.get("uploader", info.get("channel", "")),
            views=info.get("view_count", 0) or 0,
            likes=info.get("like_count", 0) or 0,
            duration_sec=info.get("duration", 0) or 0,
            upload_date=info.get("upload_date", ""),
            description=(info.get("description", "") or "")[:2000],
            tags=info.get("tags", []) or [],
            niche=niche,
        )

    def _save_metadata_index(self, results: list[VideoMeta], niche: str, source: str) -> Path:
        """Salva índice de metadados em JSON."""
        METADATA_BASE.mkdir(parents=True, exist_ok=True)
        safe_source = re.sub(r"[^\w]", "_", source)[:50]
        out_path = METADATA_BASE / f"{niche}_{safe_source}_{int(time.time())}.json"
        index = {
            "source": source,
            "niche": niche,
            "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total": len(results),
            "videos": [v.to_dict() for v in results],
        }
        out_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))
        log.info("MediaDownloader: índice salvo → %s", out_path)
        return out_path

    def _detect_platform(self, url: str) -> str:
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        if "instagram.com" in url:
            return "instagram"
        if "tiktok.com" in url:
            return "tiktok"
        return "unknown"

    def download_channel(
        self,
        channel_url: str,
        niche: str = "dark",
        top_n: Optional[int] = None,
        min_views: Optional[int] = None,
        date_after: Optional[str] = None,   # formato YYYYMMDD
        audio_only: bool = False,
    ) -> list[VideoMeta]:
        """
        Baixa vídeos de um canal/perfil inteiro.

        Args:
            channel_url: URL do canal (@usuario, /channel/ID, perfil IG, etc.)
            niche: nicho para indexação
            top_n: baixar apenas os top-N por views (None = todos que passam no filtro)
            date_after: baixar apenas vídeos após esta data (YYYYMMDD)
        """
        import yt_dlp

        platform = self._detect_platform(channel_url)
        max_dl = top_n or self.config.max_videos
        if min_views:
            old_cfg = self.config.min_views
            self.config.min_views = min_views

        output_dir = DOWNLOAD_BASE / niche / re.sub(r"[^\w]", "_", channel_url.split("/")[-1])[:40]

        log.info(
            "MediaDownloader: baixando %s — %s (top %d, min %s views)",
            platform, channel_url, max_dl, f"{(min_views or self.config.min_views):,}",
        )

        opts = self._build_ydl_opts(
            output_dir=output_dir,
            audio_only=audio_only,
            max_downloads=max_dl,
            date_after=date_after,
        )
        opts["playlistend"] = max_dl

        results: list[VideoMeta] = []

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # First pass: extract info without downloading to sort by views
                info_opts = {**opts, "extract_flat": "in_playlist", "quiet": True}
                with yt_dlp.YoutubeDL(info_opts) as ydl_info:
                    try:
                        info = ydl_info.extract_info(channel_url, download=False)
                    except Exception as e:
                        log.warning("MediaDownloader: extração de info falhou: %s", e)
                        info = None

                if info and "entries" in info:
                    entries = [e for e in (info.get("entries") or []) if e]
                    # Sort by view_count descending (para pegar os mais virais)
                    entries.sort(key=lambda e: e.get("view_count") or 0, reverse=True)
                    entries = entries[:max_dl]
                    log.info(
                        "MediaDownloader: %d vídeos encontrados, baixando top %d",
                        len(info.get("entries", [])), len(entries),
                    )

                    for entry in entries:
                        entry_url = entry.get("url") or entry.get("webpage_url", "")
                        if not entry_url:
                            continue

                        try:
                            with yt_dlp.YoutubeDL(opts) as ydl_single:
                                entry_info = ydl_single.extract_info(entry_url, download=True)
                            if entry_info:
                                meta = self._extract_metadata_from_info(entry_info, platform, niche)
                                meta.local_path = self._find_downloaded_file(output_dir, entry_info.get("id", ""))
                                results.append(meta)
                                log.info(
                                    "MediaDownloader: ✓ %s (%s views)",
                                    meta.title[:50], f"{meta.views:,}",
                                )
                        except Exception as exc:
                            log.warning("MediaDownloader: falha no vídeo %s: %s", entry_url[-30:], exc)
                else:
                    # Fallback: download direto da URL (sem playlist)
                    try:
                        info = ydl.extract_info(channel_url, download=True)
                        if info:
                            meta = self._extract_metadata_from_info(info, platform, niche)
                            meta.local_path = self._find_downloaded_file(output_dir, info.get("id", ""))
                            results.append(meta)
                    except Exception as exc:
                        log.error("MediaDownloader: download direto falhou: %s", exc)

        except Exception as exc:
            log.error("MediaDownloader: erro geral: %s", exc)

        if min_views:
            self.config.min_views = old_cfg

        if results:
            self._save_metadata_index(results, niche, channel_url)

        log.info(
            "MediaDownloader: concluído — %d/%d vídeos baixados de %s",
            len(results), max_dl, channel_url,
        )
        return results

    def download_video(
        self,
        url: str,
        niche: str = "dark",
        audio_only: bool = False,
    ) -> Optional[VideoMeta]:
        """Baixa um único vídeo por URL."""
        import yt_dlp

        platform = self._detect_platform(url)
        output_dir = DOWNLOAD_BASE / niche / "single"

        # Para vídeo único, desabilitar filtro de views
        opts = self._build_ydl_opts(output_dir=output_dir, audio_only=audio_only)
        opts.pop("match_filter", None)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    meta = self._extract_metadata_from_info(info, platform, niche)
                    meta.local_path = self._find_downloaded_file(output_dir, info.get("id", ""))
                    log.info("MediaDownloader: vídeo único baixado → %s", meta.title[:60])
                    return meta
        except Exception as exc:
            log.error("MediaDownloader: erro ao baixar vídeo %s: %s", url, exc)
        return None

    def download_multiple_channels(
        self,
        sources: list[dict],
    ) -> dict[str, list[VideoMeta]]:
        """
        Baixa de múltiplos canais/perfis em lote.

        Args:
            sources: lista de dicts com {url, niche, top_n?, min_views?, date_after?}

        Returns:
            dict {url: [VideoMeta, ...]}
        """
        results = {}
        for source in sources:
            url = source["url"]
            niche = source.get("niche", "dark")
            log.info("MediaDownloader: processando %s (%s)", url, niche)
            try:
                videos = self.download_channel(
                    channel_url=url,
                    niche=niche,
                    top_n=source.get("top_n"),
                    min_views=source.get("min_views"),
                    date_after=source.get("date_after"),
                )
                results[url] = videos
            except Exception as exc:
                log.error("MediaDownloader: falha em %s: %s", url, exc)
                results[url] = []
        return results

    def extract_metadata_only(
        self,
        url: str,
        niche: str = "dark",
        max_videos: int = 100,
    ) -> list[VideoMeta]:
        """
        Extrai APENAS metadados (sem baixar vídeos).
        Útil para analisar catálogo antes de decidir o que baixar.
        """
        import yt_dlp

        platform = self._detect_platform(url)
        opts = {
            "extract_flat": "in_playlist",
            "quiet": True,
            "ignoreerrors": True,
            "playlistend": max_videos,
        }

        if self.config.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.config.cookies_from_browser,)

        results: list[VideoMeta] = []
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return []

                entries = info.get("entries") or ([info] if info.get("id") else [])
                for entry in entries:
                    if not entry:
                        continue
                    meta = self._extract_metadata_from_info(entry, platform, niche)
                    results.append(meta)

            results.sort(key=lambda m: m.views, reverse=True)
            log.info(
                "MediaDownloader: extraídos metadados de %d vídeos de %s",
                len(results), url,
            )
        except Exception as exc:
            log.error("MediaDownloader: erro na extração de metadados: %s", exc)

        return results

    def _find_downloaded_file(self, output_dir: Path, video_id: str) -> Optional[str]:
        """Localiza o arquivo baixado pelo ID do vídeo."""
        if not output_dir.exists():
            return None
        for f in output_dir.glob(f"{video_id}*.mp4"):
            return str(f)
        for f in output_dir.glob(f"{video_id}*"):
            if f.suffix in (".mp4", ".mkv", ".webm", ".mov"):
                return str(f)
        return None

    def list_downloaded(self, niche: Optional[str] = None) -> list[VideoMeta]:
        """Lista todos os vídeos baixados, opcionalmente filtrados por nicho."""
        results: list[VideoMeta] = []
        search_dir = DOWNLOAD_BASE / niche if niche else DOWNLOAD_BASE
        if not search_dir.exists():
            return []

        for json_file in search_dir.rglob("*.info.json"):
            try:
                info = json.loads(json_file.read_text())
                detected_niche = json_file.parts[-3] if len(json_file.parts) >= 3 else "unknown"
                platform = self._detect_platform(info.get("webpage_url", ""))
                meta = self._extract_metadata_from_info(info, platform, detected_niche)
                # Find associated video file
                video_id = info.get("id", "")
                meta.local_path = self._find_downloaded_file(json_file.parent, video_id)
                results.append(meta)
            except Exception:
                pass

        results.sort(key=lambda m: m.views, reverse=True)
        return results


_downloader: Optional[MediaDownloader] = None


def get_downloader(config: Optional[DownloadConfig] = None) -> MediaDownloader:
    global _downloader
    if _downloader is None or config is not None:
        _downloader = MediaDownloader(config=config)
    return _downloader
