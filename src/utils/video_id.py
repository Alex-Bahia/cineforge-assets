"""Generate deterministic video IDs for filenames."""
import hashlib
import re
import time


def make_video_id(topic: str) -> str:
    """
    Create a filesystem-safe video ID from topic + timestamp.
    e.g. "assassino_serial_a1b2c3d4"
    """
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower())[:30].strip("_")
    ts   = hashlib.md5(f"{topic}{time.time()}".encode()).hexdigest()[:8]
    return f"{slug}_{ts}"
