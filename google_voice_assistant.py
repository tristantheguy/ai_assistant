"""Google Voice automation assistant.

This module uses Selenium to log into Google Voice, send and receive
SMS messages, and periodically report system status. It does not
circumvent captchas or two-factor authentication; manual intervention
is required if Google prompts for additional verification.
"""

from __future__ import annotations

import os
import time
import json
import logging
from datetime import datetime
from typing import List

import psutil
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


LOG_DIR = "ai_memos"
LOG_PATH = os.path.join(LOG_DIR, "voice_log.txt")
CHECKIN_INTERVAL = 60 * 60  # seconds


def _setup_logging() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[logging.FileHandler(LOG_PATH, "a", encoding="utf-8"), logging.StreamHandler()],
    )


def create_driver() -> webdriver.Chrome:
    """Return a headless Chrome driver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def login_to_google_voice(driver: webdriver.Chrome, email: str, password: str) -> bool:
    """Log into Google Voice. Returns True on success."""
    driver.get("https://voice.google.com")
    time.sleep(2)

    if "signin" in driver.current_url:
        logging.info("Entering Google credentials.")
        driver.find_element(By.ID, "identifierId").send_keys(email, Keys.ENTER)
        time.sleep(2)
        driver.find_element(By.NAME, "password").send_keys(password, Keys.ENTER)
        time.sleep(5)

    if "challenge" in driver.current_url:
        logging.warning("Manual login challenge detected. Please complete it in the browser.")
        while "challenge" in driver.current_url:
            time.sleep(2)

    return "voice.google.com" in driver.current_url


def send_text(driver: webdriver.Chrome, phone_number: str, message: str) -> None:
    logging.info("Sending SMS to %s: %s", phone_number, message)
    driver.get("https://voice.google.com/messages")
    time.sleep(3)
    new_button = driver.find_element(By.CSS_SELECTOR, "button[gv-test-id='new-message-button']")
    new_button.click()
    time.sleep(1)
    number_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Phone number']")
    number_input.send_keys(phone_number, Keys.ENTER)
    time.sleep(1)
    box = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
    box.send_keys(message, Keys.ENTER)


def get_recent_messages(driver: webdriver.Chrome) -> List[str]:
    driver.get("https://voice.google.com/messages")
    time.sleep(3)
    texts = driver.find_elements(By.CSS_SELECTOR, "div[gv-message-text]")
    return [t.text for t in texts[-5:]]


def monitor_system() -> str:
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    return f"CPU: {cpu}% | MEM: {mem}%"


class VoiceAssistant:
    def __init__(self, phone: str, driver: webdriver.Chrome) -> None:
        self.phone = phone
        self.driver = driver
        self.last_checkin = 0

    def event_handler(self) -> None:
        usage = monitor_system()
        if psutil.cpu_percent() > 90:
            send_text(self.driver, self.phone, f"High CPU usage! {usage}")
        elif time.time() - self.last_checkin > CHECKIN_INTERVAL:
            self.periodic_checkin()

    def periodic_checkin(self) -> None:
        msg = "Still alive. Your computer hasn't burst into flames. Yet."
        send_text(self.driver, self.phone, msg)
        self.last_checkin = time.time()

    def handle_reply(self) -> None:
        messages = get_recent_messages(self.driver)
        if messages and messages[-1].startswith("ping"):
            send_text(self.driver, self.phone, "pong")


def main() -> None:
    _setup_logging()
    email = os.getenv("GV_EMAIL") or input("Google email: ")
    password = os.getenv("GV_PASS") or input("Google password: ")
    my_phone = os.getenv("MY_PHONE") or input("Your phone number: ")

    driver = create_driver()
    if not login_to_google_voice(driver, email, password):
        logging.error("Failed to login to Google Voice.")
        return

    assistant = VoiceAssistant(my_phone, driver)
    schedule.every(5).minutes.do(assistant.event_handler)
    schedule.every(2).minutes.do(assistant.handle_reply)

    logging.info("Assistant running. Press Ctrl+C to quit.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
