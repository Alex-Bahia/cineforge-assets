"""Step 5 — Upload or schedule video to YouTube via YouTube Data API v3."""
import json
import logging
import sys
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import (
    YT_TOKEN_FILE, YT_SCOPES, YT_CATEGORY_ID, YT_PRIVACY, YT_MADE_FOR_KIDS,
    OUTPUT,
)

log = logging.getLogger(__name__)


def _get_credentials(client_secrets_file: str = "config/client_secrets.json") -> Credentials:
    """OAuth 2.0 flow — opens browser on first run, caches token for subsequent runs."""
    creds = None

    if YT_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(YT_TOKEN_FILE), YT_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, YT_SCOPES)
            creds = flow.run_local_server(port=0)
        YT_TOKEN_FILE.write_text(creds.to_json())
        log.info("YouTube credentials saved to %s", YT_TOKEN_FILE)

    return creds


def _build_service(client_secrets_file: str = "config/client_secrets.json"):
    creds = _get_credentials(client_secrets_file)
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_path: Path | None = None,
    privacy: str = YT_PRIVACY,
    publish_at: str | None = None,        # ISO 8601 e.g. "2024-12-25T09:00:00Z"
    client_secrets_file: str = "config/client_secrets.json",
    category_id: str = YT_CATEGORY_ID,
    language: str = "",                   # e.g. "pt", "en", "fr", "de", "es", "it"
    made_for_kids: bool = None,           # overrides YT_MADE_FOR_KIDS when set
) -> str:
    """
    Upload video to YouTube. Returns the YouTube video ID.
    If publish_at is set, the video is scheduled (privacy forced to 'private').
    """
    youtube = _build_service(client_secrets_file)

    # If scheduled, must be private
    if publish_at:
        privacy = "private"

    # Auto-detect language code from full locale
    lang_code = language.split("-")[0] if language else "pt"

    _made_for_kids = made_for_kids if made_for_kids is not None else YT_MADE_FOR_KIDS

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
            "defaultLanguage": lang_code,
            "defaultAudioLanguage": lang_code,
        },
        "status": {
            "privacyStatus": privacy,
            "madeForKids": _made_for_kids,
            "selfDeclaredMadeForKids": _made_for_kids,
        },
    }

    if publish_at:
        body["status"]["publishAt"] = publish_at

    media = MediaFileUpload(str(video_path), chunksize=10 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    log.info("Uploading '%s' to YouTube...", title)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            log.info("Upload progress: %d%%", pct)

    video_id = response["id"]
    log.info("✅ Uploaded! Video ID: %s", video_id)

    # Set thumbnail if provided
    if thumbnail_path and thumbnail_path.exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path)),
            ).execute()
            log.info("Thumbnail set for %s", video_id)
        except Exception as e:
            log.warning("Thumbnail upload failed: %s", e)

    return video_id


def schedule_video(
    video_path: Path,
    script: dict,
    publish_at: str,
    thumbnail_path: Path | None = None,
    client_secrets_file: str = "config/client_secrets.json",
) -> str:
    """Convenience wrapper: upload + schedule from script metadata."""
    return upload_video(
        video_path=video_path,
        title=script["titulo"],
        description=script["descricao"],
        tags=script.get("tags", []),
        thumbnail_path=thumbnail_path,
        privacy="private",
        publish_at=publish_at,
        client_secrets_file=client_secrets_file,
    )


def get_channel_stats(client_secrets_file: str = "config/client_secrets.json") -> dict:
    """Return basic channel stats for monitoring."""
    youtube = _build_service(client_secrets_file)
    response = youtube.channels().list(part="statistics,snippet", mine=True).execute()
    items = response.get("items", [])
    if not items:
        return {}
    ch = items[0]
    return {
        "channel_id": ch["id"],
        "title": ch["snippet"]["title"],
        "subscribers": ch["statistics"].get("subscriberCount", "hidden"),
        "views": ch["statistics"].get("viewCount", 0),
        "video_count": ch["statistics"].get("videoCount", 0),
    }


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="Upload video to YouTube")
    p.add_argument("video_id",      help="Video ID (used to find MP4 in output/videos/)")
    p.add_argument("script_json",   help="Path to script JSON for metadata")
    p.add_argument("--publish-at",  help='ISO 8601 schedule e.g. "2024-12-31T18:00:00Z"')
    p.add_argument("--privacy",     default=YT_PRIVACY)
    p.add_argument("--secrets",     default="config/client_secrets.json")
    args = p.parse_args()

    script = json.loads(Path(args.script_json).read_text())
    video_path = OUTPUT / "videos" / f"{args.video_id}.mp4"
    thumb_path = OUTPUT / "thumbnails" / f"{args.video_id}.jpg"

    yt_id = upload_video(
        video_path=video_path,
        title=script["titulo"],
        description=script["descricao"],
        tags=script.get("tags", []),
        thumbnail_path=thumb_path if thumb_path.exists() else None,
        privacy=args.privacy,
        publish_at=args.publish_at,
        client_secrets_file=args.secrets,
    )
    print(f"\n✅ YouTube video ID: {yt_id}")
    print(f"   https://www.youtube.com/watch?v={yt_id}")
