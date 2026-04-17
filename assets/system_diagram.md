# System Architecture Diagram
## AI Music Recommender — Data Flow & Components

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                   │
│                                                                     │
│   genre, mood, energy, valence, danceability, acousticness, tempo   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LOADER                                  │
│                    load_songs("data/songs.csv")                     │
│                                                                     │
│   Reads 18 songs → list of dicts with audio features               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SCORING ENGINE                                 │
│                    score_song(user_prefs, song)                     │
│                                                                     │
│   For each song:                                                    │
│   • Genre match      → +1.0                                        │
│   • Mood match       → +1.0  /  mismatch → -0.5                   │
│   • Energy (±0.15)   → +2.0                                        │
│   • Valence (±0.20)  → +0.5                                        │
│   • Danceability     → +0.5                                        │
│   • Acousticness     → +0.5                                        │
│   • Tempo (±20 BPM)  → +0.5                                        │
│                                                                     │
│   Output: (score: float, reasons: List[str])                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       RECOMMENDER                                   │
│               recommend_songs(user_prefs, songs, k=5)               │
│                                                                     │
│   • Filters songs with score > 0                                    │
│   • Sorts by score descending                                       │
│   • Returns top-k results                                          │
│                                                                     │
│   Output: [(song, score, raw_reasons), ...]                        │
└─────────────┬───────────────────────────────────────────────────────┘
              │
              │         ┌──────────────────────────────────────┐
              │         │         SONG CATALOG                 │
              │◄────────│         data/songs.csv               │
              │         │   18 songs, 10 audio features each   │
              │         └──────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   AI EXPLANATION GENERATOR                          │
│              generate_explanation(song, user_prefs,                 │
│                                   score, reasons)                   │
│                                                                     │
│   Prompt: song features + score breakdown → Gemini API              │
│   Model: gemini-2.0-flash                                           │
│   Max tokens: 150                                                   │
│   Guardrail: fallback to raw reasons string if API call fails       │
│                                                                     │
│   Output: human-readable explanation (1-2 sentences)               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          OUTPUT                                     │
│                                                                     │
│   #1  Sunrise City by Neon Echo                                    │
│       Genre: pop  |  Mood: happy                                   │
│       Score: 5.5                                                    │
│       Why:  "This upbeat pop track matches your happy mood and      │
│             high energy preference perfectly, with a tempo          │
│             close to your target of 128 BPM."                      │
│                                                                     │
│   ... (top-k results)                                               │
└─────────────┬───────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   LOGGING & AUDIT TRAIL                             │
│                     logs/recommender.log                            │
│                                                                     │
│   Records per run:                                                  │
│   • Timestamp, profile name, song title, score                     │
│   • Claude API call: prompt tokens, response tokens                 │
│   • Errors and fallback events                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Testing & Human Evaluation Layer

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AUTOMATED TEST SUITE                            │
│                   tests/test_recommender.py                         │
│                                                                     │
│   Unit Tests (rule-based):                                         │
│   ├── test_recommend_returns_songs_sorted_by_score()               │
│   └── test_explain_recommendation_returns_non_empty_string()       │
│                                                                     │
│   AI Validation Tests:                                              │
│   ├── test_explanations_are_truthful()                             │
│   │     → Asks Gemini to verify each explanation matches score     │
│   │     → Asserts truthfulness rate ≥ 95%                         │
│   └── test_explanations_non_empty_for_all_profiles()              │
│         → Runs all 11 profiles, checks no empty strings            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    HUMAN REVIEW        │
              │                        │
              │  Developer checks:     │
              │  • Explanation text    │
              │    sounds natural      │
              │  • Score breakdown     │
              │    matches output      │
              │  • Edge cases behave   │
              │    as expected         │
              └────────────────────────┘
```

---

## Component Summary

| Component | File | Role |
|---|---|---|
| Data Loader | `src/recommender.py` | Reads CSV into list of song dicts |
| Scoring Engine | `src/recommender.py` | Rule-based feature scoring |
| Recommender | `src/recommender.py` | Filters and ranks top-k songs |
| AI Explainer | `src/recommender.py` | Claude API — generates natural language explanation |
| CLI Runner | `src/main.py` | Runs all 11 profiles, prints results |
| Logger | `logs/recommender.log` | Audit trail for all API calls and errors |
| Unit Tests | `tests/test_recommender.py` | Validates scoring logic and explanation quality |
| Song Catalog | `data/songs.csv` | 18 songs with 10 audio features each |
