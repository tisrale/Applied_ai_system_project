"""Chat mode: follow-ups refine the previous profile. All offline (FakeGemini or keywords)."""

import json

from src.chat import ChatSession, describe_changes, refine, resolve_exclusions
from src.llm_client import FakeGemini
from src.pipeline import VibeJudge

BASE = {"favorite_genre": "ethio-jazz", "favorite_mood": "peaceful", "target_energy": 0.3,
        "likes_acoustic": True, "favorite_mood_tags": None, "preferred_language": None,
        "preferred_decade": None, "allow_explicit": True}


def titles(result):
    return [s["title"] for s, _, _ in result.recommendations]


def test_offline_follow_up_raises_energy_and_excludes_artist(catalog):
    chat = ChatSession(VibeJudge(songs=catalog, llm=None))
    first, _ = chat.send("calm ethiopian jazz")
    assert titles(first)[0] == "Kahine (My Priest)"
    second, changes = chat.send("a bit livelier, and no Gigi this time")
    assert chat.prefs["target_energy"] > first.prefs["target_energy"]
    assert chat.prefs["favorite_genre"] == "ethio-jazz"            # unchanged
    assert not any(s["artist"] == "Gigi" for s, _, _ in second.recommendations)
    assert any("energy" in c for c in changes) and any("Gigi" in c for c in changes)


def test_exclusions_stick_across_turns(catalog):
    chat = ChatSession(VibeJudge(songs=catalog, llm=None))
    chat.send("calm ethiopian jazz")
    chat.send("no Gigi")
    third, _ = chat.send("a bit calmer")
    assert not any(s["artist"] == "Gigi" for s, _, _ in third.recommendations)


def test_start_over_clears_exclusions(catalog):
    chat = ChatSession(VibeJudge(songs=catalog, llm=None))
    chat.send("calm ethiopian jazz")
    chat.send("no Gigi")
    result, changes = chat.send("start over: calm ethiopian jazz")
    assert changes == ["started a new request"]
    assert titles(result)[0] == "Kahine (My Priest)"


def test_gemini_refinement_is_validated_against_catalog(catalog, vocab):
    reply = json.dumps({"start_over": False,
                        "profile": dict(BASE, target_energy=1.4, favorite_genre="zouk"),
                        "exclude_artists": ["Gigi", "Taylor Swift"], "exclude_genres": [],
                        "exclude_titles": ["Tizita"]})
    r = refine("way more energy, no Gigi", BASE, ["Kahine (My Priest)"], vocab, catalog, FakeGemini([reply]))
    assert r.source == "gemini"
    assert r.prefs["target_energy"] == 1.0                     # clamped
    assert r.prefs["favorite_genre"] == "any"                  # zouk isn't in the catalog
    gigi_ids = {s["id"] for s in catalog if s["artist"] == "Gigi"}
    assert r.exclude_ids == gigi_ids                            # unknown artist/title ignored


def test_refine_prompt_carries_context(catalog, vocab):
    fake = FakeGemini([json.dumps({"start_over": False, "profile": BASE})])
    refine("calmer", BASE, ["Kahine (My Priest)", "Abayi"], vocab, catalog, fake)
    assert "Kahine (My Priest)" in fake.prompts[0] and "'ethio-jazz'" in fake.prompts[0]
    assert "<<<calmer>>>" in fake.prompts[0]


def test_gemini_failure_falls_back_to_keywords(catalog, vocab):
    r = refine("a bit calmer", BASE, [], vocab, catalog, FakeGemini(fail=True))
    assert r.source == "keywords"
    assert r.prefs["target_energy"] < BASE["target_energy"]


def test_changes_are_computed_not_generated():
    new = dict(BASE, target_energy=0.5, favorite_mood="nostalgic")
    assert describe_changes(BASE, new, ["Gigi"]) == ["mood peaceful → nostalgic", "energy 0.30 → 0.50",
                                                     "leaving out Gigi"]


def test_resolve_exclusions_by_genre_and_title(catalog):
    ids, labels = resolve_exclusions(catalog, genres=["reggae"], titles=["Kahine"])
    assert {s["title"] for s in catalog if s["id"] in ids} == {"Red Red Wine", "One Love", "Jerusalem",
                                                                 "Kahine (My Priest)"}
    assert "reggae songs" in labels


def test_exclusions_the_listener_did_not_name_are_ignored(catalog, vocab):
    # Seen live: asked to "make it reggae", Gemini excluded all previous picks and ethio-jazz,
    # which also removed Jerusalem (a reggae song).
    reply = json.dumps({"start_over": False, "profile": dict(BASE, favorite_genre="reggae"),
                        "exclude_artists": [], "exclude_genres": ["ethio-jazz"],
                        "exclude_titles": ["Jerusalem", "Clair de Lune"]})
    r = refine("now make it reggae", BASE, ["Jerusalem", "Clair de Lune"], vocab, catalog, FakeGemini([reply]))
    assert r.prefs["favorite_genre"] == "reggae"
    assert r.exclude_ids == set()


def test_named_exclusions_are_kept(catalog, vocab):
    reply = json.dumps({"start_over": False, "profile": BASE, "exclude_artists": ["Bob Marley & The Wailers"],
                        "exclude_genres": [], "exclude_titles": ["Red Red Wine"]})
    r = refine("no Marley and skip Red Red Wine", BASE, [], vocab, catalog, FakeGemini([reply]))
    assert {s["title"] for s in catalog if s["id"] in r.exclude_ids} == {"One Love", "Red Red Wine"}
