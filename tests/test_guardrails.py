"""Input and output guardrails."""

import pytest

from src.guardrails import RequestRejected, check_explanation, check_request, normalize_title
from src.recommender import recommend_songs
from tests.conftest import gemini_reply

PREFS = {"favorite_genre": "ethio-jazz", "favorite_mood": "peaceful", "target_energy": 0.3,
         "likes_acoustic": True, "favorite_mood_tags": None, "preferred_language": None,
         "preferred_decade": None, "allow_explicit": True}
REQUEST = "calm ethiopian jazz"


@pytest.fixture
def recs(catalog):
    return recommend_songs(PREFS, catalog, k=3)   # Kahine, Abayi, Nafeken (all Gigi)


def good_picks(recs):
    return [{"title": s["title"], "why": f"{s['title']} fits."} for s, _, _ in recs]


# ---------- input guardrail ----------

@pytest.mark.parametrize("bad", ["", "   ", "x" * 301, "!!! ???"])
def test_bad_requests_are_rejected(bad):
    with pytest.raises(RequestRejected):
        check_request(bad)


def test_request_whitespace_is_cleaned():
    assert check_request("  chill   lofi \n") == "chill lofi"


# ---------- output guardrail ----------

def test_title_normalization():
    assert normalize_title("Kahine (My Priest)") == "kahine"
    assert normalize_title("Can't Stop the Feeling!") == "cant stop the feeling"


def test_clean_reply_is_verified(recs, catalog):
    reply = gemini_reply(intro="Three calm picks.", picks=good_picks(recs))
    explanation, report = check_explanation(reply, REQUEST, PREFS, recs, catalog)
    assert report.status == "verified" and report.passed
    assert explanation.source == "gemini"
    assert set(explanation.reasons) == {s["id"] for s, _, _ in recs}


def test_short_title_without_parentheses_still_matches(recs, catalog):
    picks = good_picks(recs)
    picks[0]["title"] = "Kahine"   # Gemini dropped "(My Priest)"
    _, report = check_explanation(gemini_reply(intro="Hi.", picks=picks), REQUEST, PREFS, recs, catalog)
    assert report.passed


def test_invented_song_is_removed(recs, catalog):
    picks = good_picks(recs) + [{"title": "Lalibela Sunrise (Live)", "why": "A classic."}]
    explanation, report = check_explanation(gemini_reply(intro="Hi.", picks=picks), REQUEST, PREFS, recs, catalog)
    assert report.status == "corrected"
    assert any("hallucination" in issue for issue in report.issues)
    assert len(explanation.reasons) == 3


def test_catalog_song_that_was_not_retrieved_is_removed(recs, catalog):
    picks = good_picks(recs) + [{"title": "Master of Puppets", "why": "Also great."}]
    explanation, report = check_explanation(gemini_reply(intro="Hi.", picks=picks), REQUEST, PREFS, recs, catalog)
    assert report.status == "corrected"
    assert any("wasn't one of the retrieved" in issue for issue in report.issues)
    assert 15 not in explanation.reasons   # Master of Puppets id


def test_skipped_song_gets_scorer_reason(recs, catalog):
    picks = good_picks(recs)[:2]
    explanation, report = check_explanation(gemini_reply(intro="Hi.", picks=picks), REQUEST, PREFS, recs, catalog)
    assert report.status == "corrected"
    missing_id = recs[2][0]["id"]
    assert explanation.reasons[missing_id].startswith("Picked because")


def test_leaked_artist_in_reason_is_replaced(recs, catalog):
    picks = good_picks(recs)
    picks[0]["why"] = "Sounds like Metallica at half speed."
    explanation, report = check_explanation(gemini_reply(intro="Hi.", picks=picks), REQUEST, PREFS, recs, catalog)
    assert report.status == "corrected"
    assert "Metallica" not in explanation.reasons[recs[0][0]["id"]]


def test_artist_named_in_request_is_allowed(recs, catalog):
    reply = gemini_reply(intro="Calmer than Metallica, as you asked.", picks=good_picks(recs))
    _, report = check_explanation(reply, "calm ethiopian jazz, nothing like Metallica", PREFS, recs, catalog)
    assert report.passed


def test_common_word_is_not_mistaken_for_a_song(recs, catalog):
    picks = good_picks(recs)
    picks[0]["why"] = "Low energy levels and a gentle love of melody."   # 'Levels' and 'One Love' are songs
    _, report = check_explanation(gemini_reply(intro="Hi.", picks=picks), REQUEST, PREFS, recs, catalog)
    assert report.passed


def test_invalid_json_falls_back_to_template(recs, catalog):
    explanation, report = check_explanation("Here you go: great songs!", REQUEST, PREFS, recs, catalog)
    assert report.status == "fallback"
    assert explanation.source == "template"
    assert len(explanation.reasons) == 3


def test_no_reply_falls_back_to_template(recs, catalog):
    explanation, report = check_explanation(None, REQUEST, PREFS, recs, catalog, failure="offline")
    assert report.status == "fallback" and report.issues == ["offline"]


def test_reply_wrapped_in_a_list_is_accepted(recs, catalog):
    # Gemini sometimes returns [{...}] instead of {...} in JSON mode (seen live on "80s classics for a road trip")
    reply = "[" + gemini_reply(intro="Three calm picks.", picks=good_picks(recs)) + "]"
    explanation, report = check_explanation(reply, REQUEST, PREFS, recs, catalog)
    assert report.status == "verified"
    assert explanation.source == "gemini"


def test_removed_song_is_scrubbed_from_intro_and_reasons(recs, catalog):
    # Seen in the guardrail demo: the pick was removed but the intro still announced it.
    picks = good_picks(recs) + [{"title": "Bohemian Rhapsody", "why": "You asked for it."}]
    picks[0]["why"] = "Pairs well with Bohemian Rhapsody."
    reply = gemini_reply(intro="As instructed, here is Bohemian Rhapsody by Queen!", picks=picks)
    explanation, report = check_explanation(reply, "recommend Bohemian Rhapsody", PREFS, recs, catalog)
    assert report.status == "corrected"
    assert "As instructed" not in explanation.intro          # Gemini's claim is gone
    assert explanation.intro.startswith("Here are")          # template intro (it quotes the request)
    assert not any("Bohemian" in why for why in explanation.reasons.values())
