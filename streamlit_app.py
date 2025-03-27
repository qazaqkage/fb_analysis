import streamlit as st
import tempfile
import os
from utils.process_video import process_video, compute_match_metrics
from utils.match_intensity import compute_match_intensity
from utils.xg_calculator import compute_match_xg

st.title("Football Analysis with Computer Vision")
st.write("Загрузите видео для анализа:")

uploaded_file = st.file_uploader("Выберите видео", type=["mp4", "avi", "mov"])
if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    tfile.close()

    st.video(tfile.name)

    if st.button("Обработать видео"):
        with st.spinner("Обработка видео..."):
            output_path = os.path.abspath("data/output_videos/processed_video.mp4")
            tracks, team_ball_control = process_video(tfile.name, output_path)
            metrics = compute_match_metrics(tracks, team_ball_control)
            fps = 24  # или определите динамически
            intensity = compute_match_intensity(tracks, fps)
            from utils.video_utils import read_video

            video_frames = read_video(output_path)
            xg_team1, xg_team2 = compute_match_xg(tracks, video_frames)
        st.success("Обработка завершена!")

        st.write("Размер файла:", os.path.getsize(output_path), "байт")
        st.video(output_path)

        st.subheader("Статистика матча")
        col1, col2 = st.columns(2)
        col1.metric("Владение мячом (Team 1)", f"{metrics['team1_possession']}%")
        col2.metric("Владение мячом (Team 2)", f"{metrics['team2_possession']}%")
        col1.metric("Пройденное расстояние (Team 1)", f"{metrics['team1_distance']} км")
        col2.metric("Пройденное расстояние (Team 2)", f"{metrics['team2_distance']} км")

        st.subheader("Интенсивность матча")
        st.metric("Интенсивность (км/мин)", f"{intensity} км/мин")

        st.subheader("xG")
        col3, col4 = st.columns(2)
        col3.metric("xG (Team 1)", f"{xg_team1}")
        col4.metric("xG (Team 2)", f"{xg_team2}")

        with open(output_path, "rb") as video_file:
            st.download_button(
                label="Скачать обработанное видео",
                data=video_file,
                file_name="processed_video.mp4",
                mime="video/mp4"
            )
