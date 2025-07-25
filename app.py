import re
import os
from telegram.ext import Application, MessageHandler, filters
import logging
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNELS = ["@V2RAYROZ", "@v2rayngvpn", "@V2ray_Alpha"]
DESTINATION_CHANNEL = "@configs_freeiran"
CHANNEL_ID = "@configs_freeiran"

CONFIG_PATTERN = r'(vmess://[^\s]+|vless://[^\s]+|trojan://[^\s]+|ss://[^\s]+)'

async def forward_message(update, context):
    if update.channel_post and update.channel_post.text:
        message_text = update.channel_post.text
        configs = re.findall(CONFIG_PATTERN, message_text)
        for config in configs:
            try:
                await context.bot.send_message(
                    chat_id=DESTINATION_CHANNEL,
                    text=f"{config}\n\nمنبع: {CHANNEL_ID}",
                    disable_web_page_preview=True
                )
                logger.info(f"کانفیگ از {update.channel_post.chat.username} به {DESTINATION_CHANNEL} ارسال شد")
            except Exception as e:
                logger.error(f"خطا در ارسال کانفیگ: {e}")

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Chat(chat_id=SOURCE_CHANNELS) & ~filters.COMMAND,
        forward_message
    ))
    logger.info("ربات شروع به کار کرد...")
    await application.initialize()
    await application.updater.start_polling()
    await asyncio.sleep(300)  # 5 دقیقه اجرا می‌مونه
    await application.updater.stop()
    await application.stop()

if __name__ == '__main__':
    asyncio.run(main())
