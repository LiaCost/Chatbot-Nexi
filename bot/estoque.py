"""
Estoque mantido em memoria.
"""

from typing import Optional

# ===============================
# ESTOQUE LOCAL
# ===============================

_produtos = {
    "heineken": {
        "nome": "Heineken",
        "categoria": "Cervejas",
        "quantidade": 10,
        "estoque_minimo": 3,
    },
    "skol": {
        "nome": "Skol",
        "categoria": "Cervejas",
        "quantidade": 0,
        "estoque_minimo": 5,
    },
    "red label": {
        "nome": "Red Label",
        "categoria": "Whisky",
        "quantidade": 4,
        "estoque_minimo": 2,
    },
    "carvao": {
        "nome": "Carvao",
        "categoria": "Utilidades",
        "quantidade": 8,
        "estoque_minimo": 2,
    },
}


# ===============================
# SERVICO DE ESTOQUE
# ===============================

class EstoqueService:

    def buscar_produto(self, termo: str) -> Optional[dict]:
        termo = termo.lower().strip()

        # busca exata
        if termo in _produtos:
            return _produtos[termo]

        # busca parcial
        for chave, produto in _produtos.items():
            if termo in chave:
                return produto

        return None

    def buscar_varios(self, termo: str, limite: int = 5):
        termo = termo.lower()
        encontrados = [
            p for k, p in _produtos.items()
            if termo in k
        ]
        return encontrados[:limite]

    def listar_todos(self):
        return list(_produtos.values())

    def listar_por_categoria(self, categoria: str):
        categoria = categoria.lower()
        return [
            p for p in _produtos.values()
            if categoria in p["categoria"].lower()
        ]

    def produtos_sem_estoque(self):
        return [p for p in _produtos.values() if p["quantidade"] <= 0]

    def produtos_abaixo_minimo(self):
        return [
            p for p in _produtos.values()
            if p["quantidade"] < p["estoque_minimo"]
        ]

    def resumo(self):
        todos = self.listar_todos()
        return {
            "total_produtos": len(todos),
            "sem_estoque": len(self.produtos_sem_estoque()),
            "abaixo_minimo": len(self.produtos_abaixo_minimo()),
            "categorias": self.categorias(),
        }

    def categorias(self):
        return sorted({p["categoria"] for p in _produtos.values()})


# ===============================
# INSTANCIA GLOBAL
# ===============================

estoque_service = EstoqueService()

"""
estoque.py -- Camada de dados: controle de produtos e vendas
Responsavel por TODA a logica de negocio relacionada a estoque.
Implementa o padrao Repository: o restante do sistema nunca acessa
dados diretamente -- sempre passa por aqui.

Design para substituicao futura:
  - A classe SimulatedDB pode ser trocada por Neo4jDB sem alterar bot.py ou ia.py.
  - Basta implementar os mesmos metodos publicos na nova classe.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from config import USE_SIMULATION

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# MODELOS DE DADOS
# -----------------------------------------------------------------------------

@dataclass
class Produto:
    """Representa um produto no estoque."""
    nome: str
    quantidade: int
    preco_unitario: float
    categoria: str


@dataclass
class Venda:
    """Representa um registro de venda."""
    produto: str
    quantidade: int
    preco_total: float
    data: str = field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y %H:%M"))


# -----------------------------------------------------------------------------
# BANCO DE DADOS SIMULADO (dicionario Python)
# -----------------------------------------------------------------------------

class SimulatedDB:
    """
    Banco de dados em memoria usando dicionarios Python.
    Simula exatamente a estrutura que seria usada no Neo4j:
      - No :Produto {nome, quantidade, preco, categoria}
      - No :Venda   {produto, quantidade, total, data}
      - Relacionamento (:Venda)-[:REFERENCIA]->(:Produto)
    """

    def __init__(self) -> None:
        # Estoque inicial para demonstracao
        self._produtos: dict[str, Produto] = {
            "camisa":   Produto("camisa",   25, 59.90,  "vestuario"),
            "calca":    Produto("calca",    18, 89.90,  "vestuario"),
            "bolsa":    Produto("bolsa",    12, 149.90, "acessorios"),
            "tenis":    Produto("tenis",    8,  219.90, "calcados"),
            "bone":     Produto("bone",     30, 39.90,  "acessorios"),
            "meia":     Produto("meia",     50, 14.90,  "vestuario"),
            "jaqueta":  Produto("jaqueta",  6,  299.90, "vestuario"),
            "sandalia": Produto("sandalia", 10, 99.90,  "calcados"),
        }
        self._vendas: list[Venda] = []

    # -- Produtos ------------------------------------------------------------

    def get_produto(self, nome: str) -> Optional[Produto]:
        """Retorna um produto pelo nome (busca normalizada)."""
        return self._produtos.get(self._normalizar(nome))

    def listar_estoque(self) -> list[Produto]:
        """Retorna todos os produtos ordenados por nome."""
        return sorted(self._produtos.values(), key=lambda p: p.nome)

    def atualizar_quantidade(self, nome: str, nova_qtd: int) -> bool:
        """Atualiza a quantidade de um produto. Retorna False se nao existir."""
        key = self._normalizar(nome)
        if key not in self._produtos:
            return False
        self._produtos[key].quantidade = nova_qtd
        return True

    # -- Vendas --------------------------------------------------------------

    def registrar_venda(self, produto: str, quantidade: int) -> Optional[Venda]:
        """
        Tenta registrar uma venda.
        Retorna a Venda criada em caso de sucesso, ou None se invalida.
        """
        key = self._normalizar(produto)
        p = self._produtos.get(key)

        if p is None:
            logger.warning(f"Tentativa de venda de produto inexistente: {produto}")
            return None

        if quantidade <= 0:
            logger.warning(f"Quantidade invalida na venda: {quantidade}")
            return None

        if p.quantidade < quantidade:
            logger.warning(f"Estoque insuficiente: {p.nome} tem {p.quantidade}, pedido {quantidade}")
            return None

        # Efetua a baixa no estoque
        p.quantidade -= quantidade

        # Registra a venda
        venda = Venda(
            produto=p.nome,
            quantidade=quantidade,
            preco_total=round(p.preco_unitario * quantidade, 2),
        )
        self._vendas.append(venda)
        logger.info(f"Venda registrada: {quantidade}x {p.nome} -- R$ {venda.preco_total:.2f}")
        return venda

    def historico_vendas(self, limite: int = 10) -> list[Venda]:
        """Retorna as ultimas vendas registradas."""
        return self._vendas[-limite:]

    # -- Utilitarios ---------------------------------------------------------

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Padroniza o nome do produto para busca (minusculas, sem espacos extras)."""
        return texto.strip().lower()

    def produto_existe(self, nome: str) -> bool:
        return self._normalizar(nome) in self._produtos

    def busca_aproximada(self, termo: str) -> list[str]:
        """
        Tenta encontrar produtos com nomes parecidos ao termo buscado.
        Util para sugestoes quando o produto exato nao e encontrado.
        """
        termo_n = self._normalizar(termo)
        sugestoes = [
            nome for nome in self._produtos
            if termo_n in nome or nome in termo_n
        ]
        return sugestoes


