"""
Music Recommender core logic.

Exports:
    load_songs         — read songs.csv into a list of dicts
    score_song         — score one song against a user preference dict
    recommend_songs    — score all songs, rank, return top-k with AI explanations
    generate_explanation — call Gemini to narrate a score breakdown in plain language

    Song, UserProfile, Recommender — dataclass / OOP interface used by the test suite
"""

import csv
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional; set GEMINI_API_KEY in your shell instead

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini client — initialised once at import time.
# Falls back gracefully if the key is missing or the package is not installed.
# ---------------------------------------------------------------------------
_gemini_client = None
_genai_types = None
_GenaiAPIError: tuple = (ValueError, RuntimeError, ConnectionError, OSError)

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    from google.genai import errors as _genai_errors

    _GenaiAPIError = (
        ValueError, RuntimeError, ConnectionError, OSError,
        _genai_errors.APIError,
    )

    _api_key = os.environ.get("GEMINI_API_KEY")
    if _api_key:
        _gemini_client = _genai.Client(api_key=_api_key)
        logger.debug("Gemini client ready (gemini-2.0-flash)")
    else:
        logger.warning(
            "GEMINI_API_KEY not set — "
            "AI explanations will fall back to raw score reasons."
        )
except ImportError:
    logger.warning(
        "google-genai not installed — "
        "AI explanations will fall back to raw score reasons."
    )


# ---------------------------------------------------------------------------
# Dataclasses (used by the OOP Recommender and the test suite)
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """Represents a song and its audio features."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """Represents a listener's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


# ---------------------------------------------------------------------------
# OOP interface (wraps the functional API below)
# ---------------------------------------------------------------------------

class Recommender:
    """Score-based music recommender with AI-generated explanations."""

    def __init__(self, songs: List[Song]) -> None:
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs sorted by score for the given user profile."""
        if not self.songs or k <= 0:
            return []

        user_prefs = {
            "genre": user.favorite_genre,
            "mood":  user.favorite_mood,
            "energy": user.target_energy,
        }

        scored: List[Tuple[Song, float]] = []
        for song in self.songs:
            song_dict = _song_to_dict(song)
            score, _ = score_song(user_prefs, song_dict)
            scored.append((song, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return an AI-generated explanation for why this song was recommended."""
        user_prefs = {
            "genre": user.favorite_genre,
            "mood":  user.favorite_mood,
            "energy": user.target_energy,
        }
        song_dict = _song_to_dict(song)
        score, reasons = score_song(user_prefs, song_dict)
        return generate_explanation(song_dict, user_prefs, score, reasons)


def _song_to_dict(song: Song) -> Dict:
    """Convert a Song dataclass to the dict format used by score_song."""
    return {
        "title":        song.title,
        "artist":       song.artist,
        "genre":        song.genre,
        "mood":         song.mood,
        "energy":       song.energy,
        "tempo_bpm":    song.tempo_bpm,
        "valence":      song.valence,
        "danceability": song.danceability,
        "acousticness": song.acousticness,
    }


