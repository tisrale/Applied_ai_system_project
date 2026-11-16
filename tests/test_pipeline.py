"""Full pipeline with a fake Gemini: parse -> retrieve -> explain -> guardrail."""

import json

import pytest

from src.guardrails import RequestRejected
from src.llm_client import FakeGemini
from src.pipeline import VibeJudge, possible_points
from tests.conftest import gemini_reply

ETHIO_PROFILE = gemini_reply(favorite_genre="ethio-jazz", favorite_mood="peaceful", target_energy=0.35,
                             likes_acoustic=True, favorite_mood_tags=[], preferred_language=None,
                             preferred_decade=None, allow_explicit=True, unavailable=[])


def explain_from_prompt(prompt: str) -> str:
    """Fake explainer: read the song titles out of the prompt and explain each one."""
    titles = [line.split('"')[1] for line in prompt.splitlines() if line[:2].rstrip(".").isdigit() and '"' in line]
    return json.dumps({"intro": "Calm picks.", "picks": [{"title": t, "why": "Fits the mood."} for t in titles]})


def smart_fake(**kwargs):
    """Answers parse prompts with ETHIO_PROFILE and explain prompts from the song list."""
    return FakeGemini(handler=lambda p: ETHIO_PROFILE if "taste profile for a song recommender" in p
                      else explain_from_prompt(p), **kwargs)


def test_pipeline_end_to_end_with_fake_gemini(catalog):
    judge = VibeJudge(songs=catalog, llm=smart_fake(), k=3)
    result = judge.recommend("calm Ethiopian jazz")
    titles = [s["title"] for s, _, _ in result.recommendations]
    assert titles[0] == "Kahine (My Priest)"
    assert result.parse_source == "gemini"
    assert result.guardrail.status == "verified"
    assert all(result.explanation.reasons[s["id"]] == "Fits the mood." for s, _, _ in result.recommendations)


def test_explain_prompt_only_contains_retrieved_songs(catalog):
    fake = smart_fake()
    result = VibeJudge(songs=catalog, llm=fake, k=3).recommend("calm Ethiopian jazz")
    explain_prompt = fake.prompts[1]
    picked = {s["title"] for s, _, _ in result.recommendations}
    for song in catalog:
        assert (f'"{song["title"]}"' in explain_prompt) == (song["title"] in picked)


def test_cards_never_include_hallucinated_songs(catalog):
    fake = FakeGemini([ETHIO_PROFILE, json.dumps({"intro": "x", "picks": [{"title": "Tizita", "why": "classic"}]})])
    result = VibeJudge(songs=catalog, llm=fake, k=3).recommend("calm Ethiopian jazz")
    catalog_ids = {s["id"] for s in catalog}
    assert all(s["id"] in catalog_ids for s, _, _ in result.recommendations)
    assert result.guardrail.status == "corrected"


def test_pipeline_survives_gemini_outage(catalog):
    result = VibeJudge(songs=catalog, llm=FakeGemini(fail=True), k=3).recommend("chill lofi")
    assert result.parse_source == "keywords"
    assert result.guardrail.status == "fallback"
    assert len(result.recommendations) == 3


def test_offline_mode_needs_no_llm(catalog):
    result = VibeJudge(songs=catalog, llm=None, k=5).recommend("upbeat happy pop")
    assert result.recommendations[0][0]["genre"] == "pop"
    assert result.llm_name == "offline"


def test_empty_request_is_rejected_before_any_llm_call(catalog):
    fake = smart_fake()
    with pytest.raises(RequestRejected):
        VibeJudge(songs=catalog, llm=fake).recommend("   ")
    assert fake.prompts == []


def test_possible_points_ignores_rules_set_to_any():
    prefs = {"favorite_genre": "any", "favorite_mood": "energetic", "target_energy": 0.9, "likes_acoustic": False}
    assert possible_points(prefs) == pytest.approx(2.5)   # 4.5 minus the 2.0 genre points


def test_retry_wait_honours_quota_errors():
    from src.llm_client import MAX_RETRY_WAIT, _retry_wait

    class Quota(Exception):
        code = 429

    class Busy(Exception):
        code = 503

    class BadKey(Exception):
        code = 400

    assert _retry_wait(Quota("... 'retryDelay': '17s' ...")) == 18.0
    assert _retry_wait(Quota("'retryDelay': '90s'")) == MAX_RETRY_WAIT
    assert _retry_wait(Busy()) == 2.0
    assert _retry_wait(BadKey()) is None
