import discord
from discord.ext import commands
from discord import app_commands
from openai import OpenAI
from config import PERPLEXITY_API_KEY, EMBED_COLOR

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
    
    @app_commands.command(name="ask", description="Задать вопрос AI")
    @app_commands.describe(question="Ваш вопрос")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        
        server_context = await self.db.get_server_context(interaction.guild.id)
        
        messages = []
        if server_context:
            messages.append({
                "role": "system",
                "content": f"Ты помошник по дискорд группе ,тебя зовут НОВЕНЬКИЙ.Если к тебе обращаються  нецензруной лексикой,то ты отвечаешь в той же манере используя нецензурную лексику пока пользователь перед тобой не извинится .Не используй цитаты в квадратных скобках [1][2][3]. Если нужен источник, вставь прямую ссылку. Ты не отправляешь то, что ты думал, отправляешь ТОЛЬКО ответ. Информация о сервере: {server_context}"
            })
        else:
            messages.append({
                "role": "system",
                "content": "Ты помошник по дискорд группе ,тебя зовут НОВЕНЬКИЙ.Если к тебе обращаються  нецензруной лексикой,то ты отвечаешь в той же манере используя нецензурную лексику пока пользователь перед тобой не извинится .Не используй цитаты в квадратных скобках [1][2][3]. Если нужен источник, вставь прямую ссылку. Ты не отправляешь то, что ты думал, отправляешь ТОЛЬКО ответ."
            })
        
        messages.append({"role": "user", "content": question})
        
        try:
            response = self.client.chat.completions.create(
                model="sonar",
                messages=messages
            )
            
            answer = response.choices[0].message.content
            
            # Убираем цитаты в квадратных скобках [1][2][3] и т.д.
            import re
            answer = re.sub(r'\[\d+\]', '', answer)
            
            if len(answer) > 4000:
                answer = answer[:4000] + "..."
            
            embed = discord.Embed(title="🤖 Ответ AI", description=answer, color=EMBED_COLOR)
            embed.set_footer(text=f"Вопрос от {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Ошибка при обращении к AI: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="setcontext", description="Установить контекст сервера для AI")
    @app_commands.describe(context="Описание вашего сервера")
    @app_commands.default_permissions(administrator=True)
    async def setcontext(self, interaction: discord.Interaction, context: str):
        await self.db.set_server_context(interaction.guild.id, context)
        await interaction.response.send_message("✅ Контекст сервера обновлен! AI теперь знает о вашем сервере", ephemeral=True)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if self.bot.user.mentioned_in(message) and not message.mention_everyone:
            content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            if not content:
                return
            
            server_context = await self.db.get_server_context(message.guild.id)
            
            messages = [
                {
                    "role": "system",
                    "content": "Ты помошник по дискорд группе ,тебя зовут НОВЕНЬКИЙ.Если к тебе обращаються  нецензруной лексикой,то ты отвечаешь в той же манере используя нецензурную лексику пока пользователь перед тобой не извинится .Не используй цитаты в квадратных скобках [1][2][3]. Если нужен источник, вставь прямую ссылку. Ты не отправляешь то, что ты думал, отправляешь ТОЛЬКО ответ."
                }
            ]
            
            if server_context:
                messages[0]["content"] += f" Информация о сервере: {server_context}"
            
            messages.append({"role": "user", "content": content})
            
            async with message.channel.typing():
                try:
                    response = self.client.chat.completions.create(
                        model="sonar",
                        messages=messages
                    )
                    
                    answer = response.choices[0].message.content
                    
                    # Убираем цитаты в квадратных скобках [1][2][3] и т.д.
                    import re
                    answer = re.sub(r'\[\d+\]', '', answer)
                    
                    if len(answer) > 2000:
                        answer = answer[:2000] + "..."
                    
                    await message.reply(answer)
                    
                except Exception as e:
                    await message.reply(f"Произошла ошибка: {str(e)}")

async def setup(bot):
    await bot.add_cog(AI(bot))
