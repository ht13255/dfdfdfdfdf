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

# 기기별 UI 최적화 (User-Agent 확인)
device_type = "PC"
def detect_device():
    global device_type
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={USER_AGENT}")
        driver = uc.Chrome(options=options)
        driver.get("https://www.whatismybrowser.com/detect/what-is-my-user-agent")
        user_agent = driver.find_element(By.TAG_NAME, "body").text
        driver.quit()

        if "Android" in user_agent or "iPhone" in user_agent:
            device_type = "모바일"
        elif "iPad" in user_agent or "Tablet" in user_agent:
            device_type = "태블릿"
        else:
            device_type = "PC"
    except:
        device_type = "PC"

if "device_type" not in st.session_state:
    detect_device()
    st.session_state.device_type = device_type

# Streamlit UI
st.title("📖 노벨피아 소설 크롤러")
st.write(f"현재 기기: **{st.session_state.device_type}**")