from utils.video_utils import read_video, save_video
from functions.tracker import Tracker
from functions.camera_movement_estimator import CameraMovementEstimator
from functions.view_transformer import ViewTransformer
from functions.speed_and_distance_estimator import SpeedAndDistance_Estimator
from functions.team_assigner import TeamAssigner
from functions.player_ball_assigner import PlayerBallAssigner
import numpy as np
import os



def process_video(input_path, output_path):
    video_frames = read_video(input_path)

    tracker = Tracker('../models/best.pt')

    track_stub_path = os.path.join(os.path.dirname(__file__), '..', 'stubs', 'track_stubs.pkl')
    camera_stub_path = os.path.join(os.path.dirname(__file__), '..', 'stubs', 'camera_movement_stub.pkl')

    tracks = tracker.get_object_tracks(video_frames,
                                       read_from_stub=True,
                                       stub_path=track_stub_path)
    tracker.add_position_to_tracks(tracks)

    camera_movement_estimator = CameraMovementEstimator(video_frames[0])
    camera_movement_per_frame = camera_movement_estimator.get_camera_movement(
        video_frames,
        read_from_stub=True,
        stub_path=camera_stub_path)
    camera_movement_estimator.add_adjust_positions_to_tracks(tracks, camera_movement_per_frame)

    view_transformer = ViewTransformer()
    view_transformer.add_transformed_position_to_tracks(tracks)

    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])

    speed_and_distance_estimator = SpeedAndDistance_Estimator()
    speed_and_distance_estimator.add_speed_and_distance_to_tracks(tracks)

    team_assigner = TeamAssigner()
    team_assigner.assign_team_color(video_frames[0], tracks['players'][0])
    for frame_num, player_track in enumerate(tracks['players']):
        for player_id, track in player_track.items():
            team = team_assigner.get_player_team(video_frames[frame_num], track['bbox'], player_id)
            tracks['players'][frame_num][player_id]['team'] = team
            tracks['players'][frame_num][player_id]['team_color'] = team_assigner.team_colors[team]

    player_assigner = PlayerBallAssigner()
    team_ball_control = []
    for frame_num, player_track in enumerate(tracks['players']):
        ball_bbox = tracks['ball'][frame_num][1]['bbox']
        assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)
        if assigned_player != -1:
            tracks['players'][frame_num][assigned_player]['has_ball'] = True
            team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
        else:
            team_ball_control.append(team_ball_control[-1] if team_ball_control else 0)
    team_ball_control = np.array(team_ball_control)

    output_video_frames = tracker.draw_annotations(video_frames, tracks, team_ball_control)
    output_video_frames = camera_movement_estimator.draw_camera_movement(output_video_frames, camera_movement_per_frame)
    speed_and_distance_estimator.draw_speed_and_distance(output_video_frames, tracks)

    save_video(output_video_frames, output_path)

    return tracks, team_ball_control

def compute_match_metrics(tracks, team_ball_control):
    """
    Вычисляет метрики матча:
      - Владение мячом (процент кадров, когда каждая команда владеет мячом)
      - Общее пройденное расстояние для каждой команды (сумма расстояний, пройденных игроками)
    """
    total_frames = len(team_ball_control)
    team1_frames = (team_ball_control == 1).sum() if total_frames > 0 else 0
    team2_frames = (team_ball_control == 2).sum() if total_frames > 0 else 0
    team1_possession = (team1_frames / total_frames) * 100 if total_frames > 0 else 0
    team2_possession = (team2_frames / total_frames) * 100 if total_frames > 0 else 0

    team_distance = {1: 0.0, 2: 0.0}
    for frame_tracks in tracks.get("players", []):
        for player_id, player_data in frame_tracks.items():
            if "distance" in player_data:
                team = player_data.get("team")
                if team in team_distance:
                    team_distance[team] += player_data["distance"]

    distance_team1_km = team_distance[1] / 100000.0
    distance_team2_km = team_distance[2] / 100000.0

    return {
        "team1_possession": round(team1_possession, 2),
        "team2_possession": round(team2_possession, 2),
        "team1_distance": round(distance_team1_km, 2),
        "team2_distance": round(distance_team2_km, 2)
    }

if __name__ == "__main__":
    process_video('../data/input_videos/1.mp4', 'data/output_videos/output_video.mp4')
