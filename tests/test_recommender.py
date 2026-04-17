"""
Test suite for the Music Recommender.

Structure:
    Unit tests  — test scoring logic with no API calls (always run)
    API tests   — test Gemini explanation quality (skipped if GEMINI_API_KEY not set)
"""

import os
import pytest

from src.recommender import (
    Recommender,
    Song,
    UserProfile,
    generate_explanation,
    score_song,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_recommender() -> Recommender:
    return Recommender(
        songs=[
            Song(
                id=1, title="Test Pop Track", artist="Test Artist",
                genre="pop", mood="happy", energy=0.8, tempo_bpm=120,
                valence=0.9, danceability=0.8, acousticness=0.2,
            ),
            Song(
                id=2, title="Chill Lofi Loop", artist="Test Artist",
                genre="lofi", mood="chill", energy=0.4, tempo_bpm=80,
                valence=0.6, danceability=0.5, acousticness=0.9,
            ),
        ]
    )


POP_USER = UserProfile(
    favorite_genre="pop",
    favorite_mood="happy",
    target_energy=0.8,
    likes_acoustic=False,
)

# A full song dict reused across several tests
SUNRISE_CITY = {
    "title": "Sunrise City", "artist": "Neon Echo",
    "genre": "pop", "mood": "happy",
    "energy": 0.82, "tempo_bpm": 118,
    "valence": 0.84, "danceability": 0.79, "acousticness": 0.18,
}

# ---------------------------------------------------------------------------
# Unit tests — scoring logic (no API)
# ---------------------------------------------------------------------------

class TestScoreSong:
    def test_genre_and_mood_match(self):
        user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
        score, reasons = score_song(user_prefs, SUNRISE_CITY)
        assert score >= 4.0
        assert any("genre match" in r for r in reasons)
        assert any("mood match" in r for r in reasons)
        assert any("energy match" in r for r in reasons)

    def test_mood_mismatch_applies_penalty(self):
        user_prefs = {"genre": "pop", "mood": "happy"}
        song = {**SUNRISE_CITY, "mood": "intense"}
        score, reasons = score_song(user_prefs, song)
        assert any("mood mismatch" in r for r in reasons)
        # genre match (+1) + mood mismatch (-0.5) = 0.5
        assert abs(score - 0.5) < 1e-9

    def test_energy_match_within_threshold(self):
        user_prefs = {"energy": 0.8}
        song = {**SUNRISE_CITY, "energy": 0.69}  # diff = 0.11 < 0.15
        _, reasons = score_song(user_prefs, song)
        assert any("energy match" in r for r in reasons)

    def test_energy_above_threshold_does_not_score(self):
        """diff > 0.15 must not award energy points."""
        user_prefs = {"energy": 0.9}
        song = {**SUNRISE_CITY, "energy": 0.7}  # diff = 0.20, clearly > 0.15
        _, reasons = score_song(user_prefs, song)
        assert not any("energy match" in r for r in reasons)

    def test_tempo_match(self):
        user_prefs = {"tempo_bpm": 120.0}
        song = {**SUNRISE_CITY, "tempo_bpm": 118.0}  # diff = 2 < 20
        _, reasons = score_song(user_prefs, song)
        assert any("tempo match" in r for r in reasons)

    def test_tempo_out_of_range_does_not_score(self):
        user_prefs = {"tempo_bpm": 300.0}
        _, reasons = score_song(user_prefs, SUNRISE_CITY)
        assert not any("tempo match" in r for r in reasons)

    def test_no_prefs_given_returns_zero_score(self):
        score, reasons = score_song({}, SUNRISE_CITY)
        assert score == 0.0
        assert reasons == []

    def test_case_insensitive_genre_match(self):
        user_prefs = {"genre": "POP"}
        _, reasons = score_song(user_prefs, SUNRISE_CITY)
        assert any("genre match" in r for r in reasons)


class TestRecommender:
    def test_recommend_returns_correct_count(self):
        rec = make_recommender()
        results = rec.recommend(POP_USER, k=2)
        assert len(results) == 2

    def test_recommend_sorts_by_score(self):
        rec = make_recommender()
        results = rec.recommend(POP_USER, k=2)
        # pop/happy/energy=0.8 song should rank above lofi/chill/energy=0.4
        assert results[0].genre == "pop"
        assert results[0].mood == "happy"

    def test_recommend_empty_catalog(self):
        rec = Recommender(songs=[])
        assert rec.recommend(POP_USER, k=5) == []

    def test_recommend_k_zero(self):
        rec = make_recommender()
        assert rec.recommend(POP_USER, k=0) == []

    def test_recommend_k_larger_than_catalog(self):
        rec = make_recommender()
        results = rec.recommend(POP_USER, k=100)
        assert len(results) <= 2

    def test_explain_recommendation_returns_non_empty_string(self):
        rec = make_recommender()
        explanation = rec.explain_recommendation(POP_USER, rec.songs[0])
        assert isinstance(explanation, str)
        assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# API tests — Gemini explanations (skipped without a key)
# ---------------------------------------------------------------------------

_needs_key = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set",
)


@_needs_key
def test_generate_explanation_is_non_empty():
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.9, "tempo_bpm": 128}
    reasons = ["genre match (+1.0)", "mood match (+1.0)", "energy match: 0.82 ≈ 0.90 (+2.0)"]
    explanation = generate_explanation(SUNRISE_CITY, user_prefs, 4.0, reasons)
    assert isinstance(explanation, str)
    assert len(explanation.strip()) > 10


@_needs_key
def test_generate_explanation_no_match_still_returns_string():
    """Even when nothing matches the fallback path returns a string."""
    user_prefs = {"genre": "bluegrass", "mood": "angry"}
    song = {**SUNRISE_CITY, "genre": "pop", "mood": "happy"}
    explanation = generate_explanation(song, user_prefs, -0.5, ["mood mismatch (-0.5)"])
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


@_needs_key
def test_explanations_are_truthful():
    """
    Validation harness: ask Gemini to verify its own explanation against the
    score breakdown. Passes if the explanation is consistent with the data.
    Skips gracefully if the free-tier rate limit is hit during testing.
    """
    from google import genai as _genai
    from google.genai import types as _genai_types
    from google.genai.errors import ClientError

    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.9}
    reasons = [
        "genre match (+1.0)",
        "mood match (+1.0)",
        "energy match: 0.82 ≈ 0.90 (+2.0)",
    ]
    explanation = generate_explanation(SUNRISE_CITY, user_prefs, 4.0, reasons)

    # If generate_explanation fell back to raw reasons due to a rate limit,
    # there is nothing to validate — skip rather than fail.
    if explanation == ", ".join(reasons):
        pytest.skip("generate_explanation hit rate limit; skipping truthfulness check")

    client = _genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    validation_prompt = (
        'A music recommender gave this explanation for recommending "Sunrise City":\n\n'
        f'"{explanation}"\n\n'
        "Actual score breakdown:\n"
        + "\n".join(f"- {r}" for r in reasons)
        + "\n\nDoes the explanation accurately reflect the score data "
        "without contradicting any factor? Answer only 'yes' or 'no'."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=validation_prompt,
            config=_genai_types.GenerateContentConfig(
                max_output_tokens=5,
                temperature=0.0,
            ),
        )
    except ClientError as exc:
        if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
            pytest.skip(f"Validation call hit rate limit: {exc}")
        raise

    answer = response.text.strip().lower()
    assert answer.startswith("yes"), (
        f"Explanation failed truthfulness check.\n"
        f"Explanation: {explanation}\n"
        f"Validator answer: {answer}"
    )
