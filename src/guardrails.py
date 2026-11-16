"""
Guardrails: checks that keep the AI honest.

check_request      - input guardrail: rejects empty or oversized requests before any API call.
check_explanation  - output guardrail: Gemini may only talk about the songs the scorer retrieved.
                     Invented songs, songs from elsewhere in the catalog, and skipped songs are
                     caught and corrected with template reasons, and each fix is reported.

The song cards themselves always come from the scorer, never from Gemini, so an invented
song can never be shown or played. This guardrail protects the *text* around them.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.parser import extract_json
from src.explainer import Explanation, Rec, template_explanation, template_intro, template_reason

MAX_REQUEST_CHARS = 300
MAX_REASON_CHARS = 400


class RequestRejected(ValueError):
    """The request can't be processed (empty, too long, ...). The message is safe to show users."""


@dataclass
class GuardrailReport:
    status: str                              # "verified", "corrected" or "fallback"
    issues: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == "verified"


def check_request(text: str) -> str:
    """Return the cleaned request, or raise RequestRejected with a user-friendly message."""
    cleaned = " ".join((text or "").split())
    if not cleaned:
        raise RequestRejected("Please describe the music you're in the mood for.")
    if len(cleaned) > MAX_REQUEST_CHARS:
        raise RequestRejected(f"Please keep the request under {MAX_REQUEST_CHARS} characters.")
    if not re.search(r"[A-Za-zሀ-፿]", cleaned):  # Latin or Ethiopic letters
        raise RequestRejected("Please describe the music in words.")
    return cleaned


def normalize_title(title: str) -> str:
    """'Kahine (My Priest)' -> 'kahine'; "Can't Stop the Feeling!" -> 'cant stop the feeling'."""
    title = re.sub(r"\(.*?\)", "", str(title)).lower().replace("'", "").replace("’", "")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", title).split())


def _mentions(text: str, name: str) -> bool:
    """Case-sensitive whole-phrase search, so 'energy levels' doesn't count as the song 'Levels'."""
    short = re.sub(r"\(.*?\)", "", name).strip()
    return len(short) >= 4 and re.search(rf"(?<!\w){re.escape(short)}(?!\w)", text) is not None


def find_leaks(text: str, recs: List[Rec], catalog: List[Dict], request: str = "") -> List[str]:
    """Catalog songs/artists mentioned in text that were NOT retrieved.

    Names the user typed in their own request are allowed (e.g. "something like Bob Marley").
    """
    picked_ids = {song["id"] for song, _, _ in recs}
    picked_artists = {song["artist"] for song, _, _ in recs}
    asked = request.lower()
    leaks = []
    for song in catalog:
        if song["id"] in picked_ids:
            continue
        if _mentions(text, song["title"]) and song["title"].lower() not in asked:
            leaks.append(f"song '{song['title']}'")
        if (song["artist"] not in picked_artists and _mentions(text, song["artist"])
                and song["artist"].lower() not in asked):
            leaks.append(f"artist '{song['artist']}'")
    return sorted(set(leaks))


def check_explanation(reply: Optional[str], request: str, prefs: Dict, recs: List[Rec],
                      catalog: List[Dict], failure: str = "") -> Tuple[Explanation, GuardrailReport]:
    """Verify Gemini's JSON explanation against the retrieved songs and repair what's wrong.

    reply=None means there was no usable LLM reply (offline or error); failure says why.
    """
    if reply is None:
        issues = [failure] if failure else []
        return template_explanation(request, prefs, recs), GuardrailReport("fallback", issues)

    try:
        data = extract_json(reply)
        picks = data["picks"]
        intro = data.get("intro", "")
        if not isinstance(picks, list):
            raise ValueError("'picks' is not a list")
    except (ValueError, KeyError, TypeError) as exc:
        return (template_explanation(request, prefs, recs),
                GuardrailReport("fallback", [f"Gemini's reply wasn't valid JSON ({exc}); used template text."]))

    issues: List[str] = []
    retrieved = {normalize_title(song["title"]): song for song, _, _ in recs}
    catalog_titles = {normalize_title(song["title"]): song for song in catalog}
    reasons: Dict[int, str] = {}

    for pick in picks:
        if not isinstance(pick, dict):
            continue
        title = str(pick.get("title", "")).strip()
        why = str(pick.get("why", "")).strip()[:MAX_REASON_CHARS]
        key = normalize_title(title)
        if key in retrieved:
            song = retrieved[key]
            if song["id"] in reasons:
                continue  # duplicate entry: keep the first
            leaks = find_leaks(why, recs, catalog, request)
            if leaks:
                issues.append(f"Reason for '{song['title']}' mentioned {', '.join(leaks)}; replaced with scorer reason.")
                why = ""
            reasons[song["id"]] = why or template_reason(song, prefs)
        elif key in catalog_titles:
            issues.append(f"Removed '{title}': it's in the catalog but wasn't one of the retrieved picks.")
        else:
            issues.append(f"Removed '{title}': not a song in the catalog (hallucination).")

    for song, _, _ in recs:
        if song["id"] not in reasons:
            issues.append(f"Gemini skipped '{song['title']}'; used scorer reason.")
            reasons[song["id"]] = template_reason(song, prefs)

    intro = intro.strip() if isinstance(intro, str) else ""
    intro_leaks = find_leaks(intro, recs, catalog, request)
    if intro_leaks:
        issues.append(f"Intro mentioned {', '.join(intro_leaks)}; replaced with template intro.")
        intro = ""
    if not intro:
        intro = template_intro(request, prefs, recs)

    if issues:
        return Explanation(intro, reasons, "gemini+template"), GuardrailReport("corrected", issues)
    return Explanation(intro, reasons, "gemini"), GuardrailReport("verified", [])
