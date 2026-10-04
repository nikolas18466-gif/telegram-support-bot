import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))
WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE", "Привіт! Напишіть ваше повідомлення, і ми відповімо якнайшвидше.")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def forward_to_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.forward(chat_id=SUPPORT_CHAT_ID)

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.reply_to_message.forward_origin:
        # Новий спосіб (python-telegram-bot 21+)
        origin = update.message.reply_to_message.forward_origin
        if hasattr(origin, "sender_user") and origin.sender_user:
            user_id = origin.sender_user.id
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
    elif update.message.reply_to_message and update.message.reply_to_message.forward_from:
        # Старий спосіб (на всякий випадок)
        user_id = update.message.reply_to_message.forward_from.id
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, forward_to_support))
    app.add_handler(MessageHandler(filters.Chat(SUPPORT_CHAT_ID) & filters.REPLY, reply_to_user))

    print("Бот запущений...")
    app.run_polling()

if __name__ == "__main__":
    main()
