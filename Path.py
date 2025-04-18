import datetime
import pandas as pd
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv  # Добавлен импорт

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение токена бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в .env файле")

# Configuration
EXCEL_FILE = "HoneyTrack_Data.xlsx"
BEAR_TYPES = {
    "Chronic Planner Bear": 0,
    "Approval Seeker Bear": 0,
    "Pseudo-Productive Bear": 0
}

# Initialize Excel file with correct structure
def init_excel():
    if not os.path.exists(EXCEL_FILE):
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            pd.DataFrame(columns=["Date", "Time", "User ID", "Category"]).to_excel(
                writer, 
                sheet_name="HoneyPath", 
                index=False
            )
    else:
        # Check if sheet exists
        with pd.ExcelFile(EXCEL_FILE, engine='openpyxl') as xls:
            if 'HoneyPath' not in xls.sheet_names:
                with pd.ExcelWriter(EXCEL_FILE, mode='a', engine='openpyxl') as writer:
                    pd.DataFrame(columns=["Date", "Time", "User ID", "Category"]).to_excel(
                        writer, 
                        sheet_name="HoneyPath", 
                        index=False
                    )

# Initialize Excel file on startup
init_excel()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the test"""
    BEAR_TYPES.update({key: 0 for key in BEAR_TYPES})
    context.user_data["current_question"] = 0
    await update.message.reply_text(
        "🐻 **Discover your Bear Type!**\n"
        "1. How do you usually start working toward a new goal?\n"
        "A) I create a detailed plan\n"
        "B) I talk it over with others\n"
        "C) I just start doing something",
        reply_markup=ReplyKeyboardMarkup([["A", "B", "C"]], resize_keyboard=True)
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz answers"""
    user_id = update.message.from_user.id
    answer = update.message.text.upper()
    question_num = context.user_data.get("current_question", 0)

    # Scoring logic
    if question_num == 0:
        if answer == "A": BEAR_TYPES["Chronic Planner Bear"] += 2
        elif answer == "B": BEAR_TYPES["Approval Seeker Bear"] += 2
        elif answer == "C": BEAR_TYPES["Pseudo-Productive Bear"] += 2
        await update.message.reply_text(
            "2. What is the hardest part of achieving goals for you?\n"
            "A) Starting without guaranteed success\n"
            "B) Making decisions without approval\n"
            "C) Staying focused on the main task",
            reply_markup=ReplyKeyboardMarkup([["A", "B", "C"]], resize_keyboard=True)
        )
        context.user_data["current_question"] = 1

    elif question_num == 1:
        if answer == "A": BEAR_TYPES["Chronic Planner Bear"] += 1
        elif answer == "B": BEAR_TYPES["Approval Seeker Bear"] += 1
        elif answer == "C": BEAR_TYPES["Pseudo-Productive Bear"] += 1
        await update.message.reply_text(
            "3. How do you react to mistakes?\n"
            "A) I analyze and replan\n"
            "B) I ask for advice\n"
            "C) I switch to something else",
            reply_markup=ReplyKeyboardMarkup([["A", "B", "C"]], resize_keyboard=True)
        )
        context.user_data["current_question"] = 2

    elif question_num == 2:
        if answer == "A": BEAR_TYPES["Chronic Planner Bear"] += 1
        elif answer == "B": BEAR_TYPES["Approval Seeker Bear"] += 1
        elif answer == "C": BEAR_TYPES["Pseudo-Productive Bear"] += 1

        # Determine type
        user_type = max(BEAR_TYPES, key=BEAR_TYPES.get)
        now = datetime.datetime.now()

        try:
            # Read existing data
            df = pd.read_excel(EXCEL_FILE, sheet_name="HoneyPath")
        except ValueError:
            # Create new DataFrame if sheet is missing
            df = pd.DataFrame(columns=["Date", "Time", "User ID", "Category"])

        # Add new row
        new_row = pd.DataFrame([{
            "Date": now.date(),
            "Time": now.time().strftime("%H:%M:%S"),
            "User ID": user_id,
            "Category": user_type
        }])
        df = pd.concat([df, new_row], ignore_index=True)

        # Save to Excel
        with pd.ExcelWriter(
            EXCEL_FILE,
            mode="a",
            engine="openpyxl",
            if_sheet_exists="replace"
        ) as writer:
            df.to_excel(writer, sheet_name="HoneyPath", index=False)

        # Weekly plan based on type
        if user_type == "Chronic Planner Bear":
            plan = """✅ Your weekly plan:
            1. Day 1: Take action WITHOUT preparation.
            2. Day 3: 20 minutes of pure action with a timer.
            3. Day 5: Write down a risk worth taking.✨ Finished your chores?
		Action plan in my description. ("information about the bot" is above)"""
        elif user_type == "Approval Seeker Bear":
            plan = """✅ Your weekly plan:
            1. Day 1: Make a decision independently.
            2. Day 3: Write down 3 personal achievements.
            3. Day 5: Run a solo experiment.✨ Finished your chores?
		Action plan in my description. ("information about the bot" is above)"""
        else:
            plan = """✅ Your weekly plan:
            1. Day 1: Drop 3 secondary tasks.
            2. Day 3: Spend 1 hour on your main goal.
            3. Day 5: Assess your actual contribution.✨ Finished your chores?
		Action plan in my description. ("information about the bot" is above)"""

        await update.message.reply_text(f"🎯 Your type: **{user_type}**\n{plan}", parse_mode="Markdown")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    print(f"Update {update} caused error {context.error}")

def main():
    # Используем токен из переменной окружения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    application.run_polling()

if __name__ == "__main__":
    main()