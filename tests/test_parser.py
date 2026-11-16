"""Step 1: request -> validated taste profile."""

from src.llm_client import FakeGemini
from src.parser import keyword_parse, parse_request, validate_profile
from tests.conftest import gemini_reply


def test_gemini_profile_is_used_when_valid(vocab):
    fake = FakeGemini([gemini_reply(favorite_genre="ethio-jazz", favorite_mood="peaceful",
                                    target_energy=0.3, likes_acoustic=True,
                                    favorite_mood_tags=["devotional"], preferred_language=None,
                                    preferred_decade=None, allow_explicit=True, unavailable=[])])
    result = parse_request("calm Ethiopian jazz", vocab, fake)
    assert result.source == "gemini"
    assert result.prefs["favorite_genre"] == "ethio-jazz"
    assert result.prefs["favorite_mood_tags"] == ["devotional"]
    assert "calm Ethiopian jazz" in fake.prompts[0]


def test_prompt_lists_only_catalog_genres(vocab):
    fake = FakeGemini([gemini_reply(favorite_genre="pop", favorite_mood="happy", target_energy=0.8)])
    parse_request("happy pop", vocab, fake)
    assert "ethio-jazz" in fake.prompts[0]
    assert "k-pop" not in fake.prompts[0]


def test_gemini_outage_falls_back_to_keywords(vocab):
    result = parse_request("chill lofi for studying", vocab, FakeGemini(fail=True))
    assert result.source == "keywords"
    assert result.prefs["favorite_genre"] == "lofi"
    assert result.prefs["favorite_mood"] == "chill"
    assert any("keyword" in w for w in result.warnings)


def test_gemini_garbage_reply_falls_back_to_keywords(vocab):
    result = parse_request("reggae please", vocab, FakeGemini(["Sure! Here's some reggae for you."]))
    assert result.source == "keywords"
    assert result.prefs["favorite_genre"] == "reggae"


def test_validation_snaps_aliases_and_clamps_energy(vocab):
    prefs, warnings = validate_profile({"favorite_genre": "Hip Hop", "favorite_mood": "calm",
                                        "target_energy": 1.7}, vocab)
    assert prefs["favorite_genre"] == "hip-hop"
    assert prefs["favorite_mood"] == "peaceful"
    assert prefs["target_energy"] == 1.0
    assert any("clamped" in w for w in warnings)


def test_validation_drops_unknown_genre_and_tags_with_warning(vocab):
    prefs, warnings = validate_profile({"favorite_genre": "k-pop", "favorite_mood": "happy",
                                        "target_energy": 0.8, "favorite_mood_tags": ["sparkly", "joyful"]}, vocab)
    assert prefs["favorite_genre"] == "any"
    assert prefs["favorite_mood_tags"] == ["joyful"]
    assert any("k-pop" in w for w in warnings)


def test_keyword_parse_uses_first_mood_word(vocab):
    raw = keyword_parse("calm ethiopian jazz for a rainy evening", vocab)
    assert raw["favorite_genre"] == "ethiopian"      # alias, snapped to ethio-jazz in validation
    assert raw["favorite_mood"] == "calm"            # not "rainy", which comes later
    prefs, _ = validate_profile(raw, vocab)
    assert prefs["favorite_genre"] == "ethio-jazz"
    assert prefs["target_energy"] < 0.4


def test_keyword_parse_reads_clean_and_language_and_decade(vocab):
    prefs, _ = validate_profile(keyword_parse("clean 80s songs in amharic", vocab), vocab)
    assert prefs["allow_explicit"] is False
    assert prefs["preferred_language"] == "amharic"
    assert prefs["preferred_decade"] == 1980


def test_keyword_parse_does_not_match_pop_inside_kpop(vocab):
    prefs, _ = validate_profile(keyword_parse("k-pop bangers", vocab), vocab)
    assert prefs["favorite_genre"] == "any"


def test_keyword_parse_reports_genres_the_catalog_lacks(vocab):
    prefs, warnings = validate_profile(keyword_parse("k-pop bangers", vocab), vocab)
    assert prefs["favorite_genre"] == "any"
    assert any("k-pop" in w for w in warnings)


def test_unavailable_items_that_exist_in_catalog_are_not_reported(vocab):
    _, warnings = validate_profile({"favorite_genre": "reggae", "favorite_mood": "uplifting", "target_energy": 0.6,
                                    "unavailable": ["Bob Marley", "Tizita", "k-pop", "reggae"]}, vocab)
    reported = [w for w in warnings if w.startswith("Not in the catalog")]
    assert reported == ["Not in the catalog: Tizita", "Not in the catalog: k-pop"]


def test_profile_wrapped_in_a_list_is_accepted(vocab):
    fake = FakeGemini(["[" + gemini_reply(favorite_genre="rock", favorite_mood="energetic", target_energy=0.8) + "]"])
    result = parse_request("80s rock", vocab, fake)
    assert result.source == "gemini" and result.prefs["favorite_genre"] == "rock"
