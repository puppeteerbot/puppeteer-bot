import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
from collections import deque

CACHE_DIR = "yt_downloads"
os.makedirs(CACHE_DIR, exist_ok=True)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.song_queues = {}
        self.song_initiators = {}
        self.song_loops = {}
        self.ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(CACHE_DIR, "%(id)s.%(ext)s"),
            "noplaylist": True,
        }

    def search_youtube(self, query):
        with YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
            video_url = f"https://www.youtube.com/watch?v={info['id']}"
            return video_url, info["id"]

    def download_audio(self, video_url, video_id):
        # Ensure the cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)

        audio_path = os.path.join(CACHE_DIR, f"{video_id}.mp3")

        # Debugging: Check if the file already exists
        if os.path.exists(audio_path):
            print(f"Cache hit: {audio_path}")
            return audio_path  # Return cached file

        # Debugging: Log cache miss
        print(f"Cache miss: {audio_path}. Downloading...")

        # yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_path.replace(".mp3", ""),  # Save audio as video_id.mp3
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": False,  # Keep quiet mode off for debugging
        }

        # Download using yt-dlp
        with YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
            except Exception as e:
                print(f"Error downloading {video_url}: {e}")
                raise

        # Check if the file exists after download
        if os.path.exists(audio_path):
            print(f"Downloaded successfully: {audio_path}")
            return audio_path
        else:
            raise FileNotFoundError(f"File not found after download: {audio_path}")

    def join_vc(self, ctx):
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            guild_id = ctx.guild.id
            if (
                guild_id not in self.voice_clients
                or not self.voice_clients[guild_id].is_connected()
            ):
                return voice_channel
            else:
                return None
        else:
            return "You need to be in a voice channel."

    def queue_next_song(self, guild_id):
        if guild_id in self.song_queues and self.song_queues[guild_id]:
            if self.song_loops.get(guild_id, False):
                # Re-add the current song to the queue for looping
                self.song_queues[guild_id].append(self.song_queues[guild_id][0])
            return self.song_queues[guild_id].popleft()
        return None

    async def play_next_song(self, ctx):
        guild_id = ctx.guild.id
        next_song = self.queue_next_song(guild_id)
        if next_song:
            video_url, video_id = next_song["url"], next_song["id"]
            audio_path = self.download_audio(video_url, video_id)
            source = FFmpegPCMAudio(audio_path)
            self.voice_clients[guild_id].play(
                source,
                after=lambda e: self.bot.loop.create_task(self.play_next_song(ctx)),
            )
            return f"Now playing: {video_url}"
        else:
            await self.bot.change_presence(activity=None)
            return "Queue is empty. No more songs to play."

    @commands.command()
    async def join(self, ctx):
        voice_channel = self.join_vc(ctx)
        if isinstance(voice_channel, str):  # Error message
            await ctx.send(voice_channel)
            return
        guild_id = ctx.guild.id
        vc = await voice_channel.connect()
        self.voice_clients[guild_id] = vc
        await ctx.send(f"Joined {voice_channel}.")

    @commands.command()
    async def play(self, ctx, *, search_query):
        guild_id = ctx.guild.id
        if (
            guild_id not in self.voice_clients
            or not self.voice_clients[guild_id].is_connected()
        ):
            await self.join(ctx)
        video_url, video_id = self.search_youtube(search_query)
        song_info = {"url": video_url, "id": video_id, "initiator": ctx.author}
        if guild_id not in self.song_queues:
            self.song_queues[guild_id] = deque()
        self.song_queues[guild_id].append(song_info)
        if not self.voice_clients[guild_id].is_playing():
            now_playing = await self.play_next_song(ctx)
            await ctx.send(now_playing)
        else:
            await ctx.send(f"Added to queue: {video_url}")

    @commands.command()
    async def skip(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            if self.song_queues[guild_id]:
                current_song = self.song_queues[guild_id][0]
                if (
                    ctx.author != current_song["initiator"]
                    and not ctx.author.guild_permissions.administrator
                ):
                    await ctx.send("You don't have permission to skip this song.")
                    return
                # Disable looping for the current song
                self.song_loops[guild_id] = False
                self.voice_clients[guild_id].stop()
                await ctx.send("Skipped the current song.")
        else:
            await ctx.send("No song is playing.")

    @commands.command()
    async def loop(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to toggle loop mode.")
            return
        guild_id = ctx.guild.id
        self.song_loops[guild_id] = not self.song_loops.get(guild_id, False)
        status = "enabled" if self.song_loops[guild_id] else "disabled"
        await ctx.send(f"Loop mode {status}.")

    @commands.command()
    async def stop(self, ctx):
        guild_id = ctx.guild.id

        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            current_song = (
                self.song_queues[guild_id][0]
                if guild_id in self.song_queues and self.song_queues[guild_id]
                else None
            )
            if (
                current_song
                and ctx.author != current_song["initiator"]
                and not ctx.author.guild_permissions.administrator
            ):
                await ctx.send("You don't have permission to stop the current song.")
                return

            # Stop playback
            self.voice_clients[guild_id].stop()

            # Clear the queue
            if guild_id in self.song_queues:
                self.song_queues[guild_id].clear()

            await ctx.send("Stopped playback and cleared the queue.")
        else:
            await ctx.send("No song is playing or queue is empty.")

    @commands.command()
    async def leave(self, ctx):
        guild_id = ctx.guild.id
        if (
            guild_id in self.voice_clients
            and self.voice_clients[guild_id].is_connected()
        ):
            current_song = (
                self.song_queues[guild_id][0]
                if guild_id in self.song_queues and self.song_queues[guild_id]
                else None
            )
            if (
                current_song
                and ctx.author != current_song["initiator"]
                and not ctx.author.guild_permissions.administrator
            ):
                await ctx.send("You don't have permission to disconnect the bot.")
                return
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]
            self.song_queues.pop(guild_id, None)
            await ctx.send("Disconnected.")
        else:
            await ctx.send("Bot is not connected.")


# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(Music(bot))
