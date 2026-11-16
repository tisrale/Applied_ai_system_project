# 🎧 Model Card: VibeJudge

This card has two parts. **Part A** covers **VibeJudge 2.0**, the applied AI system for my final project: Gemini plus retrieval plus guardrails. **Part B** is the original **VibeJudge 1.0** card from Module 3. That scorer is still inside 2.0 as the retrieval step, so its limitations still apply.

---

# Part A: VibeJudge 2.0 (AI system)

## A1. Model summary

| | |
|---|---|
| **Name** | VibeJudge 2.0 |
| **Type** | Retrieval-augmented recommender: LLM for language, rule-based scorer for ranking |
| **LLM** | Google Gemini `gemini-3.5-flash-lite` (free tier), temperature 0.2, JSON output mode |
| **Retriever** | VibeJudge 1.0 content-based scorer (Part B), unchanged |
| **Catalog** | 25 real songs in `data/songs.csv`, with 30-second previews from iTunes/Deezer |
| **Interfaces** | Streamlit web app (`app.py`), CLI (`src/ask.py`) |

You describe what you want in your own words. Gemini turns that into a taste profile, the scorer picks the 5 best songs from the catalog, and Gemini explains each pick. A guardrail then checks that the explanation only talks about those 5 songs.

## A2. Intended use

- **For:** a classroom demo of RAG and guardrails, and casual discovery within a small catalog ("what fits a rainy evening?").
- **Not for:** a real music service, filtering content for children (the explicit flag is hand-labeled, and only one song has it), or learning facts about songs or artists. Gemini is told to use only the catalog's attributes, which are estimates.

## A3. How the AI is used

There are two Gemini calls per request (three in chat follow-ups):

1. **Request → taste profile.** The prompt includes the exact genres, moods, tags, languages and artists in the catalog, and asks for JSON. Gemini can only *choose* from those values. `validate_profile` then snaps or removes anything else, clamps energy to 0–1, and turns things the catalog lacks into visible notes ("Not in the catalog: k-pop").
2. **Retrieved songs → explanation.** Gemini receives only the 5 retrieved songs, with their attributes and score reasons, and returns one reason per song as JSON.

3. **Chat follow-up → updated profile** (chat mode only). Gemini gets the current profile, the last picks and the follow-up, and returns the updated profile plus anything the listener wants left out. That goes through the same validation, and exclusions only count if the listener actually named them.

**Gemini never picks songs.** The ranking is fully done by the transparent scorer, so every recommendation can be reproduced and explained with points.

## A4. Guardrails and reliability

| Risk | Guardrail | Tested by |
|---|---|---|
| Empty, huge or nonsense input | `check_request`: rejects before any API call | `test_bad_requests_are_rejected`, eval case 13 |
| Gemini invents a song | output guardrail removes it; song cards come from the scorer anyway | `test_invented_song_is_removed`, `test_cards_never_include_hallucinated_songs` |
| Gemini talks about a catalog song it wasn't given | removed and reported | `test_catalog_song_that_was_not_retrieved_is_removed` |
| Gemini slips another artist into a reason | that reason is replaced with the scorer's own reason | `test_leaked_artist_in_reason_is_replaced` |
| Gemini skips a song | the scorer's reason fills the gap | `test_skipped_song_gets_scorer_reason` |
| Bad or oddly shaped JSON | template fallback; `[{...}]` is unwrapped | `test_invalid_json_falls_back_to_template`, `test_reply_wrapped_in_a_list_is_accepted` |
| Prompt injection ("ignore your rules…") | request framed as data; Gemini can't pick songs; output guardrail | eval case 12 (passed: catalog songs only, "Not in the catalog: Mulatu Astatke") |
| Chat: Gemini excludes songs the listener never mentioned | exclusions must be named in the message; others are ignored and logged | `test_exclusions_the_listener_did_not_name_are_ignored` |
| Chat: Gemini claims a change it didn't make | the "what changed" line is computed from the profile difference | `test_changes_are_computed_not_generated` |
| Gemini down, quota hit (429), overloaded (503) | one retry after Google's suggested delay (max 20s), then keyword parser + template text | `test_pipeline_survives_gemini_outage`, `test_retry_wait_honours_quota_errors` |

