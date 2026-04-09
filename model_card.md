# Model Card: Music Recommender Simulation

## 1. Model Name

**GoodVIBES 1.0**

A context-aware music recommender that matches songs to a user's current mood, energy level, and genre preference.

---

## 2. Goal / Task

GoodVIBES tries to answer one question: given how a user feels right now and what kind of music they like, which songs in the catalog fit best?

It is designed for casual listeners who want context-aware suggestions — for example, someone who wants calm background music while studying, or high-energy tracks for a workout.

**Intended use:** Classroom exploration of how scoring-based recommenders work. Can be extended for real use cases with a larger catalog.

**Not intended for:** Large-scale production music apps, editorial playlist curation, or any situation where user privacy, fairness auditing, or catalog licensing matters. The system has no concept of song popularity, artist diversity, or listening history, so it should not be the sole input for real recommendations.

---

## 3. Algorithm Summary

The model scores every song in the catalog against the user's preferences, then returns the top 5 highest-scoring songs.

Here is how the scoring works, in plain language:

- If the song's genre exactly matches what the user asked for, it gets **1 point**.
- If the song's mood exactly matches what the user asked for, it gets **1 point**. If the mood is wrong, it loses **0.5 points**.
- If the song's energy level is close to what the user wants (within 0.15 on a 0–1 scale), it gets **2 points**. Energy carries the most weight because it most directly captures listening context (calm vs. intense).
- Valence, danceability, acousticness, and tempo each add **0.5 points** if they are close enough to the user's preference.
- The maximum possible score is **6.0**.

Songs are ranked from highest to lowest score. The explanation shown to the user lists exactly which features matched or mismatched.

One key change from the original starter logic: mood mismatches now subtract 0.5 points instead of simply scoring zero. This makes wrong-mood songs less likely to dominate the results just because they match genre and energy.

---

## 4. Data

- **Catalog size:** 18 songs
- **Genres represented:** pop, indie pop, lofi, rock, metal, ambient, jazz, synthwave, reggae, latin, classical, folk, house, blues, afrobeats (15 genres total)
- **Moods represented:** happy, chill, intense, focused, relaxed, moody, nostalgic, euphoric, cinematic, rebellious, dreamy, melancholic (12 mood labels)
- **Song features used:** genre, mood, energy (0–1), tempo in BPM, valence (0–1), danceability (0–1), acousticness (0–1)

**Dataset limits:**
- Most genres have exactly 1 song. Only lofi has 3 songs and pop has 2. This means genre matching acts more like a hard filter than a soft preference signal.
- The catalog skews toward high-energy songs. Nine of 18 songs have energy above 0.75. Only 2 songs fall in the mid-range energy band (0.5–0.65), so users who prefer moderate energy get fewer good matches.
- No lyrics, language data, artist popularity, release year, or listening history. The system only knows how a song sounds, not what it means.

---

## 5. Strengths

- **Clear, extreme preferences work well.** A user who wants high-energy pop or low-energy lofi gets intuitive, accurate results. The top-ranked songs genuinely match the described vibe.
- **Explanations are honest.** The "Why" text shows exactly which features matched and which did not. Users can see when the model rewarded energy but penalized mood, which builds trust.
- **Profile changes produce meaningful shifts.** Switching from pop to rock, or from high energy to low energy, reliably changes the top results. The system is sensitive to the inputs that matter.
- **Genre + mood agreement gives a strong signal.** When a user's genre and mood both match a song exactly, that song cleanly separates from the rest. For example, "High-Energy Pop" with mood "happy" gives Sunrise City a perfect 6.0 score.

---

## 6. Limitations and Bias

The system has a significant mood vocabulary filter bubble: the dataset uses 12 fixed mood labels (e.g., "chill", "intense", "euphoric"), but users expressing their preferences with natural language alternatives like "calm", "sad", or "angry" receive zero mood credit — or an active penalty of -0.5 — even when their intent closely matches an available mood. This silently disadvantages any user whose vocabulary does not exactly match the dataset's internal labels, with no indication to the user that their mood preference was ignored.

The energy scoring compounds this problem by using a hard binary threshold (the gap must be strictly less than 0.15). A song that is 0.14 away scores the same as a perfect match, while a song 0.15 away scores nothing. This creates an invisible cliff that particularly harms users who prefer mid-range energy levels (0.5–0.65), since only 2 of 18 songs fall in that range.

Together, these two biases create a filter bubble where users with nuanced or emotionally complex preferences — such as someone wanting sad but energetic music — consistently receive recommendations that match their genre label but contradict their actual emotional state.

