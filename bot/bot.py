"""
bot.py — Bot Telegram SEM Excel
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
from telegram.constants import ParseMode

from config import TELEGRAM_TOKEN, BOT_NAME, BOT_VERSION, FALLBACK_MESSAGE
from ia import interpretar, Intent

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s → %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ===============================
# ESTOQUE SIMPLES (SEM EXCEL)
# ===============================

estoque = [
    {"nome": "Heineken", "categoria": "Cervejas", "quantidade": 10, "estoque_minimo": 3},
    {"nome": "Skol", "categoria": "Cervejas", "quantidade": 0, "estoque_minimo": 5},
    {"nome": "Red Label", "categoria": "Whisky", "quantidade": 4, "estoque_minimo": 2},
    {"nome": "Carvão", "categoria": "Utilidades", "quantidade": 8, "estoque_minimo": 2},
]

# ===============================
# FUNÇÕES DE ESTOQUE
# ===============================

def listar_todos():
    return estoque

def categorias():
    return sorted(set(p["categoria"] for p in estoque))

def buscar_produto(nome):
    nome = nome.lower()
    for p in estoque:
        if nome in p["nome"].lower():
            return p
    return None

def listar_por_categoria(cat):
    cat = cat.lower()
    return [p for p in estoque if cat in p["categoria"].lower()]

def produtos_abaixo_minimo():
    return [p for p in estoque if p["quantidade"] < p["estoque_minimo"]]

# ===============================
# FORMATADORES
# ===============================

def _fmt_estoque_completo():
    linhas = ["📦 *ESTOQUE COMPLETO*\n"]
    categoria_atual = ""

    for p in sorted(estoque, key=lambda x: x["categoria"]):
        if p["categoria"] != categoria_atual:
            categoria_atual = p["categoria"]
            linhas.append(f"\n🏷️ _{categoria_atual.upper()}_")

        qtd = p["quantidade"]
        icone = "❌" if qtd <= 0 else "✅"
        linhas.append(f"{icone} *{p['nome']}*: {qtd}")

    return "\n".join(linhas)


def _fmt_produto(p):
    qtd = p["quantidade"]
    minimo = p["estoque_minimo"]

    if qtd <= 0:
        status = "❌ Fora de estoque"
    elif qtd < minimo:
        status = "⚠️ Abaixo do mínimo"
    else:
        status = "✅ Em estoque"

    return (
        f"🏷️ *{p['nome']}*\n"
        f"{status}\n"
        f"📂 Categoria: {p['categoria']}\n"
        f"📦 Quantidade: {qtd}"
    )

# ===============================
# INTENT
# ===============================

def _processar_intent(intent: Intent):

    if intent.tipo == "listar_estoque":
        return _fmt_estoque_completo()

    if intent.tipo == "consultar_produto":
        produto = buscar_produto(intent.produto or "")
        if produto:
            return _fmt_produto(produto)

        por_cat = listar_por_categoria(intent.produto or "")
        if por_cat:
            linhas = [f"📂 *{intent.produto.upper()}*\n"]
            for p in por_cat:
                linhas.append(f"• {p['nome']}: {p['quantidade']}")
            return "\n".join(linhas)

        return "❌ Produto não encontrado."

    if intent.tipo == "ajuda":
        return "/estoque /minimo /categorias /ajuda"

    return FALLBACK_MESSAGE

# ===============================
# COMANDOS TELEGRAM
# ===============================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Ver Estoque", callback_data="estoque")],
        [InlineKeyboardButton("⚠️ Abaixo do Mínimo", callback_data="minimo")],
        [InlineKeyboardButton("📂 Categorias", callback_data="categorias")],
    ])

    await update.message.reply_text(
        f"👋 Olá! Sou o *{BOT_NAME}* v{BOT_VERSION}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )


async def cmd_estoque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        _fmt_estoque_completo(),
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_minimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    produtos = produtos_abaixo_minimo()

    if not produtos:
        await update.message.reply_text("✅ Tudo ok no estoque!")
        return

    linhas = ["⚠️ *ABAIXO DO MÍNIMO*\n"]
    for p in produtos:
        linhas.append(f"• {p['nome']} ({p['quantidade']})")

    await update.message.reply_text("\n".join(linhas), parse_mode=ParseMode.MARKDOWN)


async def cmd_categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📂 *CATEGORIAS*\n\n" + "\n".join(f"• {c}" for c in categorias()),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    intent: Intent = await interpretar(texto)
    resposta = _processar_intent(intent)
    await update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "estoque":
        await query.message.reply_text(_fmt_estoque_completo(), parse_mode=ParseMode.MARKDOWN)

    elif query.data == "minimo":
        await cmd_minimo(update, context)

    elif query.data == "categorias":
        await cmd_categorias(update, context)


# ===============================
# MAIN
# ===============================

def main():
    logger.info(f"Iniciando {BOT_NAME}")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("estoque", cmd_estoque))
    app.add_handler(CommandHandler("minimo", cmd_minimo))
    app.add_handler(CommandHandler("categorias", cmd_categorias))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mensagem))

    app.run_polling()


if __name__ == "__main__":
    main()
