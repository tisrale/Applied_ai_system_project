"""
VibeJudge web app.

    .venv\\Scripts\\python.exe -m streamlit run app.py

Tabs:
  Ask VibeJudge  - plain-English request -> Gemini profile -> scorer picks -> Gemini explanation
                   -> guardrail badge, with playable song cards
  Browse catalog - every song with previews, filterable
  How it works   - the pipeline and the latest evaluation results
"""

import html
import os

import streamlit as st

from src.chat import ChatSession
from src.explainer import describe_profile
from src.guardrails import RequestRejected
from src.llm_client import LLMError, GeminiClient
from src.main import short_reason
from src.pipeline import DATA_PATH, ROOT, VibeJudge, setup_logging
from src.previews import PREVIEWS_PATH, SOURCES, load_previews, resolve_deezer
from src.recommender import MODES

st.set_page_config(page_title="VibeJudge", page_icon="🎧", layout="wide")

# On Streamlit Community Cloud the key lives in st.secrets instead of .env
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ.setdefault("GEMINI_API_KEY", st.secrets["GEMINI_API_KEY"])
except Exception:
    pass

EXAMPLES = [
    "Calm Ethiopian jazz for a rainy evening",
    "Upbeat pop to dance around the kitchen",
    "Focus music for studying, no lyrics",
    "Angry metal for the gym",
    "Heartbroken songs to cry to",
    "Positive reggae vibes like Bob Marley",
]

st.markdown("""
<style>
.vj-title {font-size: 2.6rem; font-weight: 800; margin-bottom: 0;}
.vj-title span {color: #E8A33D;}
.vj-tagline {opacity: .75; margin-top: -4px; margin-bottom: 1rem;}
.vj-chip {display: inline-block; padding: 2px 10px; margin: 2px 4px 2px 0; border-radius: 999px;
          background: rgba(232,163,61,.14); color: #F0B65A; font-size: .78rem; white-space: nowrap;}
.vj-chip.muted {background: rgba(255,255,255,.07); color: #CFC8D8;}
.vj-rank {font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; color: #E8A33D; font-weight: 700;}
.vj-song {font-size: 1.25rem; font-weight: 700; line-height: 1.2;}
.vj-artist {opacity: .75; margin-bottom: .35rem;}
.vj-why {font-size: .95rem; margin: .4rem 0 .5rem; line-height: 1.45;}
.vj-src {font-size: .75rem; opacity: .6;}
</style>
""", unsafe_allow_html=True)


# ---------- cached resources ----------

@st.cache_resource(show_spinner=False)
def get_llm(use_gemini: bool):
    """GeminiClient, or (None, reason) when offline or the key is missing."""
    if not use_gemini:
        return None, "Offline mode"
    try:
        return GeminiClient(), ""
    except LLMError as exc:
        return None, str(exc)


@st.cache_resource(show_spinner=False)
def get_judge(use_gemini: bool, mode: str, diverse: bool, k: int, catalog_version: float = 0.0):
    # catalog_version = songs.csv modified time, so editing the catalog reloads it (no server restart)
    setup_logging()
    llm, reason = get_llm(use_gemini)
    return VibeJudge(llm=llm, k=k, mode=mode, diverse=diverse), reason


@st.cache_data(show_spinner=False)
def _previews(version: float):
    return load_previews()


def previews():
    """Preview rows, reloaded whenever previews.csv changes."""
    return _previews(PREVIEWS_PATH.stat().st_mtime)


@st.cache_data(ttl=600, show_spinner=False)
def deezer_audio(track_id: str):
    """Deezer preview links expire, so fetch a fresh one (cached for 10 minutes)."""
    return resolve_deezer(track_id)


# ---------- small render helpers ----------

def chips(values, muted=False) -> str:
    cls = "vj-chip muted" if muted else "vj-chip"
    return "".join(f'<span class="{cls}">{html.escape(str(v))}</span>' for v in values if v)


