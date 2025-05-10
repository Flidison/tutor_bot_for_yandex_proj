from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import asyncio
from telegram.ext import ApplicationBuilder
import database_teacher_student
import database
from config import BOT_TOKEN
from database import get_user, add_user, confirm_user
import nest_asyncio
from datetime import datetime
from database import DB_NAME
import aiosqlite
nest_asyncio.apply()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        await update.message.reply_text("Привет! Ты новый пользователь. Введи своё имя:")
        context.user_data["register_step"] = "name"
        return

    telegram_id, name, role, confirmed = user
    if not confirmed:
        await update.message.reply_text("Ожидается подтверждение регистрации.")
        return

    if role == "tutor":
        await update.message.reply_text("Ваши ближайшие уроки:")
    else:
        message = update.message or update.callback_query.message
        await message.reply_text(f"Привет, {name}! Ожидайте уроков от вашего репетитора.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("register_step")

    if step == "name":
        context.user_data["name"] = update.message.text
        await update.message.reply_text("Выберите статус:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Репетитор", callback_data="role_tutor")],
            [InlineKeyboardButton("Ученик", callback_data="role_student")]
        ]))
        context.user_data["register_step"] = "role"

'''async def handle_role_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    role = query.data.split("_")[1]
    user_id = query.from_user.id
    user = await get_user(user_id)

    if not user:
        await query.edit_message_text("Ошибка: пользователь не найден.")
        return

    name = user[1]  # имя уже есть в базе
    await add_user(user_id, name, role, confirmed=1)
    await query.edit_message_text(text=f"Вы зарегистрированы как {role.capitalize()}.")
    await start(update, context)'''


async def handle_role_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    role = query.data.split("_")[1]
    name = context.user_data.get("name")
    user_id = query.from_user.id

    await add_user(user_id, name, role, confirmed=1)
    await query.edit_message_text(text=f"Вы зарегистрированы как {role.capitalize()}.")
    await start(update, context)

async def add_student_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if not user or user[2] != "tutor":
        await update.message.reply_text("Эта команда доступна только для репетиторов.")
        return

    await update.message.reply_text("Введите Telegram ID ученика:")
    context.user_data["add_student_step"] = "awaiting_id"


async def handle_student_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("add_student_step")

    if step == "awaiting_id":
        try:
            student_id = int(update.message.text)
        except ValueError:
            await update.message.reply_text("Некорректный Telegram ID.")
            return

        user = await get_user(student_id)
        if not user:
            await update.message.reply_text(
                "Этот пользователь ещё не написал боту, и его имя неизвестно. Попросите его начать с команды /start."
            )
            return

        student_name = user[1]
        teacher_id = update.effective_user.id

        # Сохраняем временное ожидание подтверждения
        context.user_data["pending_student_id"] = student_id

        await update.message.reply_text(f"Отправлено приглашение ученику: {student_name}. Ждём подтверждения.")

        try:
            await context.bot.send_message(
                chat_id=student_id,
                text=f"{update.effective_user.first_name} хочет добавить вас как ученика. Подтвердите?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_student:{teacher_id}")],
                    [InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_student:{teacher_id}")]
                ])
            )
        except:
            await update.message.reply_text("Не удалось отправить сообщение ученику. Возможно, он не запускал бота.")
        context.user_data.clear()


'''async def handle_student_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("add_student_step")

    if step == "awaiting_id":
        try:
            student_id = int(update.message.text)

        except ValueError:
            await update.message.reply_text("Не удалось отправить сообщение ученику. Убедитесь, что он написал боту хотя бы одно сообщение, проверьте корректность введеного Telegram ID.")
            return


        context.user_data["new_student_id"] = student_id
        await update.message.reply_text("Введите имя ученика:")
        context.user_data["add_student_step"] = "awaiting_name"

    elif step == "awaiting_name":
        name = update.message.text
        student_id = context.user_data["new_student_id"]

        await add_user(student_id, name, "student", confirmed=0)
        await update.message.reply_text("Ученик добавлен. Ждём подтверждения.")
        try:
            await context.bot.send_message(
                chat_id=student_id,
                text=f"Репетитор добавил вас как ученика с именем {name}. Подтвердите регистрацию.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Подтвердить", callback_data=f"confirm_{student_id}")],
                    [InlineKeyboardButton("Отклонить", callback_data=f"decline_{student_id}")]
                ])
            )
        except:
            await update.message.reply_text("Не удалось отправить сообщение ученику. Проверьте ID.")
        context.user_data["add_student_step"] = None'''
