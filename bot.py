import os
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
intents.message_content = True
client = discord.Client(intents=intents)

# Channels
SOURCE_CHANNEL_ID = 1289729762310225941  # Grab messages from this channel
TARGET_CHANNEL_ID = 1428532464996974602  # Send messages here

# Allowed roles for !Update command
ALLOWED_ROLE_IDS = {
    1428547947410362368,
    1428547946273570828,
    1428547945514668042,
    1428547944403046530
}

client.http_session = None

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

        # Check for !Update command
        if message.content.strip() == "!Update":
            # Check if user has any allowed role
            user_roles = {role.id for role in message.author.roles}
            if not user_roles.intersection(ALLOWED_ROLE_IDS):
                await message.channel.send("You don't have permission to run this command.")
                return

            source_channel = client.get_channel(SOURCE_CHANNEL_ID)
            target_channel = client.get_channel(TARGET_CHANNEL_ID)
            if source_channel is None or target_channel is None:
                logger.error("Source or target channel not found.")
                return

            # Fetch last 2 messages from source channel
            messages = await source_channel.history(limit=2, oldest_first=True).flatten()

            for msg in messages:
                content = f"{msg.author.name}: {msg.content}" if msg.content else None

                files = []
                for attachment in msg.attachments:
                    file = await fetch_attachment(attachment.url)
                    if file:
                        files.append(file)

                embeds = msg.embeds if msg.embeds else None

                await target_channel.send(content=content, files=files if files else None, embeds=embeds if embeds else None)

            await message.channel.send("Last 2 messages mirrored successfully!")
            return

        # Automatic mirroring of messages from source to target
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
    app.run(host='0.0.0.0', port=10000)

t = Thread(target=run_web, daemon=True)
t.start()

# -----------------------------
# Run the bot
# -----------------------------
if __name__ == "__main__":
    token = "MTQyODUzMjkzMTQ0MTQ2MzQzNg.G3AFI3.ixVEWIRIg3IIAxcdQWkV2pEzughjx0tisztwOc"  # Replace with your bot token
    if not token:
        logger.error("Bot token not set. Exiting.")
        raise SystemExit("Set the bot token and restart.")

    client.run(token)
