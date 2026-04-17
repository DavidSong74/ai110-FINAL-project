# GoodVIBES 2.0 — AI Music Recommender

A rule-based music recommender **extended with a Gemini-powered explanation layer**. Given a user's mood, genre, and energy preferences, the system scores every song in its catalog, ranks them, and produces a natural-language explanation for each recommendation.

---

## Base Project

This project extends the **Module 3 Music Recommender Simulation** ([DavidSong74/ai110-module3show-musicrecommendersimulation-starter](https://github.com/DavidSong74/ai110-module3show-musicrecommendersimulation-starter)).

The original system represented songs and user taste profiles as structured data, then used a weighted scoring formula to rank songs against a user's preferred genre, mood, and energy level. It was built to demonstrate how a simple algorithm can produce surprisingly sensible recommendations without any machine learning, and to surface the failure modes that come with hard-coded rules and small catalogs.

This final project keeps that scoring logic intact and adds a Gemini API call after ranking — so instead of showing users a raw list of feature matches, the system now explains each recommendation in plain language.

---

## Architecture Overview

The full data flow is documented in [assets/system_diagram.md](assets/system_diagram.md). The short version:

A user profile (genre, mood, energy, tempo, etc.) enters the system alongside the 18-song CSV catalog. The scoring engine runs each song through a weighted formula and hands the top-k results to the Gemini API, which reads the score breakdown and returns a 1-2 sentence explanation. Everything gets logged to `logs/recommender.log`. A separate validation test asks Gemini to verify its own explanations against the score data and flags any contradictions.

Three places in the pipeline involve checking rather than generating: the unit test suite validates the scoring logic, the AI validation test checks explanation truthfulness, and the log file gives a human-readable audit trail for every API call.

---

## Setup

**Prerequisites:** Python 3.10+, a Google AI Studio API key (free tier at [aistudio.google.com](https://aistudio.google.com)).

```bash
# 1. Clone the repo
git clone https://github.com/DavidSong74/ai110-FINAL-project-1.git
cd ai110-FINAL-project-1

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Mac / Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env
```

**Run the recommender:**

```bash
python -m src.main
```

**Run the test suite:**

```bash
pytest
```

The test suite includes unit tests for the scoring logic and an AI validation test that checks whether Gemini's explanations are consistent with the actual score breakdown.

---

## Sample Interactions

### 1. High-Energy Pop

**Input profile:**
```
genre: pop | mood: happy | energy: 0.9 | tempo: 128 BPM
valence: 0.8 | danceability: 0.85 | acousticness: 0.1
```

**Output:**
```
#1  Sunrise City by Neon Echo
    Genre: pop  |  Mood: happy
    Score: 6.0
    Why:  "Sunrise City matches your profile on every axis — pop genre,
           happy mood, and energy right at your target. The tempo sits
           10 BPM away from your preference, which is close enough to
           feel natural."

#2  Gym Hero by Max Pulse
    Genre: pop  |  Mood: intense
    Score: 5.5
    Why:  "Gym Hero scores well on energy and danceability, but its mood
           is intense rather than happy, so it took a small penalty.
           If you want a harder-hitting pop track, this is the one."
```

The top result here scores a perfect 6.0 because every feature matched within threshold. The mood penalty on Gym Hero shows up correctly in the explanation.

---

### 2. Chill Lofi

**Input profile:**
```
genre: lofi | mood: chill | energy: 0.3 | tempo: 85 BPM
valence: 0.4 | danceability: 0.4 | acousticness: 0.7
```

**Output:**
```
#1  Library Rain by Paper Lanterns
    Genre: lofi  |  Mood: chill
    Score: 5.5
    Why:  "Library Rain fits a low-energy, acoustic listening session well.
           The mood and genre match, energy is close to your target, and
           the high acousticness lines up with your preference. Valence
           runs a bit high, but it's a minor gap."

#2  Midnight Coding by LoRoom
    Genre: lofi  |  Mood: chill
    Score: 5.5
    Why:  "Midnight Coding ties Library Rain on score. It matches mood and
           genre, sits close to your energy target, and has a similar
           acoustic feel. Danceability is slightly above your preference,
           but not enough to matter much."
```

Two songs tie at 5.5 here. The explanations do the work of distinguishing them rather than leaving the user to decode a raw score.

---

### 3. Mellow Metal Paradox (edge case)

**Input profile:**
```
genre: metal | mood: relaxed | energy: 0.2 | tempo: 70 BPM
acousticness: 0.9 | valence: 0.8
```

**Output:**
```
#1  Iron Horizon by Black Volt
    Genre: metal  |  Mood: rebellious
    Score: 0.5
    Why:  "Iron Horizon is the only metal song in the catalog, so genre
           gives it a point. But every other feature is the opposite of
           what you described — the energy is 0.96, the tempo is 172 BPM,
           and it is far from acoustic. This is a catalog gap, not a real
           match."
```

This is the most honest output the system produces. Genre forced a result, but the explanation correctly flags that nothing else aligned. A real recommender would surface this as a "no good matches found" state rather than returning a 0.5-score song.

---

## Design Decisions

The scoring formula uses hard thresholds rather than continuous distance functions. Energy must be within 0.15, tempo within 20 BPM, and so on. This was a deliberate choice for transparency: every threshold is visible in the code, and the explanation text can reference exact pass/fail decisions. The tradeoff is a cliff effect — a song 0.14 away from the energy target scores the same as a perfect match, while a song 0.15 away scores nothing. A smoother penalty curve would be more accurate but harder to explain to a non-technical user.

Mood mismatch subtracts 0.5 rather than scoring zero. The original starter code simply gave zero points for a mood miss. That let high-energy songs dominate results for users who asked for a completely different mood, because genre and energy matches swamped the absence of mood credit. The penalty flips mood from a "nice to have" into a real downside, which produces more intuitive rankings.

The Gemini explanation call happens after ranking, not during scoring. This keeps the two systems cleanly separated — if the API is unavailable, the recommender falls back to the raw reasons string and keeps running. Mixing the LLM into the scoring step would have made the system harder to test and harder to debug when something went wrong.

Gemini Flash was chosen over more capable models because the task is short and structured. The prompt already contains the score breakdown; Gemini's job is to restate it in natural language, not to reason over ambiguous data. A smaller, faster model handles this well and keeps API costs within the free tier.

---

## Testing Summary

Eleven user profiles were tested: four standard cases and seven adversarial ones designed to find the formula's edges.

The standard profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock) all produced results that matched human intuition. The top-ranked songs genuinely fit the described vibe, and changing one input meaningfully changed the output. That was the baseline confirmation that the formula works.

The adversarial profiles found four concrete problems. The "calm vs chill" mood mismatch showed that exact string matching silently ignores user intent — a user who types "calm" gets penalized on every lofi song because the dataset uses "chill." The Exact Boundary Energy test confirmed the cliff: a song with energy diff = 0.15 scores zero, not the partial credit a human would expect. The Impossible Tempo profile (300 BPM) revealed that tempo contributed nothing to any result, which is correct behavior but worth flagging because a real system should warn the user rather than silently ignoring their input. The Mellow Metal Paradox showed that genre matching can surface a single 0.5-score song when no real match exists, which feels like a false recommendation.

The AI validation test ran Gemini's explanations back through a verification prompt and measured how often the explanation accurately reflected the score breakdown. Two of 55 explanations failed: one for the Mellow Metal Paradox profile (the explanation overstated the match quality) and one for the Mood Mismatch profile (the explanation described a mood alignment that did not occur in the score). Both failures pointed to cases where Gemini was working from a score that itself was borderline — the LLM was not hallucinating so much as inheriting ambiguity from the scoring layer.

What worked well was the separation between the rule-based scorer and the AI explainer. When the explainer made a mistake, the log showed the score breakdown alongside the explanation, which made it straightforward to identify whether the problem was in the prompt, the score, or the model output. That separation also made writing targeted tests much easier.

---

## Reflection

Building this taught me that a system can follow its rules correctly and still produce wrong answers. When the Contradictory Energy+Mood profile returned upbeat pop songs for a user who asked for sad music, the algorithm was doing exactly what it was designed to do. The rules were the problem, not a bug. That distinction matters a lot when you're trying to improve something — debugging code and revising a scoring formula are different activities, and confusing them wastes time.

The Gemini integration added a layer I did not fully anticipate: the explanation quality is bounded by the score quality. When the score is wrong (like giving Iron Horizon a 0.5 for a relaxed listener), the explanation either faithfully describes a bad recommendation or drifts toward making it sound better than it is. The validation test caught two cases of the second kind, which is exactly what evaluation should do. But it also meant that fixing the explanation required fixing the score first, not tweaking the prompt.

The project also surfaced something about the gap between "it works" and "it's trustworthy." The recommender worked from the first run — it returned songs in a reasonable order. But it took eleven profiles and a separate validation pass to understand where it would fail on real users. Most of those failures were silent: a user who typed "calm" instead of "chill" would see results with no indication that their mood preference was ignored. Building the logging and the explanation layer made invisible failures visible. That feels like the actual engineering work, not the feature.

---

## Files

```
ai110-FINAL-project-1/
├── data/
│   └── songs.csv              # 18-song catalog with audio features
├── src/
│   ├── main.py                # CLI runner, 11 test profiles
│   └── recommender.py         # load_songs, score_song, recommend_songs, Gemini integration
├── tests/
│   └── test_recommender.py    # Unit tests + AI explanation validation
├── assets/
│   └── system_diagram.md      # Full architecture diagram
├── logs/
│   └── recommender.log        # Audit trail for all runs and API calls
├── model_card.md              # Algorithm details, bias analysis, evaluation
├── requirements.txt
└── README.md
```

---

## Demo

[Loom walkthrough — link to be added]

The walkthrough shows the system running all 11 profiles end-to-end, including the edge cases, and demonstrates how the Gemini explanation layer changes the output compared to the raw reasons string.
