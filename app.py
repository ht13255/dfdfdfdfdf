# app.py
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


# 트위터 영상 URL 추출 함수
def get_video_links(account_name):
    # 기본 URL 구성
    twitter_url = f"https://twitter.com/{account_name}"
    st.write(f"트위터 페이지: {twitter_url}")

    # Selenium WebDriver 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 백그라운드에서 실행
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 트위터 페이지 열기
    driver.get(twitter_url)
    time.sleep(3)  # 초기 로드 대기

    # 스크롤하여 추가 콘텐츠 로드
    st.write("추가 콘텐츠를 로드 중...")
    scroll_count = 0
    video_links = set()  # 중복 제거를 위해 Set 사용
    while scroll_count < 10:  # 최대 10회 스크롤 (필요에 따라 조정 가능)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 스크롤 후 로드 대기
        scroll_count += 1

        # HTML 가져오기 및 파싱
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 영상 URL 추출
        for video in soup.find_all("video"):
            source = video.find("source")
            if source and source.get("src"):
                video_links.add(source.get("src"))

        # 스크롤 후 새 데이터가 없으면 중지
        if len(video_links) > 0 and scroll_count > 3:
            break

    driver.quit()
    return list(video_links)


# Streamlit 앱 설정
st.title("트위터 영상 링크 추출기")
st.write("트위터 계정 이름을 입력하여 영상 게시물의 링크를 추출합니다.")

# 계정 이름 입력
account_name = st.text_input("트위터 계정 이름을 입력하세요 (예: account_name):").strip()

if st.button("추출 시작"):
    if not account_name:
        st.error("계정 이름을 입력해주세요!")
    else:
        try:
            video_links = get_video_links(account_name)
            if video_links:
                st.success(f"총 {len(video_links)}개의 영상 링크를 찾았습니다!")
                for i, link in enumerate(video_links, start=1):
                    st.write(f"{i}. [영상 링크]({link})", unsafe_allow_html=True)
            else:
                st.warning("영상 링크를 찾지 못했습니다.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
