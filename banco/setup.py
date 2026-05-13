import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def setup_banco():
    with driver.session() as session:
        session.run("CREATE INDEX produto_codigo IF NOT EXISTS FOR (p:Produto) ON (p.codigo)")
        session.run("CREATE INDEX cliente_nome IF NOT EXISTS FOR (c:Cliente) ON (c.nome)")
        session.run("CREATE INDEX fornecedor_nome IF NOT EXISTS FOR (f:Fornecedor) ON (f.nome)")
        print("Banco configurado e pronto.")

if __name__ == "__main__":
    setup_banco()