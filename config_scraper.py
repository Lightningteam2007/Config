import os
import re
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import logging
import asyncio
import time
from datetime import datetime

# تنظیمات پیشرفته لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تنظیمات
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("Environment variable BOT_TOKEN is not set!")
    raise ValueError("BOT_TOKEN is required")

SOURCE_CHANNELS = [
    "https://t.me/s/V2RAYROZ",
    "https://t.me/s/v2rayngvpn",
    "https://t.me/s/V2ray_Alpha"
]
DEST_CHANNEL = "@configs_freeiran"
CONFIG_PATTERN = r'(vmess://[^\s]+|vless://[^\s]+|trojan://[^\s]+|ss://[^\s]+)'
OUTPUT_FILE = "processed_configs.txt"
WEBSITE_URL = "https://lightningteam2007.github.io/Configfree.github.io/"
MAX_MESSAGE_LENGTH = 4000  # محدودیت تلگرام
REQUEST_TIMEOUT = 20  # زمان انتظار برای درخواست‌ها
DELAY_BETWEEN_SENDS = 1.5  # تاخیر بین ارسال پیام‌ها

def read_processed_configs():
    try:
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                return set(f.read().splitlines())
        return set()
    except Exception as e:
        logger.error(f"Error reading processed configs: {e}")
        return set()

def split_message(message, max_length=MAX_MESSAGE_LENGTH):
    """تقسیم پیام به بخش‌های کوچکتر با حفظ ساختار"""
    if len(message) <= max_length:
        return [message]
    
    parts = []
    current_part = ""
    
    for line in message.split('\n'):
        if len(current_part) + len(line) + 1 > max_length and current_part:
            parts.append(current_part.strip())
            current_part = line + '\n'
        else:
            current_part += line + '\n'
    
    if current_part:
        parts.append(current_part.strip())
    
    return parts

def scrape_channel(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        logger.info(f"Scraping channel: {url}")
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all("div", class_=lambda x: x and "tgme_widget_message_bubble" in x)
        
        configs = []
        for msg in messages:
            text_elements = msg.find_all("div", class_="tgme_widget_message_text")
            for text_elem in text_elements:
                text = text_elem.get_text(strip=True)
                found_configs = re.findall(CONFIG_PATTERN, text)
                if found_configs:
                    logger.debug(f"Found {len(found_configs)} config(s) in message")
                    configs.extend(found_configs)
        
        logger.info(f"Found {len(configs)} config(s) from {url}")
        return configs

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while scraping {url}: {str(e)}")
        return []

async def send_to_telegram(configs):
    if not configs:
        logger.info("No new configs to send")
        return
    
    bot = Bot(token=TOKEN)
    processed_configs = read_processed_configs()
    new_configs = [c for c in configs if c not in processed_configs]
    
    if not new_configs:
        logger.info("All configs already processed")
        return
    
    logger.info(f"Preparing to send {len(new_configs)} new config(s)")
    
    for config in new_configs:
        try:
            message = (
                "🌟 *کانفیگ جدید* 🌟\n\n"
                "🔗 کانفیگ (کپی‌شدنی):\n"
                f"<code>{config}</code>\n\n"
                "🌐 وبسایت برای کانفیگ‌های بیشتر:\n"
                f"{WEBSITE_URL}\n\n"
                "📌 کانال ما: @configs_freeiran\n"
                "⏱ زمان: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
                "============================"
            )
            
            message_parts = split_message(message)
            for part in message_parts:
                await bot.send_message(
                    chat_id=DEST_CHANNEL,
                    text=part,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                logger.debug(f"Message part sent for config: {config[:30]}...")
                await asyncio.sleep(DELAY_BETWEEN_SENDS)
            
            # ذخیره کانفیگ پردازش شده
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"{config}\n")
            
            logger.info(f"Config sent successfully: {config[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to send config {config[:30]}...: {str(e)}")
            await asyncio.sleep(5)  # تاخیر بیشتر در صورت خطا

async def main():
    logger.info("=== Starting Scraper ===")
    start_time = time.time()
    
    all_configs = []
    for channel in SOURCE_CHANNELS:
        configs = scrape_channel(channel)
        all_configs.extend(configs)
        await asyncio.sleep(2)  # تاخیر بین اسکراپ کردن کانال‌های مختلف
    
    if all_configs:
        await send_to_telegram(all_configs)
    else:
        logger.info("No configs found in any channel")
    
    logger.info(f"Finished in {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
