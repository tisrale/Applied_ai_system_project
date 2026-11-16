# VibeJudge human evaluation

Eight requests were run through the full live system (Gemini `gemini-3.5-flash-lite`, balanced ranking, top 5) on 2026-11-16, with the **41-song catalog**.
Scores and notes were first suggested by my AI assistant from the outputs below. I reviewed them and agree with them.

**Relevance (1-5):** do the 5 songs fit what I asked for? 5 = all fit, 1 = none fit.  
**Explanation (1-5):** are Gemini's reasons accurate, specific and honest about weak picks? 5 = excellent, 1 = wrong or misleading.

## Ratings

| # | Request | Top 3 picks | Guardrail | Relevance | Explanation | My notes |
|---|---------|-------------|-----------|-----------|-------------|----------|
| 1 | calm Ethiopian jazz for a rainy evening | Kahine (My Priest), Tezeta (Nostalgia), Abayi | verified | 5/5 | 5/5 | Ethio-jazz on top, including the new Tezeta. One Man's Dream is a calm fit for rain. Honest that Nafeken is livelier. |
| 2 | songs to hype me up before a soccer match | Levels, Blinding Lights, Santorini | verified | 4/5 | 5/5 | All high energy. Santorini (new age) is an odd hype song, but the reason admits it's a surprise. |
| 3 | something to fall asleep to | Weightless, One Man's Dream, Clair de Lune | verified | 5/5 | 4/5 | All five are calm (before: Jerusalem and Adorn crept in). Two reasons just say "lower match score", which is vague. |
| 4 | sad but beautiful songs for a long night | Skinny Love, One Man's Dream, Clair de Lune | verified | 4/5 | 5/5 | Skinny Love and Tezeta fit well. One Man's Dream is beautiful but not really sad. |
| 5 | 80s classics for a road trip | Don't Stop Believin', Mr. Brightside, Blinding Lights | verified | 3/5 | 5/5 | Don't Stop Believin' is a great #1, but Take On Me and Billie Jean (real 80s songs) were missed because Gemini chose *rock*. This time the reasons do say Mr. Brightside is from the 2000s. |
| 6 | Spanish party music | Danza Kuduro, Vivir Mi Vida, Hips Don't Lie | verified | 4/5 | 5/5 | Big improvement (before: 2/5): Danza Kuduro, Vivir Mi Vida, Hips Don't Lie. Can't Stop the Feeling! at #5 doesn't fit. |
| 7 | moody music for a night drive through the city | Midnight City, Nightcall, Blinding Lights | verified | 4/5 | 5/5 | Big improvement (before: 2/5): Midnight City, Nightcall, Blinding Lights, Billie Jean. Santorini at #5 is weak, and the reason says so. |
| 8 | something like Gigi but more upbeat | Nafeken, Kahine (My Priest), Abayi | verified | 2/5 | 4/5 | Genre lock: Gemini chose ethio-jazz, so the upbeat Ethiopian songs (Checheho, Sebebu, Nin Deema) were never considered, and slow Tezeta made the list. |

**Averages:** Relevance **3.9/5** · Explanation **4.8/5**

**Before vs. after growing the catalog.** I first rated the same 8 requests on the 25-song catalog: relevance **3.1/5**, explanation **4.5/5**. Then I added 16 songs aimed at the weakest results (Ethiopian and Malian music, Latin party, 80s, night drive, sleep). Relevance rose to **3.9/5**. Spanish party and night drive went from 2/5 to 4/5. The code didn't change; the data did.

**What I noticed overall:** The explanations stay strong. Gemini is accurate and says "this is a looser fit" whenever a pick is weak, as the prompt asks. The remaining failures come from the **genre bonus**. For "something like Gigi but more upbeat", Gemini picked *ethio-jazz*, so upbeat Ethiopian songs filed under afro-pop and r&b were never considered. One culture's music spread across several genre labels gets walled off by the +2.0 genre points. Omissions are **inconsistent**: in the first run, the "80s classics" reasons never said Mr. Brightside was from the 2000s. In this run they did. The guardrail can't catch either case.

## Full outputs

### 1. "calm Ethiopian jazz for a rainy evening"
Read as: *ethio-jazz, peaceful, energy 0.2, acoustic, tags: calm/cozy/mellow* (parsed by gemini) · guardrail: **verified** · 2.8s  

> Here is a cozy selection of ethio-jazz and peaceful tracks tailored for your rainy evening, blending mellow acoustic sounds and low energy levels.

