# VibeJudge human evaluation

Eight requests were run through the full live system (Gemini `gemini-3.5-flash-lite`, balanced ranking, top 5) on 2026-11-15.
I listened to the picks and rated each output myself.

> **DRAFT: suggested scores written by my AI assistant from the outputs below. Before submitting, I need to listen, change any score I disagree with, and delete this line.**

**Relevance (1-5):** do the 5 songs fit what I asked for? 5 = all fit, 1 = none fit.  
**Explanation (1-5):** are Gemini's reasons accurate, specific and honest about weak picks? 5 = excellent, 1 = wrong or misleading.

## Ratings

| # | Request | Top 3 picks | Guardrail | Relevance | Explanation | My notes |
|---|---------|-------------|-----------|-----------|-------------|----------|
| 1 | calm Ethiopian jazz for a rainy evening | Kahine (My Priest), Abayi, Nafeken | verified | 5/5 | 5/5 | All three Gigi songs on top, then calm acoustic filler. Honest that Nafeken is livelier. |
| 2 | songs to hype me up before a soccer match | Levels, Mr. Brightside, Bad Romance | verified | 4/5 | 5/5 | Every pick is high energy and good for hype. Only one EDM match; the rest are filler, and the reasons say so. |
| 3 | something to fall asleep to | Weightless, Clair de Lune, Kahine (My Priest) | verified | 3/5 | 4/5 | Top 3 are good for sleep, but Jerusalem (0.60) and Adorn don't fit. Gemini read sleep as *electronic*, an odd parse. |
| 4 | sad but beautiful songs for a long night | Skinny Love, Snowman, Blue in Green | verified | 4/5 | 5/5 | Skinny Love is perfect, and Blue in Green and Clair de Lune fit. Reasons name the real tags (heartbroken, melancholic). |
| 5 | 80s classics for a road trip | Mr. Brightside, Levels, Master of Puppets | verified | 2/5 | 3/5 | Only Master of Puppets and Red Red Wine are from the 80s. #1 Mr. Brightside is from the 2000s, and the reason doesn't say so: misleading by omission. |
| 6 | Spanish party music | Vivir Mi Vida, Can't Stop the Feeling!, Levels | verified | 2/5 | 5/5 | Only one Latin/Spanish song exists in the catalog. The rest are English pop/EDM, and every reason admits it. |
| 7 | moody music for a night drive through the city | Nightcall, Bad Romance, Mr. Brightside | verified | 2/5 | 4/5 | Nightcall is a perfect #1, but the catalog has nothing else moody/synth. Reasons are honest. |
| 8 | something like Gigi but more upbeat | Nafeken, Kahine (My Priest), Abayi | verified | 3/5 | 5/5 | Nafeken correctly first (the most upbeat Gigi song). Kahine and Abayi aren't upbeat, and Levels isn't like Gigi. Reasons are honest about both. |

**Averages:** Relevance **3.1/5** · Explanation **4.5/5**

**What I noticed overall:** The explanations are much stronger than the picks. Gemini was accurate and honest in almost every reason, saying "this is a looser fit" whenever a pick was weak, as the prompt asks. Relevance drops whenever the catalog has only one song for the request (Spanish party, night drive) or when the genre bonus beats another preference (80s classics). The biggest problem the guardrail can't catch is **omission**: for "80s classics", Gemini never said Mr. Brightside isn't from the 80s. The guardrail checks *which* songs are named, not whether the reasons leave out something important.

## Full outputs

### 1. "calm Ethiopian jazz for a rainy evening"
Read as: *ethio-jazz, peaceful, energy 0.2, acoustic, tags: calm/cozy/mellow* (parsed by gemini) · guardrail: **verified** · 3.0s  

> Here is a cozy selection of ethio-jazz and atmospheric tracks to match your rainy evening. These picks lean into peaceful moods, acoustic textures, and mellow vibes.

1. **Kahine (My Priest)** (Gigi), match 4.28/5.25: This ethio-jazz track is a strong match with its peaceful mood, acoustic sound, and low energy that fits right into a calm evening.
2. **Abayi** (Gigi), match 3.05/5.25: With its ethio-jazz style and acoustic elements, this song brings a nostalgic and flowing atmosphere to your rainy night.
3. **Nafeken** (Gigi), match 2.90/5.25: This is a slightly looser fit with a higher energy level, but it still delivers the ethio-jazz genre and acoustic warmth you are looking for.
4. **Clair de Lune** (Claude Debussy), match 2.46/5.25: This is a looser fit because it strays from the ethio-jazz genre, but its peaceful mood and very low energy make it a tranquil addition to the rain.
5. **Snowman** (WYS), match 1.78/5.25: This is a looser fit since it is lofi rather than ethio-jazz, but its cozy tags and mellow energy help complete your rainy evening background.

