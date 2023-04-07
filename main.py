import os
import discord
from time import sleep
from datetime import datetime
from discord.ext import commands, tasks
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import asyncio

load_dotenv()
# selenium webdrivers
options = webdriver.ChromeOptions()
options.add_argument("--enable-javascript")
driver = webdriver.Chrome(options=options)

# discord clients
intents = discord.Intents.all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='/', intents=intents)

# pandas dataframes
df = pd.read_csv("users.csv")

async def get_tee(username: str) -> int:
    url = f"https://kenkoooo.com/atcoder/#/user/{username}"
    driver.get(url)
    await asyncio.sleep(20)  # wait until page loaded

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    tee = soup.select("#root > div > div.my-5.container > div > div.my-3.row > div:nth-child(9) > h3")
    return int(tee[0].text)

async def update_tee() -> None:
    for id, row in df.iterrows():
        df.at[id, "last_tee"] = row["tee"]
        tee = await get_tee(row["username"])
        df.at[id, "tee"] = tee - row["initial_tee"]
    df.to_csv("users.csv", index=False)
    return

async def create_message() -> str:
    await update_tee()
    updates = []
    message = ""
    for _, row in df.iterrows():
        username = row["username"]
        tee = row["tee"]
        last_tee = row["last_tee"]
        if tee != last_tee:
            updates.append(f"{username}: {last_tee} -> {tee}  (+{tee - last_tee})")
    if updates:
        message += ":information_source: **TEE速報**\n"
        for update in updates:
            message += update + "\n"
        message += "\n"
    message += ":crown: **Ranking**\n"
    rank = 1
    for _, row in df.sort_values("tee", ascending=False).iterrows():
        username = row["username"]
        tee = row["tee"]
        message += f"{rank}. {username} (TEE: {tee})\n"
        rank += 1
    return message

@client.event
async def on_ready():
    loop.start()
    return

@bot.command(name='update_tee')
async def update(ext):
    message = await create_message()
    await ext.send(message)

@tasks.loop(seconds=60)
async def loop():
    message = await create_message()
    channel = client.get_channel(int(os.environ["CHANNEL_ID"]))
    await channel.send(message)

client.run(os.environ["BOT_TOKEN"])