async def handle_student_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("confirm_"):
        tutor_id = int(data.split(":")[1])
        student_id = query.from_user.id
        await confirm_user(student_id)


        async with aiosqlite.connect(database_teacher_student.DB_NAME_TS) as db:
            await db.execute(
                "INSERT INTO student_teacher (student_id, teacher_id) VALUES (?, ?)",
                (student_id, tutor_id)
            )
            await db.commit()


        await context.bot.send_message(
            chat_id=tutor_id,
            text=f"Ученик принял ваше приглашение")
        await query.edit_message_text(f"Вы были добавлены в ученики")
    elif data.startswith("decline_"):
        # Если отклоняем регистрацию
        tutor_id = int(data.split(":")[1])
        await query.edit_message_text("Вы отклонили регистрацию.")
        await context.bot.send_message(
            chat_id=tutor_id,
            text=f"Ученик не принял ваше приглашение")
    context.user_data.clear()

'''async def handle_student_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("confirm_"):
        student_id = int(data.split("_")[1])
        await confirm_user(student_id)
        await query.edit_message_text("Вы подтвердили регистрацию.")
    elif data.startswith("decline_"):
        await query.edit_message_text("Вы отклонили регистрацию.")'''

async def create_lesson_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if not user or user[2] != "tutor":
        await update.message.reply_text("Эта команда доступна только для репетиторов.")
        return

    await update.message.reply_text("Введите название урока:")
    context.user_data["create_lesson_step"] = "title"


async def handle_zoom_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lesson_id = context.user_data.get("awaiting_zoom_link")
    link = update.message.text

    if link.lower() != "пропустить":
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE lessons SET zoom_link = ? WHERE id = ?", (link, lesson_id))
            await db.commit()

    await update.message.reply_text("Ссылка сохранена.")
    context.user_data.clear()