def play_preview(song_id: int) -> None:
    """Audio player (iTunes/Deezer) or embedded video (YouTube), plus an 'open in' link."""
    p = previews().get(song_id)
    if not p:
        st.caption("No preview available.")
        return
    if p["source"] == "youtube":
        # Direct iframe instead of st.video: YouTube's player refuses some wrapped embeds.
        st.iframe(f"https://www.youtube-nocookie.com/embed/{p['ref']}", height=200)
    elif p["source"] == "spotify":
        # Spotify's embed plays a 30-second preview without logging in.
        st.iframe(f"https://open.spotify.com/embed/track/{p['ref']}?utm_source=generator", height=80)
    else:
        url = p["preview_url"] if p["source"] == "itunes" else deezer_audio(p["ref"])
        if url:
            st.audio(url)
        else:
            st.caption("Preview couldn't load right now.")
    label = "Video" if p["source"] == "youtube" else "30-second preview"
    st.markdown(f'<span class="vj-src">{label} via {SOURCES[p["source"]]} · '
                f'<a href="{html.escape(p["link"])}" target="_blank">open full song ↗</a></span>',
                unsafe_allow_html=True)


def artwork(song_id: int) -> None:
    p = previews().get(song_id)
    if p and p["artwork_url"]:
        st.image(p["artwork_url"], width="stretch")


def song_card(song, rank=None, score=None, max_points=None, why=None, reasons=None) -> None:
    with st.container(border=True):
        art_col, info_col = st.columns([1, 3], gap="medium")
        with art_col:
            artwork(song["id"])
        with info_col:
            if rank is not None:
                st.markdown(f'<div class="vj-rank">#{rank} pick</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="vj-song">{html.escape(song["title"])}</div>'
                        f'<div class="vj-artist">{html.escape(song["artist"])} · {song["release_decade"]}s · '
                        f'{song["language"]}</div>', unsafe_allow_html=True)
            st.markdown(chips([song["genre"], song["mood"]]) + chips(song["mood_tags"], muted=True),
                        unsafe_allow_html=True)
            if score is not None:
                st.progress(min(score / max_points, 1.0), text=f"Match {score:.2f} / {max_points:.2f}")
            if why:
                st.markdown(f'<div class="vj-why">{html.escape(why)}</div>', unsafe_allow_html=True)
            if reasons:
                st.markdown(chips([short_reason(r) for r in reasons.split(", ")], muted=True),
                            unsafe_allow_html=True)
            play_preview(song["id"])


def guardrail_badge(g) -> None:
    if g.status == "verified":
        st.success("**Verified.** Every song in the explanation is one of the catalog picks.", icon="✅")
    elif g.status == "corrected":
        st.warning(f"**Corrected.** The guardrail fixed {len(g.issues)} issue(s) in Gemini's answer.", icon="🛠️")
    else:
        st.info("**Fallback.** Explanations were written from the scorer's reasons.", icon="🧩")
    if g.issues:
        with st.expander("Guardrail details"):
            for issue in g.issues:
                st.write("•", issue)


def result_cards(result) -> None:
    for rank, (song, score, reasons) in enumerate(result.recommendations, start=1):
        song_card(song, rank=rank, score=score, max_points=result.max_points,
                  why=result.explanation.reasons.get(song["id"]), reasons=reasons)


# ---------- sidebar ----------

with st.sidebar:
    st.header("⚙️ Settings")
    use_gemini = st.toggle("Use Gemini", value=True,
                           help="Off = offline mode: keyword parser and template explanations.")
    mode = st.selectbox("Ranking mode", MODES, help="How the scorer weighs genre, mood and energy.")
    diverse = st.toggle("Spread across artists/genres", value=False)
    k = st.slider("Number of songs", 3, 8, 5)
    judge, llm_reason = get_judge(use_gemini, mode, diverse, k, DATA_PATH.stat().st_mtime)
    if judge.llm is not None:
        st.success(f"Connected: {judge.llm.model}")
    else:
        st.info(f"Offline: {llm_reason}" if llm_reason else "Offline mode")
    st.caption(f"Catalog: {len(judge.songs)} songs. Every run is logged to logs/vibejudge.log.")