### 2. "songs to hype me up before a soccer match"
Read as: *edm, energetic, energy 0.9, electronic, tags: energetic/driving* (parsed by gemini) · guardrail: **verified** · 2.5s  

> Here is a high-energy set to get you ready for your soccer match, featuring a mix of strong EDM tracks and some looser fits.

1. **Levels** (Avicii), match 4.69/5.00: This EDM track is a fantastic fit with an energetic mood and high energy level of 0.95, plus euphoric and uplifting tags that will get you pumped.
2. **Mr. Brightside** (The Killers), match 1.69/5.00: This is a looser fit since it is a rock song, but its high energy and driving mood tag still match your requested vibe.
3. **Bad Romance** (Lady Gaga), match 1.44/5.00: This pop song is a looser fit due to its intense mood, but it makes the list thanks to its high energy level of 0.93.
4. **Master of Puppets** (Metallica), match 1.42/5.00: As a metal song, this is a looser fit, but it delivers on your energy needs with an intense energy score of 0.97.
5. **Can't Stop the Feeling!** (Justin Timberlake), match 1.33/5.00: This is a looser fit because it is a happy pop track, though it still provides a solid energy level of 0.82 to keep things moving.

### 3. "something to fall asleep to"
Read as: *ambient, peaceful, energy 0.1, electronic, tags: calm/peaceful/meditative* (parsed by gemini) · guardrail: **verified** · 2.3s  

> Here is a gentle selection of tracks to help you drift off, blending calming ambient sounds with peaceful melodies.

1. **Weightless** (Marconi Union), match 3.36/5.25: It is a great match for your profile because it is an ambient, instrumental track featuring calm and meditative tags.
2. **Clair de Lune** (Claude Debussy), match 1.90/5.25: This classical piece fits your peaceful mood well, featuring a low energy level that suits sleep.
3. **Kahine (My Priest)** (Gigi), match 1.82/5.25: This ethio-jazz track has a peaceful mood and low energy, though it is a slightly looser fit for your electronic preference.
4. **Jerusalem** (Alpha Blondy), match 1.07/5.25: This is a looser fit for your sleep request since it has a higher energy level, but it does include a peaceful mood tag.
5. **Adorn** (Miguel), match 0.92/5.25: This is a much looser fit for your request, as it leans toward an R&B genre with higher energy than your ideal taste profile.

### 4. "sad but beautiful songs for a long night"
Read as: *sad, energy 0.2, acoustic, tags: melancholic/wistful/heartbroken* (parsed by gemini) · guardrail: **verified** · 2.7s  

> Here is a carefully selected mix of sad and beautiful tracks to accompany you through a long night, blending heartbroken vocals with tender instrumentals.

1. **Skinny Love** (Bon Iver), match 2.61/3.25: This track is a strong match for your taste profile, featuring a sad mood, raw acoustic sound, and the heartbroken tag you were looking for.
2. **Snowman** (WYS), match 1.53/3.25: This is a looser fit since it leans toward a chill mood rather than outright sadness, but it brings in the wistful tag you requested with a cozy acoustic sound.
3. **Blue in Green** (Miles Davis), match 1.53/3.25: A looser fit because of its relaxed mood, yet it captures the melancholic tag you wanted through a deeply tender and acoustic jazz performance.
4. **Clair de Lune** (Claude Debussy), match 1.46/3.25: This classical piece is a looser fit with its peaceful mood, but its extremely high acousticness and quiet energy make it a fitting backdrop for the night.
5. **Weightless** (Marconi Union), match 1.38/3.25: A looser fit driven by a chill ambient mood, yet it shares your desired low energy level and high acoustic sound for a calming late-night listen.

### 5. "80s classics for a road trip"
Read as: *rock, energetic, energy 0.8, electronic, tags: driving/anthemic/energetic, english, 1980s* (parsed by gemini) · guardrail: **verified** · 2.7s  

> Here is a high-energy road trip selection featuring a mix of driving beats and classic decades.

