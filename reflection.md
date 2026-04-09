# Reflection on Profile Comparisons

Profiles compared:
- High-Energy Pop
- Chill Lofi
- Deep Intense Rock
- Mood Mismatch (calm vs chill)

## Pair-by-pair comments

1. High-Energy Pop vs Chill Lofi
The top songs changed from upbeat pop tracks (like "Sunrise City" and "Gym Hero") to softer lofi tracks (like "Library Rain" and "Midnight Coding"). This makes sense because the lofi profile asks for lower energy and higher acousticness, while pop asks for high energy and danceability.

2. High-Energy Pop vs Deep Intense Rock
Both profiles still got high-energy songs, but the ordering changed. Rock moved "Storm Runner" to the top because genre and energy fit better, while pop kept "Sunrise City" on top because of the pop + happy match. This makes sense because both users want intensity, but not the same style.

3. High-Energy Pop vs Mood Mismatch (calm vs chill)
The mood mismatch profile still got energetic songs, including "Gym Hero," even though mood did not match. This makes sense in the current scoring system because strong energy and partial genre matches can overpower one mood penalty.

4. Chill Lofi vs Deep Intense Rock
Chill Lofi returned mostly lower-energy, more acoustic songs, while Deep Intense Rock returned high-energy tracks like "Storm Runner" and "Iron Horizon." This is a healthy separation and shows the model can respond to opposite energy targets.

5. Chill Lofi vs Mood Mismatch (calm vs chill)
These two profiles shared many songs, but the mood mismatch version paid a penalty on each song because "calm" does not exactly equal "chill" in the dataset. That makes sense with exact text matching, but it also shows the model is strict with wording.

6. Deep Intense Rock vs Mood Mismatch (calm vs chill)
Deep Intense Rock and the mood mismatch profile both surfaced some intense songs, but rock gave stronger priority to rock-like intensity and put "Storm Runner" first. Mood mismatch spread across genres more because it lacked a solid mood anchor and relied more on energy closeness.

## Plain-language takeaway

"Gym Hero" keeps showing up for people who ask for "Happy Pop" because the model rewards high energy very strongly. "Gym Hero" is very high-energy and in pop, so it still scores well even though its mood is "intense" instead of "happy." In non-technical terms: the recommender is currently treating "high energy" as a louder signal than the mood label.