# ---------- header ----------

st.markdown('<div class="vj-title">🎧 Vibe<span>Judge</span></div>', unsafe_allow_html=True)
st.markdown('<div class="vj-tagline">Describe the vibe in your own words. VibeJudge finds it in the '
            'catalog, explains every pick, and checks its own work.</div>', unsafe_allow_html=True)

ask_tab, chat_tab, browse_tab, about_tab = st.tabs(
    ["✨ Ask VibeJudge", "💬 Chat", "🎵 Browse catalog", "🔍 How it works"])


# ---------- Ask tab ----------

def use_example(text: str) -> None:
    st.session_state["request"] = text
    st.session_state["run_now"] = True


with ask_tab:
    with st.form("ask"):
        request = st.text_input("What are you in the mood for?", key="request",
                                placeholder="e.g. calm Ethiopian jazz for a rainy evening")
        submitted = st.form_submit_button("Find my vibe", type="primary")

    st.caption("Try one:")
    cols = st.columns(3)
    for i, example in enumerate(EXAMPLES):
        cols[i % 3].button(example, key=f"ex{i}", on_click=use_example, args=(example,),
                           width="stretch")

    if submitted or st.session_state.pop("run_now", False):
        with st.spinner("Reading your vibe, searching the catalog, checking the picks..."):
            try:
                st.session_state["result"] = judge.recommend(st.session_state["request"])
                st.session_state.pop("error", None)
            except RequestRejected as exc:
                st.session_state["error"] = str(exc)
                st.session_state.pop("result", None)

    if "error" in st.session_state:
        st.warning(st.session_state["error"])

    result = st.session_state.get("result")
    if result:
        st.divider()
        prof_col, guard_col = st.columns([3, 2], gap="large")
        with prof_col:
            st.markdown("**How I read your request**")
            st.markdown(chips(describe_profile(result.prefs).split(", ")), unsafe_allow_html=True)
            st.caption(f"Parsed by {'Gemini' if result.parse_source == 'gemini' else 'keyword matching'} · "
                       f"{result.seconds:.1f}s")
            for warning in result.parse_warnings:
                st.info(warning, icon="ℹ️")
        with guard_col:
            guardrail_badge(result.guardrail)

        st.subheader(result.explanation.intro)
        result_cards(result)


# ---------- Chat tab ----------

FOLLOW_UPS = ["A bit calmer", "A bit livelier", "More acoustic"]


def queue_chat(text: str) -> None:
    st.session_state["chat_pending"] = text


def reset_chat() -> None:
    st.session_state["chat_session"].reset()
    st.session_state["chat_msgs"] = []