# ---------------------------------------------------------------------------
# Functional API
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of song dicts."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Score one song against a user preference dict.

    Scoring rules (max 6.0):
        genre match               +1.0
        mood match                +1.0  |  mood mismatch  -0.5
        energy within ±0.15       +2.0
        valence within ±0.20      +0.5
        danceability within ±0.20 +0.5
        acousticness within ±0.20 +0.5
        tempo within ±20 BPM      +0.5

    Returns (score, reasons) where reasons is a list of match strings.
    """
    score = 0.0
    reasons: List[str] = []

    if user_prefs.get("genre"):
        if song["genre"].lower() == user_prefs["genre"].lower():
            score += 1.0
            reasons.append("genre match (+1.0)")

    if user_prefs.get("mood"):
        if song["mood"].lower() == user_prefs["mood"].lower():
            score += 1.0
            reasons.append("mood match (+1.0)")
        else:
            score -= 0.5
            wanted = user_prefs["mood"]
            got = song["mood"]
            reasons.append(
                f"mood mismatch: wanted '{wanted}', got '{got}' (-0.5)"
            )

    if user_prefs.get("energy") is not None:
        if abs(song["energy"] - user_prefs["energy"]) < 0.15:
            score += 2.0
            reasons.append(
                f"energy match: {song['energy']:.2f} ≈ "
                f"{user_prefs['energy']:.2f} (+2.0)"
            )

    if user_prefs.get("valence") is not None:
        if abs(song["valence"] - user_prefs["valence"]) < 0.20:
            score += 0.5
            reasons.append("valence match (+0.5)")

    if user_prefs.get("danceability") is not None:
        if abs(song["danceability"] - user_prefs["danceability"]) < 0.20:
            score += 0.5
            reasons.append("danceability match (+0.5)")

    if user_prefs.get("acousticness") is not None:
        if abs(song["acousticness"] - user_prefs["acousticness"]) < 0.20:
            score += 0.5
            reasons.append("acousticness match (+0.5)")

    if user_prefs.get("tempo_bpm") is not None:
        if abs(song["tempo_bpm"] - user_prefs["tempo_bpm"]) < 20:
            score += 0.5
            reasons.append(
                f"tempo match: {song['tempo_bpm']:.0f} ≈ "
                f"{user_prefs['tempo_bpm']:.0f} BPM (+0.5)"
            )

    return (score, reasons)


def generate_explanation(
    song: Dict,
    user_prefs: Dict,
    score: float,
    reasons: List[str],
) -> str:
    """
    Call Gemini to narrate the score breakdown in plain language.

    Guardrail: if the API key is missing, the package is not installed,
    or the API call fails, returns the raw reasons string instead.
    The system never crashes due to an explanation failure.
    """
    if _gemini_client is None:
        fallback = ", ".join(reasons) if reasons else "no features matched"
        logger.debug(
            "Gemini unavailable — using fallback for '%s'", song.get("title")
        )
        return fallback

    reasons_block = (
        "\n".join(f"  - {r}" for r in reasons)
        if reasons else "  - no features matched"
    )

    prompt = (
        "A music recommender matched a song to a listener's taste profile. "
        "Based only on the data below, write 1-2 sentences explaining why "
        "this song was recommended. Be specific about what matched or did not "
        "match. Do not use filler phrases. State facts directly.\n\n"
        "Listener preferences:\n"
        f"  genre: {user_prefs.get('genre', 'not specified')}\n"
        f"  mood: {user_prefs.get('mood', 'not specified')}\n"
        f"  energy target: {user_prefs.get('energy', 'not specified')}\n"
        f"  tempo target: {user_prefs.get('tempo_bpm', 'not specified')} BPM\n\n"
        "Recommended song:\n"
        f"  {song['title']} by {song['artist']}\n"
        f"  genre: {song['genre']}, mood: {song['mood']}\n"
        f"  energy: {song['energy']}, tempo: {song['tempo_bpm']} BPM\n"
        f"  valence: {song['valence']}, "
        f"danceability: {song['danceability']}, "
        f"acousticness: {song['acousticness']}\n\n"
        f"Score: {score:.1f} / 6.0\n"
        "Score breakdown:\n"
        f"{reasons_block}"
    )

    config = None
    if _genai_types is not None:
        config = _genai_types.GenerateContentConfig(
            max_output_tokens=150,
            temperature=0.3,
        )

    try:
        response = _gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config,
        )
        explanation = response.text.strip()
        logger.info(
            "Explanation OK | %-30s | score=%.1f | ~%d tokens",
            song.get("title", "?"),
            score,
            len(prompt.split()) + len(explanation.split()),
        )
        return explanation

    except _GenaiAPIError as exc:  # type: ignore[misc]
        logger.error(
            "Gemini API error for '%s': %s — falling back to raw reasons",
            song.get("title"), exc,
        )
        return ", ".join(reasons) if reasons else "no features matched"


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
) -> List[Tuple[Dict, float, str]]:
    """
    Score every song, rank by score descending, return top-k with AI explanations.

    Returns:
        List of (song_dict, score, explanation_string)
    """
    scored: List[Tuple[Dict, float, List[str]]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        if score > 0:
            scored.append((song, score, reasons))

    scored.sort(key=lambda x: x[1], reverse=True)

    results: List[Tuple[Dict, float, str]] = []
    for song, score, reasons in scored[:k]:
        explanation = generate_explanation(song, user_prefs, score, reasons)
        results.append((song, score, explanation))

    return results
