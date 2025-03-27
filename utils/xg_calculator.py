import numpy as np

def compute_xg_for_frame(frame, ball_bbox):
    center_x = (ball_bbox[0] + ball_bbox[2]) / 2
    if center_x < 300:
        return 0.25  # условно, 25% шанс
    else:
        return 0.05

def compute_match_xg(tracks, video_frames):
    xg_team1 = 0.0
    xg_team2 = 0.0
    for frame_num, frame in enumerate(video_frames):
        if 1 in tracks["ball"][frame_num]:
            ball_bbox = tracks["ball"][frame_num][1]["bbox"]
            # Вычисляем xG для этого кадра
            xg_value = compute_xg_for_frame(frame, ball_bbox)
            center_x = (ball_bbox[0] + ball_bbox[2]) / 2
            if center_x < 400:
                xg_team1 += xg_value
            else:
                xg_team2 += xg_value
    return round(round(xg_team1, 2)/1500, 2), round(round(xg_team2, 2)/1500, 2)
