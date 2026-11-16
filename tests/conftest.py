"""Shared fixtures. Everything here runs offline: no API key, no network."""

import json
from pathlib import Path

import pytest

from src.parser import build_vocab
from src.recommender import load_songs

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.csv"


@pytest.fixture(scope="session")
def catalog():
    return load_songs(str(CATALOG_PATH))


@pytest.fixture(scope="session")
def vocab(catalog):
    return build_vocab(catalog)


def gemini_reply(**fields) -> str:
    """Build a JSON string the way Gemini would send it."""
    return json.dumps(fields)
