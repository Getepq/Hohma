import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, BOT_PREFIX, ALLOWED_GUILD_ID
from database import Database

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.db = Database()
        self.allowed_guild = ALLOWED_GUILD_ID
    
    async def setup_hook(self):
        await self.db.init_db()
        
        await self.load_extension('cogs.moderation')
        await self.load_extension('cogs.ai')
        
        if self.allowed_guild:
            guild = discord.Object(id=self.allowed_guild)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Команды синхронизированы для сервера {self.allowed_guild}")
        else:
            await self.tree.sync()
            print("Команды синхронизированы глобально")
    
    async def on_ready(self):
        print(f'Бот запущен как {self.user.name}')
        print(f'ID: {self.user.id}')
        
        if self.allowed_guild:
            for guild in self.guilds:
                if guild.id != self.allowed_guild:
                    print(f"Бот покинул неразрешенный сервер: {guild.name}")
                    await guild.leave()
        
        await self.change_presence(activity=discord.Game(name="/ask для вопросов"))
    
    async def on_guild_join(self, guild):
        if self.allowed_guild and guild.id != self.allowed_guild:
            print(f"Попытка добавить на неразрешенный сервер: {guild.name}. Выхожу...")
            await guild.leave()

async def main():
    bot = DiscordBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
