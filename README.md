# Discord Message Mirror Bot

A Discord bot that **mirrors messages** from one channel to another, including text, attachments, and embeds.  
Designed to run **24/7** on platforms like Render, Replit, or a local Python environment.

---

## Features

- Mirrors messages from a **source channel** to a **target channel**.
- Forwards **text content**, **attachments**, and **embeds**.
- Includes **Flask web server** to keep the bot alive on free hosting services.
- Safe environment variable usage for the bot token.

---

## Requirements

- Python 3.10+  
- Packages listed in `requirements.txt`:

```txt
discord.py>=2.6.0
aiohttp>=3.8.5
Flask>=2.3.3
