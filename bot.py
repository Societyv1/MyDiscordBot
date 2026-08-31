import asyncio
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

# ตั้งค่าบอท Discord และเปิดสิทธิ์การอ่านข้อความ/เห็นสมาชิก
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # เปิดตาวิเศษให้บอทมองเห็นคนในเซิร์ฟเวอร์
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
                    model='gemini-1.5-flash', # แนะนำให้ใช้ 1.5-flash เพราะ 3.5 ยังไม่มีนะ!
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

@bot.command()
async def drag(ctx, member: discord.Member, times: int = 3):
    # --- โค้ดใหม่: จำกัดจำนวนรอบสูงสุดที่ 20 รอบ ---
    if times > 20:
        await ctx.send("เยอะไป! เดี๋ยวบอทบิน ขอจำกัดไว้ที่ 20 รอบละกันนะ 🤣")
        times = 20 
    # ---------------------------------------------

    # 1. เช็คว่าคนที่โดนแท็กอยู่ในห้องเสียงมั้ย
    if not member.voice or not member.voice.channel:
        await ctx.send(f"จะดึงยังไงล่ะ! {member.display_name} ไม่ได้อยู่ในห้องเสียงสักหน่อย 😅")
        return

    original_channel = member.voice.channel
    
    # 2. หาห้องเสียงอื่นในเซิร์ฟเวอร์เพื่อเอาไว้สลับไปมา
    available_channels = [vc for vc in ctx.guild.voice_channels if vc.id != original_channel.id]
    
    if not available_channels:
        await ctx.send("ต้องสร้างห้องเสียงสำรองไว้อย่างน้อย 1 ห้องนะ ถึงจะสลับไปมาให้เกิดเสียงได้!")
        return

    temp_channel = available_channels[0] # เลือกห้องแรกที่เจอเพื่อเอาไปสลับ

    await ctx.send(f"🚨 จัดให้! กำลังลาก {member.mention} สลับห้องรัวๆ {times} รอบ ให้หูแตกไปเลย!")

    # 3. เริ่มมหกรรมการดึงสลับห้อง
    try:
        for i in range(times):
            await member.move_to(temp_channel)
            await asyncio.sleep(0.5) # หน่วงเวลา 0.5 วินาทีเพื่อไม่ให้บอทโดนแบนสแปม
            await member.move_to(original_channel)
            await asyncio.sleep(0.5)
            
        await ctx.send("กระชากเสร็จแล้ว! หวังว่าจะตื่นมาแบกเกมนะ 🤣")
        
    except discord.Forbidden:
        await ctx.send("❌ บอทไม่มีสิทธิ์ดึงคนอะเตอร์! ต้องไปให้ยศบอทเปิดสิทธิ์ 'Move Members' (ย้ายสมาชิก) ก่อนนะ")
    except Exception as e:
        await ctx.send("มีบางอย่างผิดพลาด อาจจะดึงเร็วไปหรือเพื่อนหนีออกห้องไปแล้ว")

# เรียกใช้เว็บจำลอง
keep_alive()
# สั่งเดินเครื่องบอท!
bot.run(DISCORD_TOKEN)