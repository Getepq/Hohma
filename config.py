import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Исправление для GUILD_ID
guild_id_env = os.getenv('GUILD_ID')
if guild_id_env:
    try:
        ALLOWED_GUILD_ID = int(guild_id_env)
    except (ValueError, TypeError):
        ALLOWED_GUILD_ID = None
else:
    ALLOWED_GUILD_ID = None

BOT_PREFIX = '!'
EMBED_COLOR = 0x5865F2

MAX_WARNINGS = 3
MUTE_ROLE_NAME = "Muted"

MODERATOR_ROLE_NAMES = ["Модератор", "Moderator", "Мод", "Admin", "Администратор"]
