from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8339548505:AAEekrJgislwNGCnvSb14zaJMO5sboCqaMY"

# ======================
# COMANDOS
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou o VexiBot!\n\n"
        "Use /menu para ver o que posso fazer."
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "MENU VEXIBOT\n\n"
        "/start - iniciar\n"
        "/menu - ver menu\n"
        "/ajuda - ajuda\n"
        "/sobre - sobre mim\n"
        "/hora - horário\n"
        "/piada - ouvir piada"
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Posso conversar, responder perguntas simples e ajudar você!"
    )

async def sobre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Eu sou o VexiBot!\nCriado em Python usando a API do Telegram."
    )

async def hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime
    agora = datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"Agora são {agora}")

async def piada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Por que o programador terminou o namoro?\nPorque não houve conexão!"
    )

# ======================
# CONVERSA INTELIGENTE
# ======================

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()

    if "oi" in texto or "olá" in texto:
        await update.message.reply_text("Oi! Como posso ajudar?")
    
    elif "tudo bem" in texto:
        await update.message.reply_text("Estou funcionando perfeitamente")

    elif "seu nome" in texto:
        await update.message.reply_text("Meu nome é VexiBot")

    elif "quem te criou" in texto:
        await update.message.reply_text("Fui criado por uma futura programadora incrível")

    elif "obrigado" in texto:
        await update.message.reply_text("Sempre às ordens!")

    elif "menu" in texto:
        await menu(update, context)

    elif "python" in texto:
        await update.message.reply_text("Python é minha linguagem favorita!")

    elif "bot" in texto:
        await update.message.reply_text("Sim! Eu sou um bot do Telegram.")

    else:
        await update.message.reply_text(
            "🤖 Ainda estou aprendendo!\nDigite /menu para ver meus comandos."
        )

# ======================
# INICIAR BOT
# ======================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("sobre", sobre))
app.add_handler(CommandHandler("hora", hora))
app.add_handler(CommandHandler("piada", piada))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

print("VexiBot está ONLINE!")
app.run_polling()
