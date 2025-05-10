import aiosqlite

DB_NAME = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                name TEXT,
                role TEXT, -- 'tutor' or 'student'
                confirmed INTEGER DEFAULT 1 -- 0: pending, 1: confirmed
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                datetime TEXT,
                tutor_id INTEGER,
                homework TEXT,
                zoom_link TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lesson_students (
                lesson_id INTEGER,
                student_id INTEGER,
                homework_done INTEGER DEFAULT 0,
                feedback TEXT
            )
        """)
        await db.commit()

async def add_user(telegram_id, name, role, confirmed=1):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO users (telegram_id, name, role, confirmed) VALUES (?, ?, ?, ?)",
                         (telegram_id, name, role, confirmed))
        await db.commit()

async def get_user(telegram_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT telegram_id, name, role, confirmed FROM users WHERE telegram_id = ?", (telegram_id,))
        return await cursor.fetchone()

async def confirm_user(telegram_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET confirmed = 1 WHERE telegram_id = ?", (telegram_id,))
        await db.commit()
async def get_pending_students():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT telegram_id, name FROM users WHERE confirmed = 0 AND role = 'student'")
        return await cursor.fetchall()
async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            name TEXT,
            role TEXT,
            confirmed BOOLEAN
        );
        """)
        await db.commit()
        await db.execute("""
                    CREATE TABLE IF NOT EXISTS lessons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        datetime TEXT,
                        tutor_id INTEGER,
                        homework TEXT,
                        zoom_link TEXT
                    )
                """)
        await db.execute("""
                    CREATE TABLE IF NOT EXISTS lesson_students (
                        lesson_id INTEGER,
                        student_id INTEGER,
                        homework_done INTEGER DEFAULT 0,
                        feedback TEXT
                    )
                """)
        await db.commit()


# Вызови функцию create_table при запуске бота
async def setup_database():
    await create_table()