Genre also carries a structural advantage: because most genres have only 1 song in the catalog, a genre match is essentially a hard filter down to a single song before numeric features even matter. This means catalog size amplifies scoring bias — a problem that would shrink with a larger, more diverse dataset.

---

## 7. Evaluation

I tested eleven user profiles covering a range of listening goals, including four standard profiles and seven adversarial/edge case profiles designed to expose weaknesses.

**Profiles tested:**
- High-Energy Pop, Chill Lofi, Deep Intense Rock (standard)
- Contradictory Energy+Mood (genre=pop, mood=sad, energy=0.9)
- Mellow Metal Paradox (genre=metal, energy=0.2)
- Mood Mismatch — "calm" vs "chill"
- Pop Fan Missing Indie Pop
- Exact Boundary Energy (diff = exactly 0.15)
- Ambiguous Mid-Range (all features at 0.5)
- Impossible Tempo (300 BPM)

**What I looked for:**
- Whether top results matched the intended vibe, not just individual feature values
- Whether the explanation text accurately reflected why each song scored as it did
- Whether changing one input meaningfully changed the output

**Key findings:**
- "Calm" vs "chill" vocabulary mismatch caused mood to score 0 across all lofi songs — confirmed by seeing `mood mismatch (-0.5)` on every result for that profile
- Energy diff of exactly 0.15 does not score — confirmed by the boundary test
- Tempo of 300 BPM contributed 0 points to every song — confirmed by Impossible Tempo profile where Storm Runner scored 5.5 instead of 6.0
- Doubling energy weight (from +1.0 to +2.0) and halving genre weight (from +2.0 to +1.0) made Rooftop Lights (indie pop) rise from #3 to #2 for the Pop Fan profile — showing the weight shift improved relevance

I did not use numeric accuracy metrics. I used side-by-side output comparisons to confirm that profile changes produced ranking changes that matched human intuition.

---

## 8. Ideas for Improvement

**1. Mood synonym mapping**
Before scoring, normalize user mood input against a known synonym table. For example: "calm" → "chill", "sad" → "melancholic", "angry" → "intense". This would eliminate the vocabulary filter bubble without changing the scoring logic itself.

**2. Continuous energy distance scoring**
Replace the hard threshold with a smooth penalty. For example: `energy_score = 2.0 × max(0, 1 - diff / 0.3)`. A perfect match still scores 2.0. A song 0.15 away scores about 1.0. A song 0.3 away scores 0. This removes the invisible cliff and rewards "close" more than "far away."

**3. Partial genre matching**
Give partial credit when the user's genre preference is a substring of the song's genre or vice versa. For example, a user who wants "pop" would get +0.5 (instead of 0) for a song labeled "indie pop." This directly fixes the Rooftop Lights problem.

**4. Expand the catalog**
With only 1 song per genre in most cases, genre matching is essentially a deterministic filter. Adding 5–10 songs per genre would allow energy, mood, and valence to actually differentiate results within a genre, which is where the system's real value would show.

---

## 9. Personal Reflection

**Biggest learning moment**

I expected the recommender to feel random or arbitrary at first. What surprised me was how logical — and how wrong — it could be at the same time. When "Contradictory Energy+Mood" returned upbeat pop songs for a user who wanted sad music, the model was following its rules perfectly. That moment made it clear that a system can be technically correct and behaviorally wrong at the same time. The rules themselves were the problem, not a bug in the code.

**How AI tools helped, and when I had to verify**

AI helped me generate adversarial test profiles I wouldn't have thought to try, like the exact-boundary energy test and the impossible tempo profile. Those revealed real edge cases. But I had to verify every claim by running the actual output — for example, the prediction that "calm" ≠ "chill" causing 0 mood points was something I had to confirm by reading the scores line by line. AI suggestions are hypotheses; running the code is the test.

**What surprised me about simple algorithms**

A 7-feature weighted sum with no machine learning still produces output that feels like a recommendation. When Sunrise City scored 6.0 for High-Energy Pop, it genuinely was the right song. That felt surprising because the logic is so transparent — no hidden layers, no embeddings, just addition. It made me realize that a lot of what feels "intelligent" in recommendation apps might be more about having a good dataset and well-chosen weights than about complex models.

**What I would try next**

I would replace the hard energy threshold with continuous distance scoring, add a mood synonym map, and test with a catalog of 200+ songs to see whether the genre dominance problem naturally shrinks when users have more options per genre. I would also add a diversity penalty to avoid returning 5 songs from the same artist or genre in a single recommendation set.
