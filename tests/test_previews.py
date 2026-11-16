"""Preview data: every song playable from a known source, Deezer resolved fresh (faked here, no network)."""

from src.previews import SOURCES, audio_url, load_previews, resolve_deezer


def test_every_catalog_song_has_a_preview(catalog):
    previews = load_previews()
    assert {s["id"] for s in catalog} == set(previews)
    for row in previews.values():
        assert row["source"] in SOURCES
        assert row["link"].startswith("https://")


def test_itunes_rows_store_exact_preview_links():
    for row in load_previews().values():
        if row["source"] == "itunes":
            assert row["preview_url"].startswith("https://") and row["ref"].isdigit()


def test_deezer_rows_store_ids_not_expiring_urls():
    deezer = {i: r for i, r in load_previews().items() if r["source"] == "deezer"}
    assert deezer[22]["ref"] == "12589946"      # Gigi - Kahine ("Kahn" on Deezer)
    assert all(r["preview_url"] == "" for r in deezer.values())


def test_deezer_preview_is_resolved_at_runtime():
    fake = lambda url: {"preview": "https://cdn.example/fresh.mp3"} if url.endswith("/12589946") else {}
    assert audio_url({"source": "deezer", "ref": "12589946"}, fetch=fake) == "https://cdn.example/fresh.mp3"


def test_deezer_outage_returns_none():
    def broken(url):
        raise OSError("offline")
    assert resolve_deezer("12589946", fetch=broken) is None


def test_nafeken_uses_itunes_album_version():
    row = load_previews()[24]      # replaced Becher Yider, whose YouTube recording didn't play well
    assert row["source"] == "itunes" and row["ref"] == "2602556"
    assert row["matched"] == "Nafeken | Gigi | Gigi"


def test_youtube_rows_have_no_audio_url():
    assert audio_url({"source": "youtube", "ref": "-imslYtZO3A", "preview_url": ""}) is None
