"""
Command-line runner for the Music Recommender.

Usage:
    python -m src.main
"""

import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging — configure before importing recommender so the module-level
# logger picks up handlers at import time.
# ---------------------------------------------------------------------------
_log_dir = Path("logs")
_log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(_log_dir / "recommender.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

try:
    from .recommender import load_songs, recommend_songs
except ImportError:
    from recommender import load_songs, recommend_songs

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------
PROFILES = {
    "High-Energy Pop": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.9,
        "valence": 0.8,
        "danceability": 0.85,
        "acousticness": 0.1,
        "tempo_bpm": 128,
    },
    "Chill Lofi": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.3,
        "valence": 0.4,
        "danceability": 0.4,
        "acousticness": 0.7,
        "tempo_bpm": 85,
    },
    "Deep Intense Rock": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.95,
        "valence": 0.2,
        "danceability": 0.5,
        "acousticness": 0.05,
        "tempo_bpm": 150,
    },
    "No Match Edge Case": {
        "genre": "bluegrass",
        "mood": "angry",
    },
    # --- Adversarial / edge-case profiles ---
    "Contradictory Energy+Mood": {
        "genre": "pop",
        "mood": "sad",
        "energy": 0.9,
        "valence": 0.2,
        "danceability": 0.5,
        "acousticness": 0.1,
        "tempo_bpm": 128,
    },
    "Mellow Metal Paradox": {
        "genre": "metal",
        "mood": "relaxed",
        "energy": 0.2,
        "valence": 0.8,
        "danceability": 0.3,
        "acousticness": 0.9,
        "tempo_bpm": 70,
    },
    "Mood Mismatch (calm vs chill)": {
        "genre": "lofi",
        "mood": "calm",
        "energy": 0.35,
        "valence": 0.55,
        "danceability": 0.6,
        "acousticness": 0.75,
        "tempo_bpm": 78,
    },
    "Pop Fan Missing Indie Pop": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.76,
        "valence": 0.81,
        "danceability": 0.82,
        "acousticness": 0.35,
        "tempo_bpm": 124,
    },
    "Exact Boundary Energy": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.57,
        "valence": 0.56,
        "danceability": 0.62,
        "acousticness": 0.71,
        "tempo_bpm": 78,
    },
    "Ambiguous Mid-Range": {
        "genre": "lofi",
        "mood": "focused",
        "energy": 0.5,
        "valence": 0.5,
        "danceability": 0.5,
        "acousticness": 0.5,
        "tempo_bpm": 100,
    },
    "Impossible Tempo": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.91,
        "valence": 0.48,
        "danceability": 0.66,
        "acousticness": 0.10,
        "tempo_bpm": 300,
    },
}


def main() -> None:
    songs = load_songs("data/songs.csv")
    logger.info("Loaded %d songs from catalog", len(songs))

    for profile_name, user_prefs in PROFILES.items():
        logger.info("Profile: %s", profile_name)
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print("\n" + "=" * 50)
        print(f"  {profile_name.upper()}")
        print("=" * 50)

        if not recommendations:
            print("  No matching songs found.")
        else:
            for i, (song, score, explanation) in enumerate(recommendations, start=1):
                print(f"\n  #{i}  {song['title']} — {song['artist']}")
                print(f"       Genre: {song['genre']}  |  Mood: {song['mood']}")
                print(f"       Score: {score:.1f} / 6.0")
                print(f"       Why:   {explanation}")

        print()

    logger.info("Run complete.")


if __name__ == "__main__":
    main()
