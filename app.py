import streamlit as st
import os
import asyncio
import aiofiles
import pickle
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# **Chrome 및 ChromeDriver 경로 설정 (Streamlit Cloud용)**
CHROME_PATH = "/usr/bin/chromium"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"

# **Chrome이 설치되지 않았다면 설치 (Streamlit Cloud 실행 환경)**
if not os.path.exists(CHROME_PATH) or not os.path.exists(CHROMEDRIVER_PATH):
    os.system("apt update && apt install -y chromium chromium-driver")

# **Selenium 드라이버 설정**
def init_driver():
    chrome_options = Options()
    chrome_options.binary_location = CHROME_PATH  # Chrome 실행 파일 경로 설정
    chrome_options.add_argument("--headless=new")  # 백그라운드 실행
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # ChromeDriver 경로 설정
    chrome_service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=chrome_service, options=chrome_options)

# **Streamlit UI**
st.title("📖 노벨피아 소설 크롤러")

# **사용자 입력 필드**
st.subheader("🔑 로그인 정보 입력")
user_id = st.text_input("📌 노벨피아 ID 입력", key="user_id")
user_pw = st.text_input("🔑 노벨피아 비밀번호 입력", type="password", key="user_pw")

st.subheader("📖 소설 크롤링")
novel_url = st.text_input("🔗 노벨피아 소설 URL 입력", key="novel_url")

# **자동 로그인 기능**
def login_novelpia(driver, user_id, user_pw):
    driver.get("https://novelpia.com/login")
    time.sleep(3)

    if os.path.exists("novelpia_cookies.pkl"):
        with open("novelpia_cookies.pkl", "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(3)

        if "logout" in driver.page_source:
            return True

    driver.find_element(By.NAME, "email").send_keys(user_id)
    driver.find_element(By.NAME, "password").send_keys(user_pw)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(5)

    if "logout" in driver.page_source:
        with open("novelpia_cookies.pkl", "wb") as f:
            pickle.dump(driver.get_cookies(), f)
        return True
    else:
        return False

# **소설의 모든 화 URL 가져오기**
def get_chapter_urls(driver, novel_url):
    driver.get(novel_url)
    time.sleep(5)
    chapter_elements = driver.find_elements(By.CSS_SELECTOR, ".episode-list a")
    return ["https://novelpia.com" + elem.get_attribute("href") for elem in chapter_elements]

# **비동기 방식으로 각 화의 텍스트 가져오기**
async def get_chapter_text(driver, chapter_url):
    driver.get(chapter_url)
    time.sleep(3)
    try:
        content = driver.find_element(By.CSS_SELECTOR, ".novel-content")
        return content.text
    except:
        return ""

# **비동기 방식으로 텍스트 파일 저장**
async def export_to_txt(texts, filename="novel.txt"):
    async with aiofiles.open(filename, "w", encoding="utf-8") as f:
        for text in texts:
            await f.write(text + "\n\n")
    return filename

# **크롤링 실행 버튼**
if st.button("🚀 크롤링 시작"):
    if novel_url and user_id and user_pw:
        st.info("📡 크롬 드라이버 실행 중...")
        driver = init_driver()

        st.info("🔑 로그인 중...")
        if not login_novelpia(driver, user_id, user_pw):
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
    else:
        st.warning("⚠️ 로그인 정보와 소설 URL을 모두 입력해주세요.")

# **다운로드 버튼 유지**
if "download_ready" in st.session_state and st.session_state.download_ready:
    st.download_button("⬇️ 텍스트 파일 다운로드", open("novel.txt", "rb"), file_name="novel.txt")