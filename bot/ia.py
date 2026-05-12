"""
ia.py — Interpretação de Linguagem Natural
==========================================
Transforma mensagens humanas em intenções estruturadas.
"""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_MAX_TOKENS,
)

logger = logging.getLogger(__name__)

# =====================================================
# OPENAI (OPCIONAL)
# =====================================================

OPENAI_DISPONIVEL = False
_client = None

try:
    from openai import OpenAI

    _client = OpenAI(api_key=OPENAI_API_KEY)
    OPENAI_DISPONIVEL = True
    logger.info("✅ OpenAI inicializada.")

except Exception as e:
    logger.warning(f"OpenAI indisponível: {e}")
    OPENAI_DISPONIVEL = False


# =====================================================
# INTENT
# =====================================================

@dataclass
class Intent:
    tipo: str
    produto: Optional[str] = None
    quantidade: Optional[int] = None
    confianca: float = 1.0
    mensagem_original: str = ""
    via_ia: bool = True
    extras: dict = field(default_factory=dict)


# =====================================================
# PROMPT
# =====================================================

SYSTEM_PROMPT = """
Classifique a mensagem do usuário em uma intenção.

INTENÇÕES:
consultar_produto
listar_estoque
registrar_venda
ver_historico
ajuda
desconhecida

Responda SOMENTE JSON:

{
 "tipo":"",
 "produto":null,
 "quantidade":null,
 "confianca":0.0
}
"""


# =====================================================
# GPT
# =====================================================

def _chamar_gpt(mensagem: str):

    if not OPENAI_DISPONIVEL:
        return None

    try:
        resposta = _client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensagem},
            ],
        )

        texto = resposta.choices[0].message.content.strip()
        return json.loads(texto)

    except Exception as e:
        logger.warning(f"Erro GPT: {e}")
        return None


# =====================================================
# FALLBACK INTELIGENTE (SEM IA)
# =====================================================

_PALAVRAS_ESTOQUE = ["estoque", "listar", "mostrar", "produtos"]
_PALAVRAS_VENDA = ["vendi", "saiu", "baixar"]
_PALAVRAS_HIST = ["vendas", "histórico"]
_PALAVRAS_AJUDA = ["ajuda", "help", "?"]

_PRODUTOS = [
    "camisa",
    "calça",
    "bolsa",
    "tênis",
    "boné",
    "meia",
]


def _extrair_quantidade(texto: str):
    numeros = re.findall(r"\d+", texto)
    return int(numeros[0]) if numeros else None


def _extrair_produto(texto: str):
    for p in _PRODUTOS:
        if p in texto:
            return p
    return None


def _fallback(mensagem: str) -> Intent:

    texto = mensagem.lower()

    if any(p in texto for p in _PALAVRAS_ESTOQUE):
        return Intent("listar_estoque", via_ia=False)

    if any(p in texto for p in _PALAVRAS_HIST):
        return Intent("ver_historico", via_ia=False)

    if any(p in texto for p in _PALAVRAS_AJUDA):
        return Intent("ajuda", via_ia=False)

    if any(p in texto for p in _PALAVRAS_VENDA):
        return Intent(
            "registrar_venda",
            produto=_extrair_produto(texto),
            quantidade=_extrair_quantidade(texto),
            via_ia=False,
        )

    produto = _extrair_produto(texto)
    if produto:
        return Intent("consultar_produto", produto=produto, via_ia=False)

    return Intent("desconhecida", via_ia=False)


# =====================================================
# VALIDAÇÃO
# =====================================================

_VALIDOS = {
    "consultar_produto",
    "listar_estoque",
    "registrar_venda",
    "ver_historico",
    "ajuda",
    "desconhecida",
}


def _validar(dados):

    if not dados:
        return None

    tipo = dados.get("tipo")

    if tipo not in _VALIDOS:
        return None

    produto = dados.get("produto")
    if isinstance(produto, str):
        produto = produto.lower().strip()

    quantidade = dados.get("quantidade")
    try:
        quantidade = int(quantidade) if quantidade else None
    except:
        quantidade = None

    confianca = float(dados.get("confianca", 1.0))

    return Intent(
        tipo=tipo,
        produto=produto,
        quantidade=quantidade,
        confianca=confianca,
        via_ia=True,
    )


# =====================================================
# FUNÇÃO PRINCIPAL
# =====================================================

def interpretar(mensagem: str) -> Intent:

    mensagem = mensagem.strip()

    if not mensagem:
        return Intent("desconhecida")

    # 1️⃣ tenta IA
    dados = _chamar_gpt(mensagem)
    intent = _validar(dados)

    if intent:
        intent.mensagem_original = mensagem
        return intent

    # 2️⃣ fallback local
    intent = _fallback(mensagem)
    intent.mensagem_original = mensagem
    return intent
