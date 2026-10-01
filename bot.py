import os
import random
import asyncio
import threading
from abc import ABC, abstractmethod

import requests
from curl_cffi import requests as cffi_requests
from flask import Flask
import discord
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

app = Flask('')
intents = discord.Intents.default()
client = discord.Client(intents=intents)


class StreamChecker(ABC):
    def __init__(self, identifier, nombre, mencionar_everyone):
        self.identifier = identifier
        self.nombre = nombre
        self.mencionar_everyone = mencionar_everyone
        self.online = False

    @abstractmethod
    def check_live(self):
        ...

    @abstractmethod
    async def notify(self, live_data):
        ...


class WhowatchChecker(StreamChecker):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://whowatch.tv/",
        "Origin": "https://whowatch.tv",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        headers = dict(self.HEADERS)
        headers["X-Whowatch-Device-Id"] = (
            f"{random.randint(10**12, 10**13-1)}-{random.randint(10**7, 10**8-1)}"
        )
        self.session.headers.update(headers)

    def check_live(self):
        url = f"https://api.whowatch.tv/users/{self.identifier}/publishing"
        try:
            r = self.session.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data and "id" in data:
                    return data
        except Exception:
            pass
        return None

    async def notify(self, live_data):
        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            return
        l_id = live_data.get("id")
        titulo = live_data.get("title", "Is now live!")
        mencion = " @everyone" if self.mencionar_everyone else ""
        msg = (
            f"**{self.nombre} esta en vivo**{mencion}\n"
            f"> {titulo}\nhttps://whowatch.tv/viewer/{l_id}"
        )
        await channel.send(msg)


class KickChecker(StreamChecker):
    def check_live(self):
        url = f"https://kick.com/api/v1/channels/{self.identifier}"
        try:
            r = cffi_requests.get(url, impersonate="chrome", timeout=10)
            if r.status_code == 200:
                data = r.json()
                livestream = data.get("livestream")
                if livestream:
                    return {
                        "title": livestream.get("session_title", "Is now live!"),
                        "category": (livestream.get("categories") or [{}])[0].get("name", "No category"),
                        "avatar": (data.get("user") or {}).get("profile_pic", ""),
                    }
        except Exception:
            pass
        return None

    async def notify(self, live_data):
        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            return
        mencion = "@everyone" if self.mencionar_everyone else ""
        embed = discord.Embed(
            title=f"{self.nombre} is now live on Kick!",
            url=f"https://kick.com/{self.identifier}",
            color=0x53FC18,
        )
        embed.add_field(name="Title", value=live_data["title"], inline=False)
        embed.add_field(name="Category", value=live_data["category"], inline=False)
        embed.set_footer(text="Kick.com")
        if live_data.get("avatar"):
            embed.set_thumbnail(url=live_data["avatar"])
        await channel.send(content=mencion, embed=embed)


def cargar_checkers():
    checkers = []
    ww_raw = os.getenv("WHOWATCH_STREAMERS", "")
    for entry in filter(None, ww_raw.split(",")):
        uid, nombre, everyone = entry.split("|")
        checkers.append(WhowatchChecker(uid, nombre, everyone == "1"))

    kick_raw = os.getenv("KICK_STREAMERS", "")
    for entry in filter(None, kick_raw.split(",")):
        username, nombre, everyone = entry.split("|")
        checkers.append(KickChecker(username, nombre, everyone == "1"))

    return checkers


CHECKERS = cargar_checkers()


async def loop_infinito():
    await client.wait_until_ready()
    while True:
        for checker in CHECKERS:
            live_data = await asyncio.to_thread(checker.check_live)
            if live_data and not checker.online:
                checker.online = True
                await checker.notify(live_data)
            elif not live_data:
                checker.online = False
        await asyncio.sleep(30)


@app.route('/')
def home():
    return "OK"


task_iniciada = False

@client.event
async def on_ready():
    global task_iniciada
    if not task_iniciada:
        task_iniciada = True
        client.loop.create_task(loop_infinito())


def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", "10000")))


if __name__ == "__main__":
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    client.run(BOT_TOKEN)