1. **Kahine (My Priest)** (Gigi), match 4.28/5.25: This track matches your peaceful mood and ethio-jazz genre preference with a close energy level and high acousticness.
2. **Tezeta (Nostalgia)** (Mulatu Astatke), match 3.33/5.25: It fits your ethio-jazz preference well, offering a very close energy match and a high acoustic sound.
3. **Abayi** (Gigi), match 3.05/5.25: While it brings the right ethio-jazz genre and a decent acoustic sound, its energy is a bit higher, making it a moderately good fit.
4. **Nafeken** (Gigi), match 2.90/5.25: This song is a looser fit because its energy level is significantly higher than what you requested, though it maintains the ethio-jazz genre.
5. **One Man's Dream** (Yanni), match 2.48/5.25: This is a looser fit since it is new age rather than ethio-jazz, but it matches your peaceful mood and low energy request.

### 2. "songs to hype me up before a soccer match"
Read as: *energetic, energy 0.9, electronic, tags: energetic/driving/intense* (parsed by gemini) · guardrail: **verified** · 2.8s  

> Here is a high-energy set to get you pumped up and ready for your soccer match, featuring a mix of strong electronic vibes, driving rhythms, and intense anthems.

1. **Levels** (Avicii), match 2.69/3.25: It is a fantastic match for your hype-up session with a soaring energy of 0.95 and euphoric, energetic tags that fit your electronic taste profile perfectly.
2. **Blinding Lights** (The Weeknd), match 2.65/3.25: This synthwave track hits the mark with an energetic mood, an energy level of 0.82, and driving tags that will keep your momentum high.
3. **Santorini** (Yanni), match 2.60/3.25: Though it is a new age instrumental from the 1980s, its high energy of 0.85 and cinematic, driving tags make it a surprisingly solid fit.
4. **Mr. Brightside** (The Killers), match 1.69/3.25: This is a looser fit since it leans toward rock rather than purely electronic, but its intense energy of 0.91 and driving tags still deliver a strong anthem for motivation.
5. **Master of Puppets** (Metallica), match 1.67/3.25: This metal track is another looser fit due to its angry mood and aggressive tag, but its heavy energy of 0.97 will certainly get your adrenaline pumping.

### 3. "something to fall asleep to"
Read as: *ambient, peaceful, energy 0.1, electronic, tags: calm/dreamy, instrumental* (parsed by gemini) · guardrail: **verified** · 2.7s  

> Here is a carefully selected peaceful set designed to help you drift off to sleep easily. Every track here features a low energy level and a calming, instrumental sound.

1. **Weightless** (Marconi Union), match 3.61/5.50: This ambient track is a strong match for your request with its calm, meditative tags, floating mood, and instrumental language.
2. **One Man's Dream** (Yanni), match 2.67/5.50: This peaceful new age piece fits your need for tranquility with its dreamy mood tags and low energy level.
3. **Clair de Lune** (Claude Debussy), match 2.65/5.50: Matching your peaceful mood and low energy request, this classical piece offers tender, dreamy instrumental sounds.
4. **Kahine (My Priest)** (Gigi), match 1.82/5.50: This is a looser fit since it has a lower match score, but it shares a peaceful mood and low energy level.
5. **Reflections of Passion** (Yanni), match 1.65/5.50: This is a looser fit for your sleep request due to its lower match score, though it features a dreamy mood and instrumental style.

### 4. "sad but beautiful songs for a long night"
Read as: *sad, energy 0.2, acoustic, tags: melancholic/dreamy/heartbroken* (parsed by gemini) · guardrail: **verified** · 2.3s  

> Here is a thoughtful selection of sad and beautiful tracks to accompany your long night, ranging from intimate folk to peaceful classical and jazz.

1. **Skinny Love** (Bon Iver), match 2.61/3.25: It is a fantastic match for your sad mood, hitting your exact energy level with its raw, heartbroken tags.
2. **One Man's Dream** (Yanni), match 1.73/3.25: This instrumental piece matches your low energy preference and brings in a dreamy, tranquil vibe for the night.
3. **Clair de Lune** (Claude Debussy), match 1.71/3.25: Though a slightly looser fit overall, its acoustic sound and dreamy mood tags match your requested nighttime aesthetic well.
4. **Tezeta (Nostalgia)** (Mulatu Astatke), match 1.57/3.25: This is a looser fit for your specific mood, but it brings a melancholic feeling and acoustic sound to the mix.
5. **Blue in Green** (Miles Davis), match 1.53/3.25: This acts as a looser fit, yet its melancholic tags and acoustic qualities still suit a late-night listening session.

### 5. "80s classics for a road trip"
Read as: *rock, energetic, energy 0.8, electronic, tags: anthemic/driving/nostalgic, english, 1980s* (parsed by gemini) · guardrail: **verified** · 3.1s  

> Buckle up for your road trip with this high-energy mix of anthemic rock and electronic sounds spanning the decades, led by our 1980s classics.

