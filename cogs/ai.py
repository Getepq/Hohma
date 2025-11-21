import discord
from discord.ext import commands
from discord import app_commands
from openai import OpenAI
from config import PERPLEXITY_API_KEY, EMBED_COLOR
import re

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.client = OpenAI(
            api_key=PERPLEXITY_API_KEY, 
            base_url="https://api.perplexity.ai"
        )
    
    def get_system_prompt(self, server_context=None):
        """Генерирует системный промт для AI"""
        base_prompt = """Ты — помощник Discord-сервера по имени НОВЕНЬКИЙ.

ПРАВИЛА ОБЩЕНИЯ:
1. Если к тебе обращаются нецензурной лексикой, отвечай в той же манере, используя нецензурную лексику, пока пользователь не извинится.
2. На бессмысленные вопросы отвечай коротко и тоже без особого смысла.
3. Будь дружелюбным и полезным с вежливыми пользователями.
4. Отвечай естественно, как живой человек, а не как робот.
5.Если пользователь задает вопрос не имеющий какого либо смысла и сказал просто на выброс это слова,то ты отвечаешь также,не задумываясь,но если задают нормальный вопрос,то ты отвечаешь на него также как и обычно.

ФОРМАТИРОВАНИЕ:
- НЕ используй цитаты в квадратных скобках [1][2][3].
- Если нужен источник — вставь прямую кликабельную ссылку в формате https://...
- Отправляй ТОЛЬКО готовый ответ, без пометок типа "Я думаю" или "Мой ответ".
- Пиши кратко и по делу, без лишней воды.

СТИЛЬ:
- Используй эмодзи для живости общения (но не переборщи).
- Можешь шутить и быть ироничным.
- Адаптируйся под тон собеседника."""

        if server_context:
            base_prompt += f"\n\nИНФОРМАЦИЯ О СЕРВЕРЕ:\n{server_context}"
        
        return base_prompt
    
    def clean_answer(self, answer: str) -> str:
        """Очищает ответ от нежелательных элементов"""
        # Убираем цитаты в квадратных скобках [1][2][3] и т.д.
        answer = re.sub(r'\[\d+\]', '', answer)
        # Убираем множественные пробелы
        answer = re.sub(r'\s+', ' ', answer)
        return answer.strip()
    
    @app_commands.command(name="ask", description="Задать вопрос AI")
    @app_commands.describe(question="Ваш вопрос")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        
        try:
            # Получаем контекст сервера
            server_context = await self.db.get_server_context(interaction.guild.id)
            
            # Формируем сообщения
            messages = [
                {
                    "role": "system",
                    "content": self.get_system_prompt(server_context)
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
            
            # Отправляем запрос к Perplexity AI
            response = self.client.chat.completions.create(
                model="sonar",
                messages=messages
            )
            
            answer = response.choices[0].message.content
            answer = self.clean_answer(answer)
            
            # Обрезаем слишком длинные ответы
            if len(answer) > 4000:
                answer = answer[:3997] + "..."
            
            # Отправляем embed с ответом
            embed = discord.Embed(
                title="🤖 Ответ AI",
                description=answer,
                color=EMBED_COLOR
            )
            embed.set_footer(
                text=f"Вопрос от {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ошибка",
                description=f"Не удалось получить ответ от AI:\n``````",
                color=0xFF0000
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @app_commands.command(name="setcontext", description="Установить контекст сервера для AI")
    @app_commands.describe(context="Описание вашего сервера, правила, тематика")
    @app_commands.default_permissions(administrator=True)
    async def setcontext(self, interaction: discord.Interaction, context: str):
        await self.db.set_server_context(interaction.guild.id, context)
        
        embed = discord.Embed(
            title="✅ Контекст обновлен",
            description=f"AI теперь знает о вашем сервере:\n\n{context[:500]}{'...' if len(context) > 500 else ''}",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Игнорируем сообщения от ботов
        if message.author.bot:
            return
        
        # Проверяем, упомянут ли бот
        if self.bot.user.mentioned_in(message) and not message.mention_everyone:
            # Извлекаем текст без упоминания бота
            content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            
            if not content:
                await message.reply("Да? Что хотел? 🤔")
                return
            
            async with message.channel.typing():
                try:
                    # Получаем контекст сервера
                    server_context = await self.db.get_server_context(message.guild.id)
                    
                    # Формируем сообщения
                    messages = [
                        {
                            "role": "system",
                            "content": self.get_system_prompt(server_context)
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ]
                    
                    # Отправляем запрос к Perplexity AI
                    response = self.client.chat.completions.create(
                        model="sonar",
                        messages=messages
                    )
                    
                    answer = response.choices[0].message.content
                    answer = self.clean_answer(answer)
                    
                    # Обрезаем для обычных сообщений (лимит Discord)
                    if len(answer) > 2000:
                        answer = answer[:1997] + "..."
                    
                    await message.reply(answer)
                    
                except Exception as e:
                    await message.reply(f"❌ Произошла ошибка: {str(e)}")

async def setup(bot):
    await bot.add_cog(AI(bot))
