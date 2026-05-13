"""
estoque.py — Camada de dados: controle de produtos e vendas
===========================================================
Responsável por TODA a lógica de negócio relacionada a estoque.
Implementa o padrão Repository: o restante do sistema nunca acessa
dados diretamente — sempre passa por aqui.

Design para substituição futura:
  - A classe SimulatedDB pode ser trocada por Neo4jDB sem alterar bot.py ou ia.py.
  - Basta implementar os mesmos métodos públicos na nova classe.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from config import USE_SIMULATION

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# MODELOS DE DADOS
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# BANCO DE DADOS SIMULADO (dicionário Python)
# ─────────────────────────────────────────────────────────────────────────────

class SimulatedDB:
    """
    Banco de dados em memória usando dicionários Python.
    Simula exatamente a estrutura que seria usada no Neo4j:
      - Nó :Produto {nome, quantidade, preco, categoria}
      - Nó :Venda   {produto, quantidade, total, data}
      - Relacionamento (:Venda)-[:REFERENCIA]->(:Produto)
    """

    def __init__(self) -> None:
        # Estoque inicial para demonstração
        self._produtos: dict[str, Produto] = {
            "camisa":   Produto("camisa",   25, 59.90,  "vestuário"),
            "calça":    Produto("calça",    18, 89.90,  "vestuário"),
            "bolsa":    Produto("bolsa",    12, 149.90, "acessórios"),
            "tênis":    Produto("tênis",    8,  219.90, "calçados"),
            "boné":     Produto("boné",     30, 39.90,  "acessórios"),
            "meia":     Produto("meia",     50, 14.90,  "vestuário"),
            "jaqueta":  Produto("jaqueta",  6,  299.90, "vestuário"),
            "sandália": Produto("sandália", 10, 99.90,  "calçados"),
        }
        self._vendas: list[Venda] = []

    # ── Produtos ────────────────────────────────────────────────────────────

    def get_produto(self, nome: str) -> Optional[Produto]:
        """Retorna um produto pelo nome (busca normalizada)."""
        return self._produtos.get(self._normalizar(nome))

    def listar_estoque(self) -> list[Produto]:
        """Retorna todos os produtos ordenados por nome."""
        return sorted(self._produtos.values(), key=lambda p: p.nome)

    def atualizar_quantidade(self, nome: str, nova_qtd: int) -> bool:
        """Atualiza a quantidade de um produto. Retorna False se não existir."""
        key = self._normalizar(nome)
        if key not in self._produtos:
            return False
        self._produtos[key].quantidade = nova_qtd
        return True

    # ── Vendas ───────────────────────────────────────────────────────────────

    def registrar_venda(self, produto: str, quantidade: int) -> Optional[Venda]:
        """
        Tenta registrar uma venda.
        Retorna a Venda criada em caso de sucesso, ou None se inválida.
        """
        key = self._normalizar(produto)
        p = self._produtos.get(key)

        if p is None:
            logger.warning(f"Tentativa de venda de produto inexistente: {produto}")
            return None

        if quantidade <= 0:
            logger.warning(f"Quantidade inválida na venda: {quantidade}")
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
        logger.info(f"Venda registrada: {quantidade}x {p.nome} — R$ {venda.preco_total:.2f}")
        return venda

    def historico_vendas(self, limite: int = 10) -> list[Venda]:
        """Retorna as últimas vendas registradas."""
        return self._vendas[-limite:]

    # ── Utilitários ──────────────────────────────────────────────────────────

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Padroniza o nome do produto para busca (minúsculas, sem espaços extras)."""
        return texto.strip().lower()

    def produto_existe(self, nome: str) -> bool:
        return self._normalizar(nome) in self._produtos

    def busca_aproximada(self, termo: str) -> list[str]:
        """
        Tenta encontrar produtos com nomes parecidos ao termo buscado.
        Útil para sugestões quando o produto exato não é encontrado.
        """
        termo_n = self._normalizar(termo)
        sugestoes = [
            nome for nome in self._produtos
            if termo_n in nome or nome in termo_n
        ]
        return sugestoes


# ─────────────────────────────────────────────────────────────────────────────
# INTERFACE PÚBLICA — usada por bot.py e ia.py
# ─────────────────────────────────────────────────────────────────────────────

class EstoqueService:
    """
    Serviço de estoque que abstrai o banco de dados subjacente.
    bot.py e ia.py interagem APENAS com esta classe.
    Para trocar para Neo4j: substitua self.db = SimulatedDB() por Neo4jDB().
    """

    def __init__(self) -> None:
        if USE_SIMULATION:
            self.db = SimulatedDB()
            logger.info("EstoqueService iniciado com banco simulado.")
        else:
            # Ponto de extensão: importar e usar Neo4jDB aqui
            raise NotImplementedError("Neo4j real ainda não implementado. Configure USE_SIMULATION=True.")

    # ── Consultas ────────────────────────────────────────────────────────────

    def consultar_produto(self, nome: str) -> dict:
        """
        Consulta um produto pelo nome.
        Retorna dicionário com status e dados do produto.
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

        # Produto não encontrado — tenta sugestões
        sugestoes = self.db.busca_aproximada(nome)
        return {
            "encontrado": False,
            "nome_buscado": nome,
            "sugestoes": sugestoes,
        }

    def listar_todos(self) -> list[dict]:
        """Retorna lista completa do estoque em formato serializável."""
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
        """Retorna métricas gerais do estoque."""
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

    # ── Vendas ───────────────────────────────────────────────────────────────

    def registrar_venda(self, produto: str, quantidade: int) -> dict:
        """
        Registra uma venda com validação completa.
        Retorna dict com sucesso/erro e mensagem de contexto.
        """
        # Validação de quantidade
        if not isinstance(quantidade, int) or quantidade <= 0:
            return {"sucesso": False, "erro": "quantidade_invalida", "quantidade": quantidade}

        # Verifica existência antes de tentar registrar
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

        # Tudo validado — registra
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
        """Retorna histórico de vendas formatado."""
        return [
            {
                "produto": v.produto,
                "quantidade": v.quantidade,
                "total": v.preco_total,
                "data": v.data,
            }
            for v in self.db.historico_vendas()
        ]


# Instância única compartilhada pelo sistema (Singleton)
estoque_service = EstoqueService()
