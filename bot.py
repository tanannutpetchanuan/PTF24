import discord
from discord.ext import commands
import youtube_dl
import asyncio
import os
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('MTUwMDM4MDY1OTcyNDU4NzAzOA.GeJc8Q.qWwfCzaAM5lokCt5qKTKZusooIu6iqp8y5cJrI')

youtube_dl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(youtube_dl_opts)

# สร้าง bot object
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

# เมื่อบอทพร้อมทำงาน
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')

class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""

class InvalidVoiceChannel(VoiceConnectionError):
    """Custom exception class when the voice channel is invalid."""

# Class สำหรับจัดการ voice commands
class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None

    # เช็คว่าบอทอยู่ใน VC หรือไม่
    def is_connected(self):
        return self.voice_client and self.voice_client.is_connected()

    # Command สำหรับเข้าร่วม VC
    @commands.command(name='join', invoke_without_subcommand=True)
    async def join(self, ctx):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if destination is None:
            await ctx.send("คุณต้องอยู่ใน voice channel ก่อนครับ")
            return

        if self.is_connected():
            await self.voice_client.move_to(destination)
        else:
            try:
                self.voice_client = await destination.connect()
                await ctx.send(f"เข้าร่วม {destination.name} แล้วครับ")
            except Exception as e:
                await ctx.send(f"เกิดข้อผิดพลาดในการเข้าร่วม: {e}")

    # Command สำหรับเล่นเพลง
    @commands.command(name='play')
    async def play(self, ctx, *, search: str):
        """Plays a song from youtube"""

        if not self.is_connected():
            await ctx.invoke(self.join)

        try:
            # ค้นหาข้อมูลเพลงจาก YouTube
            data = ytdl.extract_info(f"ytsearch:{search}", download=False, process=True)
            if data['entries']:
                data = data['entries'][0]
        except Exception as e:
            await ctx.send(f"เกิดข้อผิดพลาดในการค้นหา: {e}")
            return

        # สร้าง URL ของเพลง
        url = data['url']
        title = data['title']

        # เล่นเพลง
        try:
            self.voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options), after=lambda e: print(f'Player error: {e}') if e else None)
            self.voice_client.source = discord.PCMVolumeTransformer(self.voice_client.source)
            self.voice_client.source.volume = 0.5

            await ctx.send(f"กำลังเล่น: {title}")
        except Exception as e:
            await ctx.send(f"เกิดข้อผิดพลาดในการเล่น: {e}")

    # Command สำหรับหยุดเพลง
    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        if not self.is_connected():
            return await ctx.send("ไม่ได้กำลังเล่นอะไรอยู่ครับ")

        self.voice_client.stop()
        #await self.voice_client.disconnect()  # ไม่ต้อง disconnect ทุกครั้ง
        await ctx.send("หยุดเล่นครับ")

    # Command สำหรับออกจาก VC
    @commands.command(name='leave')
    async def leave(self, ctx):
        """Leaves the voice channel"""
        if not self.is_connected():
            return await ctx.send("ไม่ได้อยู่ใน voice channel ครับ")

        await self.voice_client.disconnect()
        self.voice_client = None
        await ctx.send("ออกจาก voice channel แล้วครับ")

# เพิ่ม Cog เข้าไปใน Bot
async def setup(bot):
    await bot.add_cog(MusicBot(bot))

# รันบอท
async def main():
    async with bot:
        await setup(bot)
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())