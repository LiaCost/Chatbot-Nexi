import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)


def importar_lote(tx, registros):
    tx.run("""
        UNWIND $registros AS row
        MERGE (ct:Categoria {nome: coalesce(row.categoria, "N/D")})
        MERGE (f:Fornecedor {nome: "A Definir", contato: "N/D"})
        MERGE (p:Produto {codigo: row.codigo})
        SET p.nome = row.nome, p.unidade = row.unidade, p.ean = row.ean
        MERGE (p)-[:PERTENCE_A]->(ct)
        MERGE (p)-[:FORNECIDO_POR]->(f)
        MERGE (e:Estoque {produto_codigo: row.codigo})
        SET e.quantidade = row.quantidade, e.minimo = row.minimo
        MERGE (p)-[:TEM_ESTOQUE]->(e)
    """, registros=registros)


def importar(caminho_xlsx="banco/pivot (5).xlsx", tamanho_lote=50):
    df = pd.read_excel(caminho_xlsx, header=3)
    df = df.dropna(subset=["Código do Produto"])

    total = len(df)
    print(f"{total} produtos encontrados. Importando...")

    registros = [
        {
            "categoria": str(row["Família de Produto"]),
            "codigo": str(row["Código do Produto"]),
            "nome": str(row["Descrição (completa)"]),
            "unidade": str(row["Unidade"]),
            "ean": str(row["Código EAN (GTIN)"]),
            "quantidade": float(row["Soma de Quantidade"]),
            "minimo": float(row["Soma de Estoque Mínimo"])
        }
        for _, row in df.iterrows()
    ]

    erros = 0
    importados = 0

    with driver.session() as session:
        for i in range(0, total, tamanho_lote):
            lote = registros[i:i + tamanho_lote]
            try:
                session.execute_write(importar_lote, lote)
                importados += len(lote)
                print(f"  {importados}/{total} produtos importados...", end="\r")
            except Exception as e:
                erros += len(lote)
                print(f"\n  Erro no lote {i//tamanho_lote + 1}: {e}")

    print(f"\nConcluído. {importados} importados, {erros} erros.")


if __name__ == "__main__":
    importar()