import os
import re
import requests
from bs4 import BeautifulSoup
from telegram.ext import Application
import logging
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات
TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNELS = [
    "https://t.me/V2RAYROZ",
    "https://t.me/v2rayngvpn",
    "https://t.me/V2ray_Alpha"
]
DEST_CHANNEL = "@configs_freeiran"
CONFIG_PATTERN = r'(vmess://[^\s]+|vless://[^\s]+|trojan://[^\s]+|ss://[^\s]+)'
OUTPUT_FILE = "processed_configs.txt"

async def send_to_telegram(configs, application):
    bot = application.bot
    for config in configs:
        if config not in read_processed_configs():
            try:
                await bot.send_message(
                    chat_id=DEST_CHANNEL,
                    text=f"{config}\n\nمنبع: {DEST_CHANNEL}",
                    disable_web_page_preview=True
                )
                logger.info(f"کانفیگ به {DEST_CHANNEL} ارسال شد: {config}")
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{config}\n")
            except Exception as e:
                logger.error(f"خطا در ارسال کانفیگ: {e}")

def read_processed_configs():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def scrape_channel(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        messages = soup.find_all("div", class_="tgme_widget_message_text")
        configs = []
        for msg in messages:
            text = msg.get_text()
            found_configs = re.findall(CONFIG_PATTERN, text)
            configs.extend(found_configs)
        logger.info(f"کانفیگ‌های پیدا شده از {url}: {configs}")
        return configs
    except Exception as e:
        logger.error(f"خطا در اسکریپینگ {url}: {e}")
        return []

async def main():
    application = Application.builder().token(TOKEN).build()
    await application.initialize()
    
    all_configs = []
    for channel in SOURCE_CHANNELS:
        configs = scrape_channel(channel)
        all_configs.extend(configs)
    
    if all_configs:
        await send_to_telegram(all_configs, application)
    else:
        logger.info("هیچ کانفیگی پیدا نشد")
    
    try:
        await application.stop()
        logger.info("ربات متوقف شد")
    except Exception as e:
        logger.error(f"خطا در توقف ربات: {e}")

if __name__ == "__main__":
    asyncio.run(main())
