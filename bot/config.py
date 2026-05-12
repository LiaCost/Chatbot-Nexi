"""
config.py — Configurações centrais do sistema
============================================
"""

import os
from pathlib import Path

# ===============================
# CARREGAR .ENV
# ===============================

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass


# ===============================
# TOKENS
# ===============================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN não encontrado no .env")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY não encontrado no .env")


# ===============================
# IA
# ===============================

OPENAI_MODEL = "gpt-4o"
OPENAI_TEMPERATURE = 0.2
OPENAI_MAX_TOKENS = 300


# ===============================
# BOT
# ===============================

BOT_NAME = "EstoqueBot"
BOT_VERSION = "2.0.0"
BOT_AUTHOR = "Projeto"

FALLBACK_MESSAGE = (
    "🤔 Não entendi muito bem.\n\n"
    "Tente:\n"
    "• tem heineken?\n"
    "• mostrar estoque\n"
    "• listar produtos\n\n"
    "Use /ajuda para ver comandos."
)
