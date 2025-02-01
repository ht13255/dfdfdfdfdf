import streamlit as st
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pickle
import os
import asyncio
import aiofiles
import platform

# User-Agent 설정 (크롤링 방지 우회)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 세션 상태 초기화
if "download_ready" not in st.session_state:
    st.session_state.download_ready = False
if "cache" not in st.session_state:
    st.session_state.cache = {}
if "login_success" not in st.session_state:
    st.session_state.login_success = False

# 기기별 UI 최적화
device_type = "PC"
if st.session_state.get("device_type") is None:
    user_os = platform.system()
    user_agent = st.experimental_user_agent
    if "Android" in user_agent or "iPhone" in user_agent:
        device_type = "모바일"
    elif "iPad" in user_agent or "Tablet" in user_agent:
        device_type = "태블릿"
    else:
        device_type = "PC"
    st.session_state.device_type = device_type

# Selenium 드라이버 설정 (Headless 모드)
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={USER_AGENT}")
    try:
        driver = uc.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"🚨 크롬 드라이버 실행 실패: {e}")
        return None

# 자동 로그인 기능
def login_novelpia(driver, user_id, user_pw):
    driver.get("https://novelpia.com/login")
    time.sleep(3)

    # 쿠키가 있다면 자동 로그인
    if os.path.exists("novelpia_cookies.pkl"):
        try:
            with open("novelpia_cookies.pkl", "rb") as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
            driver.refresh()
            time.sleep(3)

            if "logout" in driver.page_source:
                st.session_state.login_success = True
                return
        except:
            os.remove("novelpia_cookies.pkl")

    # 수동 로그인
    try:
        driver.find_element(By.NAME, "email").send_keys(user_id)
        driver.find_element(By.NAME, "password").send_keys(user_pw)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(5)

        if "logout" in driver.page_source:
            st.session_state.login_success = True
            with open("novelpia_cookies.pkl", "wb") as f:
                pickle.dump(driver.get_cookies(), f)
        else:
            st.error("🚨 로그인 실패! ID/PW를 확인하세요.")
            st.session_state.login_success = False
    except Exception as e:
        st.error(f"🚨 로그인 중 오류 발생: {e}")

# 소설의 모든 화 URL 가져오기
def get_chapter_urls(driver, novel_url):
    try:
        driver.get(novel_url)
        time.sleep(5)
        chapter_elements = driver.find_elements(By.CSS_SELECTOR, ".episode-list a")
        chapter_urls = ["https://novelpia.com" + elem.get_attribute("href") for elem in chapter_elements]
        return chapter_urls
    except:
        st.error("🚨 소설 목록을 가져오는 중 오류 발생!")
        return []

# 비동기 방식으로 각 화의 텍스트 가져오기
async def get_chapter_text(driver, chapter_url):
    try:
        driver.get(chapter_url)
        time.sleep(3)
        content = driver.find_element(By.CSS_SELECTOR, ".novel-content")
        return content.text
    except:
        return ""

# 비동기 방식으로 텍스트 파일 저장
async def export_to_txt(texts, filename="novel.txt"):
    async with aiofiles.open(filename, "w", encoding="utf-8") as f:
        for text in texts:
            await f.write(text + "\n\n")
    return filename

# Streamlit UI
st.title("📖 노벨피아 소설 크롤러")
st.write(f"현재 기기: **{device_type}**")

# 로그인 상태 확인
if st.session_state.login_success:
    st.success("🔑 자동 로그인 완료!")

# 사용자 입력
user_id = st.text_input("📌 노벨피아 ID 입력", value="자동 로그인 사용 가능")
user_pw = st.text_input("🔑 노벨피아 비밀번호 입력", type="password", value="자동 로그인 사용 가능")
novel_url = st.text_input("🔗 노벨피아 소설 URL을 입력하세요:")

if st.button("🚀 크롤링 시작"):
    if novel_url:
        st.info("📡 크롬 드라이버 실행 중...")
        driver = init_driver()
        if driver is None:
            st.stop()

        st.info("🔑 로그인 중...")
        login_novelpia(driver, user_id, user_pw)

        if not st.session_state.login_success:
            st.error("🚨 로그인 실패! 프로그램을 종료합니다.")
            driver.quit()
            st.stop()

        st.info("📄 소설의 모든 화 URL 가져오는 중...")
        chapter_urls = get_chapter_urls(driver, novel_url)

        if not chapter_urls:
            st.error("⚠️ 화 목록을 가져오지 못했습니다.")
        else:
            st.success(f"✅ {len(chapter_urls)}개의 화를 찾았습니다.")

            all_texts = []
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def fetch_all_chapters():
                tasks = [get_chapter_text(driver, url) for url in chapter_urls]
                progress_bar = st.progress(0)
                results = []
                for idx, task in enumerate(asyncio.as_completed(tasks)):
                    results.append(await task)
                    progress_bar.progress((idx + 1) / len(tasks))
                return results

            all_texts = loop.run_until_complete(fetch_all_chapters())

            output_file = loop.run_until_complete(export_to_txt(all_texts))
            st.success(f"🎉 크롤링 완료! 파일 저장됨: {output_file}")

            st.session_state.download_ready = True

        driver.quit()

# 다운로드 버튼 유지
if st.session_state.download_ready:
    st.download_button("⬇️ 텍스트 파일 다운로드", open("novel.txt", "rb"), file_name="novel.txt")