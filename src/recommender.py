import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
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
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs: List[Dict] = []

    with open(csv_path, "r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            songs.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                }
            )

    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return a numeric score and list of matching reasons for a song against user preferences."""
    score = 0.0
    reasons = []

    if user_prefs.get("genre") and song["genre"].lower() == user_prefs["genre"].lower():
        score += 1.0
        reasons.append("genre match (+1.0)")

    if user_prefs.get("mood"):
        if song["mood"].lower() == user_prefs["mood"].lower():
            score += 1.0
            reasons.append("mood match (+1.0)")
        else:
            score -= 0.5
            reasons.append("mood mismatch (-0.5)")

    if user_prefs.get("energy") is not None:
        if abs(song["energy"] - user_prefs["energy"]) < 0.15:
            score += 2.0
            reasons.append("energy match (+2.0)")

    if user_prefs.get("valence") is not None:
        if abs(song["valence"] - user_prefs["valence"]) < 0.2:
            score += 0.5
            reasons.append("valence match (+0.5)")

    if user_prefs.get("danceability") is not None:
        if abs(song["danceability"] - user_prefs["danceability"]) < 0.2:
            score += 0.5
            reasons.append("danceability match (+0.5)")

    if user_prefs.get("acousticness") is not None:
        if abs(song["acousticness"] - user_prefs["acousticness"]) < 0.2:
            score += 0.5
            reasons.append("acousticness match (+0.5)")

    if user_prefs.get("tempo_bpm") is not None:
        if abs(song["tempo_bpm"] - user_prefs["tempo_bpm"]) < 20:
            score += 0.5
            reasons.append("tempo match (+0.5)")

    return (score, reasons)

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score all songs against user preferences and return the top k matches sorted by score."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        if score > 0:
            scored.append((song, score, ", ".join(reasons)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
