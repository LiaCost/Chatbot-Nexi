"""
config.py — Configurações centrais do sistema
============================================
Centraliza tokens, constantes e configurações do ambiente.
Para produção, substitua os valores pelas variáveis de ambiente reais.
"""

import os

# ─────────────────────────────────────────
# TOKENS DE API
# ─────────────────────────────────────────

# Token do bot Telegram (obtido via @BotFather)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8339548505:AAEekrJgislwNGCnvSb14zaJMO5sboCqaMY")

# Chave da API OpenAI (GPT-4o)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "SUA_CHAVE_OPENAI_AQUI")

# ─────────────────────────────────────────
# CONFIGURAÇÕES DO NEO4J (futuro)
# ─────────────────────────────────────────
# Quando migrar para Neo4j real, preencha aqui:
NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "senha_neo4j")

# Ativa simulação em memória (True) ou Neo4j real (False)
USE_SIMULATION = True

# ─────────────────────────────────────────
# CONFIGURAÇÕES DA IA
# ─────────────────────────────────────────

OPENAI_MODEL       = "gpt-4o"          # Modelo principal
OPENAI_TEMPERATURE = 0.2               # Baixo → respostas mais determinísticas
OPENAI_MAX_TOKENS  = 300               # Limite de tokens na resposta

# ─────────────────────────────────────────
# CONFIGURAÇÕES DO BOT
# ─────────────────────────────────────────

BOT_NAME    = "EstoqueBot"
BOT_VERSION = "1.0.0"
BOT_AUTHOR  = "Projeto Acadêmico"

# Mensagem exibida quando o bot não entende o usuário
FALLBACK_MESSAGE = (
    "🤔 Não entendi muito bem o que você quis dizer.\n\n"
    "Tente algo como:\n"
    "• *'tem camisa no estoque?'*\n"
    "• *'vendi 3 calças'*\n"
    "• *'mostrar estoque'*\n\n"
    "Ou use /ajuda para ver todos os comandos."
)
