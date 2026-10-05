"""Central configuration — copy .env.example to .env and fill in your keys."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Project Paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
ASSETS      = ROOT / "assets"
CANAL_DIR   = ROOT / "Canal Dark Automação"
MUSIC_DIR   = CANAL_DIR / "Canais Dark Youtube Music"
BATCH = ROOT / "batch"
LOGS = ROOT / "logs"

for d in [OUTPUT/"videos", OUTPUT/"audio", OUTPUT/"images",
          OUTPUT/"subtitles", OUTPUT/"thumbnails",
          ASSETS/"music", ASSETS/"fonts", ASSETS/"overlays",
          LOGS, BATCH]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY", "")
PEXELS_API_KEY        = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY       = os.getenv("PIXABAY_API_KEY", "")
GOOGLE_CLOUD_PROJECT  = os.getenv("GOOGLE_CLOUD_PROJECT", "")     # Veo3 via Vertex AI
ELEVENLABS_API_KEY    = os.getenv("ELEVENLABS_API_KEY", "")        # premium TTS
VEO3_TIER             = os.getenv("VEO3_TIER", "lite")             # lite|fast|standard
TTS_TIER              = os.getenv("TTS_TIER", "free")              # free|premium
YOUTUBE_CLIENT_ID     = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
GOOGLE_SHEETS_CREDS   = os.getenv("GOOGLE_SHEETS_CREDS_JSON", "")  # path to JSON

# ── Narration / Voice ──────────────────────────────────────────────────────────
TTS_VOICE     = os.getenv("TTS_VOICE", "pt-BR-AntonioNeural")   # masculine, dark
TTS_VOICE_ALT = "pt-BR-FranciscaNeural"                          # feminine option
TTS_RATE      = os.getenv("TTS_RATE", "-5%")                     # slower = more suspense
TTS_PITCH     = os.getenv("TTS_PITCH", "-10Hz")                  # deeper voice

# ── Video Rendering ────────────────────────────────────────────────────────────
VIDEO_WIDTH      = 1920
VIDEO_HEIGHT     = 1080
VIDEO_FPS        = 30
VIDEO_BITRATE    = "5000k"
AUDIO_BITRATE    = "192k"
SCENE_DURATION   = float(os.getenv("SCENE_DURATION", "5"))       # seconds per scene
SILENCE_THRESHOLD = -40                                            # dBFS for silence cut
BACKGROUND_MUSIC_VOLUME = 0.08                                    # 8% = subtle

# ── Subtitle Style ─────────────────────────────────────────────────────────────
SUBTITLE_FONT       = str(ASSETS / "fonts" / "Anton.ttf")        # download separately
SUBTITLE_FONTSIZE   = 72
SUBTITLE_COLOR      = "white"
SUBTITLE_STROKE_COLOR = "black"
SUBTITLE_STROKE_WIDTH = 3
SUBTITLE_POSITION   = ("center", 0.75)                            # 75% from top

# ── Gemini Model ───────────────────────────────────────────────────────────────
GEMINI_MODEL       = "gemini-2.0-flash-exp"
GEMINI_MAX_TOKENS  = 8192
GEMINI_TEMPERATURE = 0.9

# ── YouTube Upload ─────────────────────────────────────────────────────────────
YT_TOKEN_FILE   = ROOT / "config" / "youtube_token.json"
YT_SCOPES       = ["https://www.googleapis.com/auth/youtube.upload",
                   "https://www.googleapis.com/auth/youtube"]
YT_CATEGORY_ID  = "27"   # Education  (22=People, 24=Entertainment, 27=Education)
YT_PRIVACY      = os.getenv("YT_PRIVACY", "private")             # private → review before public
YT_MADE_FOR_KIDS = False

# ── Batch Control ──────────────────────────────────────────────────────────────
BATCH_CSV        = BATCH / "topics.csv"
MAX_PARALLEL     = int(os.getenv("MAX_PARALLEL", "2"))            # concurrent renders
SCHEDULE_HOUR    = int(os.getenv("SCHEDULE_HOUR", "6"))           # 06:00 daily run