1. **Mr. Brightside** (The Killers), match 4.34/6.25: It has an intense rock genre and energetic driving tags that match your road trip vibe well.
2. **Levels** (Avicii), match 3.09/6.25: This track brings high electronic energy and uplifting moods to keep you moving.
3. **Master of Puppets** (Metallica), match 2.31/6.25: Released in the 1980s with English language lyrics, it hits your requested era with very high energy.
4. **Red Red Wine** (UB40), match 2.05/6.25: This is a looser fit since it comes from the 1980s and is in English, but has a much lower energy score and a reggae genre.
5. **HUMBLE.** (Kendrick Lamar), match 1.92/6.25: This is a looser fit as a hip-hop track, though it shares a similar energy level to your target profile.

### 6. "Spanish party music"
Read as: *latin, festive, energy 0.8, electronic, tags: festive/danceable/energetic, spanish* (parsed by gemini) · guardrail: **verified** · 1.9s  

> Here is a selection of tracks tailored for your Spanish party music request, bringing high energy and festive vibes.

1. **Vivir Mi Vida** (Marc Anthony), match 4.89/5.75: It is a fantastic match for your taste profile, featuring a latin genre, festive mood, spanish language, and an energy level of 0.86.
2. **Can't Stop the Feeling!** (Justin Timberlake), match 1.64/5.75: This is a looser fit since it is a pop track in English, but it shares your desired energy and includes danceable tags.
3. **Levels** (Avicii), match 1.59/5.75: This is a looser fit because it is an English edm track, though it matches your energy preference and has energetic tags.
4. **HUMBLE.** (Kendrick Lamar), match 1.42/5.75: This is a looser fit as a hip-hop track in English, but it comes close to your target energy level.
5. **Bad Romance** (Lady Gaga), match 1.34/5.75: This is a looser fit since it is an intense English pop song, though it does offer high energy.

### 7. "moody music for a night drive through the city"
Read as: *synthwave, moody, energy 0.6, electronic, tags: driving/dark* (parsed by gemini) · guardrail: **verified** · 2.5s  

> Here is a hand-picked selection for your moody night drive through the city, featuring a strong electronic sound and dark tags.

1. **Nightcall** (Kavinsky), match 4.49/5.00: This is a fantastic match for your request with its synthwave genre, moody vibe, dark tags, and cinematic feel.
2. **Bad Romance** (Lady Gaga), match 1.40/5.00: This is a looser fit because its pop genre and intense mood stray a bit, though it shares the dark tags and electronic sound.
3. **Mr. Brightside** (The Killers), match 1.39/5.00: This is a looser fit since it is a rock song with an intense mood, but it does include the driving tag you wanted.
4. **Master of Puppets** (Metallica), match 1.36/5.00: This is a looser fit as a metal track with an angry mood, though it does feature dark tags and high energy.
5. **Jerusalem** (Alpha Blondy), match 1.32/5.00: This is a looser fit because it falls under reggae with an uplifting and peaceful mood rather than a moody electronic style.

### 8. "something like Gigi but more upbeat"
Read as: *ethio-jazz, energetic, energy 0.8, acoustic, tags: energetic/groovy/uplifting* (parsed by gemini) · guardrail: **verified** · 2.5s  

> Since you are looking for something like Gigi but with a more upbeat feel, I've put together a mix of her own tracks along with some higher-energy additions.

1. **Nafeken** (Gigi), match 3.16/5.25: This is by Gigi in the ethio-jazz genre, giving you that familiar sound with a decent energy level of 0.63 and an acoustic feel.
2. **Kahine (My Priest)** (Gigi), match 2.97/5.25: Another track by Gigi in the ethio-jazz style, though it has a lower energy of 0.35, making it a looser fit for your upbeat request.
3. **Abayi** (Gigi), match 2.95/5.25: This song is also by Gigi in the ethio-jazz genre, but its energy is down at 0.45, so it's another looser fit for an energetic vibe.
4. **Levels** (Avicii), match 2.36/5.25: With an edm genre and a high energy of 0.95, this brings the energetic and uplifting mood you asked for, though it is a very different style from Gigi.
5. **Electric Feel** (MGMT), match 1.39/5.25: This indie pop track hits closer to your requested energy with a 0.76 rating and features groovy tags, but it's a looser fit overall compared to the Gigi tracks.
