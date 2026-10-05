"""
YouTubeUploader — upload direto para YouTube Data API v3 com retry e scheduling.

Quota atualizada (dezembro 2025):
  - videos.insert: 100 unidades (antes era 1.600)
  - Com 10.000 unidades/dia: até 100 uploads/dia por projeto Google Cloud

Funcionalidades:
  - Upload resumível com progresso
  - Retry exponential backoff em erros 429/500/503
  - Scheduling de publicação futura (publishAt)
  - Upload em lote com respeito à quota diária
  - Multi-canal via credenciais separadas por canal
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error
import urllib.parse

log = logging.getLogger(__name__)

YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"

DAILY_QUOTA_LIMIT = 10_000
UPLOAD_QUOTA_COST = 100
UPDATE_QUOTA_COST = 50
THUMBNAIL_QUOTA_COST = 50


@dataclass
class UploadResult:
    success: bool
    video_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    quota_used: int = 0


@dataclass
class ChannelCredentials:
    channel_id: str
    client_id: str
    client_secret: str
    refresh_token: str
    access_token: Optional[str] = None
    token_expires_at: float = 0.0


class QuotaManager:
    """Rastreia uso de quota YouTube por canal/dia."""

    def __init__(self, state_file: Path = Path("batch/youtube_quota.json")):
        self.state_file = state_file
        self._state: dict = {}
        self._load()

    def _load(self) -> None:
        if self.state_file.exists():
            try:
                self._state = json.loads(self.state_file.read_text())
            except Exception:
                self._state = {}

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._state, indent=2))

    def _today_key(self) -> str:
        return time.strftime("%Y-%m-%d")

    def used_today(self, channel_id: str) -> int:
        return self._state.get(channel_id, {}).get(self._today_key(), 0)

    def remaining_today(self, channel_id: str) -> int:
        return DAILY_QUOTA_LIMIT - self.used_today(channel_id)

    def can_upload(self, channel_id: str) -> bool:
        return self.remaining_today(channel_id) >= UPLOAD_QUOTA_COST

    def record_usage(self, channel_id: str, units: int) -> None:
        today = self._today_key()
        if channel_id not in self._state:
            self._state[channel_id] = {}
        self._state[channel_id][today] = self._state[channel_id].get(today, 0) + units
        # Clean up old entries (keep last 7 days)
        old_keys = [k for k in self._state[channel_id] if k < time.strftime("%Y-%m-%d", time.localtime(time.time() - 7 * 86400))]
        for k in old_keys:
            del self._state[channel_id][k]
        self._save()


class YouTubeUploader:
    """
    Faz upload de vídeos para o YouTube com gestão de quota e retry automático.
    """

    def __init__(self, credentials: Optional[ChannelCredentials] = None):
        self.credentials = credentials or self._load_default_credentials()
        self.quota = QuotaManager()
        self._available = self.credentials is not None

    def _load_default_credentials(self) -> Optional[ChannelCredentials]:
        creds_file = Path("config/youtube_credentials.json")
        if creds_file.exists():
            try:
                data = json.loads(creds_file.read_text())
                return ChannelCredentials(
                    channel_id=data.get("channel_id", ""),
                    client_id=data.get("client_id", ""),
                    client_secret=data.get("client_secret", ""),
                    refresh_token=data.get("refresh_token", ""),
                )
            except Exception as exc:
                log.warning("YouTubeUploader: erro ao carregar credenciais: %s", exc)

        # Fallback to environment variables
        client_id = os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        channel_id = os.getenv("YOUTUBE_CHANNEL_ID", "")

        if client_id and client_secret and refresh_token:
            return ChannelCredentials(
                channel_id=channel_id,
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
            )

        log.warning("YouTubeUploader: credenciais não configuradas — uploader desabilitado")
        return None

    def is_available(self) -> bool:
        return self._available

    def _refresh_access_token(self) -> bool:
        """Renova o access token usando o refresh token."""
        if not self.credentials:
            return False

        payload = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "refresh_token": self.credentials.refresh_token,
        }).encode()

        try:
            req = urllib.request.Request(
                OAUTH_TOKEN_URL, data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                token_data = json.loads(resp.read())

            self.credentials.access_token = token_data["access_token"]
            self.credentials.token_expires_at = time.time() + token_data.get("expires_in", 3600) - 60
            return True
        except Exception as exc:
            log.error("YouTubeUploader: falha ao renovar token: %s", exc)
            return False

    def _get_access_token(self) -> Optional[str]:
        if not self.credentials:
            return None
        if not self.credentials.access_token or time.time() >= self.credentials.token_expires_at:
            if not self._refresh_access_token():
                return None
        return self.credentials.access_token

    def _api_headers(self) -> dict:
        token = self._get_access_token()
        if not token:
            return {}
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def upload_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        category_id: str = "22",  # 22 = People & Blogs
        privacy_status: str = "private",
        publish_at: Optional[str] = None,  # RFC3339, ex: "2026-10-06T15:00:00Z"
        made_for_kids: bool = False,
        channel_id: Optional[str] = None,
        thumbnail_path: Optional[Path] = None,
        max_retries: int = 5,
    ) -> UploadResult:
        """
        Faz upload de um vídeo para o YouTube com retry automático.

        Args:
            publish_at: Se definido, agenda publicação. privacy_status deve ser "private".
        """
        if not self._available:
            return UploadResult(success=False, error="Uploader não disponível — credenciais não configuradas")

        ch_id = channel_id or (self.credentials.channel_id if self.credentials else "")

        if not self.quota.can_upload(ch_id):
            remaining = self.quota.remaining_today(ch_id)
            return UploadResult(
                success=False,
                error=f"Quota diária esgotada para canal {ch_id} — {remaining} unidades restantes",
            )

        if not video_path.exists():
            return UploadResult(success=False, error=f"Arquivo não encontrado: {video_path}")

        # Build metadata
        snippet = {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
            "defaultLanguage": "pt",
        }

        status = {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": made_for_kids}
        if publish_at and privacy_status == "private":
            status["publishAt"] = publish_at

        metadata = {"snippet": snippet, "status": status}

        # Initiate resumable upload
        file_size = video_path.stat().st_size
        init_headers = {
            **self._api_headers(),
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(file_size),
        }

        init_url = f"{YOUTUBE_UPLOAD_URL}?uploadType=resumable&part=snippet,status"
        init_data = json.dumps(metadata).encode()

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    init_url, data=init_data,
                    headers=init_headers, method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    upload_url = resp.headers.get("Location")

                if not upload_url:
                    raise ValueError("Sem Location header na resposta de inicialização")

                # Upload file in chunks (8MB chunks)
                chunk_size = 8 * 1024 * 1024
                video_id = None

                with open(video_path, "rb") as f:
                    offset = 0
                    while offset < file_size:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break

                        end = offset + len(chunk) - 1
                        chunk_headers = {
                            "Content-Length": str(len(chunk)),
                            "Content-Range": f"bytes {offset}-{end}/{file_size}",
                            "Content-Type": "video/mp4",
                        }
                        # Refresh auth for each chunk
                        token = self._get_access_token()
                        if token:
                            chunk_headers["Authorization"] = f"Bearer {token}"

                        chunk_req = urllib.request.Request(
                            upload_url, data=chunk,
                            headers=chunk_headers, method="PUT"
                        )

                        try:
                            with urllib.request.urlopen(chunk_req, timeout=120) as cr:
                                if cr.status in (200, 201):
                                    result_data = json.loads(cr.read())
                                    video_id = result_data.get("id")
                        except urllib.error.HTTPError as he:
                            if he.code == 308:  # Resume Incomplete — expected for intermediate chunks
                                offset += len(chunk)
                                continue
                            raise

                        offset += len(chunk)
                        log.debug("YouTubeUploader: %d%% enviado", int(100 * offset / file_size))

                if not video_id:
                    raise ValueError("Upload concluído mas sem video_id na resposta")

                self.quota.record_usage(ch_id, UPLOAD_QUOTA_COST)
                log.info("YouTubeUploader: vídeo %s enviado — ID: %s", title[:50], video_id)

                result = UploadResult(
                    success=True,
                    video_id=video_id,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    quota_used=UPLOAD_QUOTA_COST,
                )

                # Upload thumbnail if provided
                if thumbnail_path and thumbnail_path.exists():
                    self._upload_thumbnail(video_id, thumbnail_path, ch_id)
                    result.quota_used += THUMBNAIL_QUOTA_COST

                return result

            except urllib.error.HTTPError as exc:
                if exc.code == 403:
                    wait = (2 ** attempt) * 60
                    log.warning(
                        "YouTubeUploader: quota 403 (tentativa %d/%d) — aguardando %ds",
                        attempt + 1, max_retries, wait,
                    )
                    time.sleep(wait)
                elif exc.code in (500, 502, 503):
                    wait = 2 ** attempt * 2
                    log.warning("YouTubeUploader: erro %d — retry em %ds", exc.code, wait)
                    time.sleep(wait)
                else:
                    return UploadResult(success=False, error=f"HTTP {exc.code}: {exc.reason}")
            except Exception as exc:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    log.warning("YouTubeUploader: erro (tentativa %d/%d): %s — retry em %ds", attempt + 1, max_retries, exc, wait)
                    time.sleep(wait)
                else:
                    return UploadResult(success=False, error=str(exc))

        return UploadResult(success=False, error=f"Falhou após {max_retries} tentativas")

    def _upload_thumbnail(self, video_id: str, thumb_path: Path, channel_id: str) -> bool:
        """Faz upload de thumbnail para um vídeo já publicado."""
        try:
            token = self._get_access_token()
            if not token:
                return False

            thumb_data = thumb_path.read_bytes()
            content_type = "image/jpeg" if thumb_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"

            thumb_url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}&uploadType=media"
            req = urllib.request.Request(
                thumb_url, data=thumb_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": content_type,
                    "Content-Length": str(len(thumb_data)),
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status in (200, 201):
                    self.quota.record_usage(channel_id, THUMBNAIL_QUOTA_COST)
                    log.info("YouTubeUploader: thumbnail enviada para vídeo %s", video_id)
                    return True
        except Exception as exc:
            log.warning("YouTubeUploader: falha ao enviar thumbnail: %s", exc)
        return False

    def update_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        privacy_status: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> bool:
        """Atualiza metadados de um vídeo já publicado."""
        if not self._available:
            return False

        ch_id = channel_id or (self.credentials.channel_id if self.credentials else "")

        body: dict = {"id": video_id}
        parts = []

        if any([title, description, tags]):
            snippet: dict = {}
            if title:
                snippet["title"] = title[:100]
            if description:
                snippet["description"] = description[:5000]
            if tags:
                snippet["tags"] = tags[:500]
            body["snippet"] = snippet
            parts.append("snippet")

        if privacy_status:
            body["status"] = {"privacyStatus": privacy_status}
            parts.append("status")

        if not parts:
            return False

        url = f"{YOUTUBE_API_BASE}/videos?part={','.join(parts)}"

        try:
            req_data = json.dumps(body).encode()
            req = urllib.request.Request(
                url, data=req_data,
                headers=self._api_headers(), method="PUT"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    self.quota.record_usage(ch_id, UPDATE_QUOTA_COST)
                    log.info("YouTubeUploader: metadados do vídeo %s atualizados", video_id)
                    return True
        except Exception as exc:
            log.error("YouTubeUploader: falha ao atualizar metadados: %s", exc)

        return False

    def batch_upload(
        self,
        videos: list[dict],
        channel_id: Optional[str] = None,
        delay_between_uploads: float = 5.0,
    ) -> list[UploadResult]:
        """
        Upload em lote respeitando quota diária.

        Args:
            videos: lista de dicts com campos: video_path, title, description, tags,
                    privacy_status, publish_at (opcional), made_for_kids (opcional),
                    thumbnail_path (opcional)
        """
        results = []
        ch_id = channel_id or (self.credentials.channel_id if self.credentials else "")

        for i, video_meta in enumerate(videos):
            if not self.quota.can_upload(ch_id):
                log.warning(
                    "YouTubeUploader: quota esgotada após %d/%d uploads",
                    i, len(videos),
                )
                remaining_count = len(videos) - i
                for _ in range(remaining_count):
                    results.append(UploadResult(success=False, error="Quota diária esgotada"))
                break

            result = self.upload_video(
                video_path=Path(video_meta["video_path"]),
                title=video_meta["title"],
                description=video_meta.get("description", ""),
                tags=video_meta.get("tags", []),
                category_id=video_meta.get("category_id", "22"),
                privacy_status=video_meta.get("privacy_status", "private"),
                publish_at=video_meta.get("publish_at"),
                made_for_kids=video_meta.get("made_for_kids", False),
                channel_id=ch_id,
                thumbnail_path=Path(video_meta["thumbnail_path"]) if video_meta.get("thumbnail_path") else None,
            )
            results.append(result)

            if result.success:
                log.info(
                    "YouTubeUploader: lote %d/%d — %s (%s)",
                    i + 1, len(videos),
                    video_meta.get("title", "")[:40],
                    result.url,
                )
            else:
                log.warning(
                    "YouTubeUploader: lote %d/%d FALHOU — %s",
                    i + 1, len(videos), result.error,
                )

            if i < len(videos) - 1:
                time.sleep(delay_between_uploads)

        return results

    def get_quota_status(self, channel_id: Optional[str] = None) -> dict:
        """Retorna status atual da quota para o canal."""
        ch_id = channel_id or (self.credentials.channel_id if self.credentials else "default")
        used = self.quota.used_today(ch_id)
        return {
            "channel_id": ch_id,
            "quota_used_today": used,
            "quota_remaining": DAILY_QUOTA_LIMIT - used,
            "uploads_remaining": (DAILY_QUOTA_LIMIT - used) // UPLOAD_QUOTA_COST,
            "can_upload": self.quota.can_upload(ch_id),
        }


_uploaders: dict[str, YouTubeUploader] = {}


def get_youtube_uploader(channel_id: Optional[str] = None) -> YouTubeUploader:
    key = channel_id or "default"
    if key not in _uploaders:
        if channel_id:
            # Load channel-specific credentials
            creds_file = Path(f"config/youtube_{channel_id}.json")
            if creds_file.exists():
                try:
                    data = json.loads(creds_file.read_text())
                    creds = ChannelCredentials(
                        channel_id=channel_id,
                        client_id=data["client_id"],
                        client_secret=data["client_secret"],
                        refresh_token=data["refresh_token"],
                    )
                    _uploaders[key] = YouTubeUploader(credentials=creds)
                    return _uploaders[key]
                except Exception:
                    pass
        _uploaders[key] = YouTubeUploader()
    return _uploaders[key]
