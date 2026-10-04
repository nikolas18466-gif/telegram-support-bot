import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))
WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE", "Привіт!")

logging.basicConfig(level=logging.INFO)

# Зберігаємо зв'язок message_id → user_id
user_mapping = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def forward_to_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Просто пересилаємо повідомлення (як в Livegram)
    forwarded = await update.message.forward(chat_id=SUPPORT_CHAT_ID)
    # Запам'ятовуємо хто написав
    user_mapping[forwarded.message_id] = user.id

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    replied_id = update.message.reply_to_message.message_id
    user_id = user_mapping.get(replied_id)

    # Запасний варіант через forward
    if not user_id:
        msg = update.message.reply_to_message
        if msg.forward_from:
            user_id = msg.forward_from.id
        elif getattr(msg, "forward_origin", None) and hasattr(msg.forward_origin, "sender_user"):
            user_id = msg.forward_origin.sender_user.id

    if user_id:
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            await update.message.reply_text(f"Помилка відправки: {e}")
    else:
        await update.message.reply_text("Не вдалося визначити користувача. Відповідайте саме на переслане повідомлення.")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, forward_to_support))
    app.add_handler(MessageHandler(filters.Chat(SUPPORT_CHAT_ID) & filters.REPLY, reply_to_user))

    print("Бот запущений...")
    app.run_polling()

if __name__ == "__main__":
    main()
