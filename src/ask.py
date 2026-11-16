"""
Ask VibeJudge in plain English from the terminal.

    py -m src.ask "calm Ethiopian jazz for a rainy evening"
    py -m src.ask "songs for the gym" --offline      # no Gemini: keyword parser + template text
    py -m src.ask "chill study music" --diverse --k 3
"""

import argparse
import sys

from src.guardrails import RequestRejected
from src.llm_client import LLMError, get_llm
from src.pipeline import VibeJudge, setup_logging
from src.explainer import describe_profile
from src.recommender import MODES


def print_result(result) -> None:
    print(f"\nRequest : {result.request}")
    print(f"Profile : {describe_profile(result.prefs)}   [parsed by {result.parse_source}]")
    for warning in result.parse_warnings:
        print(f"  ! {warning}")
    print(f"\n{result.explanation.intro}\n")
    for rank, (song, score, _) in enumerate(result.recommendations, start=1):
        print(f"{rank}. {song['title']} - {song['artist']}  ({song['genre']}, {song['mood']})  "
              f"score {score:.2f}/{result.max_points:.2f}")
        print(f"   {result.explanation.reasons[song['id']]}")
    badge = {"verified": "VERIFIED", "corrected": "CORRECTED", "fallback": "FALLBACK"}[result.guardrail.status]
    print(f"\nGuardrail: {badge}  (explanation by {result.explanation.source}, model {result.llm_name}, "
          f"{result.seconds:.1f}s)")
    for issue in result.guardrail.issues:
        print(f"  - {issue}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask VibeJudge for music in plain English")
    parser.add_argument("request", help='what you want to hear, e.g. "upbeat songs for a road trip"')
    parser.add_argument("--offline", action="store_true", help="don't call Gemini")
    parser.add_argument("--k", type=int, default=5, help="number of songs")
    parser.add_argument("--mode", choices=MODES, default="balanced", help="ranking strategy")
    parser.add_argument("--diverse", action="store_true", help="spread picks across artists and genres")
    args = parser.parse_args()

    setup_logging()
    try:
        llm = get_llm(offline=args.offline)
    except LLMError as exc:
        print(f"Gemini unavailable ({exc}). Running offline.")
        llm = None
    judge = VibeJudge(llm=llm, k=args.k, mode=args.mode, diverse=args.diverse)
    try:
        print_result(judge.recommend(args.request))
    except RequestRejected as exc:
        print(f"Request rejected: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