The app always shows which path was taken: ✅ **verified**, 🛠️ **corrected** (with a list of fixes), or 🧩 **fallback**. Every request is logged to `logs/vibejudge.log` (request, profile, picks, guardrail result, latency). The API key is never logged.

## A5. Evaluation

**Automated tests:** 56 pytest tests, all passing, with no API key or network (Gemini is replaced by `FakeGemini`).

**Scripted evaluation** (`src/evaluate.py`, 13 cases: 9 normal, 2 edge, 2 adversarial):

| Run | Passed | Guardrail results |
|---|---|---|
| Live Gemini | 13/13 | 11 verified, 1 fallback (Gemini 503), 1 rejected (empty request, as expected) |
| Offline (no Gemini) | 13/13 | all fallback, by design |

**Human evaluation:** I rated 8 live outputs on relevance and explanation quality (1–5). See [human_evaluation.md](human_evaluation.md).
Average **relevance 3.1/5**, average **explanation 4.5/5**. The explanations were consistently accurate and honest. The picks were only as good as the catalog: requests with one matching song (Spanish party, night drive) or a preference the genre bonus overrides (80s classics) scored 2/5 on relevance.

**What surprised me while testing reliability:**
- **The guardrail almost never had to fire on real outputs.** Gemini stayed inside the 5 songs it was given in every live run. The failures came from places I didn't expect: the *parser* adding preferences nobody asked for ("instrumental" for "calm Ethiopian jazz"), and Gemini saying Bob Marley wasn't in the catalog when One Love is.
- **The free tier is a reliability problem in itself.** My first full evaluation hit the 15-requests-per-minute limit halfway through. Without the fallback, 4 of the 13 cases would have crashed.
- **Gemini's JSON isn't always the shape you asked for.** Once it returned `[{...}]` instead of `{...}`, which the guardrail treated as invalid until I fixed it.
- **Gemini over-helps in chat.** Asked to "make it reggae", it also removed every previous pick and all ethio-jazz, which knocked out Jerusalem, a reggae song. The fix wasn't a better prompt alone: an exclusion now has to be named in the listener's message.
- **Some failures come from my tests, not the model.** "Romantic Amharic love songs" failed at first because Gemini treated *Amharic* as a language instead of a genre. That's a better reading, so I fixed the test, not the code, and noted that in `src/evaluate.py`.

## A6. Limitations and biases

- **The scorer's biases carry over** (Part B, section 6). Genre is worth +2.0, and other preferences are worth much less. For "80s classics for a road trip", Gemini picked rock + 1980s, and the genre points beat the decade points, so Mr. Brightside (2000s) ranked #1.
- **Gemini's reading is a single point of failure.** If it misreads the request, every pick is off. For "something to fall asleep to", it chose *electronic* sound, an odd choice the scorer then followed faithfully.
- **Explanations can sound more certain than the data.** Gemini says things like "a decent energy level of 0.63" as if that were measured. Every attribute was estimated by hand or by AI. Nafeken's energy changed from 0.45 to 0.63 based on a written description, and that moved it from #2 to #3 for my own profile.
- **Western-music bias in what Gemini knows.** Gemini knows Western artists far better than Ethiopian ones, so its "not in the catalog" notes and its reading of artist names are likely less reliable for Ethiopian music. I haven't tested requests written in Amharic script. The input guardrail accepts them, but I don't know how well Gemini reads them.
- **The guardrail can't catch omissions.** It checks *which* songs Gemini names, not what the reasons leave out. For "80s classics", the #1 reason never mentioned that Mr. Brightside isn't from the 80s. Every sentence was true, but the answer was still misleading.
- **Small, uneven catalog.** Most genres have one song, so many requests get one real match plus filler, and Gemini politely calls the filler "a looser fit."
- **One genre and one mood per request.** "Ethiopian jazz or reggae" can't be expressed.

