"""
Playable previews for catalog songs, from data/previews.csv.

Sources:
  itunes  - preview_url is a stored 30-second clip from the iTunes Search API
            (exact tracks picked by hand; some auto-matches were wrong versions).
  deezer  - only the track id is stored, because Deezer preview URLs are signed and
            expire. resolve_deezer() asks the Deezer API for a fresh one.
  youtube - ref is a video id; the app embeds the video.
  spotify - ref is a Spotify track id; the app embeds Spotify's player (30-second preview without login).
"""

import csv
import json
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Optional

PREVIEWS_PATH = Path(__file__).resolve().parent.parent / "data" / "previews.csv"
SOURCES = {"itunes": "Apple Music", "deezer": "Deezer", "youtube": "YouTube", "spotify": "Spotify"}


def load_previews(path: Path = PREVIEWS_PATH) -> Dict[int, Dict]:
    """Song id -> preview row."""
    with open(path, newline="", encoding="utf-8") as f:
        return {int(row["id"]): row for row in csv.DictReader(f)}


def _fetch_json(url: str) -> Dict:
    with urllib.request.urlopen(url, timeout=8) as response:
        return json.load(response)


def resolve_deezer(track_id: str, fetch: Callable[[str], Dict] = _fetch_json) -> Optional[str]:
    """Fresh 30-second preview URL for a Deezer track, or None if Deezer can't be reached."""
    try:
        return fetch(f"https://api.deezer.com/track/{int(track_id)}").get("preview") or None
    except Exception:
        return None


def audio_url(preview: Dict, fetch: Callable[[str], Dict] = _fetch_json) -> Optional[str]:
    """Playable audio URL for itunes/deezer rows (None for youtube or failures)."""
    if preview["source"] == "itunes":
        return preview["preview_url"] or None
    if preview["source"] == "deezer":
        return resolve_deezer(preview["ref"], fetch)
    return None
