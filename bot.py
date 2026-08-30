import os
from keep_alive import keep_alive
import discord
from discord.ext import commands
from google import genai
from dotenv import load_dotenv

# โหลดค่ารหัสลับจากไฟล์ .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ตั้งค่าให้เชื่อมต่อกับสมอง Gemini AI (ใช้ระบบตัวใหม่ล่าสุด)
client = genai.Client(api_key=GEMINI_API_KEY)

# ตั้งค่าบอท Discord และเปิดสิทธิ์การอ่านข้อความ
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ บอทออนไลน์พร้อมลุยแล้วในชื่อ: {bot.user}")

@bot.event
async def on_message(message):
    # ป้องกันไม่ให้บอทคุยกับตัวเอง
    if message.author == bot.user:
        return

    # บอทจะตอบก็ต่อเมื่อโดนแท็กชื่อ (@ชื่อบอท)
    if bot.user.mentioned_in(message):
        # ลบแท็กชื่อบอทออก เพื่อเอาแค่ข้อความคำถามเพียวๆ ไปให้ AI
        user_prompt = message.clean_content.replace(f"@{bot.user.name}", "").strip()

        if not user_prompt:
            await message.reply("มีอะไรให้ผมช่วยมั้ยครับ? พิมพ์ถามมาได้เลย!")
            return

        # ขึ้นสถานะว่า "บอทกำลังพิมพ์..." ระหว่างรอ AI ประมวลผล
        async with message.channel.typing():
            try:
                # โยนคำถามไปให้ Gemini ตอบ (รูปแบบโค้ดเวอร์ชันใหม่)
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=user_prompt,
                )
                reply_text = response.text

                # กฎของ Discord ส่งข้อความได้รอบละไม่เกิน 2,000 ตัวอักษร
                if len(reply_text) <= 2000:
                    await message.reply(reply_text)
                else:
                    # ถ้าคำตอบยาวไป ให้ตัดแบ่งส่งทีละท่อน
                    for i in range(0, len(reply_text), 2000):
                        await message.channel.send(reply_text[i:i + 2000])

            except Exception as e:
                print(f"Error: {e}")
                await message.reply("ขออภัยครับ ระบบ AI เกิดข้อผิดพลาดเล็กน้อย ลองถามใหม่อีกรอบนะครับ 😅")

    # จำเป็นต้องมีบรรทัดนี้ เพื่อให้บอทยังรับคำสั่ง (Commands) อื่นๆ ได้ปกติ
    await bot.process_commands(message)
# เรียกใช้เว็บจำลอง
keep_alive()
# สั่งเดินเครื่องบอท!
bot.run(DISCORD_TOKEN)