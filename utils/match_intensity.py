def compute_match_intensity(tracks, fps):
    total_distance = 0.0
    total_frames = 0
    for frame_tracks in tracks.get("players", []):
        for player_data in frame_tracks.values():
            if "distance" in player_data:
                total_distance += player_data["distance"]
        total_frames += 1

    total_distance_km = total_distance / 40000.0
    match_duration_min = total_frames / (fps * 25.0) if fps > 0 else 1

    intensity = total_distance_km / match_duration_min if match_duration_min > 0 else 0
    return round(intensity, 2)
