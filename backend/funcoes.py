from carregar_estoque import carregar_estoque

# Carrega os dados reais da planilha
estoque = carregar_estoque()

# Função 1 — Consultar Estoque
def consultar_estoque(codigo):
    if codigo in estoque:
        produto = estoque[codigo]
        return f"Produto: {produto['nome']} | Quantidade: {produto['quantidade']} {produto['unidade']}"
    else:
        return f"Produto '{codigo}' não encontrado no estoque."

# Função 2 — Registrar Venda
def registrar_venda(codigo, quantidade):
    if codigo not in estoque:
        return f"Produto '{codigo}' não encontrado."
    if estoque[codigo]["quantidade"] < quantidade:
        return f"Estoque insuficiente. Temos apenas {estoque[codigo]['quantidade']} unidades."
    estoque[codigo]["quantidade"] -= quantidade
    return f"Venda registrada! {quantidade} unidade(s) de {estoque[codigo]['nome']} vendida(s)."

# Função 3 — Alerta de Estoque Mínimo
def alertar_estoque_minimo():
    alertas = []
    for codigo, produto in estoque.items():
        try:
            quantidade = float(produto["quantidade"] or 0)
            minimo = float(produto["estoque_minimo"] or 0)
            if minimo > 0 and quantidade < minimo:
                alertas.append(f"{produto['nome']} | Atual: {quantidade} | Mínimo: {minimo}")
        except:
            pass
    return alertas

# Testes
print(consultar_estoque("PRD00017"))
print(registrar_venda("PRD00017", 5))
print("\n--- ALERTAS DE ESTOQUE ---")
for alerta in alertar_estoque_minimo():
    print(alerta)