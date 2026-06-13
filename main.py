import streamlit as st
import pandas as pd
import re
from collections import Counter

from googleapiclient.discovery import build

from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --------------------
# 설정
# --------------------

st.set_page_config(
    page_title="유튜브 댓글 심층 분석기",
    page_icon="📺",
    layout="wide"
)

st.title("📺 유튜브 댓글 심층 분석기")

st.info(
    """
    사용 방법

    1. Streamlit Secrets에 유튜브 API 키 등록
    2. 유튜브 링크 입력
    3. 댓글 분석 시작
    """
)

# --------------------
# API KEY
# --------------------

API_KEY = "AIzaSyAfskAo3hwq83sKWCYs-pUgb_gChpvJ7tw"

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

# --------------------
# 링크 -> video id
# --------------------

def get_video_id(url):

    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None

# --------------------
# 댓글 수집
# --------------------

def get_comments(video_id):

    comments = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request:

        response = request.execute()

        for item in response["items"]:

            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]

            comments.append(text)

        request = youtube.commentThreads().list_next(
            request,
            response
        )

    return comments

# --------------------
# 댓글 분석
# --------------------

video_url = st.text_input(
    "유튜브 링크 입력"
)

if st.button("분석 시작"):

    video_id = get_video_id(video_url)

    if not video_id:
        st.error("유효한 유튜브 링크가 아닙니다.")
        st.stop()

    with st.spinner("댓글 수집 중..."):

        comments = get_comments(video_id)

    if len(comments) == 0:
        st.warning("댓글이 없습니다.")
        st.stop()

    st.success(f"{len(comments)}개의 댓글 수집 완료")

    df = pd.DataFrame(
        {"댓글": comments}
    )

    st.subheader("📋 댓글 데이터")

    st.dataframe(df.head(20))

    # --------------------
    # 단어 분석
    # --------------------

    text = " ".join(comments)

    words = re.findall(
        r"[가-힣A-Za-z]+",
        text
    )

    stopwords = {
        "그리고",
        "진짜",
        "너무",
        "그냥",
        "있는",
        "합니다",
        "입니다",
        "ㅋㅋ",
        "ㅎㅎ"
    }

    filtered = [
        w for w in words
        if len(w) > 1
        and w not in stopwords
    ]

    counter = Counter(filtered)

    st.subheader("🔥 자주 등장한 단어")

    top_words = pd.DataFrame(
        counter.most_common(20),
        columns=["단어", "빈도"]
    )

    st.dataframe(top_words)

    # --------------------
    # 워드클라우드
    # --------------------

    st.subheader("☁️ 워드클라우드")

    try:

        wc = WordCloud(
            font_path="NanumGothic.ttf",
            width=1200,
            height=600,
            background_color="white"
        ).generate_from_frequencies(counter)

        fig, ax = plt.subplots(
            figsize=(12, 6)
        )

        ax.imshow(wc)

        ax.axis("off")

        st.pyplot(fig)

    except Exception as e:

        st.error(
            f"워드클라우드 오류: {e}"
        )

    # --------------------
    # 통계
    # --------------------

    st.subheader("📊 댓글 통계")

    lengths = [
        len(c)
        for c in comments
    ]

    st.metric(
        "평균 댓글 길이",
        round(sum(lengths) / len(lengths), 1)
    )

    st.metric(
        "총 댓글 수",
        len(comments)
    )
