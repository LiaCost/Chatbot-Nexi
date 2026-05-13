"""
ia.py — Interpretação de Linguagem Natural
==========================================
Responsável por transformar mensagens humanas em intenções estruturadas.

Fluxo interno:
  1. Recebe texto do usuário
  2. Envia ao GPT-4o com prompt de sistema especializado
  3. Valida e pós-processa a resposta JSON
  4. Retorna Intent estruturado para bot.py

Fallback em camadas:
  → Se a API falha → usa regras heurísticas locais
  → Se as regras falham → retorna intenção "desconhecida"
"""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS

logger = logging.getLogger(__name__)

# Tenta importar OpenAI; se não estiver instalado, usa só o fallback
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    OPENAI_DISPONIVEL = True
except ImportError:
    OPENAI_DISPONIVEL = False
    logger.warning("Biblioteca openai não instalada. Usando fallback heurístico.")
except Exception as e:
    OPENAI_DISPONIVEL = False
    logger.warning(f"Erro ao inicializar OpenAI: {e}. Usando fallback heurístico.")


# ─────────────────────────────────────────────────────────────────────────────
# ESTRUTURA DE INTENT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Intent:
    """
    Representa a intenção interpretada de uma mensagem do usuário.

    tipo → uma das intenções reconhecidas:
      - consultar_produto   → usuário pergunta sobre produto específico
      - listar_estoque      → usuário quer ver todo o estoque
      - registrar_venda     → usuário informa que vendeu algo
      - ver_historico       → usuário quer ver vendas passadas
      - ajuda               → usuário pede ajuda ou está confuso
      - desconhecida        → não foi possível interpretar
    """
    tipo: str
    produto: Optional[str] = None
    quantidade: Optional[int] = None
    confianca: float = 1.0          # 0.0 a 1.0
    mensagem_original: str = ""
    via_ia: bool = True             # True = GPT-4o, False = fallback heurístico
    extras: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT DE SISTEMA (Prompt Engineering)
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Você é o interpretador de linguagem natural de um sistema de controle de estoque.
Sua única função é classificar mensagens de usuários em intenções estruturadas.

INTENÇÕES POSSÍVEIS:
- consultar_produto  → perguntas sobre produto específico (ex: "tem camisa?", "quantas bolsas?")
- listar_estoque     → pedir visão geral do estoque (ex: "mostrar tudo", "o que tem?", "estoque")
- registrar_venda    → registrar que uma venda ocorreu (ex: "vendi 2 calças", "saiu 1 tênis")
- ver_historico      → pedir histórico de vendas (ex: "vendas de hoje", "o que vendi?")
- ajuda              → pedido de ajuda ou dúvida sobre o sistema
- desconhecida       → impossível classificar com segurança

REGRAS OBRIGATÓRIAS:
1. Responda APENAS com JSON válido, sem markdown, sem texto extra.
2. Nunca invente produtos. Extraia somente o que o usuário disse.
3. Para "registrar_venda", tente extrair produto E quantidade.
4. Se a quantidade não for mencionada, omita o campo (não coloque null).
5. Seja tolerante com gírias, abreviações e erros de digitação.
6. Nomes de produtos devem estar no singular e em minúsculas.
7. "confianca" deve refletir o quão certo você está (0.0 a 1.0).

FORMATO DE RESPOSTA:
{
  "tipo": "<intenção>",
  "produto": "<nome do produto ou null>",
  "quantidade": <número inteiro ou null>,
  "confianca": <float entre 0.0 e 1.0>
}

EXEMPLOS:
Usuário: "tem camisa?"
{"tipo":"consultar_produto","produto":"camisa","quantidade":null,"confianca":0.98}

Usuário: "vendi 3 calças jeans"
{"tipo":"registrar_venda","produto":"calça","quantidade":3,"confianca":0.95}

Usuário: "mostra o estoque todo"
{"tipo":"listar_estoque","produto":null,"quantidade":null,"confianca":0.99}

Usuário: "quero ver as vendas de hoje"
{"tipo":"ver_historico","produto":null,"quantidade":null,"confianca":0.92}

