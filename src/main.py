"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from .recommender import load_songs, recommend_songs
except ImportError:
    # Fallback for running as a script: python src/main.py
    from recommender import load_songs, recommend_songs


def main() -> None:
    """Run the music recommender simulation."""
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    profiles = {
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
            "mood": "calm",
            "energy": 0.3,
            "valence": 0.4,
            "danceability": 0.4,
            "acousticness": 0.7,
            "tempo_bpm": 85,
        },
        "Deep Intense Rock": {
            "genre": "rock",
            "mood": "angry",
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
        # --- Adversarial / Edge Case Profiles ---
        "Contradictory Energy+Mood": {
            "genre": "pop",
            "mood": "sad",       # No song has mood="sad" → always 0 pts
            "energy": 0.9,       # Matches intense/euphoric songs instead
            "valence": 0.2,
            "danceability": 0.5,
            "acousticness": 0.1,
            "tempo_bpm": 128,
        },
        "Mellow Metal Paradox": {
            "genre": "metal",    # +2.0 locks in metal regardless of other prefs
            "mood": "relaxed",   # No metal song has mood="relaxed"
            "energy": 0.2,       # Metal songs have energy ~0.96 → no energy pts
            "valence": 0.8,
            "danceability": 0.3,
            "acousticness": 0.9,
            "tempo_bpm": 70,
        },
        "Mood Mismatch (calm vs chill)": {
            "genre": "lofi",
            "mood": "calm",      # Songs use "chill", not "calm" → 0 mood pts
            "energy": 0.35,
            "valence": 0.55,
            "danceability": 0.6,
            "acousticness": 0.75,
            "tempo_bpm": 78,
        },
        "Pop Fan Missing Indie Pop": {
            "genre": "pop",      # Won't match genre="indie pop" (Rooftop Lights)
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
            "energy": 0.57,      # Song #2 energy=0.42 → diff=0.15, NOT < 0.15 → 0 pts
            "valence": 0.56,
            "danceability": 0.62,
            "acousticness": 0.71,
            "tempo_bpm": 78,
        },
        "Ambiguous Mid-Range": {
            "genre": "lofi",
            "mood": "focused",
            "energy": 0.5,       # Many songs score identically → arbitrary ordering
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
            "tempo_bpm": 300,    # All songs are 60–172 BPM → tempo always 0 pts
        },
    }

    for profile_name, user_prefs in profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print("\n" + "=" * 40)
        print(f"  {profile_name.upper()}")
        print("=" * 40)

        if not recommendations:
            print("No matching songs found.")
        else:
            for i, (song, score, explanation) in enumerate(recommendations, start=1):
                print(f"\n#{i}  {song['title']} by {song['artist']}")
                print(f"    Genre: {song['genre']}  |  Mood: {song['mood']}")
                print(f"    Score: {score:.1f}")
                print(f"    Why:   {explanation}")

        print("\n" + "=" * 40)


if __name__ == "__main__":
    main()