async def handle_create_lesson_steps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("create_lesson_step")

    if step == "title":
        context.user_data["lesson_title"] = update.message.text
        await update.message.reply_text("Введите дату и время урока (например, 10.05.2025 16:00):")
        context.user_data["create_lesson_step"] = "datetime"

    elif step == "datetime":
        try:
            dt = datetime.strptime(update.message.text, "%d.%m.%Y %H:%M")
            context.user_data["lesson_datetime"] = dt.isoformat()
        except ValueError:
            await update.message.reply_text("Неверный формат. Введите дату как: 10.05.2025 16:00")
            return

        tutor_id = update.effective_user.id

        print(tutor_id)
        async with aiosqlite.connect(database_teacher_student.DB_NAME_TS) as db:
            cursor = await db.execute("SELECT student_id FROM student_teacher WHERE teacher_id=?",(tutor_id,))
            students = await cursor.fetchall()
        print(students)


        if not students:
            await update.message.reply_text("У вас пока нет подтверждённых учеников.")
            context.user_data["create_lesson_step"] = None
            return

        list_stun=[]
        async with aiosqlite.connect(DB_NAME) as db:
            for i in students:
                cursor = await db.execute("SELECT telegram_id, name FROM users WHERE role='student' AND confirmed=1 AND telegram_id=?",(i[0],))
                list_stun.extend(await cursor.fetchall())

        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"addstudent_{student_id}")]
            for student_id, name in list_stun
        ]
        keyboard.append([InlineKeyboardButton("Готово", callback_data="finish_lesson")])
        context.user_data["selected_students"] = []
        await update.message.reply_text("Выберите учеников для урока:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_lesson_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("addstudent_"):
        student_id = int(data.split("_")[1])
        if student_id not in context.user_data["selected_students"]:
            context.user_data["selected_students"].append(student_id)
            await query.answer("Ученик добавлен.")

    elif data == "finish_lesson":
        tutor_id = query.from_user.id
        title = context.user_data["lesson_title"]
        dt = context.user_data["lesson_datetime"]
        students = context.user_data.get("selected_students", [])

        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("INSERT INTO lessons (title, datetime, tutor_id) VALUES (?, ?, ?)",
                                      (title, dt, tutor_id))
            lesson_id = cursor.lastrowid
            for student_id in students:
                await db.execute("INSERT INTO lesson_students (lesson_id, student_id) VALUES (?, ?)",
                                 (lesson_id, student_id))
            await db.commit()



        await query.edit_message_text(f"Урок «{title}» создан и назначен {len(students)} ученикам")


        for sid in students:
            try:
                await context.bot.send_message(
                    chat_id=sid,
                    text=f"Вам назначен урок «{title}» {dt.replace('T', ' ')} от репетитора."
                )
            except:
                pass


        context.user_data.clear()

async def homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if not user or user[2] != "tutor":
        await update.message.reply_text("Эта команда доступна только для репетиторов.")
        return

    tutor_id = user[0]
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, title, datetime FROM lessons WHERE tutor_id = ?", (tutor_id,))
        lessons = await cursor.fetchall()

    if not lessons:
        await update.message.reply_text("У вас нет созданных уроков.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{title} ({dt[:16].replace('T',' ')})", callback_data=f"hwselect_{lesson_id}")]
        for lesson_id, title, dt in lessons
    ]
    await update.message.reply_text("Выберите урок для добавления домашки или Zoom-ссылки:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_homework_lesson_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lesson_id = int(query.data.split("_")[1])
    context.user_data["editing_lesson"] = lesson_id

    await query.edit_message_text("Введите текст домашнего задания (или «пропустить», если не нужно):")
    context.user_data["homework_step"] = "awaiting_homework"

async def handle_homework_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("homework_step")
    lesson_id = context.user_data.get("editing_lesson")
    global hw_text
    if step == "awaiting_homework":
        hw_text = update.message.text
        if hw_text.lower() != "пропустить":
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute("UPDATE lessons SET homework = ? WHERE id = ?", (hw_text, lesson_id))
                await db.commit()
        context.user_data["homework_step"] = "awaiting_zoom"
        await update.message.reply_text("Теперь введите ссылку на Zoom (или «пропустить»):")

    elif step == "awaiting_zoom":
        link = update.message.text
        if link.lower() != "пропустить":
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute("UPDATE lessons SET zoom_link = ? WHERE id = ?", (link, lesson_id))
                await db.commit()

        # Уведомление ученикам
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT student_id FROM lesson_students WHERE lesson_id = ?", (lesson_id,))
            students = await cursor.fetchall()
            cursor = await db.execute("SELECT title FROM lessons WHERE id = ?", (lesson_id,))
            lesson_title = (await cursor.fetchone())[0]

        for (student_id,) in students:
            try:
                print(hw_text)
                await context.bot.send_message(
                    chat_id=student_id,
                    text=f"Домашка или ссылка на конференцию к уроку «{lesson_title}» добавлены.\n"
                         f"{'Cсылка на урок: ' + link+"\n" if link.lower() != 'пропустить' else ''}"
                        f"{'Домашка по уроку: ' + hw_text +"\n" if hw_text.lower() != 'пропустить' else ''}"
                )
            except:
                pass

        await update.message.reply_text("Домашка и ссылка добавлены.")
        context.user_data.clear()

async def my_homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if not user or user[2] != "student":
        await update.message.reply_text("Эта команда доступна только для учеников.")
        return

    student_id = user[0]
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT lessons.id, lessons.title
            FROM lessons
            JOIN lesson_students ON lessons.id = lesson_students.lesson_id
            WHERE lesson_students.student_id = ? AND lesson_students.homework_done = 0 AND lessons.homework IS NOT NULL
        """, (student_id,))
        lessons = await cursor.fetchall()

    if not lessons:
        await update.message.reply_text("У вас нет заданий для выполнения.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{title}", callback_data=f"hwdone_{lesson_id}")]
        for lesson_id, title in lessons
    ]
    await update.message.reply_text("Выберите урок, по которому вы выполнили домашку:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_homework_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lesson_id = int(query.data.split("_")[1])
    student_id = query.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE lesson_students
            SET homework_done = 1
            WHERE lesson_id = ? AND student_id = ?
        """, (lesson_id, student_id))
        await db.commit()

    await query.edit_message_text("Вы отметили домашку как выполненную. Ожидайте проверки.")