with chat_tab:
    # A new chat starts whenever the settings (and so the judge) change
    if st.session_state.get("chat_judge_id") != id(judge):
        st.session_state["chat_session"] = ChatSession(judge)
        st.session_state["chat_msgs"] = []
        st.session_state["chat_judge_id"] = id(judge)
    msgs = st.session_state["chat_msgs"]

    head_col, reset_col = st.columns([5, 1])
    head_col.caption("Talk to VibeJudge. Ask for a vibe, then refine it: *\"a bit livelier\"*, "
                     "*\"no Gigi this time\"*, *\"now make it reggae\"*. Each follow-up adjusts your last "
                     "request, and the guardrail still checks every answer.")
    reset_col.button("New chat", on_click=reset_chat, width="stretch")

    prompt = st.chat_input("Describe a vibe, or refine the last one…")
    prompt = prompt or st.session_state.pop("chat_pending", None)
    if prompt:
        msgs.append({"role": "user", "text": prompt})
        with st.spinner("Thinking about your vibe..."):
            try:
                result, changes = st.session_state["chat_session"].send(prompt)
                msgs.append({"role": "assistant", "result": result, "changes": changes})
            except RequestRejected as exc:
                msgs.append({"role": "assistant", "error": str(exc)})

    if not msgs:
        with st.chat_message("assistant", avatar="🎧"):
            st.markdown("Hi! Tell me what you're in the mood for, and I'll find it in the catalog. "
                        "Then tell me what to change.")

    last_reply = max((i for i, m in enumerate(msgs) if m["role"] == "assistant"), default=-1)
    for i, m in enumerate(msgs):
        if m["role"] == "user":
            with st.chat_message("user", avatar="🙂"):
                st.markdown(m["text"])
            continue
        with st.chat_message("assistant", avatar="🎧"):
            if "error" in m:
                st.warning(m["error"])
                continue
            r = m["result"]
            if m["changes"]:
                st.markdown("**What I changed:** " + chips(m["changes"]), unsafe_allow_html=True)
            st.markdown(chips(describe_profile(r.prefs).split(", "), muted=True), unsafe_allow_html=True)
            for warning in r.parse_warnings:
                st.caption("ℹ️ " + warning)
            st.markdown(f"**{html.escape(r.explanation.intro)}**")
            if i == last_reply:
                guardrail_badge(r.guardrail)
                result_cards(r)
                st.caption("Quick follow-ups:")
                fcols = st.columns(len(FOLLOW_UPS))
                for j, f in enumerate(FOLLOW_UPS):
                    fcols[j].button(f, key=f"fu{i}_{j}", on_click=queue_chat, args=(f,), width="stretch")
            else:
                badge = {"verified": "✅", "corrected": "🛠️", "fallback": "🧩"}[r.guardrail.status]
                st.markdown(f"{badge} " + " · ".join(f"{s['title']} ({s['artist']})"
                                                   for s, _, _ in r.recommendations))


# ---------- Browse tab ----------

with browse_tab:
    songs = judge.songs
    f1, f2, f3 = st.columns([2, 2, 3])
    genres = f1.multiselect("Genre", sorted({s["genre"] for s in songs}))
    moods = f2.multiselect("Mood", sorted({s["mood"] for s in songs}))
    query = f3.text_input("Search title or artist").strip().lower()
    shown = [s for s in songs
             if (not genres or s["genre"] in genres) and (not moods or s["mood"] in moods)
             and (not query or query in s["title"].lower() or query in s["artist"].lower())]
    st.caption(f"Showing {len(shown)} of {len(songs)} songs")
    grid = st.columns(3, gap="medium")
    for i, song in enumerate(shown):
        with grid[i % 3]:
            with st.container(border=True):
                artwork(song["id"])
                st.markdown(f'<div class="vj-song">{html.escape(song["title"])}</div>'
                            f'<div class="vj-artist">{html.escape(song["artist"])}</div>', unsafe_allow_html=True)
                st.markdown(chips([song["genre"], song["mood"], f"energy {song['energy']:.2f}"]),
                            unsafe_allow_html=True)
                play_preview(song["id"])


# ---------- About tab ----------

with about_tab:
    st.markdown("""
**VibeJudge is a retrieval-augmented recommender.** Gemini never picks songs. It only reads your
request and explains songs that the scorer retrieved from the catalog.

1. **Input guardrail:** empty or oversized requests are rejected before any AI call.
2. **Understand:** Gemini turns your words into a taste profile (genre, mood, energy, sound, tags),
   limited to values that exist in the catalog. If Gemini is down, a keyword parser takes over.
3. **Retrieve:** the original VibeJudge scorer ranks all songs against that profile.
4. **Explain:** Gemini sees *only* the retrieved songs and explains why each one fits.
5. **Output guardrail:** invented songs, songs that weren't retrieved, and mentions of other
   catalog artists are removed and replaced with the scorer's own reasons.
""")
    results_path = ROOT / "eval_results.md"
    if results_path.exists():
        with st.expander("Latest evaluation results", expanded=False):
            st.markdown(results_path.read_text(encoding="utf-8"))
