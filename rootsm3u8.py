from pyrogram import Client, filters
import requests

# إعدادات البوت
api_id = 20944746
api_hash = "d169162c1bcf092a6773e685c62c3894"
bot_token = "8077469209:AAEGeu6O3m9c8DsJCczffg6BdYzLq2SzRXA"

app = Client("vimeo_downloader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

def get_vimeo_download_link(video_id):
    url = f"https://api.vimeo.com/videos/{video_id}"
    headers = {
        "Authorization": "bearer cb4db7e6644148561e3ff38c665725ee"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("❌ فشل في الوصول إلى Vimeo API")
            return None

        data = response.json()

        # 🔍 نبحث في كل شيء داخل JSON
        def search_for_link(obj):
            if isinstance(obj, dict):
                # إذا العنصر يحتوي على الرابط المطلوب
                if (
                    obj.get("quality") == "hls" and
                    obj.get("rendition") == "adaptive" and
                    obj.get("type") == "video/mp4" and
                    f"{video_id}.m3u8" in obj.get("link", "")
                ):
                    return obj["link"]

                # نتابع البحث داخل القاموس
                for value in obj.values():
                    result = search_for_link(value)
                    if result:
                        return result

            elif isinstance(obj, list):
                # نبحث في كل عنصر داخل القائمة
                for item in obj:
                    result = search_for_link(item)
                    if result:
                        return result

            return None

        return search_for_link(data)

    except Exception as e:
        print(f"Error fetching video {video_id}: {e}")
        return None

async def send_long_message(client, chat_id, text):
    max_length = 4096  # الحد الأقصى لطول الرسالة في Telegram
    if len(text) <= max_length:
        await client.send_message(chat_id, text, disable_web_page_preview=True)
        return
    
    # تقسيم الرسالة إلى أجزاء
    parts = []
    while text:
        if len(text) > max_length:
            part = text[:max_length]
            first_newline = part.rfind('\n')
            if first_newline != -1:
                part = text[:first_newline]
        else:
            part = text
        parts.append(part)
        text = text[len(part):].lstrip('\n')
    
    # إرسال الأجزاء واحدًا تلو الآخر
    for part in parts:
        await client.send_message(chat_id, part, disable_web_page_preview=True)

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply("👋 أرسل معرفات فيديوهات Vimeo (سطر لكل معرف)، وسأرسل لك روابط التحميل المباشرة بصيغة HLS.")

@app.on_message(filters.text & ~filters.command("start"))
async def handle_video_ids(client, message):
    video_ids = message.text.strip().splitlines()
    results = []

    for video_id in video_ids:
        video_id = video_id.strip()
        if not video_id.isdigit():
            continue

        link = get_vimeo_download_link(video_id)
        if link:
            results.append(link)

    if results:
        reply_text = "✅ روابط التحميل المباشرة:\n\n" + "\n".join(results)
        await send_long_message(client, message.chat.id, reply_text)
    else:
        await message.reply("😢 لم يتم العثور على روابط بصيغة m3u8 لهذا المعرف.")

app.run()
