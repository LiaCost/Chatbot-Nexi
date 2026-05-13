import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)


#Estoque

def consultar_estoque(codigo_produto):
    """Retorna nome, quantidade e mínimo de um produto pelo código."""
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Produto {codigo: $codigo})-[:TEM_ESTOQUE]->(e:Estoque)
            RETURN p.nome AS nome, e.quantidade AS quantidade, e.minimo AS minimo
        """, codigo=codigo_produto)
        return result.single()


def alertas_estoque_minimo():
    """Retorna todos os produtos com quantidade abaixo do mínimo."""
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Produto)-[:TEM_ESTOQUE]->(e:Estoque)
            WHERE e.quantidade < e.minimo OR e.quantidade < 0
            RETURN p.nome AS produto, e.quantidade AS atual, e.minimo AS minimo
            ORDER BY e.quantidade ASC
        """)
        return result.data()


def atualizar_estoque(codigo_produto, nova_quantidade):
    """Atualiza a quantidade em estoque de um produto."""
    with driver.session() as session:
        session.run("""
            MATCH (p:Produto {codigo: $codigo})-[:TEM_ESTOQUE]->(e:Estoque)
            SET e.quantidade = $quantidade
        """, codigo=codigo_produto, quantidade=nova_quantidade)


#Vendas

def registrar_venda(nome_cliente, codigo_produto, quantidade, data):
    """Registra uma venda e desconta do estoque automaticamente."""
    with driver.session() as session:
        session.run("""
            MERGE (c:Cliente {nome: $cliente})
            MATCH (p:Produto {codigo: $codigo})-[:TEM_ESTOQUE]->(e:Estoque)
            CREATE (v:Venda {data: $data, quantidade: $quantidade})
            CREATE (c)-[:REALIZOU]->(v)
            CREATE (v)-[:INCLUI {quantidade: $quantidade}]->(p)
            SET e.quantidade = e.quantidade - $quantidade
        """, cliente=nome_cliente, codigo=codigo_produto,
             quantidade=quantidade, data=data)


def historico_cliente(nome_cliente):
    """Retorna todas as compras de um cliente."""
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Cliente {nome: $nome})-[:REALIZOU]->(v:Venda)-[:INCLUI]->(p:Produto)
            RETURN p.nome AS produto, v.quantidade AS quantidade, v.data AS data
            ORDER BY v.data DESC
        """, nome=nome_cliente)
        return result.data()


#Fornecedores

def consultar_fornecedor(codigo_produto):
    """Retorna o fornecedor de um produto pelo código."""
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Produto {codigo: $codigo})-[:FORNECIDO_POR]->(f:Fornecedor)
            RETURN f.nome AS fornecedor, f.contato AS contato
        """, codigo=codigo_produto)
        return result.single()



def produtos_mais_vendidos(limite=10):
    """Retorna os produtos com maior volume de vendas."""
    with driver.session() as session:
        result = session.run("""
            MATCH (v:Venda)-[:INCLUI]->(p:Produto)
            RETURN p.nome AS produto, sum(v.quantidade) AS total
            ORDER BY total DESC
            LIMIT $limite
        """, limite=limite)
        return result.data()


def produtos_comprados_juntos(codigo_produto):
    """Retorna produtos frequentemente comprados junto com o produto informado."""
    with driver.session() as session:
        result = session.run("""
            MATCH (p1:Produto {codigo: $codigo})<-[:INCLUI]-(v1:Venda)<-[:REALIZOU]-(c:Cliente)
            MATCH (c)-[:REALIZOU]->(v2:Venda)-[:INCLUI]->(p2:Produto)
            WHERE p1 <> p2
            RETURN p2.nome AS produto, count(*) AS vezes
            ORDER BY vezes DESC
            LIMIT 5
        """, codigo=codigo_produto)
        return result.data()