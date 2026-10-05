"""Step 3 — Fetch visuals (images/video) from Pexels & Pixabay for each scene."""
import hashlib
import logging
import sys
import time
import urllib.parse
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import OUTPUT, PEXELS_API_KEY, PIXABAY_API_KEY

log = logging.getLogger(__name__)

PEXELS_VIDEO_URL   = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL   = "https://api.pexels.com/v1/search"
PIXABAY_VIDEO_URL  = "https://pixabay.com/api/videos/"
PIXABAY_PHOTO_URL  = "https://pixabay.com/api/"


# ── Pexels ─────────────────────────────────────────────────────────────────────

def _pexels_video(query: str, page: int = 1) -> str | None:
    if not PEXELS_API_KEY:
        return None
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {"query": query, "per_page": 5, "page": page, "orientation": "landscape"}
    try:
        r = requests.get(PEXELS_VIDEO_URL, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        videos = r.json().get("videos", [])
        if not videos:
            return None
        # prefer HD (1920), fall back to first available
        for v in videos:
            for file in v.get("video_files", []):
                if file.get("width", 0) >= 1280:
                    return file["link"]
        return videos[0]["video_files"][0]["link"]
    except Exception as e:
        log.warning("Pexels video error for '%s': %s", query, e)
        return None


def _pexels_photo(query: str) -> str | None:
    if not PEXELS_API_KEY:
        return None
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {"query": query, "per_page": 5, "orientation": "landscape"}
    try:
        r = requests.get(PEXELS_PHOTO_URL, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            return None
        return photos[0]["src"]["original"]
    except Exception as e:
        log.warning("Pexels photo error for '%s': %s", query, e)
        return None


# ── Pixabay ────────────────────────────────────────────────────────────────────

def _pixabay_video(query: str) -> str | None:
    if not PIXABAY_API_KEY:
        return None
    params = {
        "key": PIXABAY_API_KEY, "q": urllib.parse.quote(query),
        "video_type": "film", "per_page": 5,
    }
    try:
        r = requests.get(PIXABAY_VIDEO_URL, params=params, timeout=15)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        sizes = hits[0].get("videos", {})
        for quality in ["large", "medium", "small"]:
            url = sizes.get(quality, {}).get("url")
            if url:
                return url
    except Exception as e:
        log.warning("Pixabay video error for '%s': %s", query, e)
    return None


def _pixabay_photo(query: str) -> str | None:
    if not PIXABAY_API_KEY:
        return None
    params = {
        "key": PIXABAY_API_KEY, "q": urllib.parse.quote(query),
        "image_type": "photo", "orientation": "horizontal", "per_page": 5,
    }
    try:
        r = requests.get(PIXABAY_PHOTO_URL, params=params, timeout=15)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        return hits[0]["largeImageURL"]
    except Exception as e:
        log.warning("Pixabay photo error for '%s': %s", query, e)
    return None


# ── Pollinations fallback (free, no key) ──────────────────────────────────────

def _pollinations_image(prompt: str) -> str:
    """Generate an AI image via Pollinations.ai (completely free, no key)."""
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1920&height=1080&nologo=true"


# ── Download helper ────────────────────────────────────────────────────────────

def _download(url: str, dest: Path, retries: int = 3) -> Path | None:
    """Download URL to dest file with retry logic."""
    for attempt in range(retries):
        try:
            r = requests.get(url, stream=True, timeout=60)
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
            return dest
        except Exception as e:
            log.warning("Download attempt %d/%d failed for %s: %s", attempt + 1, retries, url, e)
            time.sleep(2 ** attempt)
    return None


# ── Main entry ─────────────────────────────────────────────────────────────────

def fetch_visual_for_scene(scene: dict, video_id: str, prefer_video: bool = True) -> Path | None:
    """
    Fetch or generate a visual asset for one scene.
    Returns local path to image/video file, or None on total failure.
    """
    query = scene.get("prompt_visual", scene.get("emocao", "dark mystery"))
    scene_id = scene["id"]
    img_dir = OUTPUT / "images" / video_id
    img_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic filename based on query hash to enable caching
    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]

    # 1. Try Pexels video
    if prefer_video:
        url = _pexels_video(query)
        if url:
            ext = ".mp4"
            dest = img_dir / f"scene_{scene_id:03d}_{query_hash}{ext}"
            if dest.exists():
                return dest
            result = _download(url, dest)
            if result:
                log.info("Scene %d: Pexels video ✓", scene_id)
                return result

    # 2. Try Pixabay video
    if prefer_video:
        url = _pixabay_video(query)
        if url:
            ext = ".mp4"
            dest = img_dir / f"scene_{scene_id:03d}_{query_hash}{ext}"
            if dest.exists():
                return dest
            result = _download(url, dest)
            if result:
                log.info("Scene %d: Pixabay video ✓", scene_id)
                return result

    # 3. Try Pexels photo
    url = _pexels_photo(query)
    if url:
        ext = ".jpg"
        dest = img_dir / f"scene_{scene_id:03d}_{query_hash}{ext}"
        if dest.exists():
            return dest
        result = _download(url, dest)
        if result:
            log.info("Scene %d: Pexels photo ✓", scene_id)
            return result

    # 4. Try Pixabay photo
    url = _pixabay_photo(query)
    if url:
        ext = ".jpg"
        dest = img_dir / f"scene_{scene_id:03d}_{query_hash}{ext}"
        if dest.exists():
            return dest
        result = _download(url, dest)
        if result:
            log.info("Scene %d: Pixabay photo ✓", scene_id)
            return result

    # 5. Pollinations AI generation fallback
    url = _pollinations_image(query)
    dest = img_dir / f"scene_{scene_id:03d}_{query_hash}_ai.jpg"
    if dest.exists():
        return dest
    result = _download(url, dest)
    if result:
        log.info("Scene %d: Pollinations AI ✓", scene_id)
        return result

    log.error("Scene %d: ALL visual sources failed for query '%s'", scene_id, query)
    return None


def fetch_all_visuals(script: dict, video_id: str, prefer_video: bool = True) -> list[Path | None]:
    """Fetch visuals for all scenes. Returns list aligned with script['cenas']."""
    visuals = []
    total = len(script["cenas"])
    for i, scene in enumerate(script["cenas"]):
        log.info("Fetching visual %d/%d: %s", i + 1, total, scene.get("prompt_visual", "")[:60])
        path = fetch_visual_for_scene(scene, video_id, prefer_video)
        visuals.append(path)
        time.sleep(0.3)  # avoid rate limiting
    return visuals


if __name__ == "__main__":
    import argparse, json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="Fetch visuals for a script")
    p.add_argument("script_json")
    p.add_argument("--video-id", default="test_video")
    p.add_argument("--photos-only", action="store_true")
    args = p.parse_args()

    script = json.loads(Path(args.script_json).read_text())
    visuals = fetch_all_visuals(script, args.video_id, prefer_video=not args.photos_only)
    found = sum(1 for v in visuals if v)
    print(f"\n✅ Fetched {found}/{len(visuals)} visuals for '{args.video_id}'")
