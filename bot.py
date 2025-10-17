import io
import logging
from threading import Thread

import discord
from discord import File
import aiohttp
from flask import Flask

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mirror-bot")

# -----------------------------
# Discord Bot Setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True  # Required to read messages
client = discord.Client(intents=intents)

SOURCE_CHANNEL_ID = 1289729762310225941  # Replace with your source channel ID
TARGET_CHANNEL_ID = 1428532464996974602  # Replace with your target channel ID

client.http_session = None  # Will hold aiohttp session

# -----------------------------
# Helper to fetch attachments
# -----------------------------
async def fetch_attachment(url):
    session = client.http_session
    if session is None:
        session = aiohttp.ClientSession()
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                logger.warning("Failed to fetch attachment %s (status %s)", url, resp.status)
                return None
            data = io.BytesIO(await resp.read())
            filename = url.split("/")[-1].split("?")[0]
            data.seek(0)
            return File(fp=data, filename=filename)
    except Exception:
        logger.exception("Error fetching attachment: %s", url)
        return None

# -----------------------------
# Discord Events
# -----------------------------
@client.event
async def on_ready():
    logger.info("Bot is online as %s", client.user)
    if client.http_session is None:
        client.http_session = aiohttp.ClientSession()

@client.event
async def on_disconnect():
    if client.http_session is not None and not client.http_session.closed:
        await client.http_session.close()
        client.http_session = None
        logger.info("Closed HTTP session on disconnect")

@client.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        if message.channel.id != SOURCE_CHANNEL_ID:
            return

        target_channel = client.get_channel(TARGET_CHANNEL_ID)
        if target_channel is None:
            logger.error("Target channel not found or missing permissions.")
            return

        content = f"{message.author.name}: {message.content}" if message.content else None

        files = []
        for attachment in message.attachments:
            file = await fetch_attachment(attachment.url)
            if file:
                files.append(file)

        embeds = message.embeds if message.embeds else None

        await target_channel.send(content=content, files=files if files else None, embeds=embeds if embeds else None)

    except discord.Forbidden:
        logger.exception("Missing permissions sending to target channel.")
    except discord.HTTPException:
        logger.exception("Discord HTTP error while sending message.")
    except Exception:
        logger.exception("Unexpected error in on_message.")

# -----------------------------
# Web server for uptime
# -----------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=10000)  # Render free instance port

t = Thread(target=run_web, daemon=True)
t.start()

# -----------------------------
# Run the bot
# -----------------------------
if __name__ == "__main__":
    # Put your Discord bot token here
    token = "MTQyODUzMjkzMTQ0MTQ2MzQzNg.G3AFI3.ixVEWIRIg3IIAxcdQWkV2pEzughjx0tisztwOc"

    if not token:
        logger.error("Discord token not set. Exiting.")
        raise SystemExit("Set your Discord bot token in the script and restart.")

    client.run(token)