1. **Don't Stop Believin'** (Journey), match 4.88/6.25: This 1980s English rock track fits your road trip with a strong match score of 4.88, delivering the exact uplifting, anthemic, and nostalgic vibe you asked for.
2. **Mr. Brightside** (The Killers), match 4.34/6.25: Although it is from the 2000s rather than the 80s, this English rock song brings a driving, anthemic energy and high electronic sound that matches your taste profile.
3. **Blinding Lights** (The Weeknd), match 3.46/6.25: Hailing from the 2010s, this synthwave track is a slightly looser fit for an 80s-specific request, but its driving, nostalgic tags and high energy fit the road trip vibe well.
4. **Santorini** (Yanni), match 3.10/6.25: This is a looser fit since it is a new age instrumental track from the 1980s, but it still delivers the high energy and driving mood you need for the highway.
5. **Levels** (Avicii), match 2.84/6.25: This is a looser fit as a 2010s EDM track rather than an 80s classic, but it compensates with a high energy level and electronic sound to keep you moving.

### 6. "Spanish party music"
Read as: *latin, festive, energy 0.8, electronic, tags: festive/danceable/energetic, spanish* (parsed by gemini) · guardrail: **verified** · 2.5s  

> Get ready for an energetic celebration with these festive Spanish tracks and danceable beats that match your party vibe perfectly!

1. **Danza Kuduro** (Don Omar), match 5.33/5.75: It is a fantastic match with its high energy of 0.92, joyful Spanish lyrics, and festive electronic sound that will get everyone dancing.
2. **Vivir Mi Vida** (Marc Anthony), match 4.89/5.75: This fits your request wonderfully with its festive Latin style, Spanish language, and high energy level of 0.86.
3. **Hips Don't Lie** (Shakira), match 4.88/5.75: It brings a great Latin groove with high energy and danceable festive tags, though it features English language rather than Spanish.
4. **Checheho** (Aster Aweke), match 2.77/5.75: This is a looser fit since it is an afro-pop song in Amharic, but it still shares your requested festive mood and high energy.
5. **Can't Stop the Feeling!** (Justin Timberlake), match 1.64/5.75: This is a much looser fit as a pop song in English, though it does match your high energy and danceable taste profile.

### 7. "moody music for a night drive through the city"
Read as: *synthwave, moody, energy 0.6, electronic, tags: driving/dark* (parsed by gemini) · guardrail: **verified** · 2.4s  

> Here is a moody synthwave and electronic soundtrack tailored for your late-night drive through the city lights.

1. **Midnight City** (M83), match 4.54/5.00: This synthwave track hits your moody vibe with an energy level of 0.78, featuring driving and cinematic tags that match your request.
2. **Nightcall** (Kavinsky), match 4.49/5.00: As a synthwave song with a moody feel and dark tags, it captures the exact mysterious atmosphere you need for a night drive.
3. **Blinding Lights** (The Weeknd), match 3.51/5.00: While it leans energetic rather than strictly moody, its synthwave style and driving tags still make it a strong match for your route.
4. **Billie Jean** (Michael Jackson), match 2.85/5.00: This is a looser fit because it belongs to the pop genre rather than synthwave, but it still shares your desired moody mood and dark driving tags.
5. **Santorini** (Yanni), match 1.40/5.00: This is a much looser fit since it is an instrumental new age track, though it shares some energy similarity and driving tags.

### 8. "something like Gigi but more upbeat"
Read as: *ethio-jazz, energetic, energy 0.8, acoustic, tags: energetic/danceable/groovy* (parsed by gemini) · guardrail: **verified** · 2.0s  

> Since you like Gigi and are looking for something more upbeat, I've gathered some ethio-jazz tracks along with a high-energy wildcard to match your taste profile.

1. **Nafeken** (Gigi), match 3.16/5.25: By Gigi herself, this ethio-jazz track has a solid energy of 0.63 and an acoustic sound, making it a good fit for your request.
2. **Kahine (My Priest)** (Gigi), match 2.97/5.25: This is another ethio-jazz track by Gigi, though its lower energy of 0.35 means it is a looser fit for your upbeat request.
3. **Abayi** (Gigi), match 2.95/5.25: Also by Gigi, this ethio-jazz song has an energy of 0.45, placing it as a somewhat looser fit for what you are looking for.
4. **Tezeta (Nostalgia)** (Mulatu Astatke), match 2.83/5.25: This ethio-jazz instrumental by Mulatu Astatke has an energy of 0.25, so it is a looser fit for an upbeat vibe.
5. **Levels** (Avicii), match 2.11/5.25: While not ethio-jazz, this edm track by Avicii matches your high energy of 0.95 and energetic mood tags.
