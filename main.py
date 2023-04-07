import os
import discord
from time import sleep
from discord.ext import commands
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

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

def get_tee(username: str) -> int:
    url = f"https://kenkoooo.com/atcoder/#/user/{username}"
    driver.get(url)
    sleep(20)  # wait until page loaded

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    tee = soup.select("#root > div > div.my-5.container > div > div.my-3.row > div:nth-child(9) > h3")
    return int(tee[0].text)

def update_tee() -> None:
    df = pd.read_csv("users.csv")
    for _, row in df.iterrows():
        row["last_tee"] = row["tee"]
        row["tee"] = get_tee(row["username"]) - row["initial_tee"]
    df.to_csv("users.csv", index=False)
    return

def create_message() -> str:
    update_tee()
    updates = []
    message = ""
    for _, row in df.iterrows():
        username = row["username"]
        tee = row["tee"]
        last_tee = row["tee"]
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
        message += f"{rank}. {username}\n"
        rank += 1
    return message

@client.event
async def on_ready():
    message = create_message()
    channel_id = os.environ["CHANNEL_ID"]
    channel = client.get_channel(int(channel_id))
    await channel.send(message)

@bot.command(name='update_tee')
async def update(ext):
    message = create_message()
    await ext.send(message)

client.run(os.environ["BOT_TOKEN"])
