#Criação do dicionarios 
estoque = {

    "Bolsas" : 4,
    "Camisa" : 10,
    "Calça" : 2,
    "Garrafinha" : 9

}

fornecedores = {
    "Camisa" : "Renner",
    "Meia" : "Lupo",
    "Chinelo": "Havaianas"
}

#1° Função consultar_estoque

def consultar_estoque(produto):
    if produto in estoque:
        quantidade = estoque[produto]
        return f"Temos {quantidade} unidades de {produto} no estoque."
    else:
        return f"Produto '{produto}' não encontrado no estoque."
    
#testes
print(consultar_estoque("Camisa"))
print(consultar_estoque("Garrafinha"))
print(consultar_estoque("Meia"))

#2° Função registrar_venda

def registrar_venda(produto, quantidade):
    if produto not in estoque:
        return f"Produto '{produto}' não encontrado."
    
    if estoque[produto] < quantidade:
        return f"Estoque insuficiente. Temos apenas {estoque[produto]} unidades de {produto}."
    
    estoque[produto] -= quantidade
    return f"Venda registrada! {quantidade} unidades de {produto} vendidas."

#testes
print(registrar_venda("Camisa", 3))
print(registrar_venda("Garrafinha", 15))
print(registrar_venda("Meia", 2))


#3° Função buscar_fornecedor
def buscar_fornecedor (produto):
     if produto in fornecedores:
        fornecedor = fornecedores[produto]
        return f"O fornecedor de {produto} é: {fornecedor}"
     else:
        return f"Fornecedor de {produto} não encontrado."

#testes   
print(buscar_fornecedor("Meia"))
print(buscar_fornecedor("Chinelo"))
print(buscar_fornecedor("Couro"))