"""
Ask VibeJudge in plain English from the terminal.

    py -m src.ask "calm Ethiopian jazz for a rainy evening"
    py -m src.ask "songs for the gym" --offline      # no Gemini: keyword parser + template text
    py -m src.ask "chill study music" --diverse --k 3

Chat mode: each extra message refines the previous one (same as the app's Chat tab).

    py -m src.ask --chat "calm Ethiopian jazz for tonight" "a bit livelier, and no Gigi this time"
"""

import argparse
import sys
import time

from src.chat import ChatSession
from src.explainer import describe_profile
from src.guardrails import RequestRejected
from src.llm_client import LLMError, get_llm
from src.pipeline import VibeJudge, setup_logging
from src.recommender import MODES

BADGES = {"verified": "VERIFIED", "corrected": "CORRECTED", "fallback": "FALLBACK"}


def print_result(result, changes=None) -> None:
    print(f"\nRequest : {result.request}")
    if changes is not None:
        print(f"Changed : {'; '.join(changes) if changes else '(new request)'}")
    print(f"Profile : {describe_profile(result.prefs)}   [parsed by {result.parse_source}]")
    for warning in result.parse_warnings:
        print(f"  ! {warning}")
    print(f"\n{result.explanation.intro}\n")
    for rank, (song, score, _) in enumerate(result.recommendations, start=1):
        print(f"{rank}. {song['title']} - {song['artist']}  ({song['genre']}, {song['mood']})  "
              f"score {score:.2f}/{result.max_points:.2f}")
        print(f"   {result.explanation.reasons[song['id']]}")
    print(f"\nGuardrail: {BADGES[result.guardrail.status]}  (explanation by {result.explanation.source}, "
          f"model {result.llm_name}, {result.seconds:.1f}s)")
    for issue in result.guardrail.issues:
        print(f"  - {issue}")


def main() -> None:
    # Windows consoles default to cp1252, which can't print "→" or "é"
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Ask VibeJudge for music in plain English")
    parser.add_argument("requests", nargs="+", metavar="request",
                        help='what you want to hear, e.g. "upbeat songs for a road trip"')
    parser.add_argument("--chat", action="store_true", help="treat each extra request as a follow-up")
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
    chat = ChatSession(judge) if args.chat else None

    failed = False
    for i, request in enumerate(args.requests):
        if i and llm is not None:
            time.sleep(4)  # stay under the free tier's 15 requests/minute
        if chat:
            print(f"\n{'=' * 70}\nYOU: {request}")
        try:
            if chat:
                result, changes = chat.send(request)
                print_result(result, changes)
            else:
                print_result(judge.recommend(request))
        except RequestRejected as exc:
            print(f"\nRequest : {request!r}\nRequest rejected: {exc}")
            failed = True
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