async def check_homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if not user or user[2] != "tutor":
        await update.message.reply_text("Эта команда только для репетиторов.")
        return

    tutor_id = user[0]
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT id, title FROM lessons
            WHERE tutor_id = ?
        """, (tutor_id,))
        lessons = await cursor.fetchall()

    if not lessons:
        await update.message.reply_text("У вас нет уроков.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{title}", callback_data=f"checkhw_{lesson_id}")]
        for lesson_id, title in lessons
    ]
    await update.message.reply_text("Выберите урок для проверки домашних работ:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_check_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson_id = int(query.data.split("_")[1])
    context.user_data["checking_lesson"] = lesson_id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT users.telegram_id, users.name
            FROM lesson_students
            JOIN users ON users.telegram_id = lesson_students.student_id
            WHERE lesson_id = ? AND homework_done = 1
        """, (lesson_id,))
        students = await cursor.fetchall()

    if not students:
        await query.edit_message_text("Никто ещё не сдал домашку.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{name}", callback_data=f"grade_{student_id}")]
        for student_id, name in students
    ]
    await query.edit_message_text("Выберите ученика для оценки:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_grading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    student_id = int(query.data.split("_")[1])
    context.user_data["grading_student"] = student_id
    await query.edit_message_text("Введите комментарий или оценку (одно сообщение):")
    context.user_data["grading_step"] = "awaiting_feedback"

async def handle_feedback_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("grading_step") != "awaiting_feedback":
        return

    student_id = context.user_data["grading_student"]
    lesson_id = context.user_data["checking_lesson"]
    feedback = update.message.text

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE lesson_students
            SET feedback = ?
            WHERE lesson_id = ? AND student_id = ?
        """, (feedback, lesson_id, student_id))
        await db.commit()

    try:
        await update.get_bot().send_message(
            chat_id=student_id,
            text=f"Ваше домашнее задание по уроку проверено:\nКомментарий: {feedback}"
        )
    except:
        pass

    await update.message.reply_text("Комментарий отправлен ученику.")
    context.user_data["grading_step"] = None






async def handle_all_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("register_step"):
        await handle_message(update, context)

    elif context.user_data.get("add_student_step"):
        await handle_student_registration(update, context)

    elif context.user_data.get("create_lesson_step"):
        await handle_create_lesson_steps(update, context)

    elif context.user_data.get("homework_step"):
        await handle_homework_input(update, context)

    elif context.user_data.get("grading_step"):
        await handle_feedback_input(update, context)


async def main():
    await database.setup_database()
    await  database_teacher_student.create_student_teacher_table()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_student", add_student_command))
    app.add_handler(CommandHandler("create_lesson", create_lesson_command))
    app.add_handler(CommandHandler("homework", homework_command))
    app.add_handler(CommandHandler("my_homework", my_homework_command))
    app.add_handler(CommandHandler("check_homework", check_homework_command))

    app.add_handler(CallbackQueryHandler(handle_role_choice, pattern="^role_"))
    app.add_handler(CallbackQueryHandler(handle_student_response, pattern="^(confirm_|decline_)"))
    app.add_handler(CallbackQueryHandler(handle_lesson_selection, pattern="^(addstudent_|finish_lesson)"))
    app.add_handler(CallbackQueryHandler(handle_homework_lesson_choice, pattern="^hwselect_"))
    app.add_handler(CallbackQueryHandler(handle_homework_done, pattern="^hwdone_"))
    app.add_handler(CallbackQueryHandler(handle_check_homework, pattern="^checkhw_"))
    app.add_handler(CallbackQueryHandler(handle_grading, pattern="^grade_"))

    print("Bot is running...")
    await app.run_polling()


if __name__ == "__main__":

    asyncio.run(main())



"""app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_role_choice, pattern="^role_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("add_student", add_student_command))
    app.add_handler(CallbackQueryHandler(handle_student_response, pattern="^(confirm|decline)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_student_registration))

    app.add_handler(CommandHandler("create_lesson", create_lesson_command))
    app.add_handler(CallbackQueryHandler(handle_lesson_selection, pattern="^(addstudent_|finish_lesson)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_lesson_steps))

    app.add_handler(CommandHandler("homework", homework_command))
    app.add_handler(CallbackQueryHandler(handle_homework_lesson_choice, pattern="^hwselect_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_homework_input))

    app.add_handler(CommandHandler("my_homework", my_homework_command))
    app.add_handler(CallbackQueryHandler(handle_homework_done, pattern="^hwdone_"))

    app.add_handler(CommandHandler("check_homework", check_homework_command))
    app.add_handler(CallbackQueryHandler(handle_check_homework, pattern="^checkhw_"))
    app.add_handler(CallbackQueryHandler(handle_grading, pattern="^grade_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback_input))'''"""