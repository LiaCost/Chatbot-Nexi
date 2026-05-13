import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
 
from config import TELEGRAM_TOKEN, BOT_NAME, BOT_VERSION, BOT_AUTHOR, FALLBACK_MESSAGE
from ia import interpretar, Intent
from estoque import estoque_service
 
# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DE LOGGING
# ─────────────────────────────────────────────────────────────────────────────
 
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s → %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# FORMATADORES DE RESPOSTA
# ─────────────────────────────────────────────────────────────────────────────
 
def _fmt_estoque_completo() -> str:
    """Formata a lista completa do estoque para exibição."""
    produtos = estoque_service.listar_todos()
    if not produtos:
        return "📦 O estoque está vazio."
 
    linhas = ["📦 *ESTOQUE COMPLETO*\n"]
    categoria_atual = ""
 
    for p in sorted(produtos, key=lambda x: x["categoria"]):
        if p["categoria"] != categoria_atual:
            categoria_atual = p["categoria"]
            linhas.append(f"\n🏷️ _{categoria_atual.upper()}_")
 
        icone = "✅" if p["quantidade"] > 5 else ("⚠️" if p["quantidade"] > 0 else "❌")
        linhas.append(
            f"{icone} *{p['nome'].title()}*: {p['quantidade']} unid. "
            f"| R$ {p['preco']:.2f}"
        )
 
    resumo = estoque_service.estoque_resumo()
    linhas.append(f"\n📊 *Total:* {resumo['total_itens']} itens em {resumo['total_produtos']} produtos")
 
    if resumo["sem_estoque"]:
        nomes = ", ".join(resumo["sem_estoque"])
        linhas.append(f"❌ *Sem estoque:* {nomes}")
    if resumo["baixo_estoque"]:
        nomes = ", ".join(resumo["baixo_estoque"])
        linhas.append(f"⚠️ *Baixo estoque:* {nomes}")
 
    return "\n".join(linhas)
 
 
def _fmt_produto(info: dict) -> str:
    """Formata informações de um produto específico."""
    nome = info["nome"].title()
    qtd = info["quantidade"]
 
    if qtd == 0:
        status = "❌ *Fora de estoque*"
    elif qtd <= 5:
        status = f"⚠️ *Baixo estoque:* {qtd} unidades"
    else:
        status = f"✅ *Em estoque:* {qtd} unidades"
 
    return (
        f"🏷️ *{nome}*\n"
        f"{status}\n"
        f"💰 Preço unitário: R$ {info['preco']:.2f}\n"
        f"📂 Categoria: {info['categoria'].title()}"
    )
 
 
def _fmt_venda_sucesso(resultado: dict) -> str:
    """Formata a confirmação de uma venda registrada."""
    return (
        f"✅ *Venda registrada com sucesso!*\n\n"
        f"🛍️ Produto: *{resultado['produto'].title()}*\n"
        f"📦 Quantidade vendida: *{resultado['quantidade']}*\n"
        f"💰 Total: *R$ {resultado['total']:.2f}*\n"
        f"🕐 Data/hora: {resultado['data']}\n"
        f"📊 Estoque restante: {resultado['estoque_restante']} unidades"
    )
 
 
def _fmt_historico(vendas: list) -> str:
    """Formata o histórico de vendas."""
    if not vendas:
        return "📋 Nenhuma venda registrada ainda."
 
    linhas = ["📋 *HISTÓRICO DE VENDAS*\n"]
    for i, v in enumerate(reversed(vendas), 1):
        linhas.append(
            f"*{i}.* {v['produto'].title()} — {v['quantidade']}x — "
            f"R$ {v['total']:.2f} — {v['data']}"
        )
 
    total_geral = sum(v["total"] for v in vendas)
    linhas.append(f"\n💵 *Total em vendas:* R$ {total_geral:.2f}")
    return "\n".join(linhas)
 
 
def _teclado_menu() -> InlineKeyboardMarkup:
    """Cria o teclado inline do menu principal."""
    botoes = [
        [
            InlineKeyboardButton("📦 Ver Estoque", callback_data="estoque"),
            InlineKeyboardButton("📋 Histórico", callback_data="historico"),
        ],
        [
            InlineKeyboardButton("❓ Ajuda", callback_data="ajuda"),
            InlineKeyboardButton("ℹ️ Sobre", callback_data="sobre"),
        ],
    ]
    return InlineKeyboardMarkup(botoes)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# HANDLERS DE COMANDOS
# ─────────────────────────────────────────────────────────────────────────────
 
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /start — boas-vindas."""
    nome = update.effective_user.first_name or "usuário"
    texto = (
        f"👋 Olá, *{nome}*! Bem-vindo ao *{BOT_NAME}*!\n\n"
        "Sou seu assistente inteligente de estoque. Posso:\n\n"
        "🔍 *Consultar* produtos no estoque\n"
        "🛍️ *Registrar* vendas em linguagem natural\n"
        "📊 *Exibir* relatórios e histórico\n\n"
        "Experimente digitar algo como:\n"
        "• _'tem camisa?'_\n"
        "• _'vendi 2 calças'_\n"
        "• _'mostrar estoque'_\n\n"
        "Ou use o menu abaixo 👇"
    )
    await update.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN, reply_markup=_teclado_menu())
 
 
async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /menu."""
    await update.message.reply_text(
        "📱 *Menu Principal* — escolha uma opção:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_teclado_menu(),
    )
 
 
async def cmd_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /ajuda."""
    texto = (
        "❓ *AJUDA — Como usar o EstoqueBot*\n\n"
        "*📌 Comandos disponíveis:*\n"
        "/start — Tela inicial\n"
        "/menu — Menu com botões\n"
        "/estoque — Ver todo o estoque\n"
        "/ajuda — Esta mensagem\n"
        "/sobre — Sobre o sistema\n\n"
        "*💬 Linguagem natural (exemplos):*\n"
        "• 'tem camisa?' → consulta produto\n"
        "• 'quantas bolsas existem?' → consulta produto\n"
        "• 'mostrar estoque' → lista tudo\n"
        "• 'vendi 2 calças' → registra venda\n"
        "• 'saiu 1 tênis' → registra venda\n"
        "• 'histórico de vendas' → ver vendas\n\n"
        "💡 *Dica:* pode escrever de forma natural — entendo gírias e abreviações!"
    )
    await update.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
 
 
async def cmd_sobre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /sobre."""
    texto = (
        f"ℹ️ *{BOT_NAME} v{BOT_VERSION}*\n\n"
        f"👨‍💻 *Autor:* {BOT_AUTHOR}\n\n"
        "🏗️ *Arquitetura:*\n"
        "• Interface: Telegram Bot API\n"
        "• IA: OpenAI GPT-4o (NLP)\n"
        "• Banco: Neo4j (simulado)\n"
        "• Linguagem: Python\n\n"
        "📐 *Módulos:*\n"
        "• `bot.py` → Interface Telegram\n"
        "• `ia.py` → Linguagem natural\n"
        "• `estoque.py` → Dados e regras\n"
        "• `config.py` → Configurações\n\n"
        "🎓 Projeto Acadêmico — Chatbot Inteligente"
    )
    await update.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)
 
 
async def cmd_estoque(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /estoque."""
    await update.message.reply_text(_fmt_estoque_completo(), parse_mode=ParseMode.MARKDOWN)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# HANDLER DE CALLBACK (botões inline)
# ─────────────────────────────────────────────────────────────────────────────
 
async def callback_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa cliques nos botões do menu inline."""
    query = update.callback_query
    await query.answer()
 
    acao = query.data
    if acao == "estoque":
        await query.edit_message_text(_fmt_estoque_completo(), parse_mode=ParseMode.MARKDOWN)
 
    elif acao == "historico":
        vendas = estoque_service.historico_vendas()
        await query.edit_message_text(_fmt_historico(vendas), parse_mode=ParseMode.MARKDOWN)
 
    elif acao == "ajuda":
        texto = (
            "❓ *Como usar:*\n\n"
            "• 'tem camisa?' → consultar produto\n"
            "• 'vendi 2 calças' → registrar venda\n"
            "• 'mostrar estoque' → listar tudo\n"
            "• 'histórico' → ver vendas\n\n"
            "Use /ajuda para mais detalhes."
        )
        await query.edit_message_text(texto, parse_mode=ParseMode.MARKDOWN)
 
    elif acao == "sobre":
        texto = (
            f"ℹ️ *{BOT_NAME} v{BOT_VERSION}*\n"
            f"👨‍💻 {BOT_AUTHOR}\n\n"
            "Stack: Python + Telegram + GPT-4o + Neo4j\n"
            "🎓 Projeto Acadêmico"
        )
        await query.edit_message_text(texto, parse_mode=ParseMode.MARKDOWN)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# HANDLER PRINCIPAL — MENSAGENS DE TEXTO
# ─────────────────────────────────────────────────────────────────────────────
 
async def handle_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler central: processa TODA mensagem de texto do usuário.
 
    Fluxo:
      1. Recebe mensagem
      2. Envia para ia.py → Intent
      3. Roteia o Intent para a ação correta no estoque.py
      4. Formata e envia resposta
    """
    mensagem = update.message.text
    user = update.effective_user.first_name or "Usuário"
    logger.info(f"Mensagem de {user}: '{mensagem}'")
 
    # Indicador de digitação enquanto processa
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )
 
    # ── Etapa 1: Interpretar com IA ──────────────────────────────────────
    intent: Intent = interpretar(mensagem)
    via = "GPT-4o" if intent.via_ia else "Heurístico"
    logger.info(f"Intent resolvido via {via}: {intent.tipo} | produto={intent.produto} | qtd={intent.quantidade}")
 
    # ── Etapa 2: Roteamento por tipo de intenção ──────────────────────────
    resposta = await _rotear_intent(intent)
 
    # ── Etapa 3: Enviar resposta ──────────────────────────────────────────
    await update.message.reply_text(resposta, parse_mode=ParseMode.MARKDOWN)
 
 
async def _rotear_intent(intent: Intent) -> str:
    """
    Roteia o Intent para a ação correta e retorna a resposta formatada.
    Centraliza todo o tratamento de edge cases.
    """
 
    # ── LISTAR ESTOQUE ────────────────────────────────────────────────────
    if intent.tipo == "listar_estoque":
        return _fmt_estoque_completo()
 
    # ── VER HISTÓRICO ─────────────────────────────────────────────────────
    if intent.tipo == "ver_historico":
        vendas = estoque_service.historico_vendas()
        return _fmt_historico(vendas)
 
    # ── CONSULTAR PRODUTO ESPECÍFICO ──────────────────────────────────────
    if intent.tipo == "consultar_produto":
        if not intent.produto:
            return (
                "🔍 Qual produto você quer consultar?\n"
                "Exemplo: _'tem camisa?'_ ou _'quantas bolsas?'_"
            )
 
        info = estoque_service.consultar_produto(intent.produto)
 
        if info["encontrado"]:
            return _fmt_produto(info)
 
        # Produto não encontrado — oferece sugestões
        resposta = f"❌ Produto *'{intent.produto}'* não encontrado no sistema."
        sugestoes = info.get("sugestoes", [])
        if sugestoes:
            nomes = ", ".join(f"*{s.title()}*" for s in sugestoes)
            resposta += f"\n\n🔎 Você quis dizer: {nomes}?"
        else:
            resposta += "\n\nUse /estoque para ver todos os produtos disponíveis."
        return resposta
 
    # ── REGISTRAR VENDA ───────────────────────────────────────────────────
    if intent.tipo == "registrar_venda":
 
        # Produto não identificado
        if not intent.produto:
            return (
                "🛍️ Entendi que você vendeu algo, mas não identifiquei o produto.\n\n"
                "Tente: _'vendi 2 calças'_ ou _'saiu 1 tênis'_"
            )
 
        # Quantidade não identificada
        if not intent.quantidade:
            return (
                f"🛍️ Entendi que você vendeu *{intent.produto.title()}*, "
                f"mas não consegui identificar a quantidade.\n\n"
                f"Tente: _'vendi 3 {intent.produto}'_"
            )
 
        # Tenta registrar a venda no EstoqueService
        resultado = estoque_service.registrar_venda(intent.produto, intent.quantidade)
 
        if resultado["sucesso"]:
            return _fmt_venda_sucesso(resultado)
 
        # Trata erros de negócio
        erro = resultado.get("erro", "falha_interna")
 
        if erro == "produto_inexistente":
            resposta = f"❌ Produto *'{resultado['nome_buscado'].title()}'* não existe no sistema."
            sugestoes = resultado.get("sugestoes", [])
            if sugestoes:
                nomes = ", ".join(f"*{s.title()}*" for s in sugestoes)
                resposta += f"\n\n🔎 Talvez você quis dizer: {nomes}?"
            return resposta
 
        if erro == "estoque_insuficiente":
            return (
                f"⚠️ *Estoque insuficiente!*\n\n"
                f"Produto: *{resultado['produto'].title()}*\n"
                f"Disponível: *{resultado['disponivel']}* unidades\n"
                f"Solicitado: *{resultado['solicitado']}* unidades\n\n"
                f"Ajuste a quantidade e tente novamente."
            )
 
        if erro == "quantidade_invalida":
            return (
                f"⚠️ Quantidade inválida: *{resultado.get('quantidade')}*\n"
                f"Por favor, informe um número positivo.\n"
                f"Exemplo: _'vendi 2 calças'_"
            )
 
        return "❌ Ocorreu um erro interno ao registrar a venda. Tente novamente."
 
    # ── AJUDA ─────────────────────────────────────────────────────────────
    if intent.tipo == "ajuda":
        return (
            "❓ *Como posso ajudar:*\n\n"
            "• Consultar produto: _'tem camisa?'_\n"
            "• Ver estoque: _'mostrar estoque'_\n"
            "• Registrar venda: _'vendi 2 calças'_\n"
            "• Histórico: _'ver vendas'_\n\n"
            "Use /ajuda para a lista completa de comandos."
        )
 
    # ── FALLBACK — NÃO ENTENDEU ───────────────────────────────────────────
    return FALLBACK_MESSAGE
 
 
# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO DO BOT
# ─────────────────────────────────────────────────────────────────────────────
 
def main() -> None:
    """Inicializa e inicia o bot Telegram."""
    logger.info(f"Iniciando {BOT_NAME} v{BOT_VERSION}...")
 
    # Cria a aplicação com o token do Telegram
    app = Application.builder().token(TELEGRAM_TOKEN).build()
 
    # ── Registra handlers de comandos ─────────────────────────────────────
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("menu",    cmd_menu))
    app.add_handler(CommandHandler("ajuda",   cmd_ajuda))
    app.add_handler(CommandHandler("sobre",   cmd_sobre))
    app.add_handler(CommandHandler("estoque", cmd_estoque))
 
    # ── Registra handler de botões inline ────────────────────────────────
    app.add_handler(CallbackQueryHandler(callback_botoes))
 
    # ── Registra handler de mensagens de texto ────────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mensagem))
 
    logger.info("Bot pronto! Aguardando mensagens...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
 
 
if __name__ == "__main__":
    main()