## A7. Misuse and how it's prevented

- **Prompt injection** (making it recommend or say something else): the request is treated as data, Gemini can't choose songs, and the output guardrail removes anything outside the retrieved songs. Tested in the evaluation.
- **Spreading false information about songs:** reasons may only use the catalog's attributes. The prompt forbids invented lyrics, chart history and backstory. Fully guaranteeing that would need a fact-checker; the guardrail only checks song and artist names.
- **API key leaks:** the key lives in `.env` (gitignored) or Streamlit secrets, and is never printed or logged.
- **Using up the quota:** requests are capped at 300 characters, and retries are limited to one with a capped wait.
- **Privacy:** logs store request text. They stay on the local machine and are gitignored, but a real deployment would need consent and a retention limit.

## A8. Data changes in 2.0

- **Previews** (`data/previews.csv`): exact iTunes tracks chosen by hand, because automatic matches were sometimes wrong (a Clair de Lune *lullaby*, One Love *feat. Patoranking*). The Deezer songs (Kahine, Abayi) store track IDs, because Deezer preview links expire.
- **Song #24:** Becher Yider (Tewodros Tadesse) was replaced with **Nafeken (Gigi)**. The only playable recording of Becher Yider (YouTube) didn't play well, and I couldn't find it on Spotify. I chose the mood (nostalgic). Its energy (0.63) and *dramatic* tag came from a written description of the song (waltz rhythm, flute, soaring vocals). Part B still mentions Becher Yider, because it describes Module 3 results recorded before the swap.

## A9. AI collaboration

I built this with an AI coding assistant (Claude Code) and checked its work as I went.

- **A helpful suggestion:** letting the original scorer pick the songs and Gemini only *explain* them, with structured JSON, so a guardrail could check every title. That one design choice is why the app can't show an invented song, and it kept my Module 3 work at the center of the system.
- **A flawed suggestion:** the assistant first used the model name `gemini-flash-lite-latest` from my earlier projects, which now returns "not found". Later, while writing a filter for "not in the catalog" items, its first version would have hidden **k-pop**, because "pop" appears inside it. It caught that before running the code, but it showed me why every rule needs a test. Separately, another AI tool gave me a description of the Gigi songs that repeated my own catalog's numbers back to me as if they were facts.

> **DRAFT: written by my AI assistant from our work log. I need to check these examples and delete this line.**

## A10. Reflection

> **DRAFT: written by my AI assistant from what happened in this project. I need to rewrite it in my own words and delete this line.**

**What changed from Module 3.** In Module 3, I learned that a recommender only knows the labels and numbers it's given. This project taught me the other half: a language model is great with *words* but shouldn't be trusted as the *source of truth*. Gemini understood "calm Ethiopian jazz for a rainy evening" far better than my keyword rules ever could, but I didn't let it choose songs. Most of the design work was deciding where the AI gets to make a decision (reading the request, writing explanations) and where it doesn't (which songs exist, which ones rank highest).

**Where I had to be the human in the loop.**
- I chose the songs and found the right recordings. The automatic iTunes matches gave me a Clair de Lune lullaby and a One Love remake.
- I replaced Becher Yider when its recording didn't play well, and I chose Nafeken's mood myself.
- When another AI tool described my Gigi songs, I noticed it was repeating my own catalog's numbers back to me as if they were facts.
- I rated the outputs. My ratings showed something no automated test did: the explanations (4.5/5) were better than the picks (3.1/5).

**What surprised me.** I expected the guardrail to catch Gemini inventing songs. It almost never did, because Gemini stayed inside the songs it was given. The real problems were quieter: preferences nobody asked for, songs excluded that I never mentioned, and a true-but-incomplete reason for an "80s classic" from the 2000s. A system can pass every check and still mislead by leaving something out.

