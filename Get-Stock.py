import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

now = datetime.now()

chrome_options = Options()
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--disable-gpu")

# ===== 信件設定 =====
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("EMAIL_ADDRESS")

# ===== 爬蟲網址 =====
URL = "https://store.google.com/tw/config/pixel_10_pro?hl=zh-TW&selections=eyJwcm9kdWN0RmFtaWx5IjoiY0dsNFpXeGZNVEJmY0hKdiIsInZhcmlhbnRzIjpbWyI3IiwiTVRFPSJdLFsiMiIsIk13PT0iXSxbIjEiLCJNalUyIl1dfQ%3D%3D"

# ===== 寄信函式 =====
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        print('Login')
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# ===== 檢查某個顏色的庫存 =====
def check_color_stock(color_label):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(URL)
    if now.minute == 0:
        print("排程整點回報")
    
    btn = driver.find_element(By.XPATH, f'//button[@data-tracking-label="{color_label}"]')
    btn.click()
    time.sleep(1)
    print(color_label)
    try:
        button = driver.find_element(By.XPATH, '//button[@data-tracking-label="256 GB"]')
        text = button.text.strip()        
        if "缺貨中" not in text:
            send_email(f"{color_label} Pixel 10 Pro 256GB 有貨了！", f"目前按鈕內容：{text}\n快去搶購！")
        else:
            print(text)
    except Exception as e:  
        print(f"[{color_label}] 抓取失敗:", e)        
    print('----------------------')
    driver.quit()


# ===== 主程式：先抓所有顏色，再用多執行緒跑 =====
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
driver.get(URL)
time.sleep(3)

sections = driver.find_elements(By.CSS_SELECTOR, 'section.tSHDcb.uKg8Bd')
color_labels = []

for sec in sections:
    try:
        btn = sec.find_element(By.TAG_NAME, "button")
        color = btn.get_attribute("data-tracking-label")
        color_labels.append(color)
    except:
        pass

driver.quit()

# 用 ThreadPoolExecutor 開多執行緒，每個顏色獨立檢查
with ThreadPoolExecutor(max_workers=len(color_labels)) as executor:
    print('Start')
    executor.map(check_color_stock, color_labels)