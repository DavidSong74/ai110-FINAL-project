# GoodVIBES 2.0 — AI Music Recommender

A rule-based music recommender with a Gemini explanation layer on top. You give it a mood, genre, and energy preference; it scores every song in the catalog, ranks them, and writes a short plain-English reason for each pick.

---

## Base Project

This project extends the **Module 3 Music Recommender Simulation** ([DavidSong74/ai110-module3show-musicrecommendersimulation-starter](https://github.com/DavidSong74/ai110-module3show-musicrecommendersimulation-starter)).

The original system stored songs and user taste profiles as structured data and used a weighted scoring formula to rank songs by genre, mood, and energy. It was built to show how a simple algorithm can produce sensible recommendations without any machine learning, and to find the failure modes that come with hard-coded rules and a small catalog.

This version keeps that scoring logic and adds a Gemini API call after ranking. Instead of outputting a raw list of feature matches, it now explains each recommendation in plain language.

---

## Architecture Overview

The full data flow is in [assets/system_diagram.md](assets/system_diagram.md). Briefly:

A user profile (genre, mood, energy, tempo, etc.) enters alongside the 18-song CSV catalog. The scoring engine runs each song through a weighted formula and passes the top-k results to Gemini, which reads the score breakdown and returns a 1-2 sentence explanation. Every call gets logged to `logs/recommender.log`. A separate validation test sends those explanations back to Gemini to check whether they match the actual score data, and flags any contradictions.

Checking happens in three places: the unit tests validate scoring logic, the AI validation test checks explanation accuracy, and the log file records every API call for manual review.

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

The test suite covers scoring logic with unit tests and runs an AI validation check that asks Gemini whether its own explanations match the score data.

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
  #1  Sunrise City — Neon Echo
       Genre: pop  |  Mood: happy
       Score: 6.0 / 6.0
       Why:   Sunrise City matches every feature you described — pop genre,
              happy mood, and energy right at your target of 0.9. Tempo,
              valence, danceability, and acousticness all fall within threshold.

  #2  Gym Hero — Max Pulse
       Genre: pop  |  Mood: intense
       Score: 4.5 / 6.0
       Why:   Gym Hero matches on genre, energy, and most numeric features,
              but its mood is intense rather than happy, which costs it 0.5
              points. It's the right sound at the wrong emotional register.
```

Sunrise City scores a perfect 6.0 because every feature matched within threshold. Gym Hero drops to 4.5 because of the mood mismatch penalty — the system treats mood as a real signal, not just a tiebreaker.

---

### 2. Chill Lofi

**Input profile:**
```
genre: lofi | mood: chill | energy: 0.3 | tempo: 85 BPM
valence: 0.4 | danceability: 0.4 | acousticness: 0.7
```

**Output:**
```
  #1  Library Rain — Paper Lanterns
       Genre: lofi  |  Mood: chill
       Score: 6.0 / 6.0
       Why:   Library Rain hits every feature — lofi genre, chill mood,
              energy close to your target, and acousticness that lines up
              well. The tempo is 13 BPM below your preference but still
              within the 20 BPM threshold.

  #2  Midnight Coding — LoRoom
       Genre: lofi  |  Mood: chill
       Score: 5.5 / 6.0
       Why:   Midnight Coding matches genre, mood, energy, acousticness,
              and tempo, but danceability sits slightly outside the
              threshold. One feature short of a perfect score.
```

Library Rain scores 6.0 because danceability matched (0.58 vs 0.40 target, within ±0.20). Midnight Coding scores 5.5 with the same genre and mood, but danceability misses by a narrow margin.

---

### 3. Mellow Metal Paradox (edge case)

**Input profile:**
```
genre: metal | mood: relaxed | energy: 0.2 | tempo: 70 BPM
acousticness: 0.9 | valence: 0.8
```

**Output:**
```
  #1  Spacewalk Thoughts — Orbit Bloom
       Genre: ambient  |  Mood: chill
       Score: 3.5 / 6.0
       Why:   Spacewalk Thoughts is not metal, but it matches what you
              actually described numerically — low energy (0.28), high
              acousticness (0.92), and a slow tempo near your target.
              The genre preference was overridden by five numeric matches.

  #4  Coffee Shop Stories — Slow Stereo
       Genre: jazz  |  Mood: relaxed
       Score: 2.0 / 6.0
       Why:   This is the only song in the catalog with a relaxed mood,
              which earns it a point. But without energy or acousticness
              close enough to your target, it ranks near the bottom.
```

The user asked for metal and got ambient. Iron Horizon, the only metal song in the catalog, has energy 0.96 against a target of 0.2 and scores just 0.5 total. Spacewalk Thoughts scored 3.5 by matching energy, acousticness, and tempo instead. This is a real design flaw: when genre and numeric features point in opposite directions, numeric features win, and the system returns songs the user would likely reject immediately.

---

## Design Decisions

The scoring formula uses hard thresholds rather than continuous distance functions. Energy must be within 0.15, tempo within 20 BPM, and so on. Hard cutoffs make every threshold visible in the code, so the explanation text can say exactly what passed and what didn't. The tradeoff is a cliff: a song 0.14 away from the energy target scores the same as a perfect match, while one 0.15 away scores nothing. A smoother penalty curve would rank songs more accurately, but explaining "you scored 1.7 out of 2.0 on energy" is harder to read than "energy matched."

Mood mismatch subtracts 0.5 rather than scoring zero. The original starter code gave zero points for a mood miss, which let high-energy songs dominate results even when the mood was completely wrong — genre and energy matches swamped the absence of mood credit. The penalty turns mood from a soft preference into something that actually costs points, which produces more intuitive rankings.

The Gemini call happens after ranking, not during scoring. Keeping the two systems separate means the recommender keeps running if the API goes down, falling back to the raw reasons string. Mixing the LLM into the scoring step would have made the system harder to test and harder to debug.

Gemini Flash was chosen over more capable models because the task is short and constrained. The prompt already contains the score breakdown; the model just rewrites it in natural language rather than reasoning over open-ended data. A faster, cheaper model handles that well and stays within the free-tier limits.

---

## Testing Summary

**Results at a glance:** 16 of 17 automated tests pass (1 skipped without a live API key). 53 of 55 AI-generated explanations passed a secondary truthfulness check — Gemini verified its own output against the score data and flagged 2 contradictions, both on borderline scores. Every API call is logged with the score breakdown so failures can be traced to the scoring layer, the prompt, or the model output.

Eleven user profiles were tested: four standard cases and seven adversarial ones built to find the formula's edges.

The standard profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock) produced results that matched intuition. Top-ranked songs fit the described vibe, and changing one input changed the output in a predictable way.

The adversarial profiles turned up four concrete problems. Exact string matching silently penalized users whose vocabulary didn't match the dataset — typing "calm" instead of "chill" gave a mood mismatch penalty on every lofi song, with no warning to the user. The boundary energy test confirmed the cliff: a song with an energy difference of exactly 0.15 scores zero, not partial credit. Entering an impossible tempo of 300 BPM contributed nothing to any score, which is correct, but a real system should tell the user their input was ignored rather than quietly dropping it. The Mellow Metal Paradox showed that when genre and numeric features conflict, the system returns numerically close songs the user would probably reject on genre alone.

The AI validation test sent Gemini's explanations back through a verification prompt to check accuracy. Two of 55 explanations failed: one for the Mellow Metal Paradox profile, where the explanation overstated the match quality, and one for the Mood Mismatch profile, where it described a mood alignment that didn't happen in the score. Both failures came from borderline scores — Gemini wasn't hallucinating so much as inheriting ambiguity from the scoring layer.

Logging the score breakdown alongside every explanation made it easy to trace which layer caused each failure, whether the prompt, the score itself, or the model output.

---

## Responsible AI

**Limitations and biases.** The catalog has 18 songs, so results reflect whoever built the catalog, not the broader music landscape. Certain genres appear once (metal, jazz) or not at all, which means niche preferences almost always lose to numeric feature matches. The scoring formula treats mood and genre as exact-match strings — "calm" and "chill" score the same as a genre miss even though most listeners would consider them equivalent. Hard thresholds also flatten similarity: a song 0.14 away from the energy target scores identically to a perfect match, while one 0.15 away scores zero. The system has no way to tell the user any of this is happening.

**Misuse potential.** A music recommender is low-stakes, but one risk is real: the Gemini explanation layer can make a bad recommendation sound credible. If the scoring formula returns a wrong result, the explanation doesn't flag it — it narrates the wrong result in natural language. A user who doesn't understand the scoring has no signal that the recommendation is off. The validation test addresses this partially by checking explanations against the score data, but it only catches contradictions in language, not flawed scores. The practical prevention here is the log file: every score breakdown is recorded alongside the explanation, so any result can be audited.

**What surprised me.** Two things. First, that the cliff at ±0.15 energy would produce results that look correct but aren't: a song that misses the threshold by 0.01 gets zero points and drops out of the top five, while a song that barely passes gets full credit. The ranked list looks clean either way. Second, that Gemini would inherit ambiguity from the scoring layer rather than catch it. I expected the model to occasionally notice when a recommendation didn't make sense. Instead, on the two explanations that failed the truthfulness check, Gemini wrote plausible-sounding sentences that papered over the contradiction rather than exposing it. The lesson: an explanation layer doesn't make a flawed scoring layer more honest.

**Collaboration with AI.** Claude wrote the core code, test suite, and documentation for this project. One useful contribution was the validation test design — the idea of sending Gemini's explanations back through a second prompt to check them against the score breakdown. That pattern wasn't something I had planned, and it caught two real failures I would have missed otherwise. One flawed contribution: early in the project, Claude repeatedly used the deprecated `google-generativeai` package with outdated API methods (`genai.configure()`, `genai.GenerativeModel()`) that no longer match how the SDK works. The code looked correct and passed a quick read, but failed at runtime. Switching to the current `google-genai` package with its `genai.Client` interface fixed it — but only after tracing the error back to the package choice, not the logic.

---

## Reflection

Building this made clear that a system can follow its rules correctly and still give wrong answers. When the Contradictory Energy+Mood profile returned upbeat pop songs for someone who asked for sad music, the algorithm was doing exactly what it was told. The rules were the problem, not a bug. That distinction matters when debugging: revising a scoring formula and fixing a code error are different problems, and treating them the same wastes time.

Adding Gemini introduced something I hadn't expected: explanation quality is tied to score quality. When the score is wrong — like ranking Iron Horizon as the best match for a relaxed listener — the explanation either accurately describes a bad recommendation or quietly drifts toward making it sound reasonable. The validation test caught two cases of the second kind. Fixing them meant fixing the score first, not rephrasing the prompt.

The gap between "it works" and "it's trustworthy" turned out to be the real project. The recommender returned songs in a reasonable order from the first run. It took eleven profiles and a separate validation pass to find where it breaks for real users, and most of those failures were silent. A user who typed "calm" saw plausible-looking results with no sign their preference had been ignored. The logging and explanation layer made those invisible failures visible, which felt like the more useful piece of work.

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

[Loom walkthrough](https://www.loom.com/share/f26e7deb84214472ad6b69734933ffb2)

The walkthrough shows the system running all 11 profiles end-to-end, including the edge cases, and demonstrates how the Gemini explanation layer changes the output compared to the raw reasons string.

---

## Portfolio

**Code:** [github.com/DavidSong74/ai110-FINAL-project-1](https://github.com/DavidSong74/ai110-FINAL-project-1)

What this project says about me as an AI engineer: I reach for observability before I reach for complexity. The recommender works in two layers — a deterministic scoring formula and a language model on top — and the first thing I built after getting both running was a way to tell them apart when something goes wrong. The log file, the validation test, the fallback to raw reasons: all of that exists because I wanted failures to be diagnosable, not just rare. Building the adversarial profiles taught me more about the system than the standard ones did. Finding that "calm" silently broke every lofi recommendation, or that a numerically precise ambient song outranked the only metal song in the catalog, wasn't embarrassing — it was the point. I'd rather surface that in testing than discover it matters to a user.