# -----------------------------------------------------------------------------
# INTERFACE PUBLICA -- usada por bot.py e ia.py
# -----------------------------------------------------------------------------

class EstoqueService:
    """
    Servico de estoque que abstrai o banco de dados subjacente.
    bot.py e ia.py interagem APENAS com esta classe.
    Para trocar para Neo4j: substitua self.db = SimulatedDB() por Neo4jDB().
    """

    def __init__(self) -> None:
        if USE_SIMULATION:
            self.db = SimulatedDB()
            logger.info("EstoqueService iniciado com banco simulado.")
        else:
            # Ponto de extensao: importar e usar Neo4jDB aqui
            raise NotImplementedError("Neo4j real ainda nao implementado. Configure USE_SIMULATION=True.")

    # -- Consultas -----------------------------------------------------------

    def consultar_produto(self, nome: str) -> dict:
        """
        Consulta um produto pelo nome.
        Retorna dicionario com status e dados do produto.
        """
        produto = self.db.get_produto(nome)

        if produto:
            return {
                "encontrado": True,
                "nome": produto.nome,
                "quantidade": produto.quantidade,
                "preco": produto.preco_unitario,
                "categoria": produto.categoria,
                "em_estoque": produto.quantidade > 0,
            }

        # Produto nao encontrado -- tenta sugestoes
        sugestoes = self.db.busca_aproximada(nome)
        return {
            "encontrado": False,
            "nome_buscado": nome,
            "sugestoes": sugestoes,
        }

    def listar_todos(self) -> list[dict]:
        """Retorna lista completa do estoque em formato serializavel."""
        return [
            {
                "nome": p.nome,
                "quantidade": p.quantidade,
                "preco": p.preco_unitario,
                "categoria": p.categoria,
                "em_estoque": p.quantidade > 0,
            }
            for p in self.db.listar_estoque()
        ]

    def estoque_resumo(self) -> dict:
        """Retorna metricas gerais do estoque."""
        produtos = self.db.listar_estoque()
        total_itens = sum(p.quantidade for p in produtos)
        sem_estoque = [p.nome for p in produtos if p.quantidade == 0]
        baixo_estoque = [p.nome for p in produtos if 0 < p.quantidade <= 5]
        return {
            "total_produtos": len(produtos),
            "total_itens": total_itens,
            "sem_estoque": sem_estoque,
            "baixo_estoque": baixo_estoque,
        }

    # -- Vendas --------------------------------------------------------------

    def registrar_venda(self, produto: str, quantidade: int) -> dict:
        """
        Registra uma venda com validacao completa.
        Retorna dict com sucesso/erro e mensagem de contexto.
        """
        # Validacao de quantidade
        if not isinstance(quantidade, int) or quantidade <= 0:
            return {"sucesso": False, "erro": "quantidade_invalida", "quantidade": quantidade}

        # Verifica existencia antes de tentar registrar
        info = self.consultar_produto(produto)
        if not info["encontrado"]:
            return {
                "sucesso": False,
                "erro": "produto_inexistente",
                "nome_buscado": produto,
                "sugestoes": info.get("sugestoes", []),
            }

        if info["quantidade"] < quantidade:
            return {
                "sucesso": False,
                "erro": "estoque_insuficiente",
                "produto": info["nome"],
                "disponivel": info["quantidade"],
                "solicitado": quantidade,
            }

        # Tudo validado -- registra
        venda = self.db.registrar_venda(produto, quantidade)
        if venda:
            return {
                "sucesso": True,
                "produto": venda.produto,
                "quantidade": venda.quantidade,
                "total": venda.preco_total,
                "data": venda.data,
                "estoque_restante": self.db.get_produto(produto).quantidade,
            }

        return {"sucesso": False, "erro": "falha_interna"}

    def historico_vendas(self) -> list[dict]:
        """Retorna historico de vendas formatado."""
        return [
            {
                "produto": v.produto,
                "quantidade": v.quantidade,
                "total": v.preco_total,
                "data": v.data,
            }
            for v in self.db.historico_vendas()
        ]


# Instancia unica compartilhada pelo sistema (Singleton)
estoque_service = EstoqueService()