**What I'd build next.**
- More songs, especially Ethiopian music, so requests like mine have more than three real matches.
- Requests that can mix genres ("Ethio-jazz or reggae").
- A check for omissions: if I ask for the 80s and a pick isn't from the 80s, the reason should have to say so.
- Measured audio features instead of hand estimates.

---

# Part B: VibeJudge 1.0 (Module 3 scorer)

## 1. Model Name  

**VibeJudge 1.0**

It judges each song like a talent-show judge and hands you the top five.

---

## 2. Intended Use  

VibeJudge suggests 5 songs from a small catalog. You tell it your favorite genre, your mood, how much energy you want, and whether you like acoustic or electronic sound. It gives back the 5 best-matching songs, with the reasons for each one.

It assumes a few things about you:

- You have one favorite genre and one mood. (You can add optional extras: detailed mood tags, a decade, a language, hits vs. hidden gems, and no explicit songs.)
- You can describe your energy level as a number from 0 (calm) to 1 (intense).
- Your words match the catalog's labels exactly ("hip-hop", not "hip hop").

This is a classroom project for learning how recommenders work. It is not meant for real users. The catalog is tiny, and most of its numbers are estimates.

---

## 3. How the Model Works  

Think of the recommender as a judge at a talent show. Each song comes up on stage one at a time, the judge gives it points based on how well it fits your taste, and at the end the songs with the most points are your recommendations.

**What the judge knows about you.** You tell it four things: your favorite genre (like pop), the mood you want (like happy), how energetic you want the music to be on a scale from calm to intense, and whether you prefer acoustic or electronic sound.

**What the judge looks at in each song.** Every song in the catalog has a genre label, a mood label, an energy level, and a measure of how acoustic it sounds. The catalog also lists tempo, danceability, and how positive a song feels, but the judge ignores those for now. Tempo and danceability rise and fall almost exactly with energy in this catalog, so counting them too would reward energy three times over.

**How points are given.**

- **Right genre: 2 points.** This counts the most, because people usually describe their taste by genre first.
- **Right mood: 1 point.** Mood matters, but a song in your genre with a slightly different mood is usually a smaller miss than a song in the wrong genre.
- **Energy: up to 1 point.** The closer a song's energy is to what you asked for, the more points it gets. A perfect match earns the full point. The judge rewards being *close*, not being *high*: if you want calm music, a calm song beats a loud one.
- **Sound: up to half a point.** If you like acoustic music, more acoustic songs earn more. If you prefer electronic, the reverse. This is kept small so it mostly settles close calls.

A perfect song would score 4.5 points.

**Extras I added later.** All of these are optional, so the basic recipe above still gives the same results:

- **Extra preferences.** A profile can also ask for mood tags (+0.25 each, up to +0.75), a decade (+0.5), a language (+0.5), or hits vs. hidden gems (up to +0.5). The top score goes up to match, for example 5.25. "No explicit songs" isn't a penalty. It removes those songs completely.
- **Ranking modes.** The same rules with different points: genre-first, mood-first, and energy-focused. Each one still tops out at 4.5.
- **Diversity.** With `--diverse`, the judge picks the top 5 one at a time. A song loses points if its artist or genre is already on the list, and no list can have more than 2 songs from one artist or genre.

**Turning scores into recommendations.** Once every song has a score, the judge lines them up from highest to lowest and hands you the top five. If two songs tie, the one listed earlier in the catalog goes first. Each recommendation comes with its reasons, such as "genre match" and "energy similarity", so you can see exactly why it was picked.

