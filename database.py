import aiosqlite
import os

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            # Путь напрямую в корень сетевого диска
            self.db_path = '/data/bot_data.db'
        else:
            self.db_path = db_path
        
    async def init_db(self):
        print(f"Попытка инициализации базы данных: {self.db_path}")
        
        # ДОБАВЛЕНО: Проверка и создание директории
        data_dir = os.path.dirname(self.db_path)
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                print(f"Создана директория: {data_dir}")
            except Exception as e:
                raise RuntimeError(f"Не удалось создать директорию {data_dir}: {e}")
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    user_id INTEGER,
                    guild_id INTEGER,
                    warnings INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_context (
                    guild_id INTEGER PRIMARY KEY,
                    context TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS mod_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    action TEXT,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
            print(f"База данных успешно инициализирована: {self.db_path}")
    
    async def add_warning(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO warnings (user_id, guild_id, warnings) VALUES (?, ?, 1) '
                'ON CONFLICT(user_id, guild_id) DO UPDATE SET warnings = warnings + 1',
                (user_id, guild_id)
            )
            await db.commit()
            
            cursor = await db.execute(
                'SELECT warnings FROM warnings WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_warnings(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT warnings FROM warnings WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def clear_warnings(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'DELETE FROM warnings WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            )
            await db.commit()
    
    async def set_server_context(self, guild_id, context):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO server_context (guild_id, context) VALUES (?, ?) '
                'ON CONFLICT(guild_id) DO UPDATE SET context = ?',
                (guild_id, context, context)
            )
            await db.commit()
    
    async def get_server_context(self, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT context FROM server_context WHERE guild_id = ?',
                (guild_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def log_action(self, guild_id, user_id, moderator_id, action, reason):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO mod_logs (guild_id, user_id, moderator_id, action, reason) '
                'VALUES (?, ?, ?, ?, ?)',
                (guild_id, user_id, moderator_id, action, reason)
            )
            await db.commit()
