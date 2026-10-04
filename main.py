import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))
WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE", "Привіт!")

logging.basicConfig(level=logging.INFO)

# Словник для збереження зв'язку: message_id в групі → user_id
user_mapping = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def forward_to_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Пересилаємо повідомлення в групу
    forwarded = await update.message.forward(chat_id=SUPPORT_CHAT_ID)
    
    # Зберігаємо зв'язок
    user_mapping[forwarded.message_id] = user.id
    
    # Додатково відправляємо інформацію про користувача (на випадок)
    await context.bot.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text=f"👤 Від: {user.full_name} (ID: {user.id})",
        reply_to_message_id=forwarded.message_id
    )

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    
    replied_msg = update.message.reply_to_message
    
    # Шукаємо user_id
    user_id = user_mapping.get(replied_msg.message_id)
    
    if not user_id:
        # Спробуємо знайти через forward
        if replied_msg.forward_from:
            user_id = replied_msg.forward_from.id
        elif replied_msg.forward_origin and hasattr(replied_msg.forward_origin, "sender_user"):
            user_id = replied_msg.forward_origin.sender_user.id
    
    if user_id:
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            await update.message.reply_text(f"Не вдалося відправити: {e}")
    else:
        await update.message.reply_text("Не можу визначити користувача. Спробуйте відповісти на повідомлення з ID.")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, forward_to_support))
    app.add_handler(MessageHandler(filters.Chat(SUPPORT_CHAT_ID) & filters.REPLY, reply_to_user))

    print("Бот запущений...")
    app.run_polling()

if __name__ == "__main__":
    main()