Usuário: "blablabla xyzabc"
{"tipo":"desconhecida","produto":null,"quantidade":null,"confianca":0.10}
"""


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DE IA — GPT-4o
# ─────────────────────────────────────────────────────────────────────────────

def _chamar_gpt(mensagem: str) -> Optional[dict]:
    """
    Envia a mensagem ao GPT-4o e retorna o JSON interpretado.
    Retorna None em caso de falha.
    """
    if not OPENAI_DISPONIVEL:
        return None

    try:
        resposta = _openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": mensagem},
            ],
        )
        texto = resposta.choices[0].message.content.strip()
        logger.debug(f"GPT-4o resposta bruta: {texto}")
        return json.loads(texto)

    except json.JSONDecodeError as e:
        logger.error(f"GPT-4o retornou JSON inválido: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro na chamada GPT-4o: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK HEURÍSTICO — regras locais sem API
# ─────────────────────────────────────────────────────────────────────────────

# Palavras-chave por intenção
_PALAVRAS_ESTOQUE   = ["estoque", "tudo", "todos", "listar", "mostrar", "produtos", "inventário"]
_PALAVRAS_VENDA     = ["vendi", "vendeu", "vendemos", "saiu", "registrar venda", "baixar", "saíram", "foi"]
_PALAVRAS_HISTORICO = ["histórico", "vendas", "o que vendi", "relatório", "lista de vendas"]
_PALAVRAS_AJUDA     = ["ajuda", "help", "como", "o que você faz", "comandos", "?"]

# Produtos conhecidos (espelho simplificado do banco)
_PRODUTOS_CONHECIDOS = [
    "camisa", "calça", "bolsa", "tênis", "boné", "meia", "jaqueta", "sandália"
]


def _fallback_heuristico(mensagem: str) -> Intent:
    """
    Tenta classificar a mensagem usando regras simples.
    Usado quando a API OpenAI não está disponível.
    """
    texto = mensagem.lower().strip()

    # Detecta intenção de listar estoque
    for palavra in _PALAVRAS_ESTOQUE:
        if palavra in texto:
            return Intent(tipo="listar_estoque", via_ia=False, confianca=0.75, mensagem_original=mensagem)

    # Detecta histórico de vendas
    for palavra in _PALAVRAS_HISTORICO:
        if palavra in texto:
            return Intent(tipo="ver_historico", via_ia=False, confianca=0.75, mensagem_original=mensagem)

    # Detecta pedido de ajuda
    for palavra in _PALAVRAS_AJUDA:
        if palavra in texto:
            return Intent(tipo="ajuda", via_ia=False, confianca=0.80, mensagem_original=mensagem)

    # Detecta venda
    for palavra in _PALAVRAS_VENDA:
        if palavra in texto:
            produto = _extrair_produto(texto)
            quantidade = _extrair_quantidade(texto)
            return Intent(
                tipo="registrar_venda",
                produto=produto,
                quantidade=quantidade,
                via_ia=False,
                confianca=0.70,
                mensagem_original=mensagem,
            )

    # Detecta consulta de produto específico
    for produto in _PRODUTOS_CONHECIDOS:
        if produto in texto:
            return Intent(
                tipo="consultar_produto",
                produto=produto,
                via_ia=False,
                confianca=0.70,
                mensagem_original=mensagem,
            )

    # Não reconheceu
    return Intent(tipo="desconhecida", via_ia=False, confianca=0.10, mensagem_original=mensagem)


def _extrair_produto(texto: str) -> Optional[str]:
    """Busca o nome de um produto conhecido no texto."""
    for produto in _PRODUTOS_CONHECIDOS:
        if produto in texto:
            return produto
    return None


def _extrair_quantidade(texto: str) -> Optional[int]:
    """Extrai o primeiro número inteiro encontrado no texto."""
    numeros = re.findall(r'\b(\d+)\b', texto)
    if numeros:
        return int(numeros[0])
    # Tenta números por extenso (básico)
    mapa = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "quatro": 4,
            "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10}
    for palavra, valor in mapa.items():
        if palavra in texto:
            return valor
    return None


# ─────────────────────────────────────────────────────────────────────────────
# VALIDAÇÃO PÓS-PROCESSAMENTO
# ─────────────────────────────────────────────────────────────────────────────

_TIPOS_VALIDOS = {
    "consultar_produto", "listar_estoque", "registrar_venda",
    "ver_historico", "ajuda", "desconhecida"
}


def _validar_resposta_ia(dados: dict) -> Optional[Intent]:
    """
    Valida e converte o dicionário retornado pela IA em um Intent seguro.
    Retorna None se a resposta for inválida.
    """
    tipo = dados.get("tipo", "").strip().lower()
    if tipo not in _TIPOS_VALIDOS:
        logger.warning(f"Tipo de intenção inválido retornado pela IA: '{tipo}'")
        return None

    # Quantidade: aceita apenas inteiros positivos
    quantidade = dados.get("quantidade")
    if quantidade is not None:
        try:
            quantidade = int(quantidade)
            if quantidade <= 0:
                quantidade = None
        except (ValueError, TypeError):
            quantidade = None

    # Produto: limpa string
    produto = dados.get("produto")
    if isinstance(produto, str):
        produto = produto.strip().lower() or None

    confianca = float(dados.get("confianca", 1.0))
    confianca = max(0.0, min(1.0, confianca))

    return Intent(
        tipo=tipo,
        produto=produto,
        quantidade=quantidade,
        confianca=confianca,
        via_ia=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# INTERFACE PÚBLICA
# ─────────────────────────────────────────────────────────────────────────────

def interpretar(mensagem: str) -> Intent:
    """
    Ponto de entrada principal do módulo de IA.
    Recebe texto do usuário e retorna um Intent estruturado.

    Estratégia:
      1. Tenta GPT-4o → valida resposta
      2. Se falhar → usa fallback heurístico
    """
    mensagem = mensagem.strip()
    if not mensagem:
        return Intent(tipo="desconhecida", mensagem_original=mensagem)

    logger.info(f"Interpretando mensagem: '{mensagem}'")

    # ── Camada 1: GPT-4o ──────────────────────────────────────────────────
    dados_ia = _chamar_gpt(mensagem)
    if dados_ia:
        intent = _validar_resposta_ia(dados_ia)
        if intent:
            intent.mensagem_original = mensagem
            logger.info(f"IA retornou: tipo={intent.tipo}, produto={intent.produto}, qtd={intent.quantidade}, confiança={intent.confianca:.2f}")
            return intent
        logger.warning("Resposta da IA inválida após validação.")

    # ── Camada 2: Fallback heurístico ────────────────────────────────────
    logger.info("Usando fallback heurístico.")
    intent = _fallback_heuristico(mensagem)
    intent.mensagem_original = mensagem
    return intent
