#!/usr/bin/env bash
# ── CineForge Setup Script ────────────────────────────────────────────────────
# Run once: bash setup.sh
set -e

echo "╔══════════════════════════════════════════╗"
echo "║   CineForge Dark Channel Setup           ║"
echo "╚══════════════════════════════════════════╝"

# Python 3.10+ required
python3 --version || { echo "Python 3.10+ required"; exit 1; }

# Virtual environment
if [ ! -d ".venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# Dependencies
echo "→ Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# FFmpeg check
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠  FFmpeg not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y ffmpeg
    elif command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "   Please install FFmpeg manually: https://ffmpeg.org/download.html"
    fi
else
    echo "✓ FFmpeg found: $(ffmpeg -version 2>&1 | head -1)"
fi

# Font download (Anton Bold — great for thumbnails)
FONT_DIR="assets/fonts"
mkdir -p "$FONT_DIR"
if [ ! -f "$FONT_DIR/Anton.ttf" ]; then
    echo "→ Downloading Anton font..."
    curl -sL "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf" \
         -o "$FONT_DIR/Anton.ttf" && echo "✓ Anton.ttf downloaded" || echo "⚠  Font download failed (optional)"
fi

# .env setup
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠  .env created from template. Fill in your API keys:"
    echo "   → GEMINI_API_KEY    : https://aistudio.google.com/app/apikey"
    echo "   → PEXELS_API_KEY    : https://www.pexels.com/api/"
    echo "   → PIXABAY_API_KEY   : https://pixabay.com/api/docs/"
    echo "   → YouTube OAuth     : https://console.cloud.google.com/"
else
    echo "✓ .env already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys"
echo "  2. Add music files to 'Canal Dark Automação/Canais Dark Youtube Music/' (MP3/WAV from YouTube Audio Library)"
echo "  3. Run a test video:"
echo "     source .venv/bin/activate"
echo '     python run_pipeline.py "O assassino serial mais misterioso do Brasil"'
echo ""
echo "  To run the full batch:"
echo "     python run_pipeline.py --batch"
echo ""
echo "  To run daily at 06:00 (keeps running in background):"
echo "     nohup python run_pipeline.py --schedule &"
