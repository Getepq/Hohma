import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import timedelta
from config import MAX_WARNINGS, MUTE_ROLE_NAME, EMBED_COLOR, MODERATOR_ROLE_NAMES

def has_moderator_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        
        user_roles = [role.name for role in interaction.user.roles]
        has_mod_role = any(mod_role in user_roles for mod_role in MODERATOR_ROLE_NAMES)
        
        if not has_mod_role:
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды. Требуется роль модератора.",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
    
    async def create_mute_role(self, guild):
        mute_role = discord.utils.get(guild.roles, name=MUTE_ROLE_NAME)
        if not mute_role:
            mute_role = await guild.create_role(name=MUTE_ROLE_NAME, reason="Для системы мута")
            for channel in guild.channels:
                await channel.set_permissions(mute_role, send_messages=False, speak=False)
        return mute_role
    
    @app_commands.command(name="kick", description="Кикнуть пользователя с сервера")
    @app_commands.describe(member="Пользователь для кика", reason="Причина")
    @has_moderator_role()
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("Вы не можете кикнуть этого пользователя", ephemeral=True)
        
        await member.kick(reason=reason)
        await self.db.log_action(interaction.guild.id, member.id, interaction.user.id, "kick", reason)
        
        embed = discord.Embed(title="Пользователь кикнут", color=EMBED_COLOR)
        embed.add_field(name="Пользователь", value=f"{member.mention}", inline=True)
        embed.add_field(name="Модератор", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ban", description="Забанить пользователя")
    @app_commands.describe(member="Пользователь для бана", reason="Причина", delete_messages="Удалить сообщения за последние дни")
    @has_moderator_role()
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана", delete_messages: int = 0):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("Вы не можете забанить этого пользователя", ephemeral=True)
        
        await member.ban(reason=reason, delete_message_days=delete_messages)
        await self.db.log_action(interaction.guild.id, member.id, interaction.user.id, "ban", reason)
        
        embed = discord.Embed(title="Пользователь забанен", color=0xFF0000)
        embed.add_field(name="Пользователь", value=f"{member.mention}", inline=True)
        embed.add_field(name="Модератор", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="unban", description="Разбанить пользователя")
    @app_commands.describe(user_id="ID пользователя")
    @has_moderator_role()
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ Пользователь {user.name} разбанен")
        except:
            await interaction.response.send_message("Ошибка: пользователь не найден или не забанен", ephemeral=True)
    
    @app_commands.command(name="mute", description="Замутить пользователя")
    @app_commands.describe(member="Пользователь", duration="Длительность в минутах", reason="Причина")
    @has_moderator_role()
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "Не указана"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("Вы не можете замутить этого пользователя", ephemeral=True)
        
        mute_duration = timedelta(minutes=duration)
        await member.timeout(mute_duration, reason=reason)
        await self.db.log_action(interaction.guild.id, member.id, interaction.user.id, f"mute ({duration}m)", reason)
        
        embed = discord.Embed(title="Пользователь замучен", color=0xFFA500)
        embed.add_field(name="Пользователь", value=f"{member.mention}", inline=True)
        embed.add_field(name="Длительность", value=f"{duration} минут", inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="unmute", description="Размутить пользователя")
    @app_commands.describe(member="Пользователь")
    @has_moderator_role()
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        await member.timeout(None)
        await interaction.response.send_message(f"✅ {member.mention} размучен")
    
    @app_commands.command(name="warn", description="Выдать предупреждение")
    @app_commands.describe(member="Пользователь", reason="Причина")
    @has_moderator_role()
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
        warnings = await self.db.add_warning(member.id, interaction.guild.id)
        await self.db.log_action(interaction.guild.id, member.id, interaction.user.id, "warn", reason)
        
        embed = discord.Embed(title="Предупреждение выдано", color=0xFFFF00)
        embed.add_field(name="Пользователь", value=f"{member.mention}", inline=True)
        embed.add_field(name="Предупреждений", value=f"{warnings}/{MAX_WARNINGS}", inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        
        if warnings >= MAX_WARNINGS:
            await member.kick(reason=f"Превышено максимальное количество предупреждений ({MAX_WARNINGS})")
            embed.add_field(name="Действие", value="Пользователь кикнут за превышение лимита предупреждений", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="warnings", description="Посмотреть предупреждения пользователя")
    @app_commands.describe(member="Пользователь")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        warnings = await self.db.get_warnings(member.id, interaction.guild.id)
        await interaction.response.send_message(f"{member.mention} имеет **{warnings}** предупреждений")
    
    @app_commands.command(name="clearwarnings", description="Очистить предупреждения")
    @app_commands.describe(member="Пользователь")
    @has_moderator_role()
    async def clearwarnings(self, interaction: discord.Interaction, member: discord.Member):
        await self.db.clear_warnings(member.id, interaction.guild.id)
        await interaction.response.send_message(f"✅ Предупреждения {member.mention} очищены")
    
    @app_commands.command(name="clear", description="Удалить сообщения в канале")
    @app_commands.describe(amount="Количество сообщений")
    @has_moderator_role()
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            return await interaction.response.send_message("Укажите число от 1 до 100", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Удалено {len(deleted)} сообщений", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