**Changes from the starter.** The starter came with empty placeholder functions, so I wrote the loading, scoring, and ranking steps. I also added the acoustic-versus-electronic preference to the sample user in `main.py` (the starter's sample only had genre, mood, and energy), made matching ignore capital letters and extra spaces, and added a clear tie-breaking rule and a list of reasons for every recommendation.

---

## 4. Data  

The catalog is `data/songs.csv`. It has 25 songs.

- **Genres (18):** pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, classical, country, r&b, metal, reggae, edm, folk, latin, blues, and ethio-jazz.
- **Moods (16):** happy, chill, intense, relaxed, moody, focused, confident, peaceful, nostalgic, romantic, angry, uplifting, energetic, sad, festive, and melancholic.
- **Numbers for each song:** energy, tempo, valence (how happy it sounds), danceability, and acousticness.
- **Extended attributes (added later):**
  - `popularity`: 0–100, how well-known the song is.
  - `release_decade`: for example, 1980 for the 1980s.
  - `mood_tags`: 2–3 detailed moods, like "devotional;mystical;yearning" for Kahine.
  - `language`: english, amharic, spanish, instrumental, or multilingual.
  - `explicit`: true or false. Only HUMBLE. is explicit.

  Each one is scored only when a profile asks for it: shared mood tags (+0.25 each, up to +0.75), decade (+0.5, or +0.25 for a neighboring decade), language (+0.5), popularity or "hidden gems" (up to +0.5), and `allow_explicit=False`, which removes explicit songs entirely. Profiles that don't use them score exactly as before. Popularity and most decades are my estimates. Becher Yider (1980s) and Abayi (2000s) decades come from the sources I found. Kahine's decade is a guess. Popularity would be risky to score: my Ethiopian songs have the lowest values (20–30), so a popularity bonus would push them down even further.

**What I changed:**

- The starter had 10 made-up songs. I added 10 more, for 20.
- Then I replaced the made-up names with real songs that fit each row's genre and mood (for example, Snowman by WYS for a chill lofi song).
- I added 5 songs I actually listen to: One Love (Bob Marley), Kahine (My Priest) and Abayi (Gigi), Becher Yider (Tewodros Tadesse), and Jerusalem (Alpha Blondy).
- For Kahine, I turned a written description into numbers. "Traditional acoustic instruments" became high acousticness. "A rolling wave, not a dance" became low danceability.

**What's missing:**

- Most numbers are hand estimates, not measurements. Rows 1–20 still use the original made-up numbers.
- Most genres have only 1 song. Only lofi, reggae, and ethio-jazz have 3.
- There are no lyrics, languages, or cultural context. The system can't tell a prayer-like song from a love song.
- Tempo, valence, and danceability are in the file but aren't used for scoring.

---

## 5. Strengths  

- **Clear, simple tastes work well.** If you want one genre and one mood, and the catalog has those songs, the #1 pick is almost always right. Every normal profile got a #1 song that matched both its genre and its mood.
- **It matched my own taste at the top.** For my "My Taste (Gigi)" profile, it picked my top 3 in the exact order I would: Kahine, Becher Yider, then Abayi.
- **"Close" beats "high."** A calm listener gets calm songs, not the loudest ones. The Chill Lofi list is all slow, soft songs.
- **The top pick is stable.** When I changed the weights, the #1 song didn't change for any profile.
- **It explains itself.** Every song comes with its reasons, like "genre match (+2.0)." That made it easy to see why a song ranked where it did.

---

## 6. Limitations and Bias 

The biggest weakness I found is that the +2.0 genre bonus, combined with a profile that holds only one genre and one mood, traps users in a genre bubble, so the system can't follow a listener whose taste crosses genres. When I ranked my own top 5, the recommender matched my first three exactly (Kahine, Becher Yider, Abayi), but it put my #4 and #5, Alpha Blondy's "Jerusalem" (reggae) and John Denver's "Take Me Home, Country Roads" (country), at #16 and #12, because neither shares the ethio-jazz genre or the "peaceful" mood. It filled those spots with Clair de Lune and Blue in Green instead, songs I would not have picked. Even my weight-shift experiment, which halved the genre weight, did not move my two songs at all, which shows the problem is not just the weight but that a profile can only describe one kind of taste. Listeners with broad tastes, or whose favorite genre has only one song in the catalog, are served the worst.

**Other biases I found:**

- **Labels decide, not feelings.** My Ethio-Jazz songs feel chill to me, but they ranked #6 or lower for the Chill Lofi profile. The system only rewards the exact word "lofi." Music from cultures that don't use the catalog's labels gets pushed down.
- **Whoever labels the data shapes the results.** At first, my Ethiopian songs were all put under one made-up genre, "ethiopian." That's a country, not a genre. If I hadn't checked, the labels would have been wrong and the rankings with them.
- **"Middle" songs are favored.** Songs in the middle of the energy and acoustic scales fit "okay" for everyone. In a sweep of 2,880 simulated users, Adorn reached 36% of top-5 lists, while Kahine reached only 11% (`python -m src.bias_sweep`). Distinctive songs get recommended less.
- **Very calm and very intense listeners get less.** On average, a song earns 0.79 energy points for a user who wants 0.6, but only 0.42 for a user who wants 0.0. The calmest song in the catalog is 0.22, so a user who wants very quiet music can never get a perfect energy match.
- **Small genres get filler.** Lofi, reggae, and ethio-jazz have 3 songs each. Most genres have 1. A metal or rock fan gets one real match, and the rest of their list is just loud songs.
- **Acoustic taste barely counts.** It's yes-or-no and worth at most 0.5 points. Someone who likes both kinds of sound can't say so, and an acoustic metal fan still gets electronic songs.
- **Bad input isn't caught.** Energy above 1.0 gives a negative score. A missing mood or energy typed as text crashes the program. A user would get a broken result with no warning.

---

## 7. Evaluation  

**Profiles I tested.** I first ran 10 profiles through `python -m src.main`. Later I added 2 more to test the extended attributes: "My Taste+ (Mood Tags)" and "Clean Hip-Hop." The full output for all 12 is in the README.

- **Three normal profiles:** High-Energy Pop, Chill Lofi, and Deep Intense Rock.
- **One personal profile:** "My Taste (Gigi)" (ethio-jazz / peaceful / energy 0.4 / acoustic), built around songs I actually listen to.
- **Six adversarial profiles meant to trick the scoring:** conflicting preferences (sad mood with 0.9 energy), a genre that isn't in the catalog ("k-pop"), a spelling variant ("hip hop" vs "hip-hop"), an energy target outside 0–1 (1.5), an acoustic metal fan, and a classical fan who wants maximum energy.

**What I looked for.** For each profile I checked whether the #1 song made sense, whether the listed reasons matched the song's data, and what filled spots 2–5 when only one or two songs matched the genre.

**Comparison with my own taste.** I ranked my own top 5 and compared it with the My Taste results. The system matched my top 3 exactly, in the same order (Kahine, Becher Yider, Abayi), but missed my #4 and #5 (Jerusalem at #16, Take Me Home, Country Roads at #12). Under the Chill Lofi profile, my own "chill" songs ranked only #6 or lower, because they aren't labeled "lofi" or "chill."

**Sensitivity experiment.** I halved the genre weight (2.0 → 1.0) and doubled the energy weight (1.0 → 2.0). The maximum score stayed 4.5. The #1 song stayed the same for every profile; only spots 2–5 reshuffled. For my profile the change made the results different but not more accurate: the same 3 of my 5 songs made the top 5.

**What surprised me:**

- In "Energetic Classical," an EDM song (Levels) beat the only classical song, the one profile where the genre match lost.
- An energy target of 1.5 produced a *negative* energy score (−0.28) instead of an error.
- A handful of songs kept appearing as filler. Mr. Brightside showed up in 8 of the first 9 profiles' top 5. Across a sweep of 2,880 simulated users (every genre × mood × 5 energy levels × acoustic yes/no), Adorn, a song in the middle of both the energy and acoustic scales, reached 36% of users' top 5, while Kahine reached only 11%. You can reproduce this with `python -m src.bias_sweep`.

**Simple checks:**

- A profile missing `favorite_mood` crashes with a `KeyError`, and an energy value given as text (`"0.8"`) crashes with a `TypeError`.
- At first the two unit tests passed only by luck, because the `Recommender` class was still a placeholder that returned songs in file order. I finished the class so it uses the same scoring as `score_song`. Now the tests check the real ranking, and the class gives the same top 5 as `main.py` for all 12 profiles, in every ranking mode, with and without diversity.

### Comparing profiles side by side

Each pair below differs in only one or two settings, so comparing their top 5 shows what that setting actually does.

- **High-Energy Pop vs. Chill Lofi.** The two lists share no songs. Pop gets loud, electronic songs (Can't Stop the Feeling!, Bad Romance), and Lofi gets slow, soft, acoustic ones (Snowman, Weightless). That makes sense: the profiles are opposites on both energy (0.8 vs. 0.35) and sound (electronic vs. acoustic), so a song that fits one is a poor fit for the other.

- **Chill Lofi vs. Deep Intense Rock.** Lofi's top 3 are close (4.43, 4.29, 3.34) because the catalog has three lofi songs that all earn the genre bonus. Rock's #1 scores 4.44, but #2 drops to 2.44, because there is only one rock song and everything after it has to win on energy alone. The difference comes from the catalog, not the user: a lofi fan simply has more songs to choose from.

- **High-Energy Pop vs. Deep Intense Rock.** These share three songs (Bad Romance, Mr. Brightside, Can't Stop the Feeling!). Both users want loud, electronic music, so the same high-energy songs fit both. Only the genre and mood labels decide who gets which song at #1.

- **High-Energy Pop vs. Edge: Unknown Genre ("k-pop").** These profiles are identical except that "k-pop" isn't in the catalog. Without any genre bonus, Bad Romance falls from #2 to #4 and Electric Feel, the happy song, moves up to #2. This shows that Bad Romance's high spot for the pop fan comes almost entirely from its "pop" label.

- **Chill Lofi vs. My Taste (Gigi).** Both want calm, acoustic music, and both end with Blue in Green at #5. But the tops are completely different, because each profile's genre label pulls in its own songs. My Ethio-Jazz songs feel chill to me, yet under Chill Lofi they rank only #6 or lower, because the system matches the word "lofi," not the feeling.

- **Deep Intense Rock vs. Edge: Acoustic Metalhead.** Both want very loud music, and each gets its own genre's single song at #1 (Mr. Brightside, Master of Puppets). Asking for acoustic sound barely helps the metal fan: only Vivir Mi Vida, the one loud song that is also somewhat acoustic, moves up to #2. The acoustic preference is worth so few points that it only reorders songs that are already close.

- **Deep Intense Rock vs. Edge: Sad but Hyped.** Both ask for energy around 0.9. The rock fan gets a loud song at #1, but the sad folk fan gets Skinny Love, a quiet song with energy 0.30, because its "folk" and "sad" labels are worth 3 points and the energy miss costs only 0.6. After #1, both lists fill up with the same loud songs. Labels beat energy whenever they match.

- **Edge: Energy Out of Range vs. Edge: Energetic Classical.** Both are classical fans, and they differ in mood (peaceful vs. energetic) and energy (1.5 vs. 1.0). The peaceful fan still gets Clair de Lune at #1, even with a negative energy score, because genre + mood are worth 3 points. The energetic fan loses Clair de Lune to Levels (EDM), because Clair de Lune is calm and gets no mood match. One mood word flips the result.

- **Edge: Spelling Variant ("hip hop") vs. Edge: Unknown Genre ("k-pop").** One user made a small typo and the other asked for a genre that doesn't exist, but the system treats them exactly the same: neither gets any genre points, and neither gets a warning. HUMBLE. still wins for the "hip hop" fan, but only on its mood, scoring 2.44 instead of the 4.44 it would get with the right spelling.

### Why does "Bad Romance" keep showing up for someone who just wants happy pop?

Bad Romance (called "Gym Hero" in the starter data) is a pop song, but its mood is "intense," not "happy." You might expect a happy-pop fan to get happy songs first. Instead, it ranks #2 for them, ahead of Electric Feel, which is happy and has almost exactly the right energy.

Think of the recommender as a judge who reads the label on each song first. Bad Romance carries a "pop" label, and the judge gives 2 points for that, the biggest prize there is. Electric Feel's label says "indie pop," which the judge doesn't count as a match, so it only gets 1 point for being happy. Being loud and electronic also suits a high-energy pop fan, so Bad Romance picks up nearly full marks for energy and sound too. The result is that a workout song with the right label beats a happy song with a slightly different one.

Bad Romance also appears in 6 of the original 10 profiles' top 5, including the rock, metal, and classical ones. That's not because it fits those people well; it's one of the loudest, most electronic songs in the catalog, so it's the safest fallback for anyone who wants high energy and doesn't get a genre match.

---

## 8. Future Work  

- **Let users pick more than one genre and mood.** Then my profile could include ethio-jazz, reggae, and country, and Jerusalem and Country Roads could make my list.
- **Give partial credit for close labels.** "Indie pop" should count a little for a pop fan. "Hip hop" should match "hip-hop."
- **Use the data we already have.** Valence could tell a happy song from a sad one with the same energy.
- **Mix up the top 5.** *(Now built as `--diverse`: at most 2 songs per genre and 1 per artist in practice. See README Experiment 3.)* Next step: let users choose how much variety they want instead of on/off.
- **Check the input.** Energy outside 0–1, a missing mood, or text instead of a number should give a clear message, not a crash or a negative score.
- **Use better data.** More songs per genre, and measured numbers instead of guesses.
- **Explain misses, too.** Show "no genre match" when a song loses points, not just what it earned.

---

## 9. Personal Reflection  

**My biggest learning moment.** It was adding my own music. My songs felt "chill" to me, but the system ranked them #6 or lower for the Chill Lofi profile. It only knew the word "lofi," not the feeling. That's when I understood that a recommender doesn't know music. It only knows the labels and numbers we give it. I also saw that the data matters as much as the code. When I made Becher Yider's numbers softer, its rank changed.

**How AI tools helped, and when I had to double-check.** The AI assistant was fast at the heavy work. I chose the scoring rules, and it turned them into code. It also ran all 12 profiles, built comparison tables, and tested 2,880 simulated users to find biases. But it got things wrong when it guessed about my music:

- It listed Becher Yider under Teddy Afro. The real artist is Tewodros Tadesse.
- It put all my Ethiopian songs under one made-up genre, "ethiopian." I found sources that call them Ethio-Jazz.
- It guessed numbers for songs it had never heard. It can't listen to music, so its numbers were estimates. Even the numbers from another AI tool were just estimates.

So I learned to trust the AI with math and code, but to check facts about the real world myself. I also had to check my own work. When I tried the weight experiment, I edited a comment line instead of the real code, and nothing changed. The AI helped me find that.

**What surprised me.** The whole system is 4 simple rules that add up points. No learning, no magic. But it picked my top 3 songs in the exact order I would. That felt like it "knew" me. It didn't. My profile just described those songs very well. The reasons next to each song ("genre match +2.0") also make it feel smart, because it explains itself like a person would. But it's still just adding numbers.

**What I'd try next.**

- Let a user pick more than one genre and mood, so my reggae and country picks could show up too.
- Give partial points for close labels, like "indie pop" for a pop fan.
- Use valence, which is already in the data, to tell happy songs from sad ones.
- Get real measured numbers instead of guesses, and more songs per genre.
- Add more unit tests, like the tricky profiles that crash or score below zero.

Now I see music apps differently. When an app keeps showing me the same kind of song, it's not reading my mind. It's following labels and numbers someone chose, and those choices can leave out music that doesn't fit the labels.
