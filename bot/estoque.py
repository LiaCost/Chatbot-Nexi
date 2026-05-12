"""
estoque.py — Controle de estoque SEM Excel
==========================================
Estoque mantido em memória.
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
    "carvão": {
        "nome": "Carvão",
        "categoria": "Utilidades",
        "quantidade": 8,
        "estoque_minimo": 2,
    },
}


# ===============================
# SERVIÇO DE ESTOQUE
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
# INSTÂNCIA GLOBAL
# ===============================

estoque_service = EstoqueService()

