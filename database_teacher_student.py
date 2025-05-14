import aiosqlite
DB_NAME_TS="bot_ts.db"
async def create_student_teacher_table():
    async with aiosqlite.connect(DB_NAME_TS) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS student_teacher (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                UNIQUE(student_id, teacher_id),
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        await db.commit()
