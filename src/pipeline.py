"""
VibeJudge pipeline: plain-English request -> explained, verified recommendations.

    request
      -> guardrails.check_request      (input guardrail)
      -> parser.parse_request          (Gemini or keywords -> validated taste profile)
      -> recommender.recommend_songs   (RETRIEVAL: the original scorer ranks the catalog)
      -> explainer.build_explain_prompt + llm.generate   (GENERATION: grounded in retrieved songs)
      -> guardrails.check_explanation  (output guardrail)
      -> PipelineResult

Every run is logged to logs/vibejudge.log (never the API key).
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.explainer import Explanation, Rec, build_explain_prompt
from src.guardrails import GuardrailReport, check_explanation, check_request
from src.parser import build_vocab, parse_request
from src.recommender import get_weights, load_songs, max_score, recommend_songs

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "songs.csv"
LOG_PATH = ROOT / "logs" / "vibejudge.log"

logger = logging.getLogger("vibejudge")


def setup_logging(path: Path = LOG_PATH, level: int = logging.INFO) -> None:
    """Send the 'vibejudge' logger to a file (once). Safe to call many times."""
    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def possible_points(prefs: Dict, mode: str = "balanced") -> float:
    """Best score any song could get. Genre/mood set to 'any' can't be earned, so they don't count."""
    weights = get_weights(mode)
    top = max_score(prefs, mode)
    for key, rule in (("favorite_genre", "genre"), ("favorite_mood", "mood")):
        if prefs[key] == "any":
            top -= weights[rule]
    return top


@dataclass
class PipelineResult:
    request: str
    prefs: Dict
    parse_source: str                 # "gemini" or "keywords"
    parse_warnings: List[str]
    recommendations: List[Rec]        # (song, score, reasons) straight from the scorer
    max_points: float
    explanation: Explanation
    guardrail: GuardrailReport
    llm_name: str
    seconds: float = 0.0
    errors: List[str] = field(default_factory=list)


class VibeJudge:
    def __init__(self, songs: Optional[List[Dict]] = None, llm=None, k: int = 5,
                 mode: str = "balanced", diverse: bool = False):
        self.songs = songs if songs is not None else load_songs(str(DATA_PATH))
        self.vocab = build_vocab(self.songs)
        self.llm = llm
        self.k = k
        self.mode = mode
        self.diverse = diverse

    def _checked(self, request: str) -> str:
        try:
            return check_request(request)
        except ValueError as exc:
            logger.info("REJECTED request=%r reason=%s", request, exc)
            raise

    def recommend(self, request: str) -> PipelineResult:
        """Run the full pipeline. Raises guardrails.RequestRejected for unusable requests."""
        start = time.perf_counter()
        request = self._checked(request)
        parsed = parse_request(request, self.vocab, self.llm)
        return self._retrieve_and_explain(request, parsed.prefs, parsed.source, parsed.warnings, start)

    def recommend_with_profile(self, request: str, prefs: Dict, source: str, warnings: List[str],
                               exclude_ids: Iterable[int] = ()) -> PipelineResult:
        """Skip parsing: retrieve + explain for a ready-made profile (used by chat follow-ups).

        exclude_ids removes songs from retrieval (e.g. "no Gigi this time").
        """
        start = time.perf_counter()
        request = self._checked(request)
        return self._retrieve_and_explain(request, prefs, source, warnings, start, set(exclude_ids))

    def _retrieve_and_explain(self, request: str, prefs: Dict, source: str, warnings: List[str],
                              start: float, exclude_ids: Optional[set] = None) -> PipelineResult:
        llm_name = getattr(self.llm, "name", "offline")
        pool = [s for s in self.songs if s["id"] not in (exclude_ids or set())]
        recs = recommend_songs(prefs, pool, k=self.k, mode=self.mode, diverse=self.diverse)
        top = possible_points(prefs, self.mode)

        reply, failure, errors = None, "", []
        if self.llm is None:
            failure = "Offline mode: explanation written from scorer reasons."
        elif recs:
            try:
                reply = self.llm.generate(build_explain_prompt(request, prefs, recs, top), json_mode=True)
            except Exception as exc:
                failure = "Gemini couldn't write the explanation; used scorer reasons instead."
                errors.append(str(exc))
                logger.warning("Gemini explain failed: %s", exc)

        # Leak check uses the FULL catalog, so excluded songs sneaking back into the text are caught too.
        explanation, report = check_explanation(reply, request, prefs, recs, self.songs, failure)
        seconds = time.perf_counter() - start

        logger.info(
            "request=%r llm=%s parse=%s prefs=%s excluded=%s top=%s guardrail=%s issues=%s secs=%.2f",
            request, llm_name, source, prefs, sorted(exclude_ids or []),
            [f"{s['id']}:{s['title']}" for s, _, _ in recs], report.status, report.issues, seconds,
        )
        return PipelineResult(request, prefs, source, warnings, recs, top,
                              explanation, report, llm_name, seconds, errors)
