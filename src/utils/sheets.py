"""Read topic queue from Google Sheets or local CSV."""
import csv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import BATCH_CSV, GOOGLE_SHEETS_CREDS

log = logging.getLogger(__name__)

# Expected CSV / Sheets columns
COL_TOPIC   = "topic"
COL_TONE    = "tone"
COL_MINUTES = "minutes"
COL_STATUS  = "status"          # blank | processing | done | error
COL_YT_ID   = "youtube_id"


def _default_row(topic: str) -> dict:
    return {
        COL_TOPIC:   topic,
        COL_TONE:    "suspense e mistério",
        COL_MINUTES: "8",
        COL_STATUS:  "",
        COL_YT_ID:   "",
    }


# ── Local CSV ──────────────────────────────────────────────────────────────────

def read_csv_topics(csv_path: Path = BATCH_CSV) -> list[dict]:
    """Read all pending topics from topics.csv."""
    if not csv_path.exists():
        _create_sample_csv(csv_path)
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get(COL_STATUS, "").strip().lower() not in {"done", "processing"}:
                rows.append(dict(row))
    return rows


def mark_csv_status(csv_path: Path, topic: str, status: str, yt_id: str = "") -> None:
    """Update status for a topic row in CSV."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row[COL_TOPIC] == topic:
                row[COL_STATUS] = status
                if yt_id:
                    row[COL_YT_ID] = yt_id
            rows.append(row)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _create_sample_csv(csv_path: Path) -> None:
    """Create a sample topics.csv if none exists."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"topic": "O assassino serial mais perturbador da história do Brasil",
         "tone": "suspense e terror", "minutes": "8", "status": "", "youtube_id": ""},
        {"topic": "Experimentos científicos proibidos que aconteceram de verdade",
         "tone": "investigativo e chocante", "minutes": "10", "status": "", "youtube_id": ""},
        {"topic": "Os crimes mais bizarros nunca explicados pela ciência",
         "tone": "mistério e curiosidade", "minutes": "9", "status": "", "youtube_id": ""},
        {"topic": "Lugares malditos que as pessoas desaparecem e nunca voltam",
         "tone": "terror e suspense", "minutes": "8", "status": "", "youtube_id": ""},
        {"topic": "A verdade sombria por trás das lendas urbanas brasileiras",
         "tone": "revelação e choque", "minutes": "10", "status": "", "youtube_id": ""},
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    log.info("Created sample topics.csv at %s", csv_path)


# ── Google Sheets ──────────────────────────────────────────────────────────────

def read_sheets_topics(sheet_id: str, worksheet: str = "Sheet1") -> list[dict]:
    """Read pending topics from Google Sheets."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds  = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDS, scopes=scopes)
        gc     = gspread.authorize(creds)
        ws     = gc.open_by_key(sheet_id).worksheet(worksheet)
        rows   = ws.get_all_records()
        return [r for r in rows if r.get(COL_STATUS, "").strip().lower() not in {"done", "processing"}]
    except Exception as e:
        log.error("Google Sheets read failed: %s — falling back to CSV", e)
        return read_csv_topics()


def mark_sheets_status(sheet_id: str, row_index: int, status: str,
                       yt_id: str = "", worksheet: str = "Sheet1") -> None:
    """Update a row status in Google Sheets (row_index is 1-based, +1 for header)."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds  = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDS, scopes=scopes)
        gc     = gspread.authorize(creds)
        ws     = gc.open_by_key(sheet_id).worksheet(worksheet)
        # Find column indices
        headers = ws.row_values(1)
        status_col = headers.index(COL_STATUS) + 1
        yt_col     = headers.index(COL_YT_ID)  + 1
        ws.update_cell(row_index + 1, status_col, status)
        if yt_id:
            ws.update_cell(row_index + 1, yt_col, yt_id)
    except Exception as e:
        log.error("Google Sheets update failed: %s", e)
