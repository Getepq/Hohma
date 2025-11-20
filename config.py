import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

BOT_PREFIX = '!'
EMBED_COLOR = 0x5865F2

MAX_WARNINGS = 3
MUTE_ROLE_NAME = "Muted"

MODERATOR_ROLE_NAMES = ["Модератор", "Moderator", "Мод", "Admin", "Администратор"